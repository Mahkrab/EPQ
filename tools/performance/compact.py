"""Measure the compact-row experiment against an independently retained executable.

Old observations remain immutable. Candidate worktree hashes, paired samples and
bounded capacity diagnostics get a new identity and never replace the baseline.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import statistics
import sys

from tools.cuda.compare import compare
from .capture import digest, invoke, load_attempt, utc, write_json
from .contract import BASELINE_SIDES, SIDES, GIB, arguments
from .report import metrics
from .study import memory


def capacity_estimate(particles: int) -> int:
    """Bound the initial lattice's rows, not arbitrary evolved/dense input."""
    if type(particles) is not int or not 1 <= particles <= 1_000_000:
        raise ValueError("unsupported capacity particle count")
    return 88 * particles + 32 * (1 << (particles - 1).bit_length()) + 96 + 8 * (particles + 1) + 744 * particles


def qualified(process: dict, document: dict | None, *, particles: int, steps: int,
              observation: bool, revision: str) -> bool:
    if (process.get("exit_code") != 0 or process.get("timed_out") or process.get("interrupted")
            or document is None or document.get("status") != "completed" or document.get("failures")):
        return False
    checkpoints = ["0", "1", "120", "240", "480"] if observation else []
    return (document["execution"] == {"mode": "cuda", "device": 0, "threads": 128}
            and document["backend"] == document["metadata"]["backend"] == "cuda-uniform-grid-pbf-binary32-8-jacobi-v1"
            and document["metadata"]["build_revision"] == revision and not document["metadata"]["debug_assertions"]
            and document["request"] == {"steps": str(steps), "checkpoints": checkpoints}
            and document["completed_steps"] == str(steps)
            and [s["completed_steps"] for s in document["steps"]] == [str(i) for i in range(1, steps + 1)]
            and all(not s["warning"] for s in document["steps"])
            and [c["snapshot"]["completed_steps"] for c in document["checkpoints"]] == checkpoints
            and len(document["input"]["particles"]) == particles
            and len(document["final_snapshot"]["particles"]) == particles)


def verify(root: Path, campaign: dict) -> None:
    for name, identity in campaign["implementations"].items():
        source = Path(identity["source_directory"])
        for relative, expected in identity["source"]["files_sha256"].items():
            path = (source / relative).resolve()
            if not path.is_relative_to(source) or digest(path.read_bytes()) != expected:
                raise ValueError(f"{name} source changed")
        if digest(Path(identity["binary"]).read_bytes()) != identity["binary_sha256"]:
            raise ValueError(f"{name} binary changed")
    if digest((root / "protocol.md").read_bytes()) != campaign["protocol_sha256"]:
        raise ValueError("prepared protocol changed")
    for name, expected in campaign["collector_sha256"].items():
        if digest((Path(__file__).parent / name).read_bytes()) != expected:
            raise ValueError("prepared collector changed")


def prepare(candidate: Path, identity: Path, baseline: Path, protocol: Path, root: Path,
            control: Path | None = None, control_identity: Path | None = None) -> None:
    old = json.loads((baseline / "campaign.json").read_bytes())
    candidate_identity = json.loads(identity.read_bytes())
    root.mkdir(parents=True, exist_ok=False)
    (root / "protocol.md").write_bytes(protocol.read_bytes())
    implementations = {"bitset": {"source": old["source"], "source_directory": old["source_directory"],
                       "binary": old["binary"], "binary_sha256": old["binary_sha256"], "revision": old["build_revision"]},
                       "compact": {"source": candidate_identity, "source_directory": str(candidate),
                       "binary": str(candidate / "target/release/maelstrom"),
                       "binary_sha256": digest((candidate / "target/release/maelstrom").read_bytes()),
                       "revision": "compact-" + candidate_identity["tree_sha256"]}}
    if control is not None and control_identity is not None:
        declared = json.loads(control_identity.read_bytes())
        implementations["bitset"] = {"source": declared, "source_directory": str(control),
            "binary": str(control / "target/release/maelstrom"),
            "binary_sha256": digest((control / "target/release/maelstrom").read_bytes()),
            "revision": "copy-ordered-bitset-" + declared["tree_sha256"]}
    campaign = {"schema_version": 1, "prepared_utc": utc(), "implementations": implementations,
                "baseline_directory": str(baseline), "baseline_campaign_sha256": digest((baseline / "campaign.json").read_bytes()),
                "protocol_sha256": digest(protocol.read_bytes()), "memory": memory(candidate),
                "collector_sha256": {p.name: digest(p.read_bytes()) for p in sorted(Path(__file__).parent.glob("*.py"))}}
    verify(root, campaign)
    write_json(root / "campaign.json", campaign)
    for side in BASELINE_SIDES:
        shutil.copytree(baseline / f"baseline/serial-grid/{side**3:06}/warmup", root / f"controls/{side**3:06}")
    for label, command in {"gpu": ["nvidia-smi", "--query-gpu=name,driver_version,memory.total,compute_cap", "--format=csv,noheader"],
                           "cpu": ["lscpu", "--json"], "rustc": ["rustc", "-Vv"],
                           "nvcc": ["/usr/local/cuda/bin/nvcc", "--version"], "nsys": ["nsys", "--version"]}.items():
        invoke(command, candidate, root / "environment" / label, timeout=30, grace=5)


