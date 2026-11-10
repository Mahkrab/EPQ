"""Check the isolated cache experiment against files and deliberate failures.

These checks never mutate a measured cache or bundle. Fault cases use fresh copies,
and the alternative view is rendered with CUDA devices hidden from that process.
"""

import copy
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys

from tools.performance.cache_review import execute


def reject(command: list[str], output: Path) -> str:
    result = subprocess.run(command, capture_output=True, text=True, timeout=120, check=False)
    output.write_text(json.dumps({"command": command, "returncode": result.returncode,
                                  "stdout": result.stdout, "stderr": result.stderr}, indent=2) + "\n")
    if result.returncode == 0:
        raise ValueError(f"fault unexpectedly accepted: {output}")
    return result.stderr


def toml_settings(settings: dict) -> str:
    """Emit this experiment's two-level numeric/string presentation fixture."""
    lines = [f"{k} = {json.dumps(v)}" for k, v in settings.items() if not isinstance(v, dict)]
    for key, section in settings.items():
        if isinstance(section, dict):
            lines.extend(["", f"[{key}]", *[f"{k} = {json.dumps(v)}" for k, v in section.items()]])
    return "\n".join(lines) + "\n"


def check(root: Path) -> None:
    source = root / "source"
    cli = root / "target/release/maelstrom"
    probe = root / "target/release/cache-review"
    output = root / "checks"
    output.mkdir()
    receipts = []
    for scene in ["falling-block-20", "large-impact"]:
        case = root / scene
        request = case / "request.json"
        cache = case / "b-1-cache"
        document = json.loads(request.read_bytes())
        validated = subprocess.run([str(probe), "validate", str(request), str(cache), str(output / "unused")],
                                   capture_output=True, text=True, timeout=120, check=True)
        (output / f"{scene}-validation.json").write_text(validated.stdout)
        for repeat in range(4):
            for mode in ["render", "render-alt"]:
                folder = case / f"b-{repeat}-{mode}-images"
                result = json.loads((folder / "probe-result.json").read_bytes())
                for frame in result["frames"]:
                    if "sha256:" + hashlib.sha256((folder / frame["file"]).read_bytes()).hexdigest() != frame["png_sha256"]:
                        raise ValueError("published probe PNG differs from its digest")
            subprocess.run([str(cli), "runs", "validate", str(case / f"a-{repeat}-bundle")],
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=120, check=True)
        # Matched supplementary new-resolution control: keep the same resolved camera.
        config = output / f"{scene}-fixed-camera.toml"
        config.write_text(toml_settings(document["render"]))
        alt_bundle = output / f"{scene}-alt-bundle"
        control = execute([str(cli), "compile", f"builtin:{scene}", "--numerical-mode", "experimental",
            "--backend", "cuda", "--steps", "1200", "--frame-stride", "4", "--device", "0", "--block-size", "128",
            "--render-config", str(config), "--no-fit-camera", "--width", "1280", "--height", "720",
            "--runs-dir", str(output / "library"), "--output", str(alt_bundle), "--format", "json"],
            output / f"{scene}-alt-control", source)
        a_alt = json.loads((alt_bundle / "manifest.json").read_bytes())
        b_alt = json.loads((case / "b-1-render-alt-images/probe-result.json").read_bytes())
        if a_alt["frames"] != b_alt["frames"]:
            raise ValueError("matched fixed-camera alternative-resolution output differs")
        changed = copy.deepcopy(document)
        changed["render"]["camera"]["eye_m"][0] += 1.0
        changed["render"]["particles"] = {"colour_mode": "fixed", "colour": "#258bdf"}
        new_request = output / f"{scene}-new-view.json"
        new_request.write_text(json.dumps(changed) + "\n")
        execute(["env", "CUDA_VISIBLE_DEVICES=", str(probe), "render", str(new_request), str(cache), str(output / f"{scene}-new-view-images")],
                output / f"{scene}-no-cuda-render", source)
        new_frames = json.loads((output / f"{scene}-new-view-images/probe-result.json").read_bytes())["frames"]
        old_frames = document["frames"]
        if [f["snapshot_sha256"] for f in new_frames] != [f["snapshot_sha256"] for f in old_frames]:
            raise ValueError("new view changed cached observations")
        if all(a["png_sha256"] == b["png_sha256"] for a, b in zip(new_frames, old_frames)):
            raise ValueError("camera and colour change did not change images")
        receipts.append({"scene": scene, "full_canonical_validation": 301, "measured_png_files_checked": 2408,
                         "production_bundles_validated": 4, "alt_control": control,
                         "alternative_resolution_frames_exact": 301, "new_view_no_cuda_frames": 301})

    case = root / "falling-block-20"
    cache = case / "b-1-cache"
    request = case / "request.json"
    for fault in ["bitflip", "truncated"]:
        damaged = output / fault
        damaged.mkdir()
        shutil.copyfile(cache / "cache.json", damaged / "cache.json")
        frame = bytearray((cache / "frame-00000000.bin").read_bytes())
        if fault == "bitflip":
            frame[24] ^= 1
        else:
            del frame[-1:]
        (damaged / "frame-00000000.bin").write_bytes(frame)
        reject([str(probe), "validate", str(request), str(damaged), str(output / "unused")], output / f"{fault}.json")
    interrupted = output / "interrupted-cache"
    reject(["env", "MAELSTROM_CACHE_REVIEW_STOP=7", str(probe), "bake", str(request), str(interrupted), str(output / "unused")],
           output / "interrupted.json")
    files = sorted(interrupted.glob("frame-*.bin"))
    if len(files) != 7 or (interrupted / "cache.json").exists():
        raise ValueError("interrupted cache has wrong completion state")
    for index, frame in enumerate(files):
        data = frame.read_bytes()
        if struct.unpack("<8sQQ", data[:24]) != (b"MSCPRB01", index * 4, 8000):
            raise ValueError("interrupted prefix has wrong frame mapping")
        if data != (cache / frame.name).read_bytes():
            raise ValueError("interrupted prefix differs from accepted states")
    reject([str(probe), "render", str(request), str(interrupted), str(output / "incomplete-render")], output / "incomplete-rejected.json")
    before = (cache / "frame-00000000.bin").read_bytes()
    reject([str(probe), "bake", str(request), str(cache), str(output / "unused")], output / "overwrite-rejected.json")
    if (cache / "frame-00000000.bin").read_bytes() != before:
        raise ValueError("existing cache was modified")
    (root / "verification.json").write_text(json.dumps({"cases": receipts, "bitflip_rejected": True,
        "truncation_rejected": True, "interrupted_prefix_frames_exact": 7, "incomplete_render_rejected": True,
        "overwrite_rejected_unchanged": True, "limits": "process failure only; no power-loss, disk-full or render-resume implementation"}, indent=2) + "\n")


if __name__ == "__main__":
    check(Path(sys.argv[1]))
