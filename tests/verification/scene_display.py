"""Check editable-scene camera persistence through our own native X11 window.

Run from EPQ with python3 -m tests.verification.scene_display. The scene must be
an isolated test package with a saved positive step limit. This check deliberately
saves its camera, then verifies that inspection reads the saved values back.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import tomllib

from tests.verification.viewer_display import X11


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--scene", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--backend", choices=("serial-grid", "threaded-grid", "cuda"), default="serial-grid")
    parser.add_argument("--software", action="store_true")
    args = parser.parse_args()
    if not args.output.is_dir() or any(args.output.iterdir()):
        parser.error("--output must be an existing empty evidence directory")
    scene = args.scene.resolve()
    render = scene.with_name("render.toml")
    original = tomllib.loads(render.read_text())
    document = tomllib.loads(scene.read_text())
    steps = document.get("run", {}).get("steps", 0)
    if steps < 2:
        parser.error("scene needs a saved run.steps of at least two")
    unchanged = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in (scene, scene.with_name("config.toml"))}
    env = os.environ.copy()
    env.pop("WAYLAND_DISPLAY", None)
    env.pop("WAYLAND_SOCKET", None)
    env["MAELSTROM_WINDOW_BACKEND"] = "x11"
    command = [str(args.binary.resolve()), "view", str(scene), "--backend", args.backend, "--paused"]
    if args.software:
        command.append("--software")
    x = X11()
    process = None
    window = None
    observations = []
    try:
        with (args.output / "viewer.log").open("x") as log:
            process = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT)
            window = x.find_window(process)
            observations.append(x.wait(window, rf"gen 1 Paused.*0/{steps} steps"))
            x.capture(window, args.output / "diagnostics.png")
            x.key(window, "h")
            x.capture(window, args.output / "initial.png")
            x.key(window, "n")
            observations.append(x.wait(window, rf"gen 1 Paused.*1/{steps} steps"))
            for key in ("Right", "Up", "equal", "s"):
                x.key(window, key)
            end = time.monotonic() + 30
            while time.monotonic() < end:
                saved = tomllib.loads(render.read_text())
                if saved.get("camera_mode") == "fixed" and "camera" in saved:
                    break
                time.sleep(0.05)
            else:
                raise RuntimeError("camera save did not publish fixed settings")
            for key, value in original.items():
                if key not in ("schema_version", "camera_mode", "camera") and saved.get(key) != value:
                    raise RuntimeError(f"camera save changed unrelated setting {key}")
            inspected = subprocess.run(
                [str(args.binary.resolve()), "inspect", str(scene), "--backend", args.backend, "--format", "json"],
                env=env, capture_output=True, text=True, check=True, timeout=30,
            )
            inspection = json.loads(inspected.stdout)
            effective = inspection["presentation"]["effective"]
            if effective["camera_mode"] != "fixed" or effective["settings"]["camera"] != saved["camera"]:
                raise RuntimeError("inspection did not reload the saved camera")
            x.capture(window, args.output / "saved-camera.png")
            for key in ("f", "Home"):
                x.key(window, key)
            observations.append(x.wait(window, rf"gen 1 Paused.*1/{steps} steps"))
            x.capture(window, args.output / "restored-camera.png")
            x.key(window, "space")
            observations.append(x.wait(window, rf"gen 1 Completed.*{steps}/{steps} steps"))
            x.capture(window, args.output / "completed.png")
            x.key(window, "Escape")
            code = process.wait(timeout=30)
            if code:
                raise RuntimeError(f"viewer shutdown exit: {code}")
        if {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in (scene, scene.with_name("config.toml"))} != unchanged:
            raise RuntimeError("viewing modified physical inputs")
        result = {"command": ["MAELSTROM_BINARY", "view", "SCENE", "--backend", args.backend, "--paused"] + (["--software"] if args.software else []),
                  "exit_code": code, "observations": observations, "physical_files_unchanged": True,
                  "saved_camera_reloaded": True, "unrelated_presentation_preserved": True,
                  "camera": saved["camera"], "binary_sha256": hashlib.sha256(args.binary.read_bytes()).hexdigest()}
        (args.output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        print("Editable scene, camera save and native viewer journey passed", flush=True)
    finally:
        if process is not None and process.poll() is None:
            if window is not None:
                x.key(window, "Escape")
            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                print(f"Own viewer process still live: PID {process.pid}", flush=True)
        x.lib.XCloseDisplay(x.display)


if __name__ == "__main__":
    main()
