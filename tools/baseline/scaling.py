"""Collect serial-grid controls and explicit worker series from one release binary.

Exact snapshot equality qualifies this arithmetic-preserving implementation. Unequal
hashes reject acceptance; they never stand in for a numerical tolerance comparison.
Run on the primary PC as ``python3 -m tools.baseline.scaling collect NEW_DIRECTORY``.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import statistics
import subprocess
import sys

from . import main as baseline
from .data import POLICY, clean, compact_result, physical_document, read_json, require_exact, sha256

WORKERS = (1, 2, 4, 8, 12, 24)
CONTRACT = baseline.ROOT / "docs/project/development/milestones/02/scaling-protocol.md"
ENVIRONMENT_FIELDS = (
    "cpu_model", "architecture", "kernel", "os_release", "cpu_topology", "cpu_affinity",
    "rustc", "cargo", "profile", "rustflags", "scheduling_controls", "virtualisation",
)


def worker_sequence(workers: list[int]) -> None:
    """Require distinct, ascending counts with a one-worker scaling denominator."""
    if (not workers or workers[0] != 1 or workers != sorted(set(workers))
            or any(type(w) is not int or not 1 <= w <= 256 for w in workers)):
        raise ValueError("workers must be distinct ascending integers in 1..=256, starting at 1")


def report(directory: Path) -> tuple[dict, str]:
    """Recompute acceptance and ratios from hashed attempts, independently of saved summaries."""
    campaign = read_json(directory / "campaign.json")
    workers = campaign["workers"]
    worker_sequence(workers)
    names = ["serial-grid", *(f"workers-{w}" for w in workers)]
    if campaign["schema_version"] != 1 or campaign["collection_order"] != names:
        raise ValueError("unsupported scaling campaign or collection order")
    if sha256((directory / "protocol.md").read_bytes()) != campaign["protocol_sha256"]:
        raise ValueError("scaling protocol hash mismatch")
    default = campaign["default_probe"]
    if (default["exit_code"] != 0 or default["timed_out"] or default["interrupted"]
            or default["result"]["execution"] != {"mode": "threaded", "workers": campaign["default_workers"]}
            or campaign["default_workers"] not in workers):
        raise ValueError("default execution was not established or included")
    datasets, attempts = {}, {}
    serial = None
    for name, count in zip(names, [None, *workers], strict=True):
        path = directory / name
        baseline.report(path)
        dataset = read_json(path / "dataset.json")
        execution, identity = baseline.execution_settings("uniform-grid", count)
        if (dataset["backend"] != "uniform-grid" or dataset["interrupted"]
                or dataset.get("execution", {"mode": "serial"}) != execution):
            raise ValueError("execution setting or campaign completion differs")
        values = baseline.load_attempts(path, dataset)
        keys = [(a["particles"], a["kind"], a["index"]) for a in values]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate sample identity")
        for a in values:
            if (a["particles"] not in POLICY["particles"] or a["kind"] not in {"warmup", "sample", "profile"}
                    or a["index"] not in (range(1, 4) if a["kind"] == "sample" else [1])):
                raise ValueError("unexpected sample identity")
            if a.get("numerical_agreement") is False:
                raise ValueError("retained sample failed exact acceptance")
        correctness = read_json(path / "correctness.json")
        for result in [correctness, *(a["result"] for a in values if a["result"] is not None)]:
            if (result["backend"] != identity or result["metadata"]["backend"] != identity
                    or result.get("execution", {"mode": "serial"}) != execution
                    or result["metadata"]["debug_assertions"]
                    or result["metadata"]["build_revision"] != dataset["build_revision"]):
                raise ValueError("sample execution differs from requested workers")
        if serial is None:
            serial = dataset
            reference_correctness = physical_document(correctness, ignore_execution=True)
        else:
            for field in ("source", "binary_sha256", "build_revision", "policy", "manifest",
                          "manifest_sha256", "collector_files_sha256", "epq_base_commit"):
                if dataset[field] != serial[field]:
                    raise ValueError(f"scaling series differ in {field}")
            for field in ENVIRONMENT_FIELDS:
                if dataset["environment"][field] != serial["environment"][field]:
                    raise ValueError(f"scaling environment differs in {field}")
        require_exact(physical_document(correctness, ignore_execution=True), reference_correctness)
        # Recheck the full retained correctness result against the frozen golden.
        golden_case = dataset["manifest"]["cases"][1]
        golden_path = baseline.SIMULATOR / golden_case["golden"]
        if sha256(golden_path.read_bytes()) != golden_case["golden_sha256"]:
            raise ValueError("correctness golden changed")
        require_exact(physical_document(correctness, ignore_execution=True),
                      physical_document(read_json(golden_path), ignore_execution=True))
        datasets[name], attempts[name] = dataset, values
    rows = []
    for i, particles in enumerate(POLICY["particles"]):
        controls = [a for a in attempts["serial-grid"] if a["particles"] == particles
                    and a["kind"] == "warmup" and clean(a)]
        reference = physical_document(controls[0]["result"], ignore_execution=True) if len(controls) == 1 else None
        qualified = {}
        for name in names:
            values = [a for a in attempts[name] if a["particles"] == particles]
            checked = 0
            for a in values:
                if clean(a) and reference is not None:
                    require_exact(physical_document(a["result"], ignore_execution=True), reference,
                                  f"{name}/{particles}/{a['kind']}/{a['index']}")
                    checked += 1
            summary = datasets[name]["summaries"][i]
            primary = summary["primary"] if reference is not None else None
            qualified[name] = primary
            samples = [a["wall_s"] for a in values if a["kind"] == "sample" and clean(a)]
            speedup = scaling = efficiency = None
            if primary and qualified.get("serial-grid"):
                speedup = qualified["serial-grid"]["median_s"] / primary["median_s"]
            if name.startswith("workers-") and primary and qualified.get("workers-1"):
                scaling = qualified["workers-1"]["median_s"] / primary["median_s"]
                efficiency = scaling / int(name.removeprefix("workers-"))
            rows.append({"particles": particles, "series": name, "exact_complete_attempts": checked,
                         "primary": primary, "profile": summary["profile"],
                         "invocation_median_s": statistics.median(samples) if primary and len(samples) == 3 else None,
                         "serial_grid_speedup": speedup, "one_worker_scaling": scaling,
                         "requested_worker_efficiency": efficiency})
    result = {"schema_version": 1, "acceptance": "exact-binary32-including-signed-zero",
              "datasets_sha256": {name: sha256((directory / name / "dataset.json").read_bytes()) for name in names},
              "rows": rows}
    text = ["# CPU worker scaling on the primary PC", "",
            f"CPU: {serial['environment']['cpu_model']}; {serial['environment']['os_release']}.",
            f"Maelstrom: `{serial['source']['base_commit']}`; binary SHA-256: `{serial['binary_sha256']}`.",
            f"Available parallelism selected by Rust: {campaign['default_workers']}; inherited affinity: {serial['environment']['cpu_affinity']}.",
            f"Collection order: {', '.join(names)}. Each series uses ascending sizes and the unchanged `{POLICY['id']}` policy.", "",
            "All clean complete attempts must equal the same-size serial-grid warm-up exactly, including sign-sensitive",
            "snapshot hashes, physical identities, checkpoints, density audits, CFL diagnostics and completion.",
            "Each full 64-particle correctness result is also checked against its frozen golden.",
            "An unequal hash rejects acceptance; no tolerance is inferred from compact data.", "",
            "| Particles | Series | Median solver s | Min–max s | SD s | Updates/s | Median invocation s | vs serial grid | vs one worker | Efficiency | Exact attempts |",
            "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for row in rows:
        p = row["primary"]
        metrics = ([f"{p['median_s']:.6f}", f"{p['minimum_s']:.6f}–{p['maximum_s']:.6f}",
                    f"{p['sample_standard_deviation_s']:.6f}", f"{p['particle_updates_per_s']:,.0f}",
                    f"{row['invocation_median_s']:.6f}"] if p else ["unavailable"] * 5)
        ratios = [f"{row[key]:.3f}" if row[key] is not None else "unavailable"
                  for key in ("serial_grid_speedup", "one_worker_scaling", "requested_worker_efficiency")]
        text.append(f"| {row['particles']:,} | {row['series']} | " + " | ".join(metrics + ratios) + f" | {row['exact_complete_attempts']} |")
    text += ["", "Speedup divides the fresh serial-grid median by the selected median. Scaling divides the threaded",
             "one-worker median by that median; efficiency divides scaling by requested workers, not physical cores.",
             "Effective pool size equals the explicit request after successful construction; this does not guarantee simultaneous CPU service.",
             "The serial row's speedup is 1. Profiles, stage seconds/proportions/residuals and all partial attempts are retained",
             "in each series report and dataset. Profiles do not enter primary ratios. Invocation time includes setup, audits and output.",
             "One-time pool setup/teardown is outside solver timing; dispatch, barriers, validation and repeated allocation are inside.",
             "No fresh brute-force series was collected, so these results support no overall gain ratio against brute force.",
             "Fixed order, host load, scheduling and thermals remain confounders. Three samples do not establish significance.",
             "No memory measurement, larger-size campaign, physical-accuracy or universal scaling claim is made."]
    return result, "\n".join(text) + "\n"


def collect(directory: Path, workers: list[int]) -> None:
    """Preserve every attempted series and stop on interruption without replacing data."""
    worker_sequence(workers)
    if directory.exists():
        raise FileExistsError(directory)
    baseline.checked_manifest()
    build = baseline.prepare_build()
    binary = baseline.SIMULATOR / "target/release/maelstrom"
    case = baseline.checked_manifest()["cases"][1]
    args = baseline.solver_args(binary, case, "warmup", "uniform-grid") + ["--execution", "threaded"]
    probe = baseline.invoke(args)
    if not clean(dict(probe, kind="warmup")):
        raise ValueError("default worker probe failed")
    default = probe["result"]["execution"]["workers"]
    if default not in workers:
        raise ValueError(f"worker sequence must include the observed default ({default})")
    probe["result"] = compact_result(probe["result"])
    directory.mkdir(parents=True, exist_ok=False)
    protocol = CONTRACT.read_bytes()
    (directory / "protocol.md").write_bytes(protocol)
    names = ["serial-grid", *(f"workers-{w}" for w in workers)]
    baseline.write_json(directory / "campaign.json", {
        "schema_version": 1, "workers": workers, "default_workers": default,
        "default_probe": probe, "collection_order": names, "protocol_sha256": sha256(protocol),
    })
    for name, count in zip(names, [None, *workers], strict=True):
        print(f"Series: {name}", file=sys.stderr, flush=True)
        baseline.collect(directory / name, "uniform-grid", count, build=build)
        if read_json(directory / name / "dataset.json")["interrupted"]:
            raise ValueError("collection interrupted; no further series started")
    result, markdown = report(directory)
    baseline.write_json(directory / "scaling.json", result)
    (directory / "report.md").write_text(markdown, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["collect", "report"])
    parser.add_argument("directory", type=Path)
    parser.add_argument("--workers", type=int, nargs="+", default=list(WORKERS))
    args = parser.parse_args()
    try:
        directory = args.directory.resolve()
        if args.operation == "collect":
            collect(directory, args.workers)
        else:
            result, markdown = report(directory)
            if result != read_json(directory / "scaling.json"):
                raise ValueError("stored scaling summary differs from raw evidence")
            print(markdown, end="")
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(f"scaling: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
