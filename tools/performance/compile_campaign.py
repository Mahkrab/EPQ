"""Collect block-size and compilation costs from isolated primary-PC exports.

All binaries, inputs and requests are fixed before timings. Bundle validation and
machine readings run outside invocation timers; original image sequences stay local.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
from pathlib import Path
import shutil

from .capture import digest, invoke, write_json
from .compilation import BLOCKS, COMPILES, compile_identity, partition, physical_run, report
from .contract import arguments, capacity_scene
from .gradient_reassessment import EFFECTS, embedded_ptx, verify
from .machine_state import capture


def collect(work: Path, protocol: Path) -> None:
    root = work / "results"
    root.mkdir(exist_ok=False)
    (root / "protocol.md").write_bytes(protocol.read_bytes())
    ids = {v: json.loads((work / f"{v}-source.json").read_bytes()) for v in ("control", "candidate")}
    verify(work, ids)
    env = dict(os.environ, CUDA_HOME="/usr/local/cuda", MAELSTROM_CUDA_ARCH="89",
        XDG_CONFIG_HOME=str(work / "isolated-config"), MAELSTROM_SCENES_DIR=str(work / "isolated-scenes"),
        MAELSTROM_RUNS_DIR=str(work / "isolated-runs"))

    def command(label: str, args: list[str], cwd: Path, *, environment: dict | None = None, timeout: int = 600):
        process, result = invoke(args, cwd, root / label, env=env if environment is None else environment, timeout=timeout)
        if process["exit_code"] != 0 or process["timed_out"] or process["interrupted"]:
            raise ValueError(label + " failed; raw attempt retained")
        return process, result

    for name, args in (("rustc", ["rustc", "-Vv"]), ("cargo", ["cargo", "-V"]),
        ("cpu", ["lscpu", "--json"]), ("gpu", ["nvidia-smi", "--query-gpu=name,driver_version,memory.total,memory.free", "--format=csv,noheader,nounits"]),
        ("nvcc", ["/usr/local/cuda/bin/nvcc", "--version"])):
        command("environment/" + name, args, work, timeout=30)
    free_gpu = int(gzip.decompress((root / "environment/gpu/stdout.gz").read_bytes()).decode().strip().split(",")[-1])
    free_host = int(next(v.split()[1] for v in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines() if v.startswith("MemAvailable:")))
    free_disk = shutil.disk_usage(work).free
    write_json(root / "resources.json", {"gpu_free_mib": free_gpu, "host_available_kib": free_host, "workspace_free_bytes": free_disk})
    if free_gpu < 2048 or free_host < 4 * 1024**2 or free_disk < 10 * 1024**3:
        raise ValueError("declared resource reserve unavailable")
    (work / "bin").mkdir()
    for variant, identity in ids.items():
        print("Build and qualify " + variant, flush=True)
        source = work / variant
        identity["revision"] = "compile-profile-" + variant + "-" + identity["tree_sha256"]
        build_env = dict(env, CARGO_TARGET_DIR=str(work / "target" / variant), MAELSTROM_BUILD_REVISION=identity["revision"])
        command(variant + "/build", ["cargo", "build", "--release", "--locked", "--offline", "--features", "cuda,render"], source, environment=build_env)
        shutil.copy2(work / "target" / variant / "release/maelstrom", work / "bin" / variant)
        identity["binary_sha256"] = digest((work / "bin" / variant).read_bytes())
        ptx = work / (variant + "-expected.ptx")
        command(variant + "/fresh-ptx", ["/usr/local/cuda/bin/nvcc", "--ptx", "--std=c++17", "--fmad=false", "--ftz=false",
            "--prec-div=true", "--prec-sqrt=true", "-O3", "--gpu-architecture=compute_89", "native/kernels.cu", "-o", str(ptx)], source, environment=build_env)
        identity["fresh_ptx_sha256"] = embedded_ptx(work / "bin" / variant, ptx)
        if variant == "candidate":
            if identity["fresh_ptx_sha256"] != ids["control"]["fresh_ptx_sha256"]:
                raise ValueError("export timing changed CUDA code")
            for label, args in (
                ("suite", ["cargo", "test", "--release", "--locked", "--offline", "--features", "cuda,render", "--no-fail-fast"]),
                ("hardware", ["cargo", "test", "--release", "--locked", "--offline", "--features", "cuda,render", "--lib", "cuda::", "--", "--include-ignored", "--test-threads=1"]),
                ("application", ["cargo", "test", "--release", "--locked", "--offline", "--features", "cuda,render", "--test", "cuda_boundary", "--", "--include-ignored"]),
                ("export-device", ["cargo", "test", "--release", "--locked", "--offline", "--features", "cuda,render", "--test", "export_device", "--", "--include-ignored", "--test-threads=1"]),
                ("export-failures", ["cargo", "test", "--release", "--locked", "--offline", "--features", "cuda,render", "--lib", "export::", "--", "--include-ignored", "--test-threads=1"]),
                ("clippy", ["cargo", "clippy", "--release", "--locked", "--offline", "--features", "cuda,render", "--all-targets", "--", "-D", "warnings"]),
                ("format", ["cargo", "fmt", "--check"])):
                command(variant + "/" + label, args, source, environment=build_env)
    write_json(root / "identities.json", ids)
    command("environment/graphics", [str(work / "bin/candidate"), "doctor", "graphics", "--format", "json"], work / "candidate", timeout=60)
    write_json(root / "collector-sha256.json", {p.relative_to(Path(__file__).parents[2]).as_posix(): digest(p.read_bytes())
        for p in sorted(Path(__file__).parent.glob("*.py"))})
    inputs = root / "inputs"
    (inputs / "scenes").mkdir(parents=True)
    (inputs / "config").mkdir()
    (inputs / "scenes/capacity-block-48.toml").write_text(capacity_scene(48), encoding="utf-8")
    (inputs / "config/defaults-v4.toml").write_bytes((work / "candidate/config/defaults-v4.toml").read_bytes())
    write_json(root / "inputs-sha256.json", {p.relative_to(inputs).as_posix(): digest(p.read_bytes()) for p in sorted(inputs.rglob("*")) if p.is_file()})
    scene = inputs / "scenes/capacity-block-48.toml"
    for name, selected, observation, effects in (("8000", work / "candidate/scenes/falling-block-20.toml", True, ()),
            ("110592", scene, False, ()), ("110592-effects", scene, False, EFFECTS)):
        reference = None
        for index in range(4):
            order = BLOCKS[index:] + BLOCKS[:index]
            for block in order:
                verify(work, ids)
                name_part = f"sample-{index}" if index else "warmup"
                label = f"headless/{name}/{block}/{name_part}"
                capture(work, root / (label + "-before"))
                args = arguments(selected, "cuda", observation=observation, kind="sample" if index else "warmup")
                args[args.index("--block-size") + 1] = str(block)
                for value in effects:
                    args += ["--set", value]
                print(label, flush=True)
                _, document = command(label, [str(work / "bin/candidate"), *args], work / "candidate", timeout=120)
                fingerprint = physical_run(document, 8000 if name == "8000" else 110592, block, ids["candidate"]["revision"])
                if reference is None:
                    reference = fingerprint
                if fingerprint != reference:
                    raise ValueError("headless physical result changed")
                capture(work, root / (label + "-after"))
    (work / "runs").mkdir()
    reference, reference_frames = None, None
    for index in range(4):
        for variant, block, stride in COMPILES[index:] + COMPILES[:index]:
            verify(work, ids)
            name_part = f"sample-{index}" if index else "warmup"
            label = f"compile/{variant}-{block}-stride-{stride}/{name_part}"
            destination = work / "runs" / f"{variant}-{block}-{stride}-{name_part}"
            capture(work, root / (label + "-before"))
            print(label, flush=True)
            process, _ = command(label, [str(work / "bin" / variant), "compile", str(scene), "--backend", "cuda", "--device", "0",
                "--block-size", str(block), "--refine-timestep", "4", "--steps", "480", "--frame-stride", str(stride),
                "--width", "1280", "--height", "720", "--fit-camera", "--format", "json", "--output", str(destination)], work / variant, timeout=240)
            capture(work, root / (label + "-after"))
            raw = (destination / "manifest.json").read_bytes()
            value = json.loads(raw)
            fingerprint, common = compile_identity(value, block, stride)
            if reference is None:
                reference, reference_frames = fingerprint, common
            if fingerprint != reference or any(reference_frames[s] != f for s, f in common.items()):
                raise ValueError("compiled observations changed")
            if variant == "candidate":
                partition(value, process["wall_s"])
            packed = gzip.compress(raw, mtime=0)
            (root / label / "manifest.json.gz").write_bytes(packed)
            frames = []
            for frame in value["frames"]:
                actual = digest((destination / frame["file"]).read_bytes())
                if "sha256:" + actual != frame["png_sha256"]:
                    raise ValueError("published PNG changed")
                frames.append({"file": frame["file"], "sha256": actual})
            write_json(root / label / "bundle.json", {"manifest_sha256": digest(raw), "manifest_gzip_sha256": digest(packed), "frames": frames})
            command(label + "/validation", [str(work / "bin" / variant), "runs", "validate", str(destination), "--format", "json"], work / variant, timeout=120)
    verify(work, ids)
    write_json(root / "summary.json", report(root))
    write_json(root / "verification.json", {"unchanged_cuda_code": True, "source_binary_hashes_unchanged": True,
        "exact_headless_and_compile_agreement": True, "protocol_sha256": digest(protocol.read_bytes())})
    print("Compilation/block-size collection complete", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("work", type=Path)
    parser.add_argument("--protocol", required=True, type=Path)
    args = parser.parse_args()
    collect(args.work.resolve(), args.protocol.resolve())
