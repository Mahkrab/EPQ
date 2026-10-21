"""Exercise a real X11 viewer through native events addressed to its own window.

This opt-in check launches its own process and never sends desktop-wide keyboard
input. Screenshots come from that client's X drawable, including its diagnostics.
Timeouts detect missing observations; they do not pace or determine solver steps.
"""
from __future__ import annotations

import argparse
import ctypes as c
import os
from pathlib import Path
import re
import struct
import subprocess
import time
import zlib


class KeyEvent(c.Structure):
    _fields_ = [("type", c.c_int), ("serial", c.c_ulong), ("send_event", c.c_int),
                ("display", c.c_void_p), ("window", c.c_ulong), ("root", c.c_ulong),
                ("subwindow", c.c_ulong), ("time", c.c_ulong), ("x", c.c_int),
                ("y", c.c_int), ("x_root", c.c_int), ("y_root", c.c_int),
                ("state", c.c_uint), ("keycode", c.c_uint), ("same_screen", c.c_int)]


class Image(c.Structure):
    _fields_ = [("width", c.c_int), ("height", c.c_int), ("xoffset", c.c_int),
                ("format", c.c_int), ("data", c.c_void_p), ("byte_order", c.c_int),
                ("bitmap_unit", c.c_int), ("bitmap_bit_order", c.c_int),
                ("bitmap_pad", c.c_int), ("depth", c.c_int),
                ("bytes_per_line", c.c_int), ("bits_per_pixel", c.c_int),
                ("red_mask", c.c_ulong), ("green_mask", c.c_ulong), ("blue_mask", c.c_ulong)]


