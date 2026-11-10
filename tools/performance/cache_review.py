"""Prepare and measure an isolated simulation-cache architecture experiment.

The probe keeps production source untouched. Measurements include process startup,
all cache/image publication and teardown; graphics and CUDA are never concurrent
in the staged path. Raw process records remain separate from derived medians.
"""

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import shutil
import statistics
import subprocess
import time


def prepare(source: Path) -> None:
    """Add diagnostic access only to an explicitly selected temporary source export."""
    if (source / ".git").exists():
        raise ValueError("prepare requires a source export, not a Git checkout")
    target = source / "src/export/mod.rs"
    text = target.read_text()
    if "cache_review_probe" in text:
        raise ValueError("source already contains the probe")
    target.write_text(text + '\n#[path = "cache_review_probe.rs"]\npub mod cache_review_probe;\n')
    shutil.copyfile(Path(__file__).with_name("cache_review_probe.rs"), target.with_name("cache_review_probe.rs"))
    with (source / "src/workflow/record.rs").open("a") as out:
        out.write('''
impl SnapshotRecord {
    /// Checked diagnostic constructor in the isolated cache experiment only.
    pub fn cache_review_from_particles(particles: &[Particle], completed_steps: u64) -> Result<Self, RecordError> {
        let record = Self { schema_version: 1, completed_steps, particles: particles.iter().map(ParticleRecord::from).collect() };
        record.validate()?;
        Ok(record)
    }
}
''')
    binary = source / "src/bin/cache-review.rs"
    binary.parent.mkdir(exist_ok=True)
    binary.write_text('fn main() -> Result<(), Box<dyn std::error::Error>> { maelstrom::export::cache_review_probe::main()?; Ok(()) }\n')


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def execute(command: list[str], directory: Path, cwd: Path) -> dict:
    """Measure one process with independent RSS and CPU accounting and GPU samples."""
    directory.mkdir()
    monitor = subprocess.Popen(["nvidia-smi", "--query-gpu=timestamp,utilization.gpu,memory.used,clocks.sm,power.draw",
                                "--format=csv,noheader,nounits", "-lms", "200"],
                               stdout=(directory / "gpu.csv").open("w"), stderr=subprocess.DEVNULL)
    started = time.perf_counter()
    try:
        with (directory / "stdout.json").open("w") as out, (directory / "stderr.log").open("w") as err:
            result = subprocess.run(["/usr/bin/time", "-v", "-o", str(directory / "resource.txt"), *command],
                                    stdout=out, stderr=err, cwd=cwd, check=False, timeout=180)
        wall = time.perf_counter() - started
    finally:
        monitor.terminate()
        monitor.wait(timeout=10)
    record = {"command": command, "wall_s": wall, "returncode": result.returncode}
    for line in (directory / "resource.txt").read_text().splitlines():
        for key, label in [("max_rss_kib", "Maximum resident set size (kbytes):"),
                           ("user_s", "User time (seconds):"), ("system_s", "System time (seconds):")]:
            if label in line:
                record[key] = float(line.split(label)[1].strip())
    (directory / "process.json").write_text(json.dumps(record, indent=2) + "\n")
    if result.returncode:
        raise RuntimeError(f"command failed: {directory}: {(directory / 'stderr.log').read_text()[-1200:]}")
    return record


def measure(root: Path) -> None:
    """Run one warm-up and three alternating streaming/staged pairs per workload."""
    source = root / "source"
    cli = root / "target/release/maelstrom"
    probe = root / "target/release/cache-review"
    protocol = {"version": 1, "warmups": 1, "rounds": 3, "steps": 1200, "stride": 4,
                "frames": 301, "numerical_mode": "experimental", "size": [640, 480],
                "alt_size": [1280, 720], "base_commit": "6bf2682325b7665e48f8a8647ce087d48ff13f0b",
                "binaries": {p.name: digest(p) for p in (cli, probe)},
                "limits": "serial cache packing/canonical hashing; render rehashes snapshots; warm OS cache; no cold-disk claim"}
    (root / "protocol.json").write_text(json.dumps(protocol, indent=2) + "\n")
    for scene in ["falling-block-20", "large-impact"]:
        case = root / scene
        case.mkdir()
        request = case / "request.json"
        def streaming(round_index: int, alt: bool = False) -> None:
            label = f"a-{round_index}" + ("-alt" if alt else "")
            run = case / label
            bundle = case / (label + "-bundle")
            command = [str(cli), "compile", f"builtin:{scene}", "--numerical-mode", "experimental", "--backend", "cuda",
                       "--device", "0", "--block-size", "128", "--steps", "1200", "--frame-stride", "4",
                       "--width", "1280" if alt else "640", "--height", "720" if alt else "480",
                       "--output", str(bundle), "--runs-dir", str(case / "library"), "--format", "json"]
            execute(command, run, source)
            manifest = json.loads((bundle / "manifest.json").read_bytes())
            with gzip.open(run / "manifest.json.gz", "wb") as out:
                out.write((bundle / "manifest.json").read_bytes())
            if not request.exists():
                request.write_text(json.dumps(manifest) + "\n")
        def staged(round_index: int) -> None:
            cache = case / f"b-{round_index}-cache"
            for mode in ["bake", "render", "render-alt"]:
                run = case / f"b-{round_index}-{mode}"
                execute([str(probe), mode, str(request), str(cache), str(case / f"b-{round_index}-{mode}-images")], run, source)
        streaming(0)
        staged(0)
        execute([str(probe), "simulate", str(request), str(case / "unused"), str(case / "unused")], case / "simulate-0", source)
        for round_index in range(1, 4):
            for action in ([staged, streaming] if round_index % 2 else [streaming, staged]):
                action(round_index)
            execute([str(probe), "simulate", str(request), str(case / "unused"), str(case / "unused")], case / f"simulate-{round_index}", source)
        streaming(1, alt=True)
    assess(root)


