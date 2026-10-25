"""Compare named CUDA entry points against the committed shared-entry control.

Ordinary alternating samples own the runtime comparison. Driver resource queries
and full-motion traces explain it without entering those measurement intervals.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import statistics
import sys

from tools.cuda.compare import compare
from .capture import digest, invoke, write_json
from .contract import BASELINE_SIDES, arguments, capacity_scene
from .correction_profile import windows
from .machine_state import capture
from .report import metrics

ENTRY_NAMES = tuple("solver_" + name for name in (
    "accelerate", "predict", "build_cells", "sort_cells", "count_neighbours",
    "validate_distances", "multipliers", "corrections", "validate_density",
    "apply_corrections", "project_planes", "reconstruct_velocity", "fill_neighbours"))


def accepted(process: dict, result: dict, reference: dict | None, steps: int) -> None:
    """Require equivalent completed work, including the warning/diagnostic schedule."""
    if (process["exit_code"] != 0 or process["timed_out"] or process["interrupted"]
            or result["completed_steps"] != str(steps) or result["failures"]
            or result["status"] not in ("completed", "completed_with_warnings")
            or result["metadata"]["debug_assertions"]
            or result["execution"] != {"mode": "cuda", "device": 0, "threads": 128}
            or (reference is not None and not compare(reference, result, exact=True)["passed"])):
        raise ValueError("different or incomplete specialisation workload")


def verify(work: Path, identities: dict) -> None:
    """Refuse collection from source or executables that changed after preparation."""
    for variant, identity in identities.items():
        source = work / variant
        for name, expected in identity["files_sha256"].items():
            path = (source / name).resolve()
            if not path.is_relative_to(source) or digest(path.read_bytes()) != expected:
                raise ValueError(f"source changed: {variant}/{name}")
        if "binary_sha256" in identity and digest((source / "target/release/maelstrom").read_bytes()) != identity["binary_sha256"]:
            raise ValueError("prepared executable changed")


def collect(work: Path, protocol: Path, *, shared_search: bool = False) -> None:
    root = work / "results"
    root.mkdir(exist_ok=False)
    (root / "protocol.md").write_bytes(protocol.read_bytes())
    entry_names = tuple("solver_shared" if shared_search and i in (2, 3, 4, 12) else name
                        for i, name in enumerate(ENTRY_NAMES))
    write_json(root / "entry-map.json", {"control": ["solver"] * 13, "candidate": entry_names,
               "shared_search": shared_search})
    identities = {v: json.loads((work / f"{v}-source.json").read_bytes()) for v in ("control", "candidate")}
    verify(work, identities)
    env = dict(os.environ, CUDA_HOME="/usr/local/cuda", MAELSTROM_CUDA_ARCH="89",
               XDG_CONFIG_HOME=str(root / "isolated-config"))
    for label, command in (("rustc", ["rustc", "-Vv"]), ("cargo", ["cargo", "-V"]),
                           ("gpu", ["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"]),
                           ("cpu", ["lscpu", "--json"]), ("nvcc", ["/usr/local/cuda/bin/nvcc", "--version"]),
                           ("nsys", ["nsys", "--version"])):
        p, _ = invoke(command, work, root / f"environment/{label}", timeout=30, env=env)
        if p["exit_code"] != 0:
            raise ValueError("environment identification failed")
    for variant in ("control", "candidate"):
        print(f"Building and qualifying {variant}", flush=True)
        source = work / variant
        p, _ = invoke(["cargo", "build", "--release", "--locked", "--features", "cuda"], source, root / f"{variant}/build", timeout=600, env=env)
        if p["exit_code"] != 0:
            raise ValueError(f"{variant} build failed")
        identities[variant]["binary_sha256"] = digest((source / "target/release/maelstrom").read_bytes())
        for label, command in (
                ("hardware", ["cargo", "test", "--release", "--locked", "--features", "cuda", "--lib", "cuda::", "--", "--include-ignored"]),
                ("application-boundary", ["cargo", "test", "--release", "--locked", "--features", "cuda", "--test", "cuda_boundary", "--", "--include-ignored"]),
                ("native-build", ["c++", "-std=c++17", "-O1", "-g", "-Wall", "-Wextra", "-Werror", "-fsanitize=address,undefined", "-fno-omit-frame-pointer", "-I/usr/local/cuda/include", "native/tests.cpp", "-ldl", "-o", str(work / f"{variant}-native-tests")]),
                ("native-tests", [str(work / f"{variant}-native-tests")])):
            p, _ = invoke(command, source, root / f"{variant}/{label}", timeout=600, env=env)
            if p["exit_code"] != 0:
                raise ValueError(f"{variant} {label} failed")
        ptx = max((source / "target/release/build").glob("maelstrom-*/out/roundtrip.ptx"), key=lambda p: p.stat().st_mtime_ns)
        probe = work / f"{variant}-resources"
        command = ["c++", "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror", "-I/usr/local/cuda/include", "-I", str(source / "native")]
        if variant == "candidate":
            command.append("-DSPECIALISED")
        command += [str(Path(__file__).with_name("kernel_resources.cpp")), "-ldl", "-o", str(probe)]
        p, _ = invoke(command, source, root / f"{variant}/resources-build", env=env)
        if p["exit_code"] != 0:
            raise ValueError("resource probe build failed")
        p, resources = invoke([str(probe), str(ptx)], source, root / f"{variant}/resources", env=env)
        expected = entry_names if variant == "candidate" else ("solver",)
        if p["exit_code"] != 0 or resources is None or tuple(f["name"] for f in resources["functions"]) != expected:
            raise ValueError("driver-loaded function resources unavailable")
        write_json(root / f"{variant}/resources.json", resources)
        identities[variant]["ptx_sha256"] = digest(ptx.read_bytes())
    write_json(root / "identities.json", identities)
    verify(work, identities)
    inputs = root / "inputs"
    (inputs / "config").mkdir(parents=True)
    (inputs / "scenes").mkdir()
    (inputs / "config/defaults-v4.toml").write_bytes((work / "control/config/defaults-v4.toml").read_bytes())
    scene = inputs / "scenes/capacity-block-48.toml"
    scene.write_text(capacity_scene(48))

    def run(variant: str, scene: Path, destination: Path, *, kind: str = "warmup",
            observation: bool = True, reference: dict | None = None) -> tuple[dict, dict]:
        verify(work, identities)
        binary = work / variant / "target/release/maelstrom"
        capture(work / variant, destination.parent / f"{destination.name}-machine-before")
        p, _ = invoke([str(binary), *arguments(scene, "cuda", kind=kind, observation=observation), "--output", str(destination / "solver.json")], work / variant, destination, env=env)
        result = json.loads((destination / "solver.json").read_bytes())
        accepted(p, result, reference, 480)
        capture(work / variant, destination.parent / f"{destination.name}-machine-after")
        return p, result

    print("Seven-size regression", flush=True)
    for side in BASELINE_SIDES:
        scene = work / f"control/scenes/falling-block-{side:02}.toml"
        _, reference = run("control", scene, root / f"regression/{side**3}/control")
        run("candidate", scene, root / f"regression/{side**3}/candidate", reference=reference)
    refs, summaries = {}, {}
    for particles, scene, observation in ((8000, work / "control/scenes/falling-block-20.toml", True),
                                          (110592, inputs / "scenes/capacity-block-48.toml", False)):
        print(f"Paired {particles}", flush=True)
        samples = {"control": [], "candidate": []}
        for index in range(6):
            for variant in (("control", "candidate") if index % 2 else ("candidate", "control")):
                label = "warmup" if index == 0 else f"sample-{index}"
                p, result = run(variant, scene, root / f"paired/{particles}/{variant}/{label}",
                    kind="warmup" if index == 0 else "sample", observation=observation, reference=refs.get(particles))
                refs[particles] = result
                if index:
                    samples[variant].append(metrics(p, result, "sample"))
        summaries[str(particles)] = {v: {"samples": rows, "median_solver_s": statistics.median(r["solver_s"] for r in rows),
            "min_solver_s": min(r["solver_s"] for r in rows), "max_solver_s": max(r["solver_s"] for r in rows),
            "median_invocation_s": statistics.median(r["invocation_s"] for r in rows),
            "median_construction_s": statistics.median(r["construction_s"] for r in rows)} for v, rows in samples.items()}
    write_json(root / "paired-summary.json", summaries)
    print("Full-motion traces", flush=True)
    traces = {}
    for variant in ("control", "candidate"):
        source = work / variant
        destination = root / f"timelines/{variant}"
        scene = inputs / "scenes/capacity-block-48.toml"
        p, _ = invoke(["nsys", "profile", "--trace=cuda", "--sample=none", "--cpuctxsw=none", "--cuda-memory-usage=true", "--force-overwrite=false", "--output", str(destination / "cuda"), str(source / "target/release/maelstrom"), *arguments(scene, "cuda", observation=False, kind="trace"), "--output", str(destination / "solver.json")], source, destination / "trace", env=env)
        result = json.loads((destination / "solver.json").read_bytes())
        accepted(p, result, refs[110592], 480)
        p, _ = invoke(["nsys", "export", "--type=sqlite", "--output", str(destination / "cuda.sqlite"), str(destination / "cuda.nsys-rep")], source, destination / "export", env=env)
        if p["exit_code"] != 0:
            raise ValueError("timeline export failed")
        traces[variant] = windows(destination, 110592, entry_names=entry_names if variant == "candidate" else None)
    verify(work, identities)
    write_json(root / "trace-summary.json", traces)
    write_json(root / "verification.json", {"source_and_binary_hashes_unchanged": True, "exact_physical_agreement": True,
        "sizes": [side**3 for side in BASELINE_SIDES], "paired_sizes": [8000, 110592],
        "protocol_sha256": digest(protocol.read_bytes()), "collector_sha256": digest(Path(__file__).read_bytes()),
        "scope": "ordinary timings plus separate traces/resources; not hosted or fluid-quality qualification"})
    print("Collection complete", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("work", type=Path)
    parser.add_argument("protocol", type=Path)
    parser.add_argument("--shared-search", action="store_true",
                        help="qualify the separately declared shared-search follow-up")
    args = parser.parse_args()
    try:
        collect(args.work.resolve(), args.protocol.resolve(), shared_search=args.shared_search)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Kernel specialisation: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
