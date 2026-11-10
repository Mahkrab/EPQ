"""Run hardware journeys, soak, video and failure checks after the timing campaign.

All outputs and optional FFmpeg wrappers live in the supplied experiment directory.
No installed application, system graphics configuration or existing cache is changed.
"""
import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess

from tools.performance.cached_faults import qualify
from tools.performance.cached_journey import journey
from tools.performance.cached_playback import run
from tools.performance.cached_video_campaign import campaign


def execute(root: Path, existing: Path, resume: bool = False):
    root=root.resolve()
    existing=existing.resolve()
    binary=root/"delivery-maelstrom"
    cache=existing/"runs/large-impact/b-1-cache"
    wrappers=root/"bin"
    wrappers.mkdir(exist_ok=resume)
    library=root/"ffmpeg-root/usr/lib/x86_64-linux-gnu"
    search=":".join(str(p) for p in [library,library/"blas",library/"lapack"])
    for name in ["ffmpeg","ffprobe"]:
        path=wrappers/name
        text="#!/bin/sh\nexec env "+shlex.quote("LD_LIBRARY_PATH="+search)+" "+shlex.quote(str(root/"ffmpeg-root/usr/bin"/name))+' "$@"\n'
        if path.exists() and path.read_text()!=text:
            raise ValueError("existing FFmpeg wrapper differs from this request")
        path.write_text(text)
        path.chmod(0o700)
    os.environ["PATH"]=str(wrappers)+os.pathsep+os.environ["PATH"]
    subprocess.run(["cc","-shared","-fPIC","-Wall","-Wextra","-O2",str(root/"tools/performance/delay_cache_reads.c"),"-ldl","-o",str(root/"delay-reads.so")],check=True)
    print("camera journey",flush=True)
    if not (resume and (root/"journey/result.json").exists()):
        journey(binary,cache,root/"journey")
    print("delayed-read camera journey",flush=True)
    if not (resume and (root/"journey-delayed/result.json").exists()):
        journey(binary,cache,root/"journey-delayed",root/"delay-reads.so")
    print("large-cache memory soak",flush=True)
    if not (resume and (root/"soak-110592/summary.json").exists()):
        run(argparse.Namespace(binary=binary,cache=cache,output=root/"soak-110592",width=1920,height=1080,
                               seconds=120,speed=4,terminal=5.000000260770321,mode=None))
    print("frame-accurate playback",flush=True)
    if not (resume and (root/"frame-accurate-110592/summary.json").exists()):
        run(argparse.Namespace(binary=binary,cache=cache,output=root/"frame-accurate-110592",width=1920,height=1080,
                               seconds=8,speed=4,terminal=5.000000260770321,mode="frame-accurate"))
    print("video matrix",flush=True)
    campaign(root,existing,binary,wrappers/"ffmpeg",wrappers/"ffprobe",root/"journey/camera.toml")
    print("failure and lifecycle checks",flush=True)
    qualify(root,binary,wrappers/"ffmpeg")
    print("post-timing qualification complete",flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--existing",type=Path,required=True)
    parser.add_argument("--resume",action="store_true",help="reuse completed journey/soak results and identical wrappers")
    args=parser.parse_args()
    execute(args.root,args.existing,args.resume)
