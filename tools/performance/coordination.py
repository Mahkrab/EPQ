"""Separate CPU coordination from transfers before changing device ownership.

Probe clocks observe disjoint intervals in a diagnostic export. Control totals
expose instrumentation effects; these results are not an optimisation campaign.
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
import os
from pathlib import Path
import shutil
import statistics
import sys

from .capture import digest, invoke, load_attempt, write_json
from .contract import arguments, capacity_scene
from .gradient_reassessment import WORKLOADS, accepted, embedded_ptx, verify
from .machine_state import capture
from .report import metrics

GROUPS = {
    "COORD_PREP": ("prepare_reserve", "prepare_pack", "prepare_upload"),
    "COORD_ROWS": ("bounds_cpu", "counts_download", "prefix_cpu", "membership_reserve", "offset_upload"),
    "COORD_STEP": ("cfl_download", "cfl_repack", "cfl_cpu", "prediction_download", "prediction_repack"),
}
COMPONENTS = tuple(name for group in GROUPS.values() for name in group)
BUNDLES = {
    "preparation": GROUPS["COORD_PREP"],
    "cfl": ("cfl_download", "cfl_repack", "cfl_cpu"),
    "bounds": ("prediction_download", "prediction_repack", "bounds_cpu"),
    "prefix": ("counts_download", "prefix_cpu", "membership_reserve", "offset_upload"),
}


def probes(text: str, particles: int, steps: int) -> list[dict[str, float]]:
    """Require one ordered preparation/row/step triple per completed step."""
    if type(particles) is not int or particles < 1 or type(steps) is not int or steps < 1:
        raise ValueError("positive particle and step counts are required")
    result, pending = [], {}
    order = tuple(GROUPS)
    next_group = 0
    for line in text.splitlines():
        if not line.startswith("COORD_"):
            continue
        fields = line.split(",")
        if (next_group >= len(order) or fields[0] != order[next_group]
                or len(fields) != len(GROUPS[fields[0]]) + 3 or int(fields[1]) != particles
                or int(fields[2]) != len(result) + 1):
            raise ValueError("malformed, duplicate or reordered coordination probe")
        values = [float(v) for v in fields[3:]]
        if any(not math.isfinite(v) or v < 0 for v in values):
            raise ValueError("invalid coordination duration")
        pending.update(zip(GROUPS[fields[0]], values, strict=True))
        next_group += 1
        if next_group == len(order):
            result.append(pending)
            pending, next_group = {}, 0
    if pending or len(result) != steps:
        raise ValueError("incomplete coordination probe sequence")
    return result


def diagnostic(process: dict, result: dict, reference: dict, revision: str,
               stderr: str, particles: int) -> dict:
    """Keep component intervals inside their enclosing complete solver steps."""
    accepted(process, result, particles=particles, revision=revision, reference=reference)
    measured = metrics(process, result, "sample")
    rows = probes(stderr, particles, 480)
    for row, step in zip(rows, result["measurements"]["steps"], strict=True):
        if math.fsum(row.values()) > step["total_s"] + 1e-8:
            raise ValueError("coordination intervals exceed the enclosing solver step")
    totals = {name: math.fsum(row[name] for row in rows) for name in COMPONENTS}
    return {"primary_timing": False, "solver_s": measured["solver_s"], "components_s": totals,
            "bundles_s": {name: math.fsum(totals[key] for key in keys) for name, keys in BUNDLES.items()},
            "first_step_s": rows[0], "windows": {
                f"{first}-{last}": {key: math.fsum(row[key] for row in rows[first-1:last]) for key in COMPONENTS}
                for first, last in ((1, 120), (121, 240), (241, 480))}}


def report(root: Path) -> dict:
    """Reconstruct all three samples and expose observer effects separately."""
    identities = json.loads((root / "identities.json").read_bytes())
    output = {"diagnostic_only": True, "workloads": {}}
    for name, particles, _, _ in WORKLOADS:
        _, reference = load_attempt(root / f"paired/{name}/control/warmup")
        control, instrumented = [], []
        for index in range(1, 4):
            p, d = load_attempt(root / f"paired/{name}/control/sample-{index}")
            accepted(p, d, particles=particles, revision=identities["control"]["revision"], reference=reference)
            control.append(metrics(p, d, "sample"))
            directory = root / f"paired/{name}/probe/sample-{index}"
            p, d = load_attempt(directory)
            instrumented.append(diagnostic(p, d, reference, identities["probe"]["revision"],
                                          (directory / "stderr.txt").read_text(), particles))
        median_total = statistics.median(row["solver_s"] for row in instrumented)
        components = {key: statistics.median(row["components_s"][key] for row in instrumented) for key in COMPONENTS}
        bundles = {key: statistics.median(row["bundles_s"][key] for row in instrumented) for key in BUNDLES}
        output["workloads"][name] = {"control_samples": control, "diagnostic_samples": instrumented,
            "median_control_solver_s": statistics.median(row["solver_s"] for row in control),
            "median_diagnostic_solver_s": median_total, "median_components_s": components,
            "median_bundles_s": bundles, "component_fractions": {key: value / median_total for key, value in components.items()},
            "bundle_fractions": {key: value / median_total for key, value in bundles.items()},
            "warning_steps": sum(s["warning"] for s in reference["steps"])}
    return output


def collect(work: Path, protocol: Path) -> None:
    root = work / "results"
    root.mkdir(exist_ok=False)
    (root / "protocol.md").write_bytes(protocol.read_bytes())
    identities = {v: json.loads((work / f"{v}-source.json").read_bytes()) for v in ("control", "probe")}
    verify(work, identities)
    env = dict(os.environ, CUDA_HOME="/usr/local/cuda", MAELSTROM_CUDA_ARCH="89",
               XDG_CONFIG_HOME=str(work / "isolated-config"), MAELSTROM_SCENES_DIR=str(work / "isolated-scenes"),
               MAELSTROM_RUNS_DIR=str(work / "isolated-runs"))
    env.pop("MAELSTROM_COORDINATION_PROBE", None)

    def command(label: str, args: list[str], source: Path, environment: dict, timeout: int = 600):
        process, result = invoke(args, source, root / label, timeout=timeout, env=environment)
        if process["exit_code"] != 0 or process["timed_out"] or process["interrupted"]:
            raise ValueError(label + " failed; raw attempt retained")
        return result

    for label, args in (("rustc", ["rustc", "-Vv"]), ("cargo", ["cargo", "-V"]),
        ("gpu", ["nvidia-smi", "--query-gpu=name,driver_version,memory.total,memory.free", "--format=csv,noheader,nounits"]),
        ("cpu", ["lscpu", "--json"]), ("nvcc", ["/usr/local/cuda/bin/nvcc", "--version"])):
        command("environment/" + label, args, work, env, 30)
    gpu = gzip.decompress((root / "environment/gpu/stdout.gz").read_bytes()).decode().strip().split(",")
    available = int(next(line.split()[1] for line in Path("/proc/meminfo").read_text().splitlines() if line.startswith("MemAvailable:")))
    if available < 4 * 1024**2 or int(gpu[-1].strip()) < 2048:
        raise ValueError("declared memory reserve unavailable")
    write_json(root / "memory.json", {"host_available_kib": available, "gpu_free_mib": int(gpu[-1].strip())})
    (work / "bin").mkdir()
    for variant, identity in identities.items():
        print("Building " + variant, flush=True)
        source = work / variant
        identity["revision"] = "host-coordination-" + variant + "-" + identity["tree_sha256"]
        build_env = dict(env, CARGO_TARGET_DIR=str(work / "target" / variant), MAELSTROM_BUILD_REVISION=identity["revision"])
        command(variant + "/build", ["cargo", "build", "--release", "--locked", "--offline", "--features", "cuda"], source, build_env)
        shutil.copy2(work / "target" / variant / "release/maelstrom", work / "bin" / variant)
        identity["binary_sha256"] = digest((work / "bin" / variant).read_bytes())
        ptx = work / f"{variant}-expected.ptx"
        command(variant + "/fresh-ptx", ["/usr/local/cuda/bin/nvcc", "--ptx", "--std=c++17", "--fmad=false", "--ftz=false",
                "--prec-div=true", "--prec-sqrt=true", "-O3", "--gpu-architecture=compute_89", "native/kernels.cu", "-o", str(ptx)], source, build_env)
        identity["fresh_ptx_sha256"] = embedded_ptx(work / "bin" / variant, ptx)
        if variant == "probe":
            if identity["fresh_ptx_sha256"] != identities["control"]["fresh_ptx_sha256"]:
                raise ValueError("host probes changed CUDA code")
            for label, args in (
                ("suite", ["cargo", "test", "--release", "--locked", "--offline", "--features", "cuda", "--no-fail-fast"]),
                ("hardware", ["cargo", "test", "--release", "--locked", "--offline", "--features", "cuda", "--lib", "cuda::", "--", "--include-ignored", "--test-threads=1"]),
                ("application", ["cargo", "test", "--release", "--locked", "--offline", "--features", "cuda", "--test", "cuda_boundary", "--", "--include-ignored"]),
                ("clippy", ["cargo", "clippy", "--release", "--locked", "--offline", "--features", "cuda", "--all-targets", "--", "-D", "warnings"]),
                ("format", ["cargo", "fmt", "--check"])):
                command(variant + "/" + label, args, source, build_env)
    write_json(root / "identities.json", identities)
    write_json(root / "collector-sha256.json", {p.relative_to(Path(__file__).parents[2]).as_posix(): digest(p.read_bytes())
        for directory in (Path(__file__).parent, Path(__file__).parents[1] / "cuda", Path(__file__).parents[1] / "baseline")
        for p in sorted(directory.glob("*.py"))})
    inputs = root / "inputs"
    (inputs / "scenes").mkdir(parents=True)
    (inputs / "config").mkdir()
    (inputs / "scenes/capacity-block-48.toml").write_text(capacity_scene(48))
    (inputs / "config/defaults-v4.toml").write_bytes((work / "control/config/defaults-v4.toml").read_bytes())
    write_json(root / "inputs-sha256.json", {p.relative_to(inputs).as_posix(): digest(p.read_bytes()) for p in sorted(inputs.rglob("*")) if p.is_file()})
    for name, particles, observation, overrides in WORKLOADS:
        print("Diagnostic pairs " + name, flush=True)
        scene = work / "control/scenes/falling-block-20.toml" if particles == 8000 else inputs / "scenes/capacity-block-48.toml"
        reference = None
        for index in range(4):
            for variant in (("control", "probe") if index == 0 or index % 2 else ("probe", "control")):
                verify(work, identities)
                label = "warmup" if index == 0 else f"sample-{index}"
                destination = root / f"paired/{name}/{variant}/{label}"
                capture(work, destination.parent / (label + "-before"))
                args = [str(work / "bin" / variant), *arguments(scene, "cuda", observation=observation, kind="sample" if index else "warmup")]
                for value in overrides:
                    args += ["--set", value]
                run_env = dict(env)
                if variant == "probe":
                    run_env["MAELSTROM_COORDINATION_PROBE"] = "1"
                process, document = invoke(args, work / variant, destination, env=run_env)
                accepted(process, document, particles=particles, revision=identities[variant]["revision"], reference=reference)
                if reference is None:
                    reference = document
                if variant == "probe" and index:
                    diagnostic(process, document, reference, identities[variant]["revision"], (destination / "stderr.txt").read_text(), particles)
                capture(work, destination.parent / (label + "-after"))
    verify(work, identities)
    write_json(root / "summary.json", report(root))
    write_json(root / "verification.json", {"unchanged_cuda_code": True, "exact_physical_agreement": True,
        "source_and_binary_hashes_unchanged": True, "protocol_sha256": digest(protocol.read_bytes()), "diagnostic_only": True})
    print("Coordination attribution complete", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("collect", "report"))
    parser.add_argument("work", type=Path)
    parser.add_argument("--protocol", type=Path)
    args = parser.parse_args()
    try:
        if args.operation == "collect":
            if args.protocol is None:
                parser.error("collection requires --protocol")
            collect(args.work.resolve(), args.protocol.resolve())
        else:
            print(json.dumps(report(args.work.resolve()), indent=2, allow_nan=False))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Host coordination: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
