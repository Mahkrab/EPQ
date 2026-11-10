"""Measure the production CLI's direct, cache and repeat-render workflows.

The two binaries must come from frozen exports of the actual working source.
All work executes sequentially on the primary PC; correctness validation and
archive creation run after the timed campaign. No prototype accessors are used.
"""

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess
import struct
import time


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def invoke(command: list[str], destination: Path, cwd: Path) -> dict:
    """Retain per-process CPU/RSS and whole-device samples beside the process clock."""
    destination.mkdir()
    with (destination / "gpu.csv").open("w") as gpu:
        monitor = subprocess.Popen(["nvidia-smi", "--query-gpu=timestamp,utilization.gpu,memory.used,clocks.sm,power.draw",
                                    "--format=csv,noheader,nounits", "-lms", "200"], stdout=gpu, stderr=subprocess.DEVNULL)
        start = time.perf_counter()
        try:
            with (destination / "stdout.json").open("w") as out, (destination / "stderr.txt").open("w") as err:
                result = subprocess.run(["/usr/bin/time", "-v", "-o", str(destination / "resource.txt"), *command],
                                        cwd=cwd, stdout=out, stderr=err, timeout=240, check=False)
            elapsed = time.perf_counter() - start
        finally:
            monitor.terminate()
            monitor.wait(timeout=10)
    record = {"command": command, "wall_s": elapsed, "returncode": result.returncode}
    for line in (destination / "resource.txt").read_text().splitlines():
        for key, label in [("rss_kib", "Maximum resident set size (kbytes):"), ("user_s", "User time (seconds):"),
                           ("system_s", "System time (seconds):")]:
            if label in line:
                record[key] = float(line.split(label)[1].strip())
    (destination / "process.json").write_text(json.dumps(record, indent=2) + "\n")
    if result.returncode:
        raise RuntimeError(f"failed process {destination}: {(destination / 'stderr.txt').read_text()[-1500:]}")
    return record


def read(path: Path) -> dict:
    return json.loads(path.read_bytes())


def diagnostic_bits(value: dict) -> tuple:
    """Compare declared binary32 quantities exactly, independently of JSON spelling.

    Direct image manifests expand f32 through serde_json::Value's f64 storage;
    typed JSONL writes shortest f32 decimals. Both must recover identical bits.
    """
    if set(value) != {"completed_steps", "maximum_speed_m_s", "cfl_limit", "warning"}:
        raise ValueError("diagnostic fields differ")
    def binary32(number: float) -> bytes:
        if isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(number):
            raise ValueError("invalid diagnostic quantity")
        bits = struct.pack("<f", number)
        if not math.isfinite(struct.unpack("<f", bits)[0]):
            raise ValueError("diagnostic exceeds binary32")
        return bits
    limit = value["cfl_limit"]
    if limit == {"kind": "unbounded"}:
        limit_bits = None
    elif set(limit) == {"kind", "seconds"} and limit["kind"] == "finite":
        limit_bits = binary32(limit["seconds"])
    else:
        raise ValueError("invalid diagnostic CFL limit")
    return (value["completed_steps"], binary32(value["maximum_speed_m_s"]), limit["kind"], limit_bits, value["warning"])


def settings_toml(settings: dict) -> str:
    lines = ['schema_version = 2', 'camera_mode = "fixed"']
    for key in ["width", "height", "format", "step_stride"]:
        lines.append(f"{key} = {json.dumps(settings[key])}")
    for section in ["camera", "particles"]:
        if section in settings:
            lines.extend(["", f"[{section}]", *[f"{key} = {json.dumps(value)}" for key, value in settings[section].items()]])
    return "\n".join(lines) + "\n"


