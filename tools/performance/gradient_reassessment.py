"""Compare bounded CUDA changes with optional fluid effects and immutable builds.

Source exports and ordinary samples stay separate from profiling. The report
describes paired evidence; the written engineering assessment decides retention.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
from pathlib import Path
import shutil
import sys

from .assessment import paired
from .capture import digest, invoke, load_attempt, write_json
from .contract import BASELINE_SIDES, arguments, capacity_scene
from .correction_profile import windows
from .machine_state import capture
from .report import metrics

EFFECTS = ("xsph_viscosity_enabled=true", "xsph_viscosity_coefficient=0.01",
           "vorticity_confinement_enabled=true", "vorticity_confinement_strength_m_s=0.1")
WORKLOADS = (("8000", 8000, True, ()), ("110592", 110592, False, ()),
             ("110592-effects", 110592, False, EFFECTS))


def physical_fingerprint(result: dict) -> str:
    """Compare complete canonical records, preserving signed zero and all inputs."""
    value = dict(result)
    value.pop("measurements", None)
    value["metadata"] = dict(value["metadata"])
    value["metadata"].pop("build_revision", None)
    return digest(json.dumps(value, sort_keys=True, allow_nan=False).encode())


def embedded_ptx(binary: Path, ptx: Path) -> str:
    """Reject a stale native build even when the Rust build identifier changed."""
    code = ptx.read_bytes()
    if not code or code not in binary.read_bytes():
        raise ValueError("freshly compiled CUDA code is absent from the executable")
    return digest(code)


def accepted(process: dict, result: dict | None, *, particles: int, revision: str,
             reference: dict | None = None) -> None:
    """Require completed, identified work and exact physical/diagnostic agreement."""
    if (process["exit_code"] != 0 or process["timed_out"] or process["interrupted"]
            or result is None or result["completed_steps"] != "480" or result["failures"]
            or result["status"] not in ("completed", "completed_with_warnings")
            or result["metadata"]["debug_assertions"]
            or result["metadata"]["build_revision"] != revision
            or result["execution"] != {"mode": "cuda", "device": 0, "threads": 128}
            or len(result["input"]["particles"]) != particles
            or len(result["final_snapshot"]["particles"]) != particles
            or result["schema_version"] != 1 or result["request"]["steps"] != "480"
            or [s["completed_steps"] for s in result["steps"]] != [str(i) for i in range(1, 481)]
            or [c["snapshot"]["completed_steps"] for c in result["checkpoints"]] != result["request"]["checkpoints"]):
        raise ValueError("different, incomplete or unidentified gradient workload")
    fingerprint = physical_fingerprint(result)
    if reference is not None and fingerprint != physical_fingerprint(reference):
        raise ValueError("physical results or diagnostic schedules differ")


def verify(work: Path, identities: dict) -> None:
    """Refuse changed source or executables after the campaign was prepared."""
    for variant, identity in identities.items():
        source = work / variant
        for name, expected in identity["files_sha256"].items():
            path = (source / name).resolve()
            if not path.is_relative_to(source) or digest(path.read_bytes()) != expected:
                raise ValueError(f"source changed: {variant}/{name}")
        binary = work / "bin" / variant
        if "binary_sha256" in identity and digest(binary.read_bytes()) != identity["binary_sha256"]:
            raise ValueError(f"binary changed: {variant}")


def collect(work: Path, protocol: Path, *, experiment: str = "gradient-reassessment") -> None:
    """Build, qualify and measure immutable exports sequentially on the primary PC."""
    root = work / "results"
    if experiment not in ("gradient-reassessment", "cooperative-sort", "resident-state"):
        raise ValueError("unknown solver comparison")
    root.mkdir(exist_ok=False)
    write_json(root / "experiment.json", {"name": experiment,
               "candidate_cooperative_sort": experiment in ("cooperative-sort", "resident-state"),
               "control_cooperative_sort": experiment == "resident-state"})
    (root / "protocol.md").write_bytes(protocol.read_bytes())
    identities = {v: json.loads((work / f"{v}-source.json").read_bytes())
                  for v in ("control", "candidate")}
    verify(work, identities)
    env = dict(os.environ, CUDA_HOME="/usr/local/cuda", MAELSTROM_CUDA_ARCH="89",
               XDG_CONFIG_HOME=str(work / "isolated-config"),
               MAELSTROM_SCENES_DIR=str(work / "isolated-scenes"),
               MAELSTROM_RUNS_DIR=str(work / "isolated-runs"))

    def command(label: str, args: list[str], source: Path, *, timeout: int = 600,
                environment: dict | None = None) -> dict | None:
        process, result = invoke(args, source, root / label, timeout=timeout,
                                 env=env if environment is None else environment)
        if process["exit_code"] != 0 or process["timed_out"] or process["interrupted"]:
            raise ValueError(f"{label} failed; raw attempt retained")
        return result

    for label, args in (("rustc", ["rustc", "-Vv"]), ("cargo", ["cargo", "-V"]),
                        ("gpu", ["nvidia-smi", "--query-gpu=name,driver_version,memory.total,memory.free", "--format=csv,noheader"]),
                        ("cpu", ["lscpu", "--json"]), ("nvcc", ["/usr/local/cuda/bin/nvcc", "--version"]),
                        ("nsys", ["nsys", "--version"])):
        command(f"environment/{label}", args, work, timeout=30)
    available_kib = int(next(line.split()[1] for line in Path("/proc/meminfo").read_text().splitlines()
                             if line.startswith("MemAvailable:")))
    gpu_text = (root / "environment/gpu/stdout.gz")
    free_mib = int(gzip.decompress(gpu_text.read_bytes()).decode().strip().split(",")[-1].strip().split()[0])
    write_json(root / "resources.json", {"host_available_kib": available_kib, "gpu_free_mib": free_mib})
    if available_kib < 4 * 1024**2 or free_mib < 2048:
        raise ValueError("declared memory reserve unavailable")
    (work / "bin").mkdir()
    for variant, identity in identities.items():
        print(f"Building and qualifying {variant}", flush=True)
        source = work / variant
        identity["revision"] = experiment + "-" + variant + "-" + identity["tree_sha256"]
        build_env = dict(env, MAELSTROM_BUILD_REVISION=identity["revision"],
                         CARGO_TARGET_DIR=str(work / "target" / variant))
        command(f"{variant}/build", ["cargo", "build", "--release", "--locked", "--offline", "--features", "cuda"], source, environment=build_env)
        shutil.copy2(work / "target" / variant / "release/maelstrom", work / "bin" / variant)
        identity["binary_sha256"] = digest((work / "bin" / variant).read_bytes())
        ptx = work / f"{variant}-expected.ptx"
        command(f"{variant}/fresh-ptx", ["/usr/local/cuda/bin/nvcc", "--ptx", "--std=c++17",
                "--fmad=false", "--ftz=false", "--prec-div=true", "--prec-sqrt=true", "-O3",
                "--gpu-architecture=compute_89", "native/kernels.cu", "-o", str(ptx)],
                source, environment=build_env)
        identity["fresh_ptx_sha256"] = embedded_ptx(work / "bin" / variant, ptx)
        if variant == "candidate":
            identical = identity["fresh_ptx_sha256"] == identities["control"]["fresh_ptx_sha256"]
            if identical != (experiment == "resident-state"):
                raise ValueError("unexpected CUDA code identity for the declared change")
        for label, args in (
            ("suite", ["cargo", "test", "--release", "--locked", "--offline", "--features", "cuda", "--no-fail-fast"]),
            ("hardware", ["cargo", "test", "--release", "--locked", "--offline", "--features", "cuda", "--lib", "cuda::", "--", "--include-ignored", "--test-threads=1"]),
            ("application", ["cargo", "test", "--release", "--locked", "--offline", "--features", "cuda", "--test", "cuda_boundary", "--", "--include-ignored", "--test-threads=1"]),
            *([("integration", ["cargo", "test", "--release", "--locked", "--offline", "--features", "cuda", "--test", "cuda_execution", "--", "--include-ignored", "--test-threads=1"])] if experiment == "resident-state" else []),
            ("clippy", ["cargo", "clippy", "--release", "--locked", "--offline", "--features", "cuda", "--all-targets", "--", "-D", "warnings"]),
            ("format", ["cargo", "fmt", "--check"]),
            ("native-build", ["c++", "-std=c++17", "-O1", "-g", "-Wall", "-Wextra", "-Werror", "-fsanitize=address,undefined", "-fno-omit-frame-pointer", "-I/usr/local/cuda/include", "native/tests.cpp", "-ldl", "-o", str(work / f"{variant}-native-tests")]),
            ("native", [str(work / f"{variant}-native-tests")])):
            command(f"{variant}/{label}", args, source, environment=build_env)
    write_json(root / "identities.json", identities)
    write_json(root / "collector-sha256.json", {
        p.relative_to(Path(__file__).parents[2]).as_posix(): digest(p.read_bytes())
        for directory in (Path(__file__).parent, Path(__file__).parents[1] / "cuda", Path(__file__).parents[1] / "baseline")
        for p in sorted(directory.glob("*.py"))})
    inputs = root / "inputs"
    (inputs / "config").mkdir(parents=True)
    (inputs / "scenes").mkdir()
    (inputs / "config/defaults-v4.toml").write_bytes((work / "control/config/defaults-v4.toml").read_bytes())
    scene = inputs / "scenes/capacity-block-48.toml"
    scene.write_text(capacity_scene(48), encoding="utf-8")
    write_json(root / "inputs-sha256.json", {p.relative_to(inputs).as_posix(): digest(p.read_bytes())
                                            for p in sorted(inputs.rglob("*")) if p.is_file()})

    def run(variant: str, label: str, scene: Path, particles: int, observation: bool,
            overrides: tuple[str, ...] = (), *, sample: bool = False,
            reference: dict | None = None) -> dict:
        verify(work, identities)
        destination = root / label
        capture(work, destination.parent / (destination.name + "-before"))
        args = [str(work / "bin" / variant), *arguments(scene, "cuda", observation=observation,
                                                       kind="sample" if sample else "warmup")]
        for value in overrides:
            args += ["--set", value]
        process, result = invoke(args, work / variant, destination, env=env)
        accepted(process, result, particles=particles, revision=identities[variant]["revision"], reference=reference)
        capture(work, destination.parent / (destination.name + "-after"))
        return result

    print("Seven-size exact regression", flush=True)
    for side in BASELINE_SIDES:
        scene = work / f"control/scenes/falling-block-{side:02}.toml"
        reference = run("control", f"regression/{side**3}/control", scene, side**3, True)
        run("candidate", f"regression/{side**3}/candidate", scene, side**3, True, reference=reference)
    references = {}
    for name, size, observation, overrides in WORKLOADS:
        print(f"Paired {name}", flush=True)
        scene = work / "control/scenes/falling-block-20.toml" if size == 8000 else inputs / "scenes/capacity-block-48.toml"
        reference = None
        for index in range(6):
            order = ("control", "candidate") if index == 0 or index % 2 else ("candidate", "control")
            for variant in order:
                label = "warmup" if index == 0 else f"sample-{index}"
                result = run(variant, f"paired/{name}/{variant}/{label}", scene, size, observation,
                             overrides, sample=index != 0, reference=reference)
                if reference is None:
                    reference = result
        references[name] = reference
    write_json(root / "summary.json", report(root))
    print("Separate full-motion profiles", flush=True)
    for variant in identities:
        destination = root / "timelines" / variant
        args = ["nsys", "profile", "--trace=cuda", "--sample=none", "--cpuctxsw=none", "--cuda-memory-usage=true", "--force-overwrite=false", "--output", str(destination / "cuda"), str(work / "bin" / variant),
                *arguments(inputs / "scenes/capacity-block-48.toml", "cuda", observation=False, kind="trace"), "--output", str(destination / "solver.json")]
        process, _ = invoke(args, work / variant, destination, env=env)
        result = json.loads((destination / "solver.json").read_bytes()) if (destination / "solver.json").exists() else None
        accepted(process, result, particles=110592, revision=identities[variant]["revision"], reference=references["110592"])
        command(f"timelines/{variant}/export", ["nsys", "export", "--type=sqlite", "--output", str(destination / "cuda.sqlite"), str(destination / "cuda.nsys-rep")], work)
        write_json(destination / "windows.json", windows(destination, 110592,
                   row_sort=experiment == "resident-state" or (experiment == "cooperative-sort" and variant == "candidate"),
                   resident=experiment == "resident-state" and variant == "candidate"))
    verify(work, identities)
    write_json(root / "verification.json", {"source_and_binary_hashes_unchanged": True,
               "protocol_sha256": digest(protocol.read_bytes()), "exact_physical_agreement": True,
               "decision": "requires written engineering assessment"})
    print("Collection complete", flush=True)


def report(root: Path) -> dict:
    """Reconstruct all paired durations and agreement from hashed raw output."""
    identities = json.loads((root / "identities.json").read_bytes())
    result = {"assessment_required": True, "workloads": {}}
    for name, size, _, _ in WORKLOADS:
        reference = None
        samples = {v: [] for v in identities}
        for variant, identity in identities.items():
            for index in range(6):
                label = "warmup" if index == 0 else f"sample-{index}"
                process, document = load_attempt(root / f"paired/{name}/{variant}/{label}")
                accepted(process, document, particles=size, revision=identity["revision"], reference=reference)
                if reference is None:
                    reference = document
                if index:
                    samples[variant].append(metrics(process, document, "sample"))
        result["workloads"][name] = {"samples": samples, "solver": paired(
            [row["solver_s"] for row in samples["control"]],
            [row["solver_s"] for row in samples["candidate"]]), "invocation": paired(
            [row["invocation_s"] for row in samples["control"]],
            [row["invocation_s"] for row in samples["candidate"]]),
            "status": reference["status"], "warning_steps": sum(s["warning"] for s in reference["steps"])}
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("collect", "report"))
    parser.add_argument("work", type=Path)
    parser.add_argument("--protocol", type=Path)
    parser.add_argument("--experiment", choices=("gradient-reassessment", "cooperative-sort", "resident-state"), default="gradient-reassessment")
    args = parser.parse_args()
    try:
        if args.operation == "collect":
            if args.protocol is None:
                parser.error("collection requires --protocol")
            collect(args.work.resolve(), args.protocol.resolve(), experiment=args.experiment)
        else:
            print(json.dumps(report(args.work.resolve()), indent=2, allow_nan=False))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Solver comparison: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