class X11:
    def __init__(self) -> None:
        self.lib = c.CDLL("libX11.so.6")
        signatures = {
            "XOpenDisplay": (c.c_void_p, [c.c_char_p]),
            "XDefaultRootWindow": (c.c_ulong, [c.c_void_p]),
            "XStringToKeysym": (c.c_ulong, [c.c_char_p]),
            "XKeysymToKeycode": (c.c_uint, [c.c_void_p, c.c_ulong]),
            "XSendEvent": (c.c_int, [c.c_void_p, c.c_ulong, c.c_int, c.c_long, c.c_void_p]),
            "XFlush": (c.c_int, [c.c_void_p]),
            "XFetchName": (c.c_int, [c.c_void_p, c.c_ulong, c.POINTER(c.c_void_p)]),
            "XFree": (c.c_int, [c.c_void_p]),
            "XResizeWindow": (c.c_int, [c.c_void_p, c.c_ulong, c.c_uint, c.c_uint]),
            "XIconifyWindow": (c.c_int, [c.c_void_p, c.c_ulong, c.c_int]),
            "XMapWindow": (c.c_int, [c.c_void_p, c.c_ulong]),
            "XGetImage": (c.POINTER(Image), [c.c_void_p, c.c_ulong, c.c_int, c.c_int, c.c_uint, c.c_uint, c.c_ulong, c.c_int]),
            "XDestroyImage": (c.c_int, [c.POINTER(Image)]),
            "XCloseDisplay": (c.c_int, [c.c_void_p]),
        }
        for name, (result, args) in signatures.items():
            function = getattr(self.lib, name)
            function.restype, function.argtypes = result, args
        self.display = self.lib.XOpenDisplay(None)
        if not self.display:
            raise RuntimeError("X11 display unavailable")
        self.root = self.lib.XDefaultRootWindow(self.display)

    def find_window(self, process: subprocess.Popen) -> int:
        end = time.monotonic() + 30
        while time.monotonic() < end:
            if process.poll() is not None:
                raise RuntimeError(f"viewer exited during creation: {process.returncode}")
            tree = subprocess.check_output(["xwininfo", "-root", "-tree"], text=True)
            for value in re.findall(r'(0x[0-9a-f]+) "Maelstrom', tree):
                pid = subprocess.run(["xprop", "-id", value, "_NET_WM_PID"], capture_output=True, text=True, check=False)
                if re.search(rf"= {process.pid}\s*$", pid.stdout):
                    return int(value, 16)
            time.sleep(0.05)
        raise RuntimeError("own viewer window did not appear")

    def title(self, window: int) -> str:
        pointer = c.c_void_p()
        if not self.lib.XFetchName(self.display, window, c.byref(pointer)):
            raise RuntimeError("cannot read viewer title")
        try:
            return c.string_at(pointer).decode("utf-8")
        finally:
            self.lib.XFree(pointer)

    def wait(self, window: int, pattern: str) -> str:
        end = time.monotonic() + 30
        while time.monotonic() < end:
            title = self.title(window)
            if re.search(pattern, title):
                print(title, flush=True)
                return title
            time.sleep(0.05)
        raise RuntimeError(f"no title matching {pattern!r}; observed {title!r}")

    def key(self, window: int, name: str) -> None:
        symbol = ord(name) if len(name) == 1 else self.lib.XStringToKeysym(name.encode())
        code = self.lib.XKeysymToKeycode(self.display, symbol)
        if not code:
            raise RuntimeError(f"no keycode for {name}")
        for kind, mask in [(2, 1), (3, 2)]:
            event = KeyEvent(type=kind, display=self.display, window=window,
                             root=self.root, keycode=code, same_screen=1)
            union = (c.c_long * 24)()
            c.memmove(union, c.byref(event), c.sizeof(event))
            if not self.lib.XSendEvent(self.display, window, False, mask, union):
                raise RuntimeError("native key delivery failed")
        self.lib.XFlush(self.display)
        print(f"Native key: {name}", flush=True)

    def text(self, window: int, value: str) -> None:
        for char in value:
            self.key(window, char)

    def capture(self, window: int, path: Path) -> None:
        # This delay allows presentation after a verified control boundary. It is
        # not an assertion about which numerical state was accepted.
        time.sleep(0.4)
        info = subprocess.check_output(["xwininfo", "-id", hex(window)], text=True)
        width = int(re.search(r"Width: (\d+)", info)[1])
        height = int(re.search(r"Height: (\d+)", info)[1])
        pointer = self.lib.XGetImage(self.display, window, 0, 0, width, height, c.c_ulong(-1), 2)
        if not pointer:
            raise RuntimeError("client screenshot unavailable")
        try:
            image = pointer.contents
            if (image.bits_per_pixel, image.byte_order, image.red_mask, image.green_mask, image.blue_mask) != (32, 0, 0xFF0000, 0xFF00, 0xFF):
                raise RuntimeError("screenshot pixel layout is unsupported")
            data = c.string_at(image.data, image.bytes_per_line * height)
            rows = bytearray()
            for y in range(height):
                row = data[y * image.bytes_per_line:y * image.bytes_per_line + width * 4]
                rgb = bytearray(width * 3)
                rgb[0::3], rgb[1::3], rgb[2::3] = row[2::4], row[1::4], row[0::4]
                rows.extend(b"\0" + rgb)
            def chunk(kind: bytes, value: bytes) -> bytes:
                return struct.pack(">I", len(value)) + kind + value + struct.pack(">I", zlib.crc32(kind + value))
            encoded = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b"")
            with path.open("xb") as destination:
                destination.write(encoded)
            print(f"Captured {path.name}: {width}x{height}", flush=True)
        finally:
            self.lib.XDestroyImage(pointer)


