"""Retain independent decode, identity and diagnostic summaries after qualification.

Raw RGBA preparation is outside FFmpeg timing. A separately invoked encoder checks
the application's frame order without executing fluid physics or sharing its loop.
"""
import argparse
import json
import os
from pathlib import Path
import re
import statistics
import subprocess
import time
from types import SimpleNamespace

from tools.performance.cached_playback import assess, read_trace, run
from tools.performance.cached_video_campaign import measure
from tools.performance.live_viewer import Window, percentile, process_resources


def ordinary(binary: Path, cache: Path, directory: Path):
    """Observe source time from titles with application tracing disabled."""
    directory.mkdir()
    command=[str(binary),"view","--cache",str(cache),"--paused","--width","1920","--height","1080"]
    env={**os.environ,"WINIT_UNIX_BACKEND":"x11","WAYLAND_DISPLAY":""}
    env.pop("MAELSTROM_CACHE_TRACE",None)
    with (directory/"viewer.log").open("w") as log:
        p=subprocess.Popen(command,env=env,stdout=log,stderr=log)
        window=None
        try:
            window=Window(p)
            window.wait("ready")
            for key in ["bracketright","bracketright","l","space"]:
                window.key(key)
            time.sleep(1)
            begin=time.monotonic()
            samples=[]
            while time.monotonic()-begin<8:
                title=window.title()
                match=re.search(r"\| ([0-9.]+) simulation s",title)
                if not match:
                    raise ValueError("cached viewer title no longer supplies source time")
                samples.append(dict(wall_s=time.monotonic()-begin,simulation_s=float(match[1]),title=title,**process_resources(p.pid)))
                time.sleep(.02)
            progress=sum(b["simulation_s"]-a["simulation_s"] if b["simulation_s"]>=a["simulation_s"] else 5.000000260770321-a["simulation_s"]+b["simulation_s"] for a,b in zip(samples,samples[1:]))
            elapsed=samples[-1]["wall_s"]-samples[0]["wall_s"]
            result=dict(command=command,trace_enabled=False,timeline_simulation_s_per_wall_s=progress/elapsed,
                        cpu_core_equivalents=(samples[-1]["cpu_s"]-samples[0]["cpu_s"])/elapsed,
                        peak_rss_mib=max(s["peak_rss_kib"] for s in samples)/1024,
                        boundary="20 ms title polling; no submission/physical-display count")
            (directory/"samples.json").write_text(json.dumps(samples,indent=2)+"\n")
            (directory/"summary.json").write_text(json.dumps(result,indent=2)+"\n")
            window.request_close()
            p.wait(timeout=20)
            if p.returncode:
                raise RuntimeError("ordinary viewer check failed")
        finally:
            if p.poll() is None:
                p.kill()
                p.wait()
            if window:
                window.close()


def decode(path: Path) -> bytes:
    return subprocess.check_output(["ffmpeg","-v","error","-i",str(path),"-f","framemd5","pipe:1"],timeout=60)


