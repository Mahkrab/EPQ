"""Measure sort submission independently of the preceding storage experiment.

Each variant has its own source and executable identity. Retained serial controls
and compact trajectories are comparison evidence, not fresh timing samples.
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
from .compact import attempt, capacity_estimate, qualified, verify
from .contract import BASELINE_SIDES, SIDES, GIB, arguments
from .report import metrics
from .study import memory


def prepare(work: Path, baseline: Path, previous: Path, protocol: Path) -> Path:
    root = work / "results"
    root.mkdir(exist_ok=False)
    (root / "protocol.md").write_bytes(protocol.read_bytes())
    implementations = {}
    for variant in ("control", "candidate"):
        source = work / variant
        identity = json.loads((work / f"{variant}-source.json").read_bytes())
        binary = source / "target/release/maelstrom"
        implementations[variant] = {"source": identity, "source_directory": str(source),
            "binary": str(binary), "binary_sha256": digest(binary.read_bytes()),
            "revision": f"sort-{variant}-" + identity["tree_sha256"]}
    campaign = {"schema_version": 1, "experiment": "sort-batch-v1", "prepared_utc": utc(),
        "implementations": implementations, "baseline_directory": str(baseline),
        "previous_directory": str(previous), "protocol_sha256": digest(protocol.read_bytes()),
        "baseline_campaign_sha256": digest((baseline / "campaign.json").read_bytes()),
        "previous_campaign_sha256": digest((previous / "campaign.json").read_bytes()),
        "collector_sha256": {p.name: digest(p.read_bytes()) for p in sorted(Path(__file__).parent.glob("*.py"))}}
    verify(root, campaign)
    write_json(root / "campaign.json", campaign)
    for side in BASELINE_SIDES:
        shutil.copytree(baseline / f"baseline/serial-grid/{side**3:06}/warmup", root / f"controls/{side**3:06}")
    for side in SIDES:
        shutil.copytree(previous / f"capacity/{side**3:06}/core", root / f"previous/{side**3:06}")
    for label, command in {"gpu": ["nvidia-smi", "--query-gpu=name,driver_version,memory.total,compute_cap", "--format=csv,noheader"],
            "cpu": ["lscpu", "--json"], "rustc": ["rustc", "-Vv"], "cargo": ["cargo", "-V"],
            "nvcc": ["/usr/local/cuda/bin/nvcc", "--version"], "nsys": ["nsys", "--version"],
            "platform": ["uname", "-srmo"]}.items():
        process, _ = invoke(command, work, root / "environment" / label, timeout=30, grace=5)
        if process["exit_code"] != 0:
            raise ValueError("environment collection failed")
    return root


def collect(root: Path) -> None:
    campaign = json.loads((root / "campaign.json").read_bytes())
    source = Path(campaign["implementations"]["candidate"]["source_directory"])
    baseline = Path(campaign["baseline_directory"])
    for side in BASELINE_SIDES:
        _, reference = load_attempt(root / f"controls/{side**3:06}")
        scene = source / f"scenes/falling-block-{side:02}.toml"
        for kind in ("warmup", "profile"):
            assessed, _ = attempt(root, campaign, f"regression/{side**3:06}/{kind}", "candidate", scene,
                                  side**3, kind=kind, reference=reference)
            if not assessed["admitted"]:
                raise ValueError("regression failed; raw evidence retained")
    _, reference = load_attempt(root / "controls/008000")
    scene = source / "scenes/falling-block-20.toml"
    for variant in ("control", "candidate"):
        assessed, _ = attempt(root, campaign, f"paired/{variant}/warmup", variant, scene, 8000,
                              kind="warmup", reference=reference)
        if not assessed["admitted"]:
            raise ValueError("paired warm-up failed")
    for index in range(1, 6):
        for variant in (("control", "candidate") if index % 2 else ("candidate", "control")):
            assessed, _ = attempt(root, campaign, f"paired/{variant}/sample-{index}", variant, scene, 8000,
                                  reference=reference)
            if not assessed["admitted"]:
                raise ValueError("primary sample failed")
    for side in SIDES:
        n = side**3
        directory = root / f"capacity/{n:06}"
        directory.mkdir(parents=True)
        available = memory(source)
        ceiling = min(6 * GIB, available["gpu_total"] * 3 // 5, max(0, available["gpu_free"] - 2 * GIB))
        admitted = available["host_available"] >= 4 * GIB and capacity_estimate(n) <= ceiling
        write_json(directory / "admission.json", {"admitted": admitted, "ceiling_bytes": ceiling,
            "initial_lattice_estimate_bytes": capacity_estimate(n), **available})
        if not admitted:
            continue
        scene = baseline / f"inputs/scenes/capacity-block-{side:02}.toml"
        verify(root, campaign)
        process, reference = invoke([campaign["implementations"]["control"]["binary"],
            *arguments(scene, "serial-grid", steps=4, observation=False, kind="warmup")], source,
            directory / "cpu-pilot", timeout=120, grace=30)
        if process["exit_code"] != 0 or reference is None or reference["status"] != "completed":
            raise ValueError("independent capacity pilot failed")
        assessed, _ = attempt(root, campaign, f"capacity/{n:06}/pilot", "candidate", scene, n,
                              kind="pilot", steps=4, observation=False, reference=reference)
        if not assessed["admitted"]:
            raise ValueError("capacity pilot failed")
        projected = assessed["metrics"]["solver_s"] * 120
        write_json(directory / "long-run-admission.json", {"projected_480_step_s": projected,
            "ceiling_s": 90, "admitted": projected <= 90})
        if projected <= 90:
            _, previous = load_attempt(root / f"previous/{n:06}")
            assessed, result = attempt(root, campaign, f"capacity/{n:06}/core", "candidate", scene, n,
                                       observation=False, reference=previous)
            if result is None or result["status"] not in ("completed", "completed_with_warnings") or assessed["exact_reference"] is not True:
                raise ValueError("capacity trajectory failed or changed")
    verify(root, campaign)


def report(root: Path) -> dict:
    campaign = json.loads((root / "campaign.json").read_bytes())
    result = {"experiment": "sort-batch-v1", "primary": {}, "capacity": []}
    _, reference = load_attempt(root / "controls/008000")
    for variant in ("control", "candidate"):
        samples = []
        for i in range(1, 6):
            process, document = load_attempt(root / f"paired/{variant}/sample-{i}")
            if not qualified(process, document, particles=8000, steps=480, observation=True,
                             revision=campaign["implementations"][variant]["revision"]) or not compare(reference, document, exact=True)["passed"]:
                raise ValueError("unclean or different primary sample")
            samples.append(metrics(process, document, "sample"))
        values = [s["solver_s"] for s in samples]
        result["primary"][variant] = {"samples": samples, "median_solver_s": statistics.median(values),
            "minimum_s": min(values), "maximum_s": max(values), "standard_deviation_s": statistics.stdev(values)}
    result["paired_solver_speedup"] = result["primary"]["control"]["median_solver_s"] / result["primary"]["candidate"]["median_solver_s"]
    for side in SIDES:
        directory = root / f"capacity/{side**3:06}"
        row = {"particles": side**3, "admission": json.loads((directory / "admission.json").read_bytes())}
        if (directory / "core").exists():
            process, document = load_attempt(directory / "core")
            _, previous = load_attempt(root / f"previous/{side**3:06}")
            if not compare(previous, document, exact=True)["passed"]:
                raise ValueError("capacity observation changed")
            row.update(status=document["status"], warning_steps=sum(s["warning"] for s in document["steps"]),
                       metrics=metrics(process, document, "sample"))
        result["capacity"].append(row)
    return result


def traces(root: Path) -> None:
    """Keep instrumented runs separate, with their original native reports private."""
    campaign = json.loads((root / "campaign.json").read_bytes())
    baseline = Path(campaign["baseline_directory"])
    for particles, side, steps in ((8000, 20, 480), (110592, 48, 4)):
        for variant in ("control", "candidate"):
            verify(root, campaign)
            selected = campaign["implementations"][variant]
            directory = root / f"timelines/{variant}-{particles}-{steps}"
            command = ["nsys", "profile", "--trace=cuda", "--sample=none", "--cpuctxsw=none",
                "--cuda-memory-usage=true", "--force-overwrite=false", "--output", str(directory / "cuda"),
                selected["binary"], *arguments(baseline / f"inputs/scenes/capacity-block-{side:02}.toml",
                "cuda", steps=steps, observation=False, kind="trace"), "--output", str(directory / "solver.json")]
            process, _ = invoke(command, Path(selected["source_directory"]), directory, timeout=120, grace=30,
                env=dict(os.environ, XDG_CONFIG_HOME=str(root / "isolated-config"),
                         MAELSTROM_SCENES_DIR=str(root / "isolated-scenes"), MAELSTROM_RUNS_DIR=str(root / "isolated-runs")))
            if process["exit_code"] != 0 or process["timed_out"]:
                raise ValueError("trace failed; raw output retained")
            document = json.loads((directory / "solver.json").read_bytes())
            if not qualified(process, document, particles=particles, steps=steps, observation=False, revision=selected["revision"]):
                raise ValueError("traced solver work differs")
            export, _ = invoke(["nsys", "export", "--type=sqlite", "--output", str(directory / "cuda.sqlite"),
                str(directory / "cuda.nsys-rep")], root, directory / "export", timeout=120, grace=30)
            if export["exit_code"] != 0:
                raise ValueError("trace export failed")
            write_json(directory / "files.json", {p.relative_to(directory).as_posix(): digest(p.read_bytes())
                       for p in sorted(directory.rglob("*")) if p.is_file()})
    verify(root, campaign)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("prepare", "collect", "report", "traces"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--protocol", type=Path)
    args = parser.parse_args()
    try:
        if args.operation == "prepare":
            if any(p is None for p in (args.baseline, args.previous, args.protocol)):
                parser.error("prepare requires baseline, previous and protocol")
            prepare(args.directory.resolve(), args.baseline.resolve(), args.previous.resolve(), args.protocol.resolve())
        elif args.operation == "collect":
            collect(args.directory.resolve())
        elif args.operation == "traces":
            traces(args.directory.resolve())
        else:
            print(json.dumps(report(args.directory.resolve()), indent=2, allow_nan=False))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Sort comparison: {error}", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
