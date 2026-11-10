"""Measure fixed-work live X11 runs, retaining frame traces and device telemetry.

The viewer reports successful surface presentations, not compositor acknowledgements
or physical scan-out. Simulation rate comes from accepted indices in those traces.
Only the launched process's window receives keys; no global input is synthesised.
"""
from __future__ import annotations

import argparse
import csv
import ctypes as c
import hashlib
import json
import math
import os
from pathlib import Path
import re
import statistics
import subprocess
import time


def process_resources(pid: int) -> dict:
    text = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8").rsplit(")", 1)[1].split()
    status = Path(f"/proc/{pid}/status").read_text(encoding="utf-8")
    return dict(cpu_s=(int(text[11]) + int(text[12])) / os.sysconf("SC_CLK_TCK"),
                peak_rss_kib=int(re.search(r"VmHWM:\s+(\d+)", status)[1]),
                virtual_kib=int(re.search(r"VmSize:\s+(\d+)", status)[1]))


class KeyEvent(c.Structure):
    _fields_ = [("type", c.c_int), ("serial", c.c_ulong), ("send_event", c.c_int),
                ("display", c.c_void_p), ("window", c.c_ulong), ("root", c.c_ulong),
                ("subwindow", c.c_ulong), ("time", c.c_ulong), ("x", c.c_int),
                ("y", c.c_int), ("x_root", c.c_int), ("y_root", c.c_int),
                ("state", c.c_uint), ("keycode", c.c_uint), ("same_screen", c.c_int)]


class ClientMessage(c.Structure):
    _fields_ = [("type", c.c_int), ("serial", c.c_ulong), ("send_event", c.c_int),
                ("display", c.c_void_p), ("window", c.c_ulong), ("message_type", c.c_ulong),
                ("format", c.c_int), ("data", c.c_long * 5)]


class Window:
    def __init__(self, process):
        self.x = c.CDLL("libX11.so.6")
        for name, result, args in [
            ("XOpenDisplay", c.c_void_p, [c.c_char_p]),
            ("XDefaultRootWindow", c.c_ulong, [c.c_void_p]),
            ("XFetchName", c.c_int, [c.c_void_p, c.c_ulong, c.POINTER(c.c_void_p)]),
            ("XFree", c.c_int, [c.c_void_p]),
            ("XStringToKeysym", c.c_ulong, [c.c_char_p]),
            ("XKeysymToKeycode", c.c_uint, [c.c_void_p, c.c_ulong]),
            ("XSetInputFocus", c.c_int, [c.c_void_p, c.c_ulong, c.c_int, c.c_ulong]),
            ("XRaiseWindow", c.c_int, [c.c_void_p, c.c_ulong]),
            ("XGetInputFocus", c.c_int, [c.c_void_p, c.POINTER(c.c_ulong), c.POINTER(c.c_int)]),
            ("XSendEvent", c.c_int, [c.c_void_p, c.c_ulong, c.c_int, c.c_long, c.c_void_p]),
            ("XSync", c.c_int, [c.c_void_p, c.c_int]),
            ("XCloseDisplay", c.c_int, [c.c_void_p]),
            ("XInternAtom", c.c_ulong, [c.c_void_p, c.c_char_p, c.c_int]),
        ]:
            function = getattr(self.x, name)
            function.restype, function.argtypes = result, args
        self.display = self.x.XOpenDisplay(None)
        if not self.display:
            raise RuntimeError("X11 display unavailable")
        self.process = process
        self.window = None
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            self.alive()
            tree = subprocess.check_output(["xwininfo", "-root", "-tree"], text=True)
            for value in re.findall(r'(0x[0-9a-f]+) "Maelstrom', tree):
                pid = subprocess.run(["xprop", "-id", value, "_NET_WM_PID"],
                                     capture_output=True, text=True, check=True)
                match = re.search(r"= (\d+)\s*$",pid.stdout)
                owner = int(match[1]) if match else 0
                ancestor = owner
                while ancestor and ancestor != process.pid:
                    try:
                        ancestor = int(Path(f"/proc/{ancestor}/stat").read_text(encoding="utf-8").rsplit(")",1)[1].split()[1])
                    except FileNotFoundError:
                        ancestor = 0
                if ancestor == process.pid:
                    self.window = int(value, 16)
                    self.pid = owner
                    return
            time.sleep(0.05)
        raise RuntimeError("own viewer window unavailable")

    def alive(self):
        if self.process.poll() is not None:
            raise RuntimeError(f"viewer exited: {self.process.returncode}")

    def title(self):
        self.alive()
        pointer = c.c_void_p()
        if not self.x.XFetchName(self.display, self.window, c.byref(pointer)):
            raise RuntimeError("viewer title unavailable")
        try:
            return c.string_at(pointer).decode()
        finally:
            self.x.XFree(pointer)

    def wait(self, expression, timeout=180):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            title = self.title()
            if "Failed" in title:
                raise RuntimeError(f"simulation failed: {title}")
            if re.search(expression, title):
                return title
            time.sleep(0.02)
        raise TimeoutError(f"no {expression}: {title}")

    def key(self, name):
        focused, revert = c.c_ulong(), c.c_int()
        for _ in range(20):
            self.x.XRaiseWindow(self.display, self.window)
            self.x.XSetInputFocus(self.display, self.window, 2, 0)
            self.x.XSync(self.display, False)
            self.x.XGetInputFocus(self.display, c.byref(focused), c.byref(revert))
            if focused.value == self.window:
                break
            time.sleep(.05)
        if focused.value != self.window:
            raise RuntimeError(f"own window {self.window:x} did not acquire keyboard focus: {focused.value:x}")
        # Let winit consume FocusIn before delivering its first core key event.
        # This setup wait is outside the running-frame measurement boundary.
        time.sleep(.1)
        code = self.x.XKeysymToKeycode(self.display, self.x.XStringToKeysym(name.encode()))
        for kind, mask in [(2, 1), (3, 2)]:
            event = KeyEvent(type=kind, display=self.display, window=self.window,
                             root=self.x.XDefaultRootWindow(self.display), keycode=code,
                             same_screen=1)
            union = (c.c_long * 24)()
            c.memmove(union, c.byref(event), c.sizeof(event))
            if not self.x.XSendEvent(self.display, self.window, False, mask, union):
                raise RuntimeError("key delivery failed")
        self.x.XSync(self.display, False)

    def request_close(self):
        event = ClientMessage(type=33, display=self.display, window=self.window,
                              message_type=self.x.XInternAtom(self.display, b"WM_PROTOCOLS", False),
                              format=32)
        event.data[0] = self.x.XInternAtom(self.display, b"WM_DELETE_WINDOW", False)
        union = (c.c_long * 24)()
        c.memmove(union, c.byref(event), c.sizeof(event))
        if not self.x.XSendEvent(self.display, self.window, False, 0, union):
            raise RuntimeError("window-close delivery failed")
        self.x.XSync(self.display, False)

    def close(self):
        self.x.XCloseDisplay(self.display)


