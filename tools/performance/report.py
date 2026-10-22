"""Recompute the diagnostic summary from original hashed process output.

Stored admission decisions are cross-checked, not accepted as timing evidence.
Profiles and failed attempts never enter primary medians or speedup ratios.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
import sys

from tools.baseline.data import timing_totals
from tools.cuda.compare import compare
from .capture import digest, load_attempt, write_json
from .contract import BASELINE_SIDES, CHECKPOINTS, SERIES, SIDES, SOURCE_COMMIT, VERSION, allocation, arguments
from .study import clean


def metrics(process: dict, document: dict, kind: str) -> dict:
    """Retain both completed solver work and the different invocation boundary."""
    totals = timing_totals({"result": document, "kind": kind})
    if totals is None:
        return {}
    total = totals["total_s"]
    steps = document["measurements"]["steps"]
    simulated = int(document["completed_steps"]) * document["input"]["configuration"]["numerical"]["fixed_timestep_s"]
    result = {"solver_s": total, "invocation_s": process["wall_s"],
              "construction_s": document["measurements"]["solver_construction_s"],
              "teardown_s": document["measurements"]["solver_teardown_s"],
              "simulated_s": simulated, "solver_real_time_factor": simulated / total if total else None,
              "invocation_real_time_factor": simulated / process["wall_s"] if process["wall_s"] else None,
              "first_step_s": steps[0]["total_s"] if steps else None,
              "remaining_step_median_s": statistics.median(s["total_s"] for s in steps[1:]) if len(steps) > 1 else None}
    if kind == "profile":
        result.update(stages_s=totals["stages_s"], residual_s=total - sum(totals["stages_s"].values()))
        result["windows"] = {}
        for name, subset in (("early_1_120", steps[:120]), ("late_241_480", steps[240:480])):
            if subset:
                result["windows"][name] = {"steps": len(subset), "solver_s": sum(s["total_s"] for s in subset),
                    "stages_s": {key: sum(s["stages"][key] for s in subset) for key in totals["stages_s"]}}
    return result


def attempt(directory: Path, relative: str, *, series: str, particles: int,
            kind: str, observation: bool = True, steps: int = 480) -> tuple[dict, dict | None]:
    target = directory / relative
    process, document = load_attempt(target)
    assessment = json.loads((target / "assessment.json").read_bytes())
    admitted = clean(process, document, series=series, steps=steps, observation=observation, particles=particles)
    if assessment["series"] != series or assessment["kind"] != kind or assessment["particles"] != particles:
        raise ValueError("retained attempt classification differs")
    campaign = json.loads((directory / "campaign.json").read_bytes())
    if process["command"][0] != campaign["binary"]:
        raise ValueError("attempt selected a different binary")
    if assessment["binary_sha256"] != campaign["binary_sha256"]:
        raise ValueError("attempt binary hash differs")
    expected = arguments(process["command"][2], series, steps=steps, observation=observation, kind=kind)
    if process["command"][1:] != expected:
        raise ValueError("attempt arguments differ from the declared request")
    if assessment["admitted"] and not admitted:
        raise ValueError("stored admission contradicts raw process result")
    result = {"file": relative, "admitted": admitted, "exit_code": process["exit_code"],
              "timed_out": process["timed_out"], "status": document.get("status") if document else None,
              "completed_steps": document.get("completed_steps") if document else None}
    if document and kind != "warmup":
        result["metrics"] = metrics(process, document, kind)
    return result, document


def report(directory: Path, source: Path) -> dict:
    """Recheck source, qualification, all observations and complete sample sets."""
    campaign = json.loads((directory / "campaign.json").read_bytes())
    if campaign["policy"] != VERSION or campaign["source"]["base_commit"] != SOURCE_COMMIT:
        raise ValueError("unknown diagnosis revision")
    for relative, expected in campaign["source"]["files_sha256"].items():
        target = (source / relative).resolve()
        if not target.is_relative_to(source.resolve()) or digest(target.read_bytes()) != expected:
            raise ValueError("local source does not reproduce the assessed export")
    for relative, expected in campaign["inputs_sha256"].items():
        target = (directory / relative).resolve()
        if not target.is_relative_to(directory.resolve()) or digest(target.read_bytes()) != expected:
            raise ValueError("retained scene/configuration changed")
    if digest((directory / "protocol.md").read_bytes()) != campaign["protocol_sha256"]:
        raise ValueError("retained protocol changed")
    manifest = json.loads((source / "reference/manifest.json").read_bytes())
    golden = json.loads((source / manifest["cases"][0]["golden"]).read_bytes())
    qualification = {}
    for series in SERIES:
        process, document = load_attempt(directory / f"qualification/{series}")
        agreement = compare(golden, document, exact=True) if document else {"passed": False}
        passed = process["exit_code"] == 0 and not process["timed_out"] and agreement["passed"]
        if not passed:
            raise ValueError("retained small golden qualification fails")
        qualification[series] = True
    rows, controls = [], {}
    exact_comparisons = 0
    for series in SERIES:
        for side in BASELINE_SIDES:
            particles = side ** 3
            prefix = f"baseline/{series}/{particles:06}"
            warmup, document = attempt(directory, prefix + "/warmup", series=series,
                                        particles=particles, kind="warmup")
            expected = controls.get(side)
            if series == "serial-grid":
                case = next(c for c in manifest["cases"] if c["particles"] == particles)
                if case["golden"]:
                    expected = json.loads((source / case["golden"]).read_bytes())
            if warmup["admitted"] and expected is not None:
                passed = compare(expected, document, exact=True)["passed"]
                exact_comparisons += 1
                if not passed:
                    raise ValueError("warm-up disagrees with independent control")
            if series == "serial-grid" and warmup["admitted"]:
                controls[side] = document
            samples = []
            for index in range(1, 4):
                relative = f"{prefix}/sample-{index}"
                if not (directory / relative).is_dir():
                    continue
                summary, document = attempt(directory, relative, series=series, particles=particles, kind="sample")
                if summary["admitted"]:
                    if side not in controls or not compare(controls[side], document, exact=True)["passed"]:
                        raise ValueError("sample disagrees with fresh serial control")
                    exact_comparisons += 1
                samples.append(summary)
            profile, document = attempt(directory, prefix + "/profile", series=series,
                                         particles=particles, kind="profile")
            if profile["admitted"]:
                if side not in controls or not compare(controls[side], document, exact=True)["passed"]:
                    raise ValueError("profile disagrees with fresh serial control")
                exact_comparisons += 1
            primary = None
            if warmup["admitted"] and len(samples) == 3 and all(s["admitted"] for s in samples):
                totals = [s["metrics"]["solver_s"] for s in samples]
                primary = {"sample_totals_s": totals, "median_solver_s": statistics.median(totals),
                    "minimum_s": min(totals), "maximum_s": max(totals), "sample_standard_deviation_s": statistics.stdev(totals),
                    "median_invocation_s": statistics.median(s["metrics"]["invocation_s"] for s in samples),
                    "median_construction_s": statistics.median(s["metrics"]["construction_s"] for s in samples),
                    "median_teardown_s": statistics.median(s["metrics"]["teardown_s"] for s in samples),
                    "median_solver_real_time_factor": statistics.median(s["metrics"]["solver_real_time_factor"] for s in samples)}
            rows.append({"series": series, "particles": particles, "warmup": warmup,
                         "samples": samples, "profile": profile, "primary": primary})
    capacity = []
    for side in SIDES:
        target = directory / f"capacity/{side ** 3:06}"
        if not target.is_dir():
            continue
        admission = json.loads((target / "admission.json").read_bytes())
        if admission["allocation_model"] != allocation(side ** 3):
            raise ValueError("capacity allocation estimate differs from source model")
        item = {"particles": side ** 3, "admission": admission}
        for kind, steps in (("pilot", 4), ("core", 480), ("profile", 480)):
            if (target / kind).is_dir():
                item[kind], _ = attempt(directory, f"capacity/{side ** 3:06}/{kind}", series="cuda",
                    particles=side ** 3, kind="sample" if kind == "core" else kind, observation=False, steps=steps)
        if (target / "long-run-admission.json").exists():
            item["long_run_admission"] = json.loads((target / "long-run-admission.json").read_bytes())
        capacity.append(item)
    return {"schema_version": 1, "policy": VERSION, "source_commit": SOURCE_COMMIT,
            "binary_sha256": campaign["binary_sha256"], "small_goldens_exact": qualification,
            "baseline_exact_comparisons": exact_comparisons, "baseline": rows, "capacity": capacity}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = report(args.directory.resolve(), args.source.resolve())
        if args.output:
            write_json(args.output, result)
        else:
            print(json.dumps(result, indent=2, allow_nan=False))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Diagnosis report: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
