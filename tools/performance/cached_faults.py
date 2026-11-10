"""Qualify launched-process failures without modifying a user's caches or system.

Small private cache copies supply corrupt, missing and partial inputs. SIGINT
targets only the encoder process launched here; child reaping and publication
cleanup are observed after it returns.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time

from tools.performance.live_viewer import Window


def qualify(root: Path, binary: Path, ffmpeg: Path):
    output=root/"faults"
    output.mkdir()
    env={**os.environ,"WINIT_UNIX_BACKEND":"x11","WAYLAND_DISPLAY":""}
    results=[]
    def call(name,args,expected):
        result=subprocess.run([str(binary),"--format","json",*args],env=env,capture_output=True,timeout=30)
        (output/f"{name}.stdout").write_bytes(result.stdout)
        (output/f"{name}.stderr").write_bytes(result.stderr)
        if result.returncode!=expected:
            raise RuntimeError(f"{name}: exit {result.returncode}, expected {expected}: {result.stderr[-1000:]}")
        results.append(dict(name=name,exit_code=result.returncode))
    cache=output/"small-cache"
    call("bake",["cache","bake","builtin:falling-block-04","--backend","serial-grid","--steps","12","--frame-stride","4","-o",str(cache)],0)
    for defect in ["missing","corrupt"]:
        copied=output/defect
        shutil.copytree(cache,copied)
        frame=copied/"frames/frame-00000001.mpc"
        if defect=="missing":
            frame.unlink()
        else:
            frame.write_bytes(b"corrupt")
        call("view-"+defect,["view","--cache",str(copied),"--paused"],3)
    partial=output/"partial"
    shutil.copytree(cache,partial)
    (partial/"cache.json").rename(partial/"original-completion.json")
    (partial/"frames/frame-00000003.mpc").unlink()
    (partial/"receipts/frame-00000003.json").unlink()
    call("partial-rejected",["view","--cache",str(partial),"--paused"],3)
    call("partial-validated",["cache","validate",str(partial),"--allow-partial","--full"],0)
    for i in range(6):
        with (output/f"cycle-{i}.log").open("w") as log:
            p=subprocess.Popen([str(binary),"view","--cache",str(partial),"--allow-partial","--paused"],env=env,stdout=log,stderr=log)
            window=None
            try:
                window=Window(p)
                window.wait("ready")
                window.key("End")
                window.wait(r"frame 2/2.*ready")
                started=time.monotonic()
                window.request_close()
                p.wait(timeout=15)
                if p.returncode:
                    raise RuntimeError(f"open/close cycle failed: {p.returncode}")
                results.append(dict(name=f"open-close-{i}",close_s=time.monotonic()-started,exit_code=p.returncode))
            finally:
                if p.poll() is None:
                    p.kill()
                    p.wait()
                if window:
                    window.close()
    images=root/"video-source-images-110592"
    for name,encoder in [("missing-encoder",output/"absent-ffmpeg"),("encoder-failure",output/"fail-ffmpeg"),("missing-codec",output/"no-codec")]:
        if name!="missing-encoder":
            text="#!/bin/sh\ncase \"$1\" in\n-version) echo qualification; exit 0;;\n-hide_banner) if [ \"$2\" = -encoders ]; then echo ' V " + ("libx264" if name=="encoder-failure" else "unavailable") + "'; exit 0; fi;;\nesac\necho 'injected encoder failure' >&2\nexit 23\n"
            encoder.write_text(text)
            encoder.chmod(0o700)
        call(name,["video","images",str(images),"--ffmpeg",str(encoder),"-o",str(output/f"{name}.mp4")],5)
        if (output/f"{name}.mp4").exists():
            raise RuntimeError("failed export published a video")
    video=output/"cancelled.mp4"
    with (output/"cancel.log").open("w") as log:
        p=subprocess.Popen([str(binary),"video","images",str(images),"--ffmpeg",str(ffmpeg),"--width","1920","--height","1080","-o",str(video)],env=env,stdout=log,stderr=log)
        children=[]
        try:
            deadline=time.monotonic()+15
            while time.monotonic()<deadline and p.poll() is None:
                children=Path(f"/proc/{p.pid}/task/{p.pid}/children").read_text().split()
                if children and list(output.glob(".maelstrom-video-*")):
                    break
                time.sleep(.01)
            if not children:
                raise RuntimeError("FFmpeg child did not start")
            time.sleep(.25)
            begin=time.monotonic()
            p.send_signal(signal.SIGINT)
            p.wait(timeout=15)
            if p.returncode!=130 or video.exists() or Path(str(video)+".json").exists():
                raise RuntimeError("cancelled video was not cleaned up with exit 130")
            if any(Path(f"/proc/{child}").exists() for child in children) or list(output.glob(".maelstrom-video-*")):
                raise RuntimeError("cancelled encoder child or staging directory survived")
            results.append(dict(name="SIGINT-during-real-encoding",exit_code=p.returncode,cleanup_s=time.monotonic()-begin,children_reaped=children))
        finally:
            if p.poll() is None:
                p.kill()
                p.wait()
    (output/"result.json").write_text(json.dumps(results,indent=2)+"\n")
    return results


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ["root","binary","ffmpeg"]:
        parser.add_argument("--"+name,type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(qualify(args.root.resolve(),args.binary.resolve(),args.ffmpeg.resolve()),indent=2))