def percentile(values: list[float], fraction: float) -> float:
    """Nearest-rank quantile; small samples expose their actual tail observations."""
    ordered = sorted(values)
    return ordered[max(0, math.ceil(fraction * len(ordered)) - 1)]


def summarise(path: Path) -> dict:
    with path.open(encoding="utf-8",newline="") as stream:
        rows = list(csv.DictReader(stream))
    running = [i for i, row in enumerate(rows) if row["status"] == "Running"]
    if len(running) < 2:
        raise ValueError("insufficient running frames")
    # Consecutive successful presentations over the same running generation.
    sample = rows[running[0]:running[-1] + 1]
    if any(row["status"] != "Running" or row["generation"] != sample[0]["generation"] for row in sample):
        raise ValueError("running interval contains a pause or generation change")
    numbers = lambda key: [float(row[key]) for row in sample]
    wall = numbers("wall_s")
    if not all(math.isfinite(t) for t in wall) or any(b <= a for a,b in zip(wall,wall[1:])):
        raise ValueError("presentation timestamps must be finite and strictly increasing")
    intervals = [b - a for a, b in zip(wall, wall[1:])]
    elapsed = wall[-1] - wall[0]
    steps = int(sample[-1]["step"]) - int(sample[0]["step"])
    if elapsed <= 0 or steps <= 0:
        raise ValueError("running interval did not advance accepted steps")
    simulated = float(sample[-1]["simulated_s"]) - float(sample[0]["simulated_s"])
    if not math.isclose(simulated / steps, 1/240, rel_tol=1e-6):
        raise ValueError("viewer did not use the experimental 240 Hz timestep")
    return dict(frames=len(intervals), interval_s=elapsed,
                presentation_fps=len(intervals) / elapsed,
                frame_mean_ms=statistics.mean(intervals) * 1000,
                frame_p95_ms=percentile(intervals, .95) * 1000,
                frame_p99_ms=percentile(intervals, .99) * 1000,
                frame_max_ms=max(intervals) * 1000,
                stutters_over_33ms=sum(t > 1/30 for t in intervals),
                stutters_over_50ms=sum(t > .05 for t in intervals),
                steps_s=steps / elapsed, simulated_s_per_wall_s=simulated / elapsed,
                solver_ms_per_step=(float(sample[-1]["solver_s"]) - float(sample[0]["solver_s"])) * 1000 / steps,
                snapshot_ms_per_step=(float(sample[-1]["snapshot_s"]) - float(sample[0]["snapshot_s"])) * 1000 / steps,
                cpu_frame_mean_ms={key: statistics.mean(numbers(key)) * 1000 for key in
                                   ("acquire_s", "prepare_s", "upload_s", "submit_s", "present_s", "redraw_s")},
                first_step=int(sample[0]["step"]), last_step=int(sample[-1]["step"]))


