"""Check native client pixels, resize and cooperative close without keyboard focus.

This journey does not establish physical desktop visibility or input-to-scan-out
latency. Keyboard and camera controls need a working desktop focus path separately.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import time

from tools.performance.live_viewer import Window
from tests.verification.viewer_display import X11


def check(binary: Path, scene: Path, output: Path) -> None:
    output.mkdir(parents=True,exist_ok=False)
    records = []
    for paused in (True,False):
        label = "paused" if paused else "running"
        env = dict(os.environ,MAELSTROM_WINDOW_BACKEND="x11",
                   MAELSTROM_VIEW_PROFILE=str(output / f"{label}.csv"))
        command = [str(binary),"view",str(scene),"--backend","cuda","--numerical-mode","experimental",
                   "--steps","100000","--width","1280","--height","720"]
        if paused:
            command.append("--paused")
        with (output / f"{label}.log").open("x",encoding="utf-8") as log:
            process = subprocess.Popen(command,env=env,stdout=log,stderr=subprocess.STDOUT)
            window = None
            x = X11()
            try:
                window = Window(process)
                initial = window.wait("Paused" if paused else "Running")
                x.capture(window.window,output / f"{label}-1280.png")
                x.lib.XResizeWindow(x.display,window.window,1000,680)
                x.lib.XSync(x.display,False)
                time.sleep(.2)
                x.capture(window.window,output / f"{label}-1000.png")
                resized = window.title()
                window.request_close()
                process.wait(timeout=30)
                if process.returncode:
                    raise RuntimeError(f"native viewer failed: {process.returncode}")
                records.append(dict(paused=paused,initial=initial,resized=resized,
                                    clean_close=True,command=command))
            finally:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=10)
                if window:
                    window.close()
                x.lib.XCloseDisplay(x.display)
    (output / "native.json").write_text(json.dumps(records,indent=2)+"\n",encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary",type=Path,required=True)
    parser.add_argument("--scene",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args = parser.parse_args()
    check(args.binary.resolve(),args.scene.resolve(),args.output.resolve())


if __name__ == "__main__":
    main()
