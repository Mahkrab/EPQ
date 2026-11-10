"""Measure saved-state playback on the process's own X11 window.

Client submissions, disk/decode work and recorded-time progress have separate
boundaries. These observations do not establish compositor or physical display FPS.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import statistics
import subprocess
import time

from tools.performance.live_viewer import Window, percentile, process_resources


def read_trace(path: Path) -> list[dict]:
    """Read complete diagnostic records, leaving a live partial line for the next poll."""
    return [json.loads(line[12:]) for line in path.read_text(encoding="utf-8").splitlines(keepends=True)
            if line.endswith("\n") and line.startswith("cache-trace ")]


def assess(directory: Path) -> dict:
    events = []
    last_wall = 0.0
    for event in read_trace(directory / "viewer.log"):
        if event["event"] == "present":
            last_wall = event["wall_s"]
        event["observed_wall_s"] = last_wall
        events.append(event)
    protocol = json.loads((directory / "protocol.json").read_text())
    samples = json.loads((directory / "samples.json").read_text())
    # Discard setup, the first second after starting, and closing.
    first, last = protocol["measure_start_s"], protocol["measure_end_s"]
    frames = [e for e in events if e["event"] == "present" and first <= e["wall_s"] <= last]
    intervals = [b["wall_s"] - a["wall_s"] for a, b in zip(frames, frames[1:])]
    reads = [e for e in events if e["event"] == "read"]
    measured_reads = [e for e in reads if first <= e["observed_wall_s"] <= last]
    loaded = [e["seconds"] for e in events if e["event"] == "loaded"]
    progress = 0.0
    for a, b in zip(frames, frames[1:]):
        if b["simulation_s"] >= a["simulation_s"]:
            progress += b["simulation_s"] - a["simulation_s"]
        else:
            progress += protocol["terminal_s"] - a["simulation_s"] + b["simulation_s"]
    span = frames[-1]["wall_s"] - frames[0]["wall_s"]
    result = dict(submissions_per_s=(len(frames)-1)/span, timeline_simulation_s_per_wall_s=progress/span,
                  new_states_presented_per_s=sum(a["index"]!=b["index"] for a,b in zip(frames,frames[1:]))/span,
                  interval_p95_ms=1000*percentile(intervals, .95), interval_p99_ms=1000*percentile(intervals, .99),
                  cpu_core_equivalents=(samples[-1]["cpu_s"]-samples[0]["cpu_s"])/(samples[-1]["wall_s"]-samples[0]["wall_s"]),
                  peak_rss_mib=max(s["peak_rss_kib"] for s in samples)/1024,
                  rss_first_mib=samples[0]["rss_kib"]/1024, rss_last_mib=samples[-1]["rss_kib"]/1024,
                  read_count_including_setup=len(reads), load_p95_ms=1000*percentile(loaded,.95),
                  loaded_frames_per_s=len(measured_reads)/(last-first),
                  read_rate_boundary="read log ordered between client submissions; completion uncertainty at most one redraw",
                  file_read_p95_ms=1000*percentile([e["timings"]["reading_s"] for e in reads],.95),
                  mean_prepare_ms=1000*statistics.mean(e["prepare_s"] for e in frames),
                  mean_upload_ms=1000*statistics.mean(e["upload_s"] for e in frames),
                  mean_submit_ms=1000*statistics.mean(e["submit_s"] for e in frames),
                  presentations=len(frames), close_s=protocol["close_s"], protocol=protocol)
    (directory / "summary.json").write_text(json.dumps(result, indent=2)+"\n")
    return result


def run(args):
    args.output.mkdir(parents=True)
    command = [str(args.binary.resolve()), "view", "--cache", str(args.cache.resolve()), "--paused",
               "--width", str(args.width), "--height", str(args.height), "--camera-output", str(args.output.resolve()/"camera.toml")]
    if args.mode:
        command += ["--cache-playback", args.mode]
    environment = {**os.environ, "WINIT_UNIX_BACKEND":"x11", "WAYLAND_DISPLAY":"", "MAELSTROM_CACHE_TRACE":"1"}
    protocol = dict(command=command, duration_s=args.seconds, speed=args.speed, terminal_s=args.terminal,
                    display=os.environ.get("DISPLAY"), cache_reads="warm OS cache; no cache flush")
    with (args.output/"viewer.log").open("w") as log, (args.output/"gpu.csv").open("w") as gpu:
        monitor = subprocess.Popen(["nvidia-smi", "--query-gpu=timestamp,utilization.gpu,memory.used,clocks.sm,power.draw", "--format=csv,noheader,nounits", "-lms", "200"], stdout=gpu, stderr=subprocess.DEVNULL)
        p = subprocess.Popen(command, stdout=log, stderr=log, env=environment)
        window = None
        try:
            window = Window(p)
            window.wait("ready")
            for _ in range(args.speed.bit_length()-1):
                window.key("bracketright")
            window.key("l")
            window.key("space")
            time.sleep(1)
            # Viewer time starts before creating its window, so bind sample clocks
            # to the most recently flushed event instead of process launch time.
            def viewer_time():
                return next(event["wall_s"] for event in reversed(read_trace(args.output/"viewer.log"))
                            if event["event"] == "present")
            protocol["measure_start_s"] = viewer_time()
            begin = time.monotonic()
            samples=[]
            while time.monotonic()-begin < args.seconds:
                window.alive()
                resource = process_resources(p.pid)
                status=Path(f"/proc/{p.pid}/status").read_text()
                resource.update(wall_s=time.monotonic()-begin,
                                rss_kib=int(next(s.split()[1] for s in status.splitlines() if s.startswith("VmRSS:"))),
                                title=window.title())
                samples.append(resource)
                time.sleep(.05)
            protocol["measure_end_s"] = viewer_time()
            (args.output/"samples.json").write_text(json.dumps(samples,indent=2)+"\n")
            start=time.monotonic()
            window.request_close()
            p.wait(timeout=20)
            protocol["close_s"]=time.monotonic()-start
            if p.returncode:
                raise RuntimeError(f"viewer failed: {p.returncode}")
        finally:
            if p.poll() is None:
                p.kill()
                p.wait()
            if window:
                window.close()
            monitor.terminate()
            monitor.wait(timeout=10)
            (args.output/"protocol.json").write_text(json.dumps(protocol,indent=2)+"\n")
    return assess(args.output)


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary",type=Path,required=True)
    parser.add_argument("--cache",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--width",type=int,default=1280)
    parser.add_argument("--height",type=int,default=720)
    parser.add_argument("--seconds",type=float,default=12)
    parser.add_argument("--terminal",type=float,default=5.00000026)
    parser.add_argument("--speed",type=int,choices=[1,2,4,8,16],default=1)
    parser.add_argument("--mode",choices=["real-time","frame-accurate"])
    args=parser.parse_args()
    print(json.dumps(run(args),indent=2))
