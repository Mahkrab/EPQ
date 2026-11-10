"""Exercise camera and inspection controls on the launched cached X11 window.

This supplies targeted synthetic X11 events, retaining camera and title evidence.
It does not certify human input feel, Windows focus behaviour or display scan-out.
"""
import argparse
import ctypes as c
import json
import os
from pathlib import Path
import subprocess
import time

from tools.performance.live_viewer import Window, process_resources
from tools.performance.cached_playback import read_trace


def pointer(window, kind, x, y, button=1, state=0):
    # winit's XI2 path ignores synthetic core pointer messages. XTest supplies
    # server-routed input, with the pointer confined to this process's window.
    window.x.XWarpPointer.argtypes=[c.c_void_p,c.c_ulong,c.c_ulong,c.c_int,c.c_int,c.c_uint,c.c_uint,c.c_int,c.c_int]
    window.x.XWarpPointer(window.display,0,window.window,0,0,0,0,x,y)
    if kind in [4,5]:
        extension=c.CDLL("libXtst.so.6")
        extension.XTestFakeButtonEvent.argtypes=[c.c_void_p,c.c_uint,c.c_int,c.c_ulong]
        if not extension.XTestFakeButtonEvent(window.display,button,kind==4,0):
            raise RuntimeError("pointer delivery failed")
    window.x.XSync(window.display,False)
    time.sleep(.02)


def records(log):
    return read_trace(log)


def wait_for(log, predicate, process, timeout=15):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        if process.poll() is not None:
            raise RuntimeError(f"viewer exited: {process.returncode}")
        frames=[e for e in records(log) if e["event"]=="present"]
        if frames and predicate(frames[-1]):
            return frames[-1]
        time.sleep(.005)
    raise TimeoutError("viewer did not reach requested state")


def journey(binary: Path, cache: Path, output: Path, preload: Path | None = None):
    output.mkdir()
    log=output/"viewer.log"
    env={**os.environ,"WINIT_UNIX_BACKEND":"x11","WAYLAND_DISPLAY":"","MAELSTROM_CACHE_TRACE":"1"}
    if preload:
        env.update(LD_PRELOAD=str(preload.resolve()), MAELSTROM_QUALIFY_READ_DELAY_US="100000")
    command=[str(binary.resolve()),"view","--cache",str(cache.resolve()),"--paused","--width","1280","--height","720",
             "--camera-output",str(output.resolve()/"camera.toml")]
    results=[]
    with log.open("w") as stream:
        process=subprocess.Popen(command,env=env,stdout=stream,stderr=stream)
        window=None
        try:
            window=Window(process)
            first=wait_for(log,lambda f:not f["loading"],process)
            def change(name, action):
                before=wait_for(log,lambda _:True,process)
                begin=time.monotonic()
                action()
                after=wait_for(log,lambda f:f["camera"]!=before["camera"],process)
                events=records(log)
                keys=[e for e in events if e["event"]=="key" and e["wall_s"]>=before["wall_s"]]
                results.append(dict(action=name,external_response_s=time.monotonic()-begin,
                                    handled_key_to_submission_s=after["wall_s"]-keys[-1]["wall_s"] if keys else None,
                                    before=before,after=after))
            for mode in ["paused","normal","fast"]:
                if mode=="normal":
                    window.key("l")
                    window.key("space")
                if mode=="fast":
                    window.key("bracketright")
                    window.key("bracketright")
                change(mode+"-orbit",lambda:window.key("Right"))
                def drag_orbit():
                    pointer(window,6,400,350)
                    pointer(window,4,400,350,1)
                    pointer(window,6,430,365,state=1<<8)
                    pointer(window,5,430,365,1)
                change(mode+"-drag-orbit",drag_orbit)
                change(mode+"-zoom",lambda:window.key("plus"))
                def wheel():
                    pointer(window,4,400,350,4)
                    pointer(window,5,400,350,4)
                change(mode+"-wheel",wheel)
                def pan():
                    pointer(window,6,400,350)
                    pointer(window,4,400,350,3)
                    pointer(window,6,440,370,state=1<<10)
                    pointer(window,5,440,370,3)
                change(mode+"-pan",pan)
            # Alternate end targets faster than a delayed read can complete.
            pointer(window,6,20,705)
            pointer(window,4,20,705)
            for i in range(40):
                pointer(window,6,1250 if i%2 else 20,705,state=1<<8)
                time.sleep(.01)
            pointer(window,5,1250,705)
            change("orbit-during-scrub",lambda:window.key("Left"))
            window.key("End")
            wait_for(log,lambda f:f["index"]==300 and not f["loading"],process)
            window.key("b")
            wait_for(log,lambda f:f["index"]==299 and not f["loading"],process)
            window.key("Home")
            wait_for(log,lambda f:f["index"]==0 and not f["loading"],process)
            window.key("b")
            wait_for(log,lambda f:f["index"]==0 and not f["loading"],process)
            window.key("t")
            wait_for(log,lambda f:f["policy"]=="FrameAccurate",process)
            window.key("space")
            wait_for(log,lambda f:f["index"]>=4,process)
            window.key("space")
            window.key("t")
            window.x.XResizeWindow.argtypes=[c.c_void_p,c.c_ulong,c.c_uint,c.c_uint]
            window.x.XResizeWindow(window.display,window.window,640,480)
            window.x.XSync(window.display,False)
            wait_for(log,lambda f:f["width"]==640 and f["height"]==480,process)
            change("resized-orbit",lambda:window.key("Up"))
            for key in ["j","1","7","Return"]:
                window.key(key)
            selected=wait_for(log,lambda f:f["index"]==17 and not f["loading"] and f["paused"],process)
            window.key("s")
            deadline=time.monotonic()+10
            while not (output/"camera.toml").exists():
                if time.monotonic()>deadline:
                    raise TimeoutError("camera was not saved")
                time.sleep(.01)
            capture = subprocess.run(["ffmpeg", "-v", "error", "-f", "x11grab", "-draw_mouse", "0",
                                      "-window_id", str(window.window), "-video_size", "640x480", "-i", os.environ.get("DISPLAY", ":0"),
                                      "-frames:v", "1", str(output/"viewer.png")], capture_output=True, timeout=20)
            result=dict(command=command, delayed_reads=bool(preload), initial=first,selected=selected,
                        camera_checks=results, resources=process_resources(process.pid),
                        capture_exit=capture.returncode, capture_stderr=capture.stderr.decode(),
                        controls="end, reverse, home, beginning, timing toggle, play/pause, arbitrary seek, resize, save")
            # Close immediately after issuing a seek, including delayed in-flight I/O.
            window.key("End")
            begin=time.monotonic()
            window.request_close()
            process.wait(timeout=20)
            result["close_s"]=time.monotonic()-begin
            result["exit_code"]=process.returncode
            if process.returncode:
                raise RuntimeError("viewer failed during close")
            (output/"result.json").write_text(json.dumps(result,indent=2)+"\n")
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            if window:
                window.close()
    return result


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary",type=Path,required=True)
    parser.add_argument("--cache",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--preload",type=Path)
    args=parser.parse_args()
    print(json.dumps(journey(args.binary,args.cache,args.output,args.preload),indent=2))
