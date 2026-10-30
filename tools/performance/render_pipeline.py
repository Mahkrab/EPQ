"""Compare complete compilation and audit every emitted frame on the primary PC.

Source exports and executables are prepared before collection. The process timer
includes startup, simulation, rendering, all publication and teardown. GPU samples
are coarse device readings, not per-kernel counters or Windows-wide CPU evidence.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
from pathlib import Path
import resource
import statistics
import subprocess
import time


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def telemetry(path: Path) -> dict:
    """Describe available coarse device samples without inventing process counters."""
    rows = list(csv.reader(path.read_text(encoding="utf-8").splitlines()))
    result = {"samples": len(rows), "scope": "whole-device sampled utilisation; not process GPU occupancy"}
    for index, label in ((1, "gpu_util_percent"), (2, "memory_util_percent"), (3, "gpu_memory_mib"),
                         (4, "temperature_c"), (5, "power_w"), (6, "sm_clock_mhz")):
        values = []
        for row in rows:
            try:
                values.append(float(row[index]))
            except (ValueError, IndexError):
                pass
        result[label] = (dict(mean=statistics.mean(values), median=statistics.median(values),
                              minimum=min(values), maximum=max(values), available_samples=len(values)) if values else None)
    return result


def observe(command: list[str], folder: Path, cwd: Path) -> dict:
    """Retain failures and bounded GPU telemetry separately from process clocks."""
    folder.mkdir(parents=True, exist_ok=False)
    environment = dict(os.environ, XDG_CONFIG_HOME=str(folder / "config"))
    with (folder / "gpu.csv").open("wb") as gpu, (folder / "gpu.stderr").open("wb") as gpu_error:
        monitor = subprocess.Popen([
            "nvidia-smi", "--query-gpu=timestamp,utilization.gpu,utilization.memory,memory.used,temperature.gpu,power.draw,clocks.sm",
            "--format=csv,noheader,nounits", "--loop-ms=200",
        ], stdout=gpu, stderr=gpu_error)
        before = resource.getrusage(resource.RUSAGE_CHILDREN)
        start = time.monotonic()
        try:
            with (folder / "stdout.json").open("xb") as stdout, (folder / "stderr").open("xb") as stderr:
                result = subprocess.run(command, cwd=cwd, env=environment, stdout=stdout,
                                        stderr=stderr, timeout=600, check=False)
            wall = time.monotonic() - start
            after = resource.getrusage(resource.RUSAGE_CHILDREN)
            record = dict(command=command, exit_code=result.returncode, wall_s=wall,
                          cpu_user_s=after.ru_utime-before.ru_utime,
                          cpu_system_s=after.ru_stime-before.ru_stime,
                          max_rss_children_kib=after.ru_maxrss,
                          scope="child CPU time; max RSS is cumulative child high-water mark")
            write(folder / "process.json", record)
        except subprocess.TimeoutExpired:
            write(folder / "process.json", dict(command=command, failure="600 second timeout"))
            raise
        finally:
            monitor.terminate()
            try:
                monitor.wait(timeout=10)
            except subprocess.TimeoutExpired:
                monitor.kill()
                monitor.wait()
    if record["exit_code"]:
        raise ValueError(f"command failed; retained {folder}")
    return record


def fingerprint(manifest: dict) -> dict:
    """Compare numerical inputs/diagnostics and complete ordered output identities."""
    return {key: json.dumps(manifest[key], sort_keys=True, allow_nan=False) for key in (
        "input", "accepted_steps", "accepted_diagnostics", "frames", "render", "status",
        "boundary_display_box", "encoder", "renderer", "graphics",
    )}


def audit_bundle(binary: Path, folder: Path, original: dict | None) -> dict:
    bundle = folder / "bundle"
    raw = (bundle / "manifest.json").read_bytes()
    manifest = json.loads(raw)
    if not manifest["complete"] or len(manifest["frames"]) != 301:
        raise ValueError("incomplete 60 Hz frame schedule")
    identity = fingerprint(manifest)
    if original is not None and identity != original:
        raise ValueError("numerical state, diagnostics or complete frame output changed")
    for frame in manifest["frames"]:
        if "sha256:" + sha(bundle / frame["file"]) != frame["png_sha256"]:
            raise ValueError("published PNG digest differs")
    validation = subprocess.run([str(binary), "runs", "validate", str(bundle), "--format", "json"],
                                capture_output=True, timeout=120, check=False)
    (folder / "validation.stdout").write_bytes(validation.stdout)
    (folder / "validation.stderr").write_bytes(validation.stderr)
    if validation.returncode:
        raise ValueError("bundle validation failed")
    (folder / "manifest.json.gz").write_bytes(gzip.compress(raw, mtime=0))
    write(folder / "bundle-audit.json", dict(manifest_sha256=hashlib.sha256(raw).hexdigest(),
          frame_count=301, png_bytes=sum((bundle / f["file"]).stat().st_size for f in manifest["frames"]),
          every_png_digest_verified=True, exact_comparison=original is not None))
    return identity


def collect(root: Path, previous: Path, family: str, repeats: int) -> None:
    binaries = {name: root / "bin" / name for name in ("control", "candidate")}
    identities = {name: sha(binary) for name, binary in binaries.items()}
    write(root / family / "protocol.json", dict(
        workloads=[8000, 110592], numerical_modes=["reference", "fast"], simulated_s=5,
        frames=301, width=640, height=480, hz=60, cuda_device=0, cuda_block=128,
        warmups=1, measured_pairs=repeats, order="AB,BA alternating including warmup",
        retention="Engineering assessment of complete process timings and exact output; no automatic threshold",
        binaries=identities, boundary="complete process including CLI stdout, final manifest and teardown",
        clock="monotonic", telemetry="200 ms nvidia-smi samples; Linux process CPU user+system",
        input_files_sha256={str(p.relative_to(previous)): sha(p) for name in ("scenes", "config")
                            for p in sorted((previous/name).rglob("*")) if p.is_file()},
    ))
    for scene in ("resolved", "large"):
        for mode in ("reference", "fast"):
            reference = None
            for repeat in range(repeats + 1):
                for variant in (("control", "candidate") if repeat % 2 == 0 else ("candidate", "control")):
                    binary = binaries[variant]
                    if sha(binary) != identities[variant]:
                        raise ValueError("binary changed during collection")
                    label = f"{scene}-{mode}-{repeat}-{variant}"
                    folder = root / family / label
                    print(label, flush=True)
                    rate = 480 if mode == "reference" else 240
                    command = [str(binary), "compile", str(previous / "scenes" / (scene + ".toml")),
                               "--runs-dir", str(root / "library/runs"), "--scenes-dir", str(root / "library/scenes"),
                               "--numerical-mode", mode, "--backend", "cuda", "--device", "0", "--block-size", "128",
                               "--steps", str(5 * rate), "--frame-stride", str(rate // 60),
                               "--width", "640", "--height", "480", "--fit-camera",
                               "--output", str(folder / "bundle"), "--format", "json", "--quiet"]
                    record = observe(command, folder, root / variant)
                    identity = audit_bundle(binary, folder, reference)
                    if reference is None:
                        historical = json.loads((previous / "compiled" / f"{scene}-r3-{mode}" / "bundle/manifest.json").read_bytes())
                        if identity != fingerprint(historical):
                            raise ValueError("current control differs from retained fast-mode outputs")
                        reference = identity
                    manifest = json.loads(gzip.decompress((folder / "manifest.json.gz").read_bytes()))
                    record.update(scene=scene, mode=mode, variant=variant, repeat=repeat, warmup=repeat == 0,
                                  profile=manifest["timing_profile"], binary_sha256=identities[variant],
                                  telemetry=telemetry(folder / "gpu.csv"))
                    write(folder / "metrics.json", record)
                    print(f"  wall={record['wall_s']:.6f}s cpu={record['cpu_user_s']+record['cpu_system_s']:.3f}s", flush=True)


def summarise(root: Path, family: str) -> list[dict]:
    rows = [json.loads(p.read_text(encoding="utf-8")) for p in (root / family).glob("*/metrics.json")]
    result = []
    for scene in ("resolved", "large"):
        for mode in ("reference", "fast"):
            selected = [r for r in rows if r["scene"] == scene and r["mode"] == mode and not r["warmup"]]
            pairs = sorted({r["repeat"] for r in selected})
            if not pairs:
                continue
            values = {v: [next(r for r in selected if r["variant"] == v and r["repeat"] == i) for i in pairs]
                      for v in ("control", "candidate")}
            summary = dict(scene=scene, mode=mode,
                control_s=[r["wall_s"] for r in values["control"]],
                candidate_s=[r["wall_s"] for r in values["candidate"]],
                paired_speedups=[a["wall_s"]/b["wall_s"] for a,b in zip(values["control"],values["candidate"])])
            for variant, measurements in values.items():
                summary[variant+"_median_s"] = statistics.median(r["wall_s"] for r in measurements)
                summary[variant+"_stages_median_s"] = {
                    scope: {key: statistics.median(r["profile"][scope][key] for r in measurements)
                            for key in measurements[0]["profile"][scope]}
                    for scope in ("components_s", "worker_components_s") if scope in measurements[0]["profile"]}
                summary[variant+"_cpu_core_equivalents"] = [(r["cpu_user_s"]+r["cpu_system_s"])/r["wall_s"] for r in measurements]
                summary[variant+"_gpu_util_mean_percent"] = [r["telemetry"]["gpu_util_percent"]["mean"]
                    for r in measurements if r.get("telemetry", {}).get("gpu_util_percent")]
            summary["speedup"] = summary["control_median_s"]/summary["candidate_median_s"]
            result.append(summary)
    write(root / family / "summary.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("previous", type=Path)
    parser.add_argument("phase", choices=("pilot", "measure", "summarise"))
    args = parser.parse_args()
    if args.phase != "summarise":
        collect(args.root.resolve(), args.previous.resolve(), args.phase, 1 if args.phase == "pilot" else 3)
    for row in summarise(args.root.resolve(), "measure" if args.phase == "summarise" else args.phase):
        print(row["scene"], row["mode"], row["speedup"])
