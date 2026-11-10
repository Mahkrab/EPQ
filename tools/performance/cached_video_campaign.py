"""Measure complete cache/video commands and independently probe every MP4.

Image production is a separate setup measurement. Encoding uses the requested
FFmpeg executable, with no installation or automatic encoder substitution.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

from tools.performance.cache_pipeline import invoke


def measure(command: list[str], destination: Path, cwd: Path) -> dict:
    """Sample application/encoder RSS separately; GNU time includes child CPU work."""
    destination.mkdir()
    samples=[]
    observed=[]
    with (destination/"stdout.json").open("w") as out, (destination/"stderr.txt").open("w") as err:
        started=time.monotonic()
        process=subprocess.Popen(["/usr/bin/time","-v","-o",str(destination/"resource.txt"),*command],cwd=cwd,stdout=out,stderr=err)
        try:
            while process.poll() is None:
                if time.monotonic()-started>240:
                    raise TimeoutError("video command exceeded 240 s")
                pending=[process.pid]
                observed=[]
                while pending:
                    pid=pending.pop()
                    try:
                        base=Path(f"/proc/{pid}")
                        pending.extend(int(p) for p in (base/f"task/{pid}/children").read_text().split())
                        status=(base/"status").read_text().splitlines()
                        stat=(base/"stat").read_text().rsplit(")",1)[1].split()
                        values={s.split(":",1)[0]:s.split(":",1)[1].strip() for s in status}
                        observed.append(dict(pid=pid,name=values["Name"],rss_kib=int(values.get("VmRSS","0 kB").split()[0]),
                                             hwm_kib=int(values.get("VmHWM","0 kB").split()[0]),
                                             cpu_s=(int(stat[11])+int(stat[12]))/os.sysconf("SC_CLK_TCK")))
                    except FileNotFoundError:
                        pass
                samples.append(dict(wall_s=time.monotonic()-started,processes=observed))
                time.sleep(.05)
            elapsed=time.monotonic()-started
        finally:
            if process.poll() is None:
                # Timeout cleanup includes only descendants captured for this run.
                for child in observed:
                    if child["pid"] == process.pid:
                        continue
                    try:
                        os.kill(child["pid"],9)
                    except ProcessLookupError:
                        pass
                process.kill()
                process.wait()
    record=dict(command=command,wall_s=elapsed,returncode=process.returncode,
                sampled_parent_peak_rss_mib=max((p["rss_kib"] for s in samples for p in s["processes"] if p["name"] not in ["time","ffmpeg"]),default=0)/1024,
                sampled_encoder_peak_rss_mib=max((p["rss_kib"] for s in samples for p in s["processes"] if p["name"]=="ffmpeg"),default=0)/1024)
    for line in (destination/"resource.txt").read_text().splitlines():
        for key,label in [("rss_kib","Maximum resident set size (kbytes):"),("user_s","User time (seconds):"),("system_s","System time (seconds):")]:
            if label in line:
                record[key]=float(line.split(label)[1].strip())
    (destination/"samples.json").write_text(json.dumps(samples,indent=2)+"\n")
    (destination/"process.json").write_text(json.dumps(record,indent=2)+"\n")
    if process.returncode:
        raise RuntimeError(f"video failed: {destination}: {(destination/'stderr.txt').read_text()[-1000:]}")
    return record


def probe(video: Path, executable: Path) -> dict:
    result=subprocess.run([str(executable),"-v","error","-count_frames","-show_streams","-show_frames","-of","json",str(video)],
                          capture_output=True,check=True,timeout=120)
    data=json.loads(result.stdout)
    sidecar=json.loads(Path(str(video)+".json").read_text())
    stream=data["streams"][0]
    frames=data["frames"]
    expected=sidecar["frame_count"]
    fps=sidecar["timing"]["fps"]
    if (stream["codec_name"],stream["pix_fmt"],stream["width"],stream["height"],len(frames)) != ("h264","yuv420p",*sidecar["output_dimensions"],expected):
        raise ValueError("independent MP4 stream checks disagree with provenance")
    if abs(float(stream["duration"])-expected/fps)>1e-5:
        raise ValueError("MP4 duration disagrees with CFR policy")
    for i,frame in enumerate(frames):
        if abs(float(frame["best_effort_timestamp_time"])-i/fps)>1e-5:
            raise ValueError("decoded frame timestamps are not ordered CFR")
    (video.parent/"ffprobe.json").write_bytes(result.stdout)
    return dict(codec=stream["codec_name"],pixel_format=stream["pix_fmt"],frame_count=len(frames),
                duration_s=float(stream["duration"]),dimensions=sidecar["output_dimensions"],
                sha256=hashlib.sha256(video.read_bytes()).hexdigest())


def campaign(root: Path, existing: Path, binary: Path, ffmpeg: Path, ffprobe: Path, camera: Path):
    caches={8000:existing/"runs/falling-block-20/b-1-cache",32000:root/"cache32000",110592:existing/"runs/large-impact/b-1-cache"}
    results=[]
    for count,cache in caches.items():
        images=root/f"video-source-images-{count}"
        invoke([str(binary),"--format","json","render",str(cache),"--render-config",str(camera),
                "--width","640","--height","480","-o",str(images)],root/f"video-images-setup-{count}",root)
        for width,height in [(640,480),(1280,720),(1920,1080)]:
            for source in ["cache","images"]:
                name=f"video-{source}-{count}-{height}"
                output=root/name/"movie.mp4"
                command=[str(binary),"--format","json","video",source,str(cache if source=="cache" else images),
                         "--ffmpeg",str(ffmpeg),"--width",str(width),"--height",str(height),"-o",str(output)]
                if source=="cache":
                    command += ["--render-config",str(camera)]
                record=measure(command,root/name,root)
                verified=probe(output,ffprobe)
                results.append(dict(name=name,source=source,particles=count,**record,**verified,
                                    complete_frames_per_s=verified["frame_count"]/record["wall_s"]))
                (root/"video-summary.json").write_text(json.dumps(results,indent=2)+"\n")
                print(name,record["wall_s"],flush=True)
    for name,options,expected in [
        ("omit-terminal",["--omit-terminal"],list(range(300))),
        ("sparse",["--first-frame","17","--last-frame","31","--every","4"],[17,21,25,29]),
        ("sparse-omit",["--first-frame","17","--last-frame","31","--every","4","--omit-terminal"],[17,21,25]),
    ]:
        for source in ["cache","images"]:
            directory=root/f"selection-{source}-{name}"
            output=directory/"movie.mp4"
            command=[str(binary),"--format","json","video",source,str(caches[110592] if source=="cache" else root/"video-source-images-110592"),
                     "--ffmpeg",str(ffmpeg),"-o",str(output),*options]
            if source=="cache":
                command += ["--render-config",str(camera)]
            measure(command,directory,root)
            probe(output,ffprobe)
            provenance=json.loads(Path(str(output)+".json").read_text())
            if [f["source_index"] for f in provenance["frames"]]!=expected:
                raise ValueError("source selection order disagrees with independent expected indices")
    return results


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ["root","existing","binary","ffmpeg","ffprobe","camera"]:
        parser.add_argument("--"+name,type=Path,required=True)
    args=parser.parse_args()
    campaign(*(getattr(args,name).resolve() for name in ["root","existing","binary","ffmpeg","ffprobe","camera"]))