def attempt(root: Path, campaign: dict, label: str, variant: str, scene: Path, particles: int,
            *, kind: str = "sample", steps: int = 480, observation: bool = True,
            reference: dict | None = None) -> tuple[dict, dict | None]:
    verify(root, campaign)
    selected = campaign["implementations"][variant]
    timeout, grace = (30, 10) if steps == 4 else (120, 30)
    if campaign.get("experiment") == "neighbour-bands-v1":
        from .machine_state import capture
        capture(Path(selected["source_directory"]), root / "telemetry" / label / "before")
    process, document = invoke([selected["binary"], *arguments(scene, "cuda", steps=steps,
        observation=observation, kind=kind)], Path(selected["source_directory"]), root / label,
        timeout=timeout, grace=grace, env=dict(os.environ, XDG_CONFIG_HOME=str(root / "isolated-config"),
        MAELSTROM_SCENES_DIR=str(root / "isolated-scenes"), MAELSTROM_RUNS_DIR=str(root / "isolated-runs")))
    if campaign.get("experiment") == "neighbour-bands-v1":
        capture(Path(selected["source_directory"]), root / "telemetry" / label / "after")
    accepted = qualified(process, document, particles=particles, steps=steps, observation=observation, revision=selected["revision"])
    agreement = None
    if document is not None and reference is not None:
        agreement = compare(reference, document, exact=True)
        write_json(root / label / "comparison.json", agreement)
        accepted &= agreement["passed"]
    assessment = {"variant": variant, "particles": particles, "kind": kind, "admitted": accepted,
                  "exact_reference": agreement["passed"] if agreement else None}
    if document is not None and kind != "warmup":
        assessment["metrics"] = metrics(process, document, "profile" if kind == "profile" else "sample")
    write_json(root / label / "assessment.json", assessment)
    print(label, document.get("status") if document else process["exit_code"], flush=True)
    return assessment, document


