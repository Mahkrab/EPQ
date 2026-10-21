"""Check saved-image controls through native events sent only to our own window.

Run from the EPQ root with python3 -m tests.verification.playback_display.
The existing X11 harness supplies event delivery and drawable screenshots; this
journey never runs a scene and verifies that its input files stay unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

from tests.verification.viewer_display import X11


def inventory(root: Path) -> dict[str, str]:
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.iterdir()) if p.is_file()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--sequence", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--runtime-lib-dir", type=Path)
    args = parser.parse_args()
    if not args.output.is_dir() or any(args.output.iterdir()):
        parser.error("--output must be an existing empty evidence directory")
    sequence = args.sequence.resolve()
    manifest = json.loads((sequence / "manifest.json").read_text())
    if manifest["frame_count"] < 3:
        parser.error("the control journey needs at least three recorded frames")
    before = inventory(sequence)
    env = os.environ.copy()
    for key in ("WAYLAND_DISPLAY", "WAYLAND_SOCKET"):
        env.pop(key, None)
    if args.runtime_lib_dir:
        env["LD_LIBRARY_PATH"] = str(args.runtime_lib_dir.resolve())
    command = [str(args.binary.resolve()), "play", str(sequence), "--software", "--paused"]
    x = X11()
    process = None
    window = None
    try:
        with (args.output / "player.log").open("x") as log:
            process = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT)
            window = x.find_window(process)
            count = manifest["frame_count"]
            x.wait(window, rf"paused.*frame 1/{count}.*step 0.*1.00x")
            x.capture(window, args.output / "initial.png")
            x.key(window, "Right")
            x.wait(window, rf"paused.*frame 2/{count}.*step {manifest['frames'][1]['step']}")
            x.key(window, "Left")
            x.wait(window, rf"paused.*frame 1/{count}")
            x.key(window, "End")
            x.wait(window, rf"paused.*frame {count}/{count}.*step {manifest['accepted_steps']}")
            x.capture(window, args.output / "final.png")
            x.lib.XResizeWindow(x.display, window, 600, 600)
            x.lib.XFlush(x.display)
            x.capture(window, args.output / "resized.png")
            x.key(window, "Home")
            x.wait(window, rf"paused.*frame 1/{count}")
            x.key(window, "equal")
            x.wait(window, r"paused.*2.00x")
            x.key(window, "minus")
            x.wait(window, r"paused.*1.00x")
            x.key(window, "r")
            x.wait(window, r"playing")
            x.key(window, "space")
            x.wait(window, r"paused")
            x.key(window, "space")
            x.wait(window, r"playing")
            x.wait(window, rf"paused.*frame {count}/{count}")
            x.key(window, "Escape")
            code = process.wait(timeout=30)
            if code != 0:
                raise RuntimeError(f"playback shutdown exit: {code}")
        if inventory(sequence) != before:
            raise RuntimeError("playback modified its saved sequence")
        result = {"command": ["MAELSTROM_BINARY", "play", "EXPORTED_SEQUENCE", "--software", "--paused"],
                  "exit": code, "sequence_files_unchanged": True,
                  "frames": count, "checks": ["initial", "seek", "endpoints", "resize",
                  "speed", "restart", "pause", "resume", "completion", "close"],
                  "binary_sha256": hashlib.sha256(args.binary.read_bytes()).hexdigest(),
                  "sequence_sha256": before}
        with (args.output / "result.json").open("x") as output:
            json.dump(result, output, indent=2)
        print("Saved-image playback journey passed; source files unchanged", flush=True)
    finally:
        if process is not None and process.poll() is None:
            if window is not None:
                x.key(window, "Escape")
            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                print(f"Own playback process still live: PID {process.pid}", flush=True)
        x.lib.XCloseDisplay(x.display)


if __name__ == "__main__":
    main()