def process_record(path: Path) -> dict:
    """Reject failed or non-finite process observations before reporting timings."""
    record = json.loads(path.read_bytes())
    if record["returncode"] != 0 or not math.isfinite(record["wall_s"]) or record["wall_s"] <= 0:
        raise ValueError(f"invalid process measurement: {path}")
    for key in ["max_rss_kib", "user_s", "system_s"]:
        if not math.isfinite(record[key]) or record[key] < 0:
            raise ValueError(f"invalid resource measurement: {path}")
    return record


def assess(root: Path) -> list[dict]:
    """Check complete matched output identities before calculating process medians."""
    summaries = []
    for scene in ["falling-block-20", "large-impact"]:
        case = root / scene
        samples = []
        expected = None
        for i in range(4):
            with gzip.open(case / f"a-{i}/manifest.json.gz", "rb") as source:
                a = json.load(source)
            bake = json.loads((case / f"b-{i}-bake/stdout.json").read_bytes())
            render = json.loads((case / f"b-{i}-render/stdout.json").read_bytes())
            alt = json.loads((case / f"b-{i}-render-alt/stdout.json").read_bytes())
            if len(a["frames"]) != 301 or a["frames"] != render["frames"]:
                raise ValueError(f"render output differs: {scene}/{i}")
            if a["accepted_diagnostics"] != bake["accepted_diagnostics"]:
                raise ValueError("accepted diagnostic mismatch")
            if [f["snapshot_sha256"] for f in bake["frames"]] != [f["snapshot_sha256"] for f in a["frames"]]:
                raise ValueError("canonical cache mismatch")
            if [f["snapshot_sha256"] for f in alt["frames"]] != [f["snapshot_sha256"] for f in a["frames"]]:
                raise ValueError("alternative-resolution cache mismatch")
            if expected is not None and a["frames"] != expected:
                raise ValueError("control changed between repeats")
            expected = a["frames"]
            record = {"round": i, "warmup": i == 0, "cache_bytes": sum(f["bytes"] for f in bake["frames"]),
                      "streaming_profile": a["timing_profile"], "bake_profile": {k:v for k,v in bake.items() if k not in ("frames", "accepted_diagnostics")},
                      "render_profile": {k:v for k,v in render.items() if k not in ("frames", "render")},
                      "alt_profile": {k:v for k,v in alt.items() if k not in ("frames", "render")}}
            for label, path in [("a", f"a-{i}"), ("bake", f"b-{i}-bake"), ("render", f"b-{i}-render"),
                                ("alt", f"b-{i}-render-alt"), ("simulate", f"simulate-{i}")]:
                record[label] = process_record(case / path / "process.json")
            record["first_staged_s"] = record["bake"]["wall_s"] + record["render"]["wall_s"]
            samples.append(record)
        with gzip.open(case / "a-1-alt/manifest.json.gz", "rb") as source:
            a_alt = json.load(source)
        b_alt = json.loads((case / "b-1-render-alt/stdout.json").read_bytes())
        # Explicit CLI fit at the new aspect ratio is copied into the alternative request
        # by the probe only when supplied; compare snapshots, not different fitted views.
        if [f["snapshot_sha256"] for f in a_alt["frames"]] != [f["snapshot_sha256"] for f in b_alt["frames"]]:
            raise ValueError("alternative-resolution state mismatch")
        measured = samples[1:]
        summaries.append({"scene":scene, "samples":samples,
            "median_s": {k: statistics.median(s[k]["wall_s"] for s in measured) for k in ["a","bake","render","alt","simulate"]},
            "first_staged_median_s":statistics.median(s["first_staged_s"] for s in measured),
            "a_alt_process":process_record(case / "a-1-alt/process.json"),
            "same_camera_pngs_exact":1204, "alternative_resolution_state_hashes_exact":301})
    (root / "summary.json").write_text(json.dumps(summaries, indent=2) + "\n")
    return summaries


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "measure", "assess"])
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    if args.action == "prepare":
        prepare(args.root)
    elif args.action == "measure":
        measure(args.root)
    else:
        assess(args.root)
