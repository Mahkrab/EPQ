"""Collect the predeclared PC diagnosis without changing the solver or old datasets.

Preparation freezes exact source/input identities. Subsequent commands append new
attempts only, and refuse to reuse destinations or silently rebuild the executable.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import tomllib

from tools.baseline.data import require_exact
from tools.cuda.compare import compare
from .capture import digest, invoke, load_attempt, utc, write_json
from .contract import (BASELINE_SIDES, CHECKPOINTS, SERIES, SIDES, SOURCE_COMMIT, VERSION,
                       admit, arguments, capacity_scene, operations)


def command_output(command: list[str], cwd: Path) -> str:
    return subprocess.check_output(command, cwd=cwd, text=True, timeout=30).strip()


def memory(cwd: Path) -> dict:
    row = command_output(["nvidia-smi", "--query-gpu=memory.total,memory.free",
                          "--format=csv,noheader,nounits", "--id=0"], cwd)
    total, free = [int(value.strip()) * 1024 ** 2 for value in row.split(",")]
    available = next(int(line.split()[1]) * 1024 for line in Path("/proc/meminfo").read_text().splitlines()
                     if line.startswith("MemAvailable:"))
    return {"gpu_total": total, "gpu_free": free, "host_available": available}


def verify(directory: Path) -> tuple[dict, Path, Path]:
    """Validate the frozen byte identities before every collection operation."""
    campaign = json.loads((directory / "campaign.json").read_bytes())
    if campaign["policy"] != VERSION or campaign["source"]["base_commit"] != SOURCE_COMMIT:
        raise ValueError("unsupported diagnosis or source revision")
    source, binary = Path(campaign["source_directory"]), Path(campaign["binary"])
    for relative, expected in campaign["source"]["files_sha256"].items():
        path = (source / relative).resolve()
        if not path.is_relative_to(source) or digest(path.read_bytes()) != expected:
            raise ValueError(f"source bytes changed: {relative}")
    if digest(binary.read_bytes()) != campaign["binary_sha256"]:
        raise ValueError("prepared executable changed")
    for relative, expected in campaign["inputs_sha256"].items():
        path = (directory / relative).resolve()
        if not path.is_relative_to(directory) or digest(path.read_bytes()) != expected:
            raise ValueError("prepared input changed")
    if digest((directory / "protocol.md").read_bytes()) != campaign["protocol_sha256"]:
        raise ValueError("protocol changed after preparation")
    for name, expected in campaign["collector_sha256"].items():
        if digest((Path(__file__).parent / name).read_bytes()) != expected:
            raise ValueError("collector changed after preparation")
    return campaign, source, binary


def prepare(source: Path, identity: Path, protocol: Path, destination: Path) -> None:
    """Retain machine context and deterministic separate inputs before any sample."""
    source = source.resolve()
    declared = json.loads(identity.read_bytes())
    if declared["base_commit"] != SOURCE_COMMIT or declared["worktree_status"]:
        raise ValueError("diagnosis requires the clean committed simulator")
    for name, expected in declared["files_sha256"].items():
        path = (source / name).resolve()
        if not path.is_relative_to(source) or digest(path.read_bytes()) != expected:
            raise ValueError(f"exported source differs: {name}")
    binary = source / "target/release/maelstrom"
    destination.mkdir(parents=True, exist_ok=False)
    (destination / "protocol.md").write_bytes(protocol.read_bytes())
    for directory in ("inputs/config", "inputs/scenes", "environment"):
        (destination / directory).mkdir(parents=True)
    (destination / "inputs/config/defaults-v4.toml").write_bytes((source / "config/defaults-v4.toml").read_bytes())
    for side in SIDES:
        (destination / f"inputs/scenes/capacity-block-{side:02}.toml").write_text(capacity_scene(side))
    commands = {"rustc": ["rustc", "-Vv"], "cargo": ["cargo", "-V"],
                "nvcc": ["/usr/local/cuda/bin/nvcc", "--version"], "cpu": ["lscpu", "--json"],
                "gpu": ["nvidia-smi", "--query-gpu=name,driver_version,memory.total,compute_cap", "--format=csv,noheader"],
                "nsys": ["nsys", "--version"], "ncu": ["ncu", "--version"],
                "perf": ["perf", "--version"]}
    context = {}
    for label, command in commands.items():
        process, _ = invoke(command, source, destination / "environment" / label, timeout=30, grace=5)
        context[label] = process
    campaign = {"schema_version": 1, "policy": VERSION, "prepared_utc": utc(),
                "epq_base_commit": "86e4c0ee0a2c1ce3ca312870f9a752127b455e69",
                "source": declared, "source_directory": str(source), "binary": str(binary),
                "binary_sha256": digest(binary.read_bytes()), "python": platform.python_version(),
                "kernel": platform.release(), "architecture": platform.machine(),
                "affinity": sorted(os.sched_getaffinity(0)), "memory_at_preparation": memory(source),
                "protocol_sha256": digest(protocol.read_bytes()), "environment": context,
                "build": "cargo build --release --locked --features cuda; CUDA_HOME=/usr/local/cuda; MAELSTROM_CUDA_ARCH=89",
                "build_revision": SOURCE_COMMIT,
                "inputs_sha256": {p.relative_to(destination).as_posix(): digest(p.read_bytes())
                                  for p in sorted((destination / "inputs").rglob("*.toml"))},
                "collector_sha256": {p.name: digest(p.read_bytes()) for p in sorted(Path(__file__).parent.glob("*.py"))}}
    write_json(destination / "campaign.json", campaign)
    write_json(destination / "source-models.json", {str(side ** 3): operations(side ** 3) for side in SIDES})
    probe, result = invoke([str(binary), "doctor", "cuda", "--device", "0", "--format", "json"],
                           source, destination / "device-probe")
    if probe["exit_code"] != 0 or result is None:
        raise ValueError("CUDA admission probe failed; raw output retained")
    manifest = json.loads((source / "reference/manifest.json").read_bytes())
    small = manifest["cases"][0]
    golden = json.loads((source / small["golden"]).read_bytes())
    for series in SERIES:
        args = arguments(source / small["scene"], series, steps=small["steps"],
                         observation=False, kind="warmup")
        args[args.index("--refine-timestep") + 1] = str(small["refine_timestep"])
        args += ["--checkpoints", ",".join(map(str, small["checkpoints"]))]
        target = destination / f"qualification/{series}"
        process, document = invoke([str(binary), *args], source, target)
        if process["exit_code"] != 0 or process["timed_out"] or document is None:
            raise ValueError("small golden request failed; raw evidence retained")
        agreement = compare(golden, document, exact=True)
        write_json(target / "comparison.json", agreement)
        if not agreement["passed"]:
            raise ValueError("small golden disagrees; raw evidence retained")


def clean(process: dict, document: dict | None, *, series: str, steps: int,
          observation: bool, particles: int) -> bool:
    """Require complete declared work and resources, not just a successful exit."""
    if (process.get("exit_code") != 0 or process.get("timed_out") or process.get("interrupted")
            or document is None or document.get("status") != "completed" or document.get("failures")):
        return False
    expected_execution = {"serial-grid": {"mode": "serial"},
                          "threaded-grid": {"mode": "threaded", "workers": 12},
                          "cuda": {"mode": "cuda", "device": 0, "threads": 128}}[series]
    checkpoints = list(map(str, CHECKPOINTS)) if observation else []
    expected_backend = {"serial-grid": "serial-uniform-grid-pbf-binary32-8-jacobi-v2",
                        "threaded-grid": "threaded-uniform-grid-pbf-binary32-8-jacobi-v2",
                        "cuda": "cuda-uniform-grid-pbf-binary32-8-jacobi-v1"}[series]
    return (document.get("execution", {"mode": "serial"}) == expected_execution
            and document["backend"] == expected_backend == document["metadata"]["backend"]
            and document["request"] == {"steps": str(steps), "checkpoints": checkpoints}
            and document["completed_steps"] == str(steps)
            and len(document["steps"]) == steps
            and all(not step["warning"] for step in document["steps"])
            and [step["completed_steps"] for step in document["steps"]] == [str(i) for i in range(1, steps + 1)]
            and [item["snapshot"]["completed_steps"] for item in document["checkpoints"]] == checkpoints
            and document["metadata"]["build_revision"] == SOURCE_COMMIT
            and not document["metadata"]["debug_assertions"]
            and len(document["input"]["particles"]) == particles
            and len(document["final_snapshot"]["particles"]) == particles
            and document["final_snapshot"]["completed_steps"] == str(steps))


def execute(directory: Path, label: str, scene: Path, series: str, *, steps: int = 480,
            observation: bool = True, kind: str = "sample", timeout: float = 120,
            grace: float = 30, reference: dict | None = None) -> tuple[bool, dict | None]:
    campaign, source, binary = verify(directory)
    target = directory / label
    scene_input = tomllib.loads(scene.read_text())
    particles = math.prod(scene_input["particles"]["counts"])
    print(label, flush=True)
    env = dict(os.environ, XDG_CONFIG_HOME=str(directory / "isolated-config"),
               MAELSTROM_SCENES_DIR=str(directory / "isolated-scenes"),
               MAELSTROM_RUNS_DIR=str(directory / "isolated-runs"))
    process, document = invoke([str(binary), *arguments(scene, series, steps=steps,
                                                      observation=observation, kind=kind)],
                               source, target, timeout=timeout, grace=grace, env=env)
    accepted = clean(process, document, series=series, steps=steps,
                     observation=observation, particles=particles)
    agreement = None
    if accepted and reference is not None:
        agreement = compare(reference, document, exact=True)
        write_json(target / "comparison.json", agreement)
        accepted = agreement["passed"]
    if accepted and kind != "warmup" and kind != "trace":
        measurements = document.get("measurements", {})
        if (len(measurements.get("steps", [])) != steps
                or measurements.get("mode") != ("stages" if kind == "profile" else "total")):
            accepted = False
    write_json(target / "assessment.json", {"series": series, "kind": kind, "steps": steps,
               "observation": observation, "particles": particles, "admitted": accepted,
               "binary_sha256": campaign["binary_sha256"],
               "exact_reference": agreement["passed"] if agreement else None})
    return accepted, document


def baseline(directory: Path) -> None:
    """Retain the original observation-rich workload and same-binary CPU controls."""
    _, source, _ = verify(directory)
    references = {}
    for series in SERIES:
        for side in BASELINE_SIDES:
            scene = source / f"scenes/falling-block-{side:02}.toml"
            prefix = f"baseline/{series}/{side ** 3:06}"
            expected = references.get(side)
            if series == "serial-grid":
                manifest = json.loads((source / "reference/manifest.json").read_bytes())
                case = next(c for c in manifest["cases"] if c["particles"] == side ** 3)
                if case["golden"]:
                    expected = json.loads((source / case["golden"]).read_bytes())
            accepted, document = execute(directory, prefix + "/warmup", scene, series,
                                         kind="warmup", reference=expected)
            if series != "serial-grid" and expected is None:
                raise ValueError(f"missing clean serial control at {side ** 3}; no comparison admitted")
            if series == "serial-grid" and accepted:
                references[side] = document
            for index in range(1, 4) if accepted else ():
                accepted, _ = execute(directory, f"{prefix}/sample-{index}", scene, series,
                                       reference=references.get(side))
                if not accepted:
                    break
            execute(directory, prefix + "/profile", scene, series, kind="profile",
                    reference=references.get(side))
    verify(directory)


def capacity(directory: Path) -> None:
    """Bound the larger core-throughput family by memory and observed pilot time."""
    _, source, _ = verify(directory)
    for side in SIDES:
        target = directory / f"capacity/{side ** 3:06}"
        target.mkdir(parents=True, exist_ok=False)
        admission = admit(side ** 3, **memory(source))
        write_json(target / "admission.json", admission)
        if not admission["admitted"]:
            continue
        scene = directory / f"inputs/scenes/capacity-block-{side:02}.toml"
        accepted, document = execute(directory, f"capacity/{side ** 3:06}/pilot", scene, "cuda",
                                     steps=4, observation=False, kind="pilot", timeout=30, grace=10)
        if not accepted:
            continue
        elapsed = sum(step["total_s"] for step in document["measurements"]["steps"])
        estimate = elapsed / 4 * 480
        write_json(target / "long-run-admission.json", {"pilot_solver_s": elapsed,
                   "projected_480_step_s": estimate, "ceiling_s": 90, "admitted": estimate <= 90,
                   "kind": "pilot-extrapolation-not-a-480-step-measurement"})
        if estimate <= 90:
            accepted, core = execute(directory, f"capacity/{side ** 3:06}/core", scene, "cuda", observation=False)
            if side == 20 and accepted:
                baseline_process, reference = load_attempt(directory / "baseline/cuda/008000/warmup")
                if not clean(baseline_process, reference, series="cuda", steps=480,
                             observation=True, particles=8000):
                    raise ValueError("observation equivalence requires a clean CUDA baseline")
                # Names and checkpoint policies differ; accepted physical state and
                # all per-step diagnostics must not. Both inputs are checked too.
                for key in ("particles", "planes", "configuration", "randomness"):
                    require_exact(core["input"][key], reference["input"][key], f"input.{key}")
                require_exact(core["final_snapshot"], reference["final_snapshot"], "final_snapshot")
                require_exact(core["steps"], reference["steps"], "steps")
                write_json(target / "observation-equivalence.json", {"passed": True,
                           "comparison": "initial geometry, numerical inputs, complete final state and all step diagnostics; checkpoint observations intentionally differ"})
            execute(directory, f"capacity/{side ** 3:06}/profile", scene, "cuda", observation=False, kind="profile")
    verify(directory)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    p = sub.add_parser("prepare")
    for name in ("source", "identity", "protocol", "directory"):
        p.add_argument(name, type=Path)
    for operation in ("baseline", "capacity"):
        p = sub.add_parser(operation)
        p.add_argument("directory", type=Path)
    args = parser.parse_args()
    try:
        if args.operation == "prepare":
            prepare(args.source, args.identity, args.protocol, args.directory.resolve())
        elif args.operation == "baseline":
            baseline(args.directory.resolve())
        else:
            capacity(args.directory.resolve())
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(f"Performance diagnosis: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