def run(binary: Path, scene: Path, output: Path, steps: int, trace: bool = False,
        renderer: str | None = None, acceptance: bool = False) -> None:
    """Run one fixed-work window; a failure leaves its partial evidence in output."""
    if not binary.is_file() or not scene.is_file() or steps <= 0:
        raise ValueError("require an existing executable, scene and positive step count")
    if renderer is not None and renderer not in ("indexed","low","impostor","adaptive"):
        raise ValueError("unknown particle renderer")
    output.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, MAELSTROM_WINDOW_BACKEND="x11",
               MAELSTROM_VIEW_PROFILE=str(output / "frames.csv"))
    if renderer is not None:
        env["MAELSTROM_PARTICLE_RENDERER"] = renderer
    if acceptance:
        env["MAELSTROM_ACCEPTANCE_PROFILE"] = str(output/"accepted.csv")
    command = [str(binary), "view", str(scene), "--backend", "cuda", "--device", "0",
               "--numerical-mode", "experimental",
               "--block-size", "128", "--steps", str(steps), "--width", "1280", "--height", "720"]
    if trace:
        command = ["nsys","profile","--sample=none","--cpuctxsw=none","--trace=cuda,nvtx,opengl,osrt",
                   "--output=" + str(output / "timeline"), *command]
    with (output / "viewer.log").open("w",encoding="utf-8") as log, (output / "gpu.csv").open("w",encoding="utf-8") as gpu_log:
        gpu = subprocess.Popen(["nvidia-smi", "--query-gpu=timestamp,utilization.gpu,utilization.memory,memory.used,temperature.gpu,power.draw,clocks.sm,clocks.mem,pstate", "--format=csv,nounits", "-lms", "200"], stdout=gpu_log, stderr=subprocess.STDOUT)
        process = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT)
        start = time.monotonic()
        start_unix_s = time.time()
        window = None
        try:
            window = Window(process)
            window.wait(r"Running|Completed", timeout=30)
            before = process_resources(window.pid)
            resource_start = time.monotonic()
            window.wait(r"Completed.*" + str(steps) + "/" + str(steps), timeout=180)
            elapsed = time.monotonic() - start
            after = process_resources(window.pid)
            resource_elapsed = time.monotonic() - resource_start
            end_unix_s = time.time()
            window.request_close()
            process.wait(timeout=30)
            if process.returncode:
                raise RuntimeError(f"viewer failed: {process.returncode}")
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            gpu.terminate()
            gpu.wait(timeout=5)
            if window:
                window.close()
    summary = summarise(output / "frames.csv")
    selected = re.findall(r"maelstrom particle renderer: (\w+)",(output / "viewer.log").read_text(encoding="utf-8"))
    if renderer is not None and (not selected or selected[-1].lower()!=renderer):
        raise ValueError("viewer did not confirm the requested particle renderer")
    with binary.open("rb") as stream:
        executable_sha256 = hashlib.file_digest(stream, "sha256").hexdigest()
    summary.update(command=command, complete_run_wall_s=elapsed,
                   start_unix_s=start_unix_s, end_unix_s=end_unix_s,
                   cpu_core_equivalents=(after["cpu_s"] - before["cpu_s"]) / resource_elapsed,
                   peak_rss_kib=after["peak_rss_kib"], virtual_kib=after["virtual_kib"],
                   executable_sha256=executable_sha256)
    if selected:
        summary["particle_renderer"] = selected[-1].lower()
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n",encoding="utf-8")
    print(json.dumps(dict(sample=output.name, **summary)), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path)
    parser.add_argument("scene", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--steps", type=int, default=1200)
    parser.add_argument("--trace",action="store_true",help="separate Nsight diagnostic; not an ordinary sample")
    parser.add_argument("--particle-renderer",choices=("indexed","low","impostor","adaptive"))
    parser.add_argument("--acceptance-profile",action="store_true",help="record every accepted boundary for capacity qualification")
    args = parser.parse_args()
    try:
        run(args.binary.resolve(), args.scene.resolve(), args.output.resolve(), args.steps,args.trace,args.particle_renderer,args.acceptance_profile)
    except (OSError,ValueError,KeyError,RuntimeError,TimeoutError,subprocess.SubprocessError) as error:
        parser.exit(1,f"live viewer measurement: {error}\n")


if __name__ == "__main__":
    main()