def identities(root: Path) -> dict:
    """Verify both frozen source trees and their freshly embedded native code."""
    result = {}
    for variant in ["baseline", "candidate"]:
        expected = read(root / f"{variant}-source.json")
        for name, digest in expected["files"].items():
            if sha(root / variant / name) != digest:
                raise ValueError(f"changed frozen source: {variant}/{name}")
        binary = root / f"{variant}-target/release/maelstrom"
        data = binary.read_bytes()
        build_digest = hashlib.sha256()
        # Rust PathBuf ordering compares path components: a directory named
        # falling-block-10 precedes falling-block-10-playground, unlike raw strings.
        source_names = sorted((name for name in expected["files"]
                               if name in ["Cargo.toml", "Cargo.lock", "build.rs"]
                               or name.split("/")[0] in ["src", "native", "build_support", "scenes", "config"]),
                              key=lambda name: Path(name).parts)
        for name in source_names:
            contents = (root / variant / name).read_bytes()
            build_digest.update(name.encode())
            build_digest.update(b"\0")
            build_digest.update(len(contents).to_bytes(8, "little"))
            build_digest.update(contents)
        embedded_source = "sha256:" + build_digest.hexdigest()
        if embedded_source.encode() not in data:
            raise ValueError("binary lacks its frozen source identity")
        embedded = [p for p in (root / f"{variant}-target/release/build").glob("maelstrom-*/out/*.ptx")
                    if p.read_bytes() in data]
        if len({sha(path) for path in embedded}) != 1:
            raise ValueError("expected one distinct freshly compiled embedded PTX")
        result[variant] = {"binary_sha256": sha(binary), "ptx_sha256": sha(embedded[0]),
                           "ptx_bytes": embedded[0].stat().st_size, "embedded_source": embedded_source,
                           "source_manifest_sha256": sha(root / f"{variant}-source.json")}
    if result["baseline"]["ptx_sha256"] != result["candidate"]["ptx_sha256"]:
        raise ValueError("native code differs between control and cache implementation")
    (root / "binary-source-identity.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def campaign(root: Path) -> None:
    identities(root)
    baseline = root / "baseline-target/release/maelstrom"
    candidate = root / "candidate-target/release/maelstrom"
    source = root / "candidate"
    results = root / "runs"
    results.mkdir()
    protocol = {"schema_version": 1, "warmups": 1, "measured_pairs": 3, "order": ["AB", "BA", "AB", "BA"],
                "steps": 1200, "frame_stride": 4, "frames": 301, "numerical_mode": "experimental",
                "device": 0, "block_size": 128, "size": [640, 480], "alternative_size": [1280, 720],
                "binary_sha256": {"baseline": sha(baseline), "candidate": sha(candidate)},
                "limits": "warm OS cache; whole-device GPU samples; no forced clocks or disk policy; stages may overlap"}
    (root / "production-protocol.json").write_text(json.dumps(protocol, indent=2) + "\n")
    for scene in ["falling-block-20", "large-impact"]:
        case = results / scene
        case.mkdir()
        render = case / "render.toml"
        render.write_text('schema_version = 2\nwidth = 640\nheight = 480\ncamera_mode = "fit"\n[particles]\ncolour_mode = "kinetic_energy"\nmin_energy_j = 0.0\nmax_energy_j = 1.962\n')
        alternative = case / "alternative.toml"
        common = [f"builtin:{scene}", "--backend", "cuda", "--device", "0", "--block-size", "128",
                  "--numerical-mode", "experimental", "--steps", "1200", "--frame-stride", "4"]
        def direct(round_index: int) -> None:
            label = f"a-{round_index}"
            bundle = case / f"{label}-images"
            invoke([str(baseline), "--format", "json", "--runs-dir", str(case / "library"), "compile", *common,
                    "--render-config", str(render), "--output", str(bundle)], case / label, source)
            manifest = read(bundle / "manifest.json")
            if not alternative.exists():
                changed = manifest["render"]
                changed["width"], changed["height"] = 1280, 720
                changed["camera"]["eye_m"][0] += 0.6
                changed["particles"] = {"colour_mode": "fixed", "colour": "#238be0"}
                alternative.write_text(settings_toml(changed))
            invoke([str(baseline), "--format", "json", "--runs-dir", str(case / "library"), "compile", *common,
                    "--render-config", str(alternative), "--no-fit-camera", "--output", str(case / f"{label}-alt-images")],
                   case / f"{label}-alt", source)
        def staged(round_index: int) -> None:
            label = f"b-{round_index}"
            cache = case / f"{label}-cache"
            invoke([str(candidate), "--format", "json", "cache", "bake", *common, "--output", str(cache)],
                   case / f"{label}-bake", source)
            for mode in ["render", "repeat", "alt"]:
                config = alternative if mode == "alt" else render
                invoke(["env", "CUDA_VISIBLE_DEVICES=", str(candidate), "--format", "json", "render", str(cache),
                        "--render-config", str(config), "--output", str(case / f"{label}-{mode}-images")],
                       case / f"{label}-{mode}", source)
        for round_index in range(4):
            for action in ([direct, staged] if round_index % 2 == 0 else [staged, direct]):
                action(round_index)
            print(f"Completed {scene} round {round_index}", flush=True)
    assess(root)
    identities(root)


def assess(root: Path) -> list[dict]:
    summaries = []
    for scene in ["falling-block-20", "large-impact"]:
        case = root / "runs" / scene
        samples = []
        for index in range(4):
            a = read(case / f"a-{index}-images/manifest.json")
            alt = read(case / f"a-{index}-alt-images/manifest.json")
            cache = case / f"b-{index}-cache"
            bake = read(cache / "cache.json")
            diagnostics = [json.loads(line) for line in (cache / "diagnostics.jsonl").read_text().splitlines()]
            if (len(a["frames"]) != 301 or bake["frames"] != 301
                    or [diagnostic_bits(d) for d in a["accepted_diagnostics"]] != [diagnostic_bits(d) for d in diagnostics]):
                raise ValueError("simulation diagnostics or frame count differ")
            record = {"round": index, "warmup": index == 0, "stages": {"bake": bake["timings"], "direct": a["timing_profile"]}}
            for mode in ["render", "repeat", "alt"]:
                rendered = read(case / f"b-{index}-{mode}-images/manifest.json")
                expected = alt if mode == "alt" else a
                if rendered["frames"] != expected["frames"] or rendered["input"] != a["input"]:
                    raise ValueError(f"render identity mismatch: {scene}/{index}/{mode}")
                if rendered["timing_seconds"]["solver_steps"] != 0.0:
                    raise ValueError("cache rendering reported fluid steps")
                record["stages"][mode] = {"profile": rendered["timing_profile"], "seconds": rendered["timing_seconds"]}
            for label, folder in [("direct", f"a-{index}"), ("direct_alt", f"a-{index}-alt"),
                                  ("bake", f"b-{index}-bake"), ("render", f"b-{index}-render"),
                                  ("repeat", f"b-{index}-repeat"), ("alt", f"b-{index}-alt")]:
                process = read(case / folder / "process.json")
                if process["returncode"] != 0 or not 0 < process["wall_s"] < 240:
                    raise ValueError("failed or invalid process measurement")
                record[label] = process
            record["first_staged_s"] = record["bake"]["wall_s"] + record["render"]["wall_s"]
            samples.append(record)
        measured = samples[1:]
        medians = {key: statistics.median(s[key]["wall_s"] for s in measured)
                   for key in ["direct", "direct_alt", "bake", "render", "repeat", "alt"]}
        summaries.append({"scene": scene, "samples": samples, "median_s": medians,
                          "first_staged_median_s": statistics.median(s["first_staged_s"] for s in measured),
                          "paired_first_speedups": [s["direct"]["wall_s"] / s["first_staged_s"] for s in measured],
                          "paired_alternative_speedups": [s["direct_alt"]["wall_s"] / s["alt"]["wall_s"] for s in measured]})
    (root / "production-summary.json").write_text(json.dumps(summaries, indent=2) + "\n")
    return summaries


def resources(root: Path) -> list[dict]:
    """Keep process RSS/CPU distinct from sampled whole-device utilisation."""
    result = []
    for scene in ["falling-block-20", "large-impact"]:
        case = root / "runs" / scene
        samples = []
        for index in range(1, 4):
            for mode, folder in [("direct", f"a-{index}"), ("direct_alt", f"a-{index}-alt"),
                                 ("bake", f"b-{index}-bake"), ("render", f"b-{index}-render"),
                                 ("repeat", f"b-{index}-repeat"), ("alt", f"b-{index}-alt")]:
                process = read(case / folder / "process.json")
                gpu = []
                for row in csv.reader((case / folder / "gpu.csv").read_text().splitlines()):
                    try:
                        gpu.append([float(value.strip()) for value in row[1:]])
                    except ValueError:
                        continue
                samples.append({"round": index, "mode": mode, "rss_mib": process["rss_kib"] / 1024,
                                "cpu_core_equivalents": (process["user_s"] + process["system_s"]) / process["wall_s"],
                                "gpu_samples": len(gpu), "mean_gpu_percent": statistics.mean(row[0] for row in gpu),
                                "max_device_memory_mib": max(row[1] for row in gpu),
                                "median_sm_clock_mhz": statistics.median(row[2] for row in gpu)})
        cache = case / "b-1-cache"
        sizes = {folder: sum(p.stat().st_size for p in (cache / folder).iterdir()) for folder in ["frames", "receipts"]}
        sizes["total"] = sum(p.stat().st_size for p in cache.rglob("*") if p.is_file())
        result.append({"scene": scene, "samples": samples, "cache_bytes": sizes})
    (root / "production-resources.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def verify_files(root: Path) -> dict:
    """Read back published images and run the application's public validators."""
    binary = root / "candidate-target/release/maelstrom"
    bundles = 0
    images = 0
    for path in sorted((root / "runs").glob("*/*-images")):
        manifest = read(path / "manifest.json")
        subprocess.run([str(binary), "runs", "validate", str(path)], check=True, timeout=120, stdout=subprocess.DEVNULL)
        for frame in manifest["frames"]:
            if "sha256:" + sha(path / frame["file"]) != frame["png_sha256"]:
                raise ValueError("published image checksum mismatch")
            images += 1
        bundles += 1
    caches = list((root / "runs").glob("*/*-cache"))
    for cache in caches:
        subprocess.run([str(binary), "cache", "validate", str(cache), "--full"], check=True, timeout=120, stdout=subprocess.DEVNULL)
    receipt = {"bundles": bundles, "pngs": images, "full_caches": len(caches), "canonical_states": len(caches) * 301}
    (root / "production-verification.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def resource_failure(root: Path) -> dict:
    """Inject a process-local file-size failure after cache frames have committed."""
    import resource
    import signal
    binary = root / "candidate-target/release/maelstrom"
    folder = root / "resource-failure"
    folder.mkdir()
    cache = folder / "cache"
    def limited_file_size() -> None:
        # This affects only the child. Ignoring SIGXFSZ lets ordinary Rust I/O
        # report EFBIG instead of terminating before it can retain failure metadata.
        signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
        resource.setrlimit(resource.RLIMIT_FSIZE, (48 * 1024, 48 * 1024))
    result = subprocess.run([str(binary), "--format", "json", "cache", "bake", "builtin:falling-block-04",
                             "--backend", "serial-grid", "--steps", "1200", "--frame-stride", "4", "--output", str(cache)],
                            preexec_fn=limited_file_size, capture_output=True, text=True, timeout=120, check=False)
    failure = read(cache / "failure.json")
    inspect = subprocess.run([str(binary), "--format", "json", "cache", "inspect", str(cache), "--allow-partial"],
                             capture_output=True, text=True, timeout=30, check=True)
    prefix = json.loads(inspect.stdout)
    if result.returncode != 5 or prefix["complete"] or prefix["frames"] == 0 or (cache / "cache.json").exists():
        raise ValueError("resource failure did not retain an explicit incomplete prefix")
    subprocess.run([str(binary), "cache", "validate", str(cache), "--allow-partial", "--full"], check=True,
                   capture_output=True, timeout=120)
    receipt = {"returncode": result.returncode, "stderr": result.stderr, "failure": failure,
               "prefix": prefix, "full_prefix_validation": True,
               "fault": "child-only RLIMIT_FSIZE=49152; SIGXFSZ ignored; no system-wide setting changed"}
    (root / "resource-failure.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["measure", "assess", "verify", "resources", "identities", "resource-failure"])
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    {"measure": campaign, "assess": assess, "verify": verify_files, "resources": resources,
     "identities": identities, "resource-failure": resource_failure}[args.action](args.root)