def journey(x: X11, window: int, output: Path) -> None:
    def wait(pattern: str) -> str:
        return x.wait(window, pattern)
    def keys(*names: str) -> None:
        for name in names:
            x.key(window, name)
    def capture(name: str) -> None:
        x.capture(window, output / f"{name}.png")
    wait(r"gen 1 Paused.*0/100000 steps")
    capture("x11-01-initial")
    keys("n")
    wait(r"gen 1 Paused.*1/100000 steps.*warnings 1")
    keys("f", "Right", "Up", "equal", "d")
    capture("x11-02-step-warning-camera-audit")
    keys("space")
    wait(r"gen 1 Running")
    keys("space")
    wait(r"gen 1 Paused")
    keys("r")
    wait(r"gen 2 Paused.*0/100000 steps")
    keys(*(["Tab"] * 6), "Return", "Delete", "2", "Return", "a")
    wait(r"gen 3 Paused.*0/2 steps")
    keys("space")
    wait(r"gen 3 Completed.*2/2 steps")
    capture("x11-03-completed")
    keys("Tab", "Return", "Delete")
    x.text(window, "missing-scene.toml")
    keys("Return", "a")
    wait(r"gen 3 Completed.*2/2 steps")
    capture("x11-04-invalid-draft")
    keys("1", "b", "a")
    wait(r"gen 4 Paused.*0/2 steps")
    keys("n")
    wait(r"gen 4 Paused.*1/2 steps")
    capture("x11-05-threaded")
    keys("b", "a")
    wait(r"gen 5 Failed.*0/2 steps")
    capture("x11-06-cuda-unavailable")
    keys("o")
    wait(r"PRIOR gen 4 Cancelled.*1/2 steps")
    capture("x11-07-prior")
    keys("o", "b", "a")
    wait(r"gen 6 Paused.*0/2 steps")
    keys("n")
    wait(r"gen 6 Paused.*1/2 steps")
    keys("g", "h")
    capture("x11-08-brute-force-recreated")
    x.lib.XResizeWindow(x.display, window, 1000, 680)
    x.lib.XFlush(x.display)
    capture("x11-09-resized")
    x.lib.XIconifyWindow(x.display, window, 0)
    x.lib.XFlush(x.display)
    time.sleep(0.3)
    x.lib.XMapWindow(x.display, window)
    x.lib.XFlush(x.display)
    wait(r"gen 6 Paused.*1/2 steps")
    keys("h")
    capture("x11-10-restored")
    keys("c")
    wait(r"gen 6 Cancelled.*1/2 steps")
    keys(*(["Tab"] * 6), "Return", "Delete")
    x.text(window, "100000")
    keys("Return", "a")
    wait(r"gen 7 Paused.*0/100000 steps")
    keys("space")
    wait(r"gen 7 Running")
    keys("Escape")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--runtime-lib-dir", type=Path)
    args = parser.parse_args()
    if not args.output.is_dir():
        parser.error("--output must be an existing evidence directory")
    env = os.environ.copy()
    for key in ("WAYLAND_DISPLAY", "WAYLAND_SOCKET"):
        env.pop(key, None)
    if args.runtime_lib_dir:
        env["LD_LIBRARY_PATH"] = str(args.runtime_lib_dir.resolve())
    if (args.output / "x11-viewer.txt").exists() or any(args.output.glob("x11-*.png")):
        parser.error("choose an evidence directory without previous X11 results")
    process = None
    x = X11()
    try:
        with (args.output / "x11-viewer.txt").open("x") as log:
            process = subprocess.Popen([str(args.binary.resolve()), "view", "falling-block-04", "--steps", "100000", "--software", "--set", "cfl_factor=0.000001"], env=env, stdout=log, stderr=subprocess.STDOUT)
            window = x.find_window(process)
            journey(x, window, args.output)
            code = process.wait(timeout=30)
            if code != 0:
                raise RuntimeError(f"viewer shutdown exit: {code}")
            print("Viewer exited cleanly after close during running work", flush=True)
    finally:
        # Preserve a failed attempt and request cooperative close on this process
        # only. Never signal or close a person's separate viewer instance.
        if process is not None and process.poll() is None:
            try:
                x.key(window, "Escape")
                process.wait(timeout=30)
            except (UnboundLocalError, subprocess.TimeoutExpired):
                print(f"Own viewer still live: PID {process.pid}; inspect it before further action", flush=True)
        x.lib.XCloseDisplay(x.display)


if __name__ == "__main__":
    main()
