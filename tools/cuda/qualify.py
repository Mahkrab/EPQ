"""Retain hardware correctness runs, fresh CPU controls and component reports.

This is numerical qualification, with no warm-up, performance summary or speedup.
Run on the selected device after building and testing the exact source manifest.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys

from .compare import compare


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write(path: Path, value: dict) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def verify_source(source: Path, manifest: dict) -> None:
    """Reject stale sources or paths outside the declared simulator directory."""
    for name, expected in manifest["files_sha256"].items():
        path = (source / name).resolve()
        if not path.is_relative_to(source) or digest(path.read_bytes()) != expected:
            raise ValueError(f"source manifest disagrees at {name}")


def invoke(binary: Path, source: Path, command: list[str], destination: Path) -> tuple[dict, dict]:
    """Finish or cancel a bounded process and retain even failed original output."""
    process = subprocess.Popen([str(binary), *command], cwd=source, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=180)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(process.pid, signal.SIGINT)
        try:
            stdout, stderr = process.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
    raw = gzip.compress(stdout, mtime=0)
    with destination.open("xb") as stream:
        stream.write(raw)
    evidence = {"command": [str(binary), *command], "exit_code": process.returncode,
                "timed_out": timed_out, "stderr": stderr.decode("utf-8", errors="replace"),
                "file": destination.name, "json_sha256": digest(stdout), "gzip_sha256": digest(raw)}
    if process.returncode or timed_out:
        return evidence, {}
    return evidence, json.loads(stdout)


def collect(binary: Path, source: Path, manifest_path: Path, destination: Path) -> dict:
    """Compare full goldens across launch settings, and the full larger family."""
    manifest = json.loads(manifest_path.read_bytes())
    verify_source(source, manifest)
    family_bytes = (source / "reference/manifest.json").read_bytes()
    family = json.loads(family_bytes)
    destination.mkdir(parents=True, exist_ok=False)
    result = {"policy": "reference-comparison-v1", "purpose": "correctness qualification only",
              "source_manifest": manifest, "family_manifest_sha256": digest(family_bytes),
              "binary_sha256": digest(binary.read_bytes()), "commands": [], "comparisons": [],
              "passed": False}
    try:
        def execute(label: str, command: list[str]) -> dict:
            evidence, document = invoke(binary, source, command, destination / f"{label}.json.gz")
            result["commands"].append(evidence)
            if not document:
                raise ValueError(f"{label}: invocation failed; original output retained")
            return document

        def check(label: str, reference: dict, candidate: dict) -> None:
            report = compare(reference, candidate, exact=True)
            report["record_sha256"] = {key: digest(json.dumps(value, separators=(",", ":")).encode())
                                        for key, value in (("reference", reference), ("candidate", candidate))}
            write(destination / f"{label}-comparison.json", report)
            result["comparisons"].append({"file": f"{label}-comparison.json", "passed": report["passed"]})
            if not report["passed"]:
                raise ValueError(f"{label}: numerical disagreement; full report retained")

        for case in family["cases"]:
            count = case["particles"]
            print(f"Qualifying {count} particles, {case['steps']} steps", flush=True)
            scene = case["scene"]
            if digest((source / scene).read_bytes()) != case["sha256"]:
                raise ValueError(f"frozen scene hash changed: {scene}")
            common = ["run", scene, "--refine-timestep", str(case["refine_timestep"]), "--steps", str(case["steps"]),
                      "--checkpoints", ",".join(map(str, case["checkpoints"])), "--format", "json"]
            reference = execute(f"{count:05}-serial-grid", [*common, "--backend", "uniform-grid"])
            threaded = execute(f"{count:05}-threaded-4", [*common, "--backend", "uniform-grid", "--execution", "threaded", "--threads", "4"])
            check(f"{count:05}-threaded", reference, threaded)
            if case.get("golden"):
                golden_bytes = (source / case["golden"]).read_bytes()
                if digest(golden_bytes) != case["golden_sha256"]:
                    raise ValueError("frozen golden hash changed")
                golden = json.loads(golden_bytes)
                check(f"{count:05}-golden-control", golden, reference)
                brute = execute(f"{count:05}-brute-force", common)
                check(f"{count:05}-brute-force", golden, brute)
                variants = [(threads, mode, repetition) for threads in (32, 64, 128, 256)
                            for mode in ("ordinary", "total", "stages") for repetition in (1, 2)]
            else:
                variants = [(128, "ordinary", 1)]
            for threads, mode, repetition in variants:
                label = f"{count:05}-cuda-{threads}-{mode}-{repetition}"
                command = [*common, "--backend", "uniform-grid", "--execution", "cuda", "--device", "0", "--block-size", str(threads)]
                if mode != "ordinary":
                    command.append("--measure")
                if mode == "stages":
                    command.append("--stage-profile")
                candidate = execute(label, command)
                check(label, reference, candidate)
                if repetition == 1 and mode == "ordinary":
                    replay_path = destination / f"{label}-replay-input.json"
                    write(replay_path, candidate)
                    replayed = execute(f"{label}-replay", ["replay", str(replay_path), "--format", "json"])
                    replay_path.unlink()
                    check(f"{label}-replay", candidate, replayed)
        verify_source(source, manifest)
        if digest(binary.read_bytes()) != result["binary_sha256"]:
            raise ValueError("binary changed during qualification")
        result["passed"] = True
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        result["error"] = str(error)
        raise
    finally:
        write(destination / "qualification.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path)
    parser.add_argument("source", type=Path)
    parser.add_argument("source_manifest", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    try:
        collect(*(path.resolve() for path in (args.binary, args.source, args.source_manifest, args.destination)))
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(f"CUDA qualification: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