def verify(root: Path, existing: Path):
    root=root.resolve()
    existing=existing.resolve()
    os.environ["PATH"]=str(root/"bin")+os.pathsep+os.environ["PATH"]
    binary=root/"final-maelstrom"
    rows=[]
    for path in sorted(root.glob("candidate-*-p*/protocol.json")):
        rows.append(dict(name=path.parent.name,**assess(path.parent)))
    for path in sorted(root.glob("control-*-p*/protocol.json")):
        rows.append(dict(name=path.parent.name,**assess(path.parent)))
    (root/"playback-final-summary.json").write_text(json.dumps(rows,indent=2)+"\n")
    gpu=[]
    for path in sorted(root.glob("gpu-*/viewer.log")):
        times=[float(line.split()[1])/1e6 for line in path.read_text().splitlines() if line.startswith("gpu-draw-ns ")]
        if not times or any(t<=0 for t in times):
            raise ValueError("GPU diagnostic returned missing/nonpositive timestamps")
        # Remove setup/initial empty scene draws from the diagnostic summary.
        times=times[30:]
        gpu.append(dict(name=path.parent.name,draws=len(times),median_ms=statistics.median(times),p95_ms=percentile(times,.95)))
    for path in sorted(root.glob("gpu-video-*/stderr.txt")):
        lines=path.read_text().splitlines()
        times=[float(line.split()[1])/1e6 for line in lines if line.startswith("gpu-draw-ns ")]
        frames=[float(line.split()[2]) for line in lines if line.startswith("video-frame-seconds ")]
        gpu.append(dict(name=path.parent.name,draws=len(times),median_ms=statistics.median(times),p95_ms=percentile(times,.95),
                        cpu_frame_mean_ms=1000*statistics.mean(frames)))
    (root/"gpu-summary.json").write_text(json.dumps(gpu,indent=2)+"\n")
    caches={8000:existing/"runs/falling-block-20/b-1-cache",32000:root/"cache32000",110592:existing/"runs/large-impact/b-1-cache"}
    for count,cache in caches.items():
        measure([str(binary),"--format","json","cache","validate",str(cache),"--full"],root/f"full-validation-{count}",root)
    reference=root/"independent-reference"
    reference.mkdir()
    images=root/"video-source-images-110592"
    raw=reference/"640x480.rgba"
    subprocess.run(["ffmpeg","-v","error","-nostdin","-n","-framerate","60","-i",str(images/"frame-%08d.png"),"-f","rawvideo","-pix_fmt","rgba",str(raw)],check=True,timeout=120)
    if raw.stat().st_size!=301*640*480*4:
        raise ValueError("independent raw frame count differs")
    for width,height in [(640,480),(1280,720),(1920,1080)]:
        directory=root/f"ffmpeg-only-{height}"
        measure([str(root/"bin/ffmpeg"),"-v","error","-nostdin","-n","-f","rawvideo","-pixel_format","rgba","-video_size","640x480","-framerate","60",
                 "-i",str(raw),"-an","-vf",f"scale={width}:{height}","-c:v","libx264","-crf","18","-pix_fmt","yuv420p","-movflags","+faststart",str(directory/"movie.mp4")],directory,root)
    full=decode(root/"ffmpeg-only-480/movie.mp4")
    (reference/"full.framemd5").write_bytes(full)
    for path in [root/"video-cache-110592-480/movie.mp4",root/"video-images-110592-480/movie.mp4"]:
        if decode(path)!=full:
            raise ValueError("application frame order/pixels differ from independent full encode")
    selected=[17,21,25,29]
    sparse=reference/"sparse.mp4"
    subprocess.run(["ffmpeg","-v","error","-nostdin","-n","-f","image2pipe","-vcodec","png","-framerate","60","-i","pipe:0","-an","-vf","scale=640:480",
                    "-c:v","libx264","-crf","18","-pix_fmt","yuv420p","-movflags","+faststart",str(sparse)],
                   input=b"".join((images/f"frame-{i:08}.png").read_bytes() for i in selected),check=True,timeout=60)
    sparse_hashes=decode(sparse)
    (reference/"sparse.framemd5").write_bytes(sparse_hashes)
    for path in [root/"selection-cache-sparse/movie.mp4",root/"selection-images-sparse/movie.mp4"]:
        if decode(path)!=sparse_hashes:
            raise ValueError("sparse application frames differ from independent selected-PNG encode")
    (root/"independent-decode.json").write_text(json.dumps(dict(full_frames=301,sparse_indices=selected,decoded_paths_match=True),indent=2)+"\n")
    # Supplementary parent/encoder sampling stays separate from the original matrix.
    for source in ["cache","images"]:
        directory=root/f"video-memory-{source}-1080"
        command=[str(binary),"--format","json","video",source,str(caches[110592] if source=="cache" else images),"--ffmpeg",str(root/"bin/ffmpeg"),
                 "--width","1920","--height","1080","-o",str(directory/"movie.mp4")]
        if source=="cache":
            command += ["--render-config",str(root/"journey/camera.toml")]
        measure(command,directory,root)
    for speed in [1,4]:
        run(SimpleNamespace(binary=binary,cache=caches[110592],output=root/f"final-view-1080-{speed}x",width=1920,height=1080,
                            seconds=8,speed=speed,terminal=5.000000260770321,mode=None))
    ordinary(binary,caches[110592],root/"final-view-untraced")
    frames=[e["index"] for e in read_trace(root/"frame-accurate-110592/viewer.log") if e["event"]=="present"]
    if any(b!=a and b!=(a+1)%301 for a,b in zip(frames,frames[1:])):
        raise ValueError("frame-accurate playback skipped an observation")
    print(json.dumps(dict(gpu=gpu,independent_decode="passed"),indent=2))


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--existing",type=Path,required=True)
    args=parser.parse_args()
    verify(args.root,args.existing)
