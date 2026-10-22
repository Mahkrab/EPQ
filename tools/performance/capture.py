"""Retain bounded subprocess output before interpreting success or timings.

Each attempt owns a process group. Timeout cancellation must finish and reap it
before another request can start; incomplete JSON and raw failures remain evidence.
"""

from __future__ import annotations

import datetime as dt
import gzip
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def invoke(command: list[str], cwd: Path, destination: Path, *, timeout: float = 120,
           grace: float = 30, env: dict[str, str] | None = None) -> tuple[dict, dict | None]:
    """Preserve original stdout/stderr and disposition, including malformed output."""
    if destination.exists():
        raise FileExistsError(destination)
    destination.mkdir(parents=True)
    started_utc, started = utc(), time.monotonic()
    try:
        process = subprocess.Popen(command, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    except OSError as error:
        metadata = {"command": command, "started_utc": started_utc, "finished_utc": utc(),
                    "wall_s": time.monotonic() - started, "launch_error": str(error),
                    "exit_code": None, "timed_out": False, "interrupted": False,
                    "killed_after_grace": False}
        write_json(destination / "process.json", metadata)
        return metadata, None
    timed_out = interrupted = killed = False
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except (subprocess.TimeoutExpired, KeyboardInterrupt) as error:
        timed_out = isinstance(error, subprocess.TimeoutExpired)
        interrupted = isinstance(error, KeyboardInterrupt)
        try:
            os.killpg(process.pid, signal.SIGINT)
        except ProcessLookupError:
            pass
        try:
            stdout, stderr = process.communicate(timeout=grace)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            killed = True
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            stdout, stderr = process.communicate()
    elapsed = time.monotonic() - started
    payload = gzip.compress(stdout, mtime=0)
    (destination / "stdout.gz").write_bytes(payload)
    (destination / "stderr.txt").write_bytes(stderr)
    result = None
    parse_error = None
    if stdout:
        try:
            parsed = json.loads(stdout)
            if not isinstance(parsed, dict):
                raise ValueError("expected a JSON object")
            result = parsed
        except (ValueError, UnicodeDecodeError) as error:
            parse_error = str(error)
    metadata = {"command": command, "started_utc": started_utc, "finished_utc": utc(),
                "wall_s": elapsed, "exit_code": process.returncode, "timed_out": timed_out,
                "interrupted": interrupted, "killed_after_grace": killed,
                "stdout_sha256": digest(stdout), "stdout_gzip_sha256": digest(payload),
                "stderr_sha256": digest(stderr), "parse_error": parse_error}
    write_json(destination / "process.json", metadata)
    return metadata, result


def load_attempt(directory: Path) -> tuple[dict, dict | None]:
    """Reject changed retained output before report generation or sample admission."""
    metadata = json.loads((directory / "process.json").read_bytes())
    if "launch_error" in metadata:
        return metadata, None
    compressed = (directory / "stdout.gz").read_bytes()
    stdout = gzip.decompress(compressed)
    if (digest(compressed) != metadata["stdout_gzip_sha256"]
            or digest(stdout) != metadata["stdout_sha256"]
            or digest((directory / "stderr.txt").read_bytes()) != metadata["stderr_sha256"]):
        raise ValueError("retained process output hash differs")
    if metadata["parse_error"] is not None or not stdout:
        return metadata, None
    document = json.loads(stdout)
    if not isinstance(document, dict):
        raise ValueError("retained result is not an object")
    return metadata, document