def collect(root: Path) -> None:
    campaign = json.loads((root / "campaign.json").read_bytes())
    baseline = Path(campaign["baseline_directory"])
    candidate = Path(campaign["implementations"]["compact"]["source_directory"])
    for side in BASELINE_SIDES:
        _, reference = load_attempt(baseline / f"baseline/serial-grid/{side**3:06}/warmup")
        scene = candidate / f"scenes/falling-block-{side:02}.toml"
        for kind in ("warmup", "profile"):
            assessed, _ = attempt(root, campaign, f"regression/{side**3:06}/{kind}", "compact", scene,
                                  side**3, kind=kind, reference=reference)
            if not assessed["admitted"]:
                raise ValueError("regression qualification failed; raw attempt retained")
    _, reference = load_attempt(baseline / "baseline/serial-grid/008000/warmup")
    scene = candidate / "scenes/falling-block-20.toml"
    for variant in ("bitset", "compact"):
        assessment, _ = attempt(root, campaign, f"paired/{variant}/warmup", variant, scene, 8000,
                                kind="warmup", reference=reference)
        if not assessment["admitted"]:
            raise ValueError("paired warm-up failed")
    for sample in range(1, 6):
        for variant in (("bitset", "compact") if sample % 2 else ("compact", "bitset")):
            assessment, _ = attempt(root, campaign, f"paired/{variant}/sample-{sample}", variant,
                                    scene, 8000, reference=reference)
            if not assessment["admitted"]:
                raise ValueError("paired primary sample failed")
    for side in SIDES:
        n = side ** 3
        directory = root / f"capacity/{n:06}"
        directory.mkdir(parents=True)
        available = memory(candidate)
        estimate = capacity_estimate(n)
        ceiling = min(6 * GIB, available["gpu_total"] * 3 // 5, max(0, available["gpu_free"] - 2 * GIB))
        allowed = available["host_available"] >= 4 * GIB and estimate <= ceiling
        write_json(directory / "admission.json", {"admitted": allowed, "initial_lattice_estimate_bytes": estimate,
                   "estimate_scope": "initial geometry with 1.5x index capacity; not an evolved peak or general neighbour cap",
                   "ceiling_bytes": ceiling, **available})
        if not allowed:
            continue
        scene = baseline / f"inputs/scenes/capacity-block-{side:02}.toml"
        # The CPU pilot is independent of both layouts and their copy ordering.
        old = campaign["implementations"]["bitset"]
        control_process, control = invoke([old["binary"], *arguments(scene, "serial-grid", steps=4,
            observation=False, kind="warmup")], Path(old["source_directory"]), directory / "cpu-pilot", timeout=120, grace=30)
        if control_process["exit_code"] != 0 or control is None or control["status"] != "completed":
            raise ValueError("independent capacity pilot failed")
        assessed, pilot = attempt(root, campaign, f"capacity/{n:06}/pilot", "compact", scene, n,
                                   kind="pilot", steps=4, observation=False, reference=control)
        if not assessed["admitted"]:
            raise ValueError("capacity pilot failed; no larger work admitted")
        projected = assessed["metrics"]["solver_s"] * 120
        write_json(directory / "long-run-admission.json", {"pilot_solver_s": assessed["metrics"]["solver_s"],
                   "projected_480_step_s": projected, "ceiling_s": 90, "admitted": projected <= 90})
        if projected <= 90:
            _, control = load_attempt(baseline / f"capacity/{n:06}/core") if n in (8000, 32768) else ({}, None)
            assessed, document = attempt(root, campaign, f"capacity/{n:06}/core", "compact", scene, n,
                                         observation=False, reference=control)
            if document is None or document["status"] not in ("completed", "completed_with_warnings"):
                raise ValueError("capacity trajectory failed")
            if assessed["exact_reference"] is False:
                raise ValueError("capacity trajectory disagrees with retained control")
    verify(root, campaign)


def report(root: Path) -> dict:
    """Recompute matched medians from original output, not stored metric flags."""
    campaign = json.loads((root / "campaign.json").read_bytes())
    result = {"schema_version": 1, "primary": {}, "regression": [], "capacity": []}
    _, control = load_attempt(root / "controls/008000")
    for variant in ("bitset", "compact"):
        samples = []
        for index in range(1, 6):
            p, d = load_attempt(root / f"paired/{variant}/sample-{index}")
            if not qualified(p, d, particles=8000, steps=480, observation=True,
                             revision=campaign["implementations"][variant]["revision"]):
                raise ValueError("unclean primary sample")
            if not compare(control, d, exact=True)["passed"]:
                raise ValueError("primary sample disagrees with independent physical control")
            samples.append(metrics(p, d, "sample"))
        totals = [s["solver_s"] for s in samples]
        result["primary"][variant] = {"samples": samples, "median_solver_s": statistics.median(totals),
            "minimum_s": min(totals), "maximum_s": max(totals), "standard_deviation_s": statistics.stdev(totals)}
    result["paired_solver_speedup"] = result["primary"]["bitset"]["median_solver_s"] / result["primary"]["compact"]["median_solver_s"]
    for side in BASELINE_SIDES:
        _, control = load_attempt(root / f"controls/{side**3:06}")
        for kind in ("warmup", "profile"):
            p, d = load_attempt(root / f"regression/{side**3:06}/{kind}")
            if not compare(control, d, exact=True)["passed"]:
                raise ValueError("regression observation changed")
            if kind == "profile":
                result["regression"].append({"particles": side**3, "metrics": metrics(p, d, "profile")})
    for side in SIDES:
        target = root / f"capacity/{side**3:06}"
        row = {"particles": side**3, "admission": json.loads((target / "admission.json").read_bytes())}
        for kind in ("pilot", "core"):
            if not (target / kind).exists():
                continue
            p, d = load_attempt(target / kind)
            row[kind] = {"exit_code": p["exit_code"], "timed_out": p["timed_out"]}
            if d is not None:
                warnings = [step["completed_steps"] for step in d["steps"] if step["warning"]]
                row[kind].update(status=d["status"], completed_steps=d["completed_steps"],
                                 warning_steps=len(warnings), first_warning_step=warnings[0] if warnings else None,
                                 metrics=metrics(p, d, "sample"))
        result["capacity"].append(row)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("prepare", "collect", "report"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--identity", type=Path)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--protocol", type=Path)
    parser.add_argument("--control", type=Path)
    parser.add_argument("--control-identity", type=Path)
    args = parser.parse_args()
    try:
        if args.operation == "prepare":
            if any(p is None for p in (args.candidate, args.identity, args.baseline, args.protocol)):
                raise ValueError("prepare needs candidate, identity, baseline and protocol")
            prepare(*(p.resolve() for p in (args.candidate, args.identity, args.baseline, args.protocol, args.directory)),
                    control=args.control.resolve() if args.control else None,
                    control_identity=args.control_identity.resolve() if args.control_identity else None)
        elif args.operation == "collect":
            collect(args.directory.resolve())
        else:
            print(json.dumps(report(args.directory.resolve()), indent=2, allow_nan=False))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Compact comparison: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
