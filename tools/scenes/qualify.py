"""Compile the shipped catalogue and compare packaged inputs with their file form.

Runs use an isolated application library. Completed bundles remain in the requested
work directory; the small receipt records checks without copying every PNG.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def qualify(binary: Path, source: Path, work: Path) -> None:
    work.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, XDG_CONFIG_HOME=str(work / "settings"),
               XDG_DATA_HOME=str(work / "data"))
    for key in ("MAELSTROM_SCENES_DIR", "MAELSTROM_RUNS_DIR"):
        env.pop(key, None)

    def run(args, label):
        started = time.monotonic()
        result = subprocess.run([str(binary), *args, "--format", "json"],
                                env=env, capture_output=True, text=True, timeout=600)
        (work / f"{label}.stdout.json").write_text(result.stdout)
        (work / f"{label}.stderr.txt").write_text(result.stderr)
        if result.returncode:
            raise RuntimeError(f"{label}: {result.stderr}")
        return json.loads(result.stdout), time.monotonic() - started

    receipt = {"binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
               "source": str(source), "cases": []}
    scenes = sorted(p.parent for p in (source / "scenes").glob("*/scene.toml"))
    for scene in scenes:
        name = scene.name
        inspect, _ = run(["inspect", f"builtin:{name}", "--backend", "cuda"], name + "-inspect")
        effective = inspect["presentation"]["effective"]
        assert effective["camera_mode"] == "fit"
        assert effective["particles"]["colour_mode"] == "kinetic_energy"
        frames = {}
        wall = {}
        for variant, selector, extra in (
            ("fast", f"builtin:{name}", []),
            ("file", str(scene / "scene.toml"), ["--steps", "4"]),
            ("reference", f"builtin:{name}", ["--frame-stride", "8", "--numerical-mode", "reference"]),
        ):
            bundle = work / (name + "-" + variant)
            _, wall[variant] = run(["compile", selector, "--backend", "cuda", "--width", "640",
                                   "--height", "480", "--output", str(bundle), *extra], name + "-" + variant)
            manifest = json.loads((bundle / "manifest.json").read_text())
            run(["runs", "validate", str(bundle)], name + "-" + variant + "-validate")
            frames[variant] = manifest["frames"]
        assert len(frames["reference"]) == 181, (name, len(frames["reference"]))
        for a, b in zip(frames["fast"], frames["file"], strict=False):
            assert a == b, (name, a, b)
        assert len(frames["fast"]) == 181, (name, len(frames["fast"]))
        receipt["cases"].append({"name": name, "wall_seconds": wall,
                                 "default_frames": len(frames["fast"]),
                                 "packaged_file_frames_exact": True,
                                 "bundle_validation": "passed in all three cases",
                                 "frames": frames["fast"]})
        (work / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
        print(name, wall, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    args = parser.parse_args()
    qualify(args.binary.resolve(), args.source.resolve(), args.work.resolve())
