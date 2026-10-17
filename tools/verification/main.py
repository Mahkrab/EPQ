"""Retain complete CPU correctness comparisons, including exact floating-point bits.

This is local verification, not a timing campaign. It reuses the frozen manifest
and records whole CLI results, replay checks and per-component disagreement reports.
Run from the parent checkout with ``python3 -m tools.verification.main --help``.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import struct
import subprocess
import sys

from tools.baseline import main as baseline
from tools.baseline.data import physical_document, read_json, sha256

ROOT = Path(__file__).resolve().parents[2]
SIMULATOR = ROOT / "Maelstrom"


def binary32(value: object) -> float:
    """Recover the finite binary32 value carried by a JSON number."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("expected a finite binary32 number")
    try:
        result = struct.unpack("!f", struct.pack("!f", value))[0]
    except (OverflowError, struct.error) as error:
        raise ValueError("value is outside binary32") from error
    if not math.isfinite(result):
        raise ValueError("value is outside binary32")
    return result


def disagreements(expected: object, actual: object, location: str = "result") -> list[dict]:
    """List shape/identity failures and exact numeric failures without tolerating zeros."""
    result = []
    if isinstance(expected, dict) and isinstance(actual, dict):
        if expected.keys() != actual.keys():
            result.append({"kind": "structure", "location": location, "reason": "object fields differ"})
        for key in expected.keys() & actual.keys():
            result.extend(disagreements(expected[key], actual[key], f"{location}.{key}"))
    elif isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            result.append({"kind": "structure", "location": location, "reason": "array lengths differ"})
        for index, (e, a) in enumerate(zip(expected, actual)):
            result.extend(disagreements(e, a, f"{location}[{index}]"))
    elif isinstance(expected, (int, float)) and not isinstance(expected, bool) and isinstance(actual, (int, float)) and not isinstance(actual, bool):
        try:
            equal = (struct.pack("!f", binary32(expected)) == struct.pack("!f", binary32(actual))
                     if isinstance(expected, float) or isinstance(actual, float) else expected == actual)
        except ValueError:
            equal = False
        if not equal:
            result.append({"kind": "numerical", "location": location,
                           "expected": repr(expected), "actual": repr(actual)})
    elif type(expected) is not type(actual) or expected != actual:
        result.append({"kind": "structure", "location": location,
                       "expected": repr(expected), "actual": repr(actual)})
    return sorted(result, key=lambda item: (item["kind"] != "structure", item["location"]))


def snapshot_report(expected: dict, actual: dict) -> dict:
    """Report every position and velocity component, or a failed structural boundary."""
    failures = disagreements(expected, actual, "snapshot")
    report = {"completed_steps": expected.get("completed_steps"), "passed": not failures,
              "disagreements": failures, "quantities": {}}
    try:
        left, right = expected["particles"], actual["particles"]
        if expected["completed_steps"] != actual["completed_steps"] or len(left) != len(right):
            raise ValueError("snapshot shape differs")
        if [p["identity"] for p in left] != [p["identity"] for p in right]:
            raise ValueError("particle identities/order differ")
        for field in ("position_m", "velocity_m_s"):
            errors = []
            worst = None
            maximum = 0.0
            exact = True
            for e, a in zip(left, right, strict=True):
                for axis in "xyz":
                    ev, av = binary32(e[field][axis]), binary32(a[field][axis])
                    error = abs(av - ev)
                    if worst is None or error > maximum:
                        maximum, worst = error, {"identity": e["identity"], "axis": axis}
                    errors.append(error)
                    exact &= struct.pack("!f", ev) == struct.pack("!f", av)
            report["quantities"][field] = {
                "particles": len(left), "components": len(errors), "maximum_absolute": maximum,
                "rms": math.sqrt(math.fsum(x*x for x in errors) / len(errors)) if errors else 0.0,
                "worst": worst, "absolute_limit": 0.0, "passed": exact,
            }
    except (KeyError, TypeError, ValueError) as error:
        report["passed"] = False
        report["structural_error"] = str(error)
    return report


def compare(expected: dict, actual: dict) -> dict:
    """Apply the unchanged-order exact policy to complete results, before reporting metrics."""
    left, right = physical_document(expected), physical_document(actual)
    left.pop("execution", None)
    right.pop("execution", None)
    failures = disagreements(left, right)
    checkpoints = []
    first = None
    for index, e in enumerate(expected["checkpoints"]):
        if index >= len(actual["checkpoints"]):
            first = first if first is not None else e["snapshot"]["completed_steps"]
            continue
        a = actual["checkpoints"][index]
        snapshot = snapshot_report(e["snapshot"], a["snapshot"])
        audit = {"expected": e["density"], "actual": a["density"],
                 "passed": not disagreements(e["density"], a["density"])}
        checkpoints.append({"snapshot": snapshot, "audit": audit})
        if not (snapshot["passed"] and audit["passed"]) and first is None:
            first = e["snapshot"]["completed_steps"]
    final = snapshot_report(expected["final_snapshot"], actual["final_snapshot"])
    if not final["passed"] and first is None:
        first = expected["final_snapshot"]["completed_steps"]
    cfl = []
    for index in range(max(len(expected["steps"]), len(actual["steps"]))):
        e = expected["steps"][index] if index < len(expected["steps"]) else None
        a = actual["steps"][index] if index < len(actual["steps"]) else None
        if disagreements(e, a):
            cfl.append({"step": str(index+1), "expected": e, "actual": a})
    return {
        "policy": "reference-comparison-v1", "acceptance": "exact binary32, including signed zero",
        "context": {"reference_metadata": expected["metadata"], "candidate_metadata": actual["metadata"],
                    "request": actual["request"], "execution": actual.get("execution", {"mode": "serial"})},
        "passed": not failures, "disagreements": failures,
        "first_divergent_checkpoint": first, "first_divergent_cfl_step": cfl[0]["step"] if cfl else None,
        "checkpoints": checkpoints, "final_snapshot": final, "cfl_disagreements": cfl,
        "completion": {"expected": expected["status"], "actual": actual["status"]},
        "failures": {"expected": expected["failures"], "actual": actual["failures"]},
    }


def report(directory: Path) -> dict:
    """Recompute judgments from retained raw results, rejecting changed files."""
    collection = read_json(directory / "collection.json")
    rows = []
    for attempt in collection["attempts"]:
        reference = (SIMULATOR / attempt["reference"]).resolve()
        if not reference.is_relative_to(SIMULATOR):
            raise ValueError("reference path escapes simulator")
        candidate = (directory / attempt["file"]).resolve()
        if not candidate.is_relative_to(directory.resolve()):
            raise ValueError("candidate path escapes evidence directory")
        if sha256(reference.read_bytes()) != attempt["reference_sha256"] or sha256(candidate.read_bytes()) != attempt["sha256"]:
            raise ValueError("reference or candidate bytes changed")
        settings_match = False
        try:
            expected, actual = read_json(reference), read_json(candidate)
            execution = actual.get("execution", {"mode": "serial"})
            settings_match = (execution == attempt["execution"] and actual["backend"] == attempt["backend"]
                              and actual["metadata"]["backend"] == attempt["backend"])
            comparison = compare(expected, actual)
        except (ValueError, KeyError, TypeError, AttributeError) as error:
            comparison = {"passed": False, "disagreements": [
                {"kind": "structure", "location": "result", "reason": str(error)}]}
        comparison["passed"] &= settings_match and attempt["exit_code"] == 0
        rows.append({"file": attempt["file"], "settings_match": settings_match, **comparison})
    return {"schema_version": 1, "policy": "reference-comparison-v1",
            "passed": bool(rows) and all(row["passed"] for row in rows), "comparisons": rows}


def collect(directory: Path, binary: Path, workers: list[int]) -> dict:
    """Run both serial controls and threaded modes into a new evidence directory."""
    if not workers or len(workers) != len(set(workers)) or any(not 1 <= n <= 256 for n in workers):
        raise ValueError("workers must be distinct counts in 1..=256")
    if os.environ.get("RUSTFLAGS") or os.environ.get("CARGO_ENCODED_RUSTFLAGS"):
        raise ValueError("verification collection requires the standard build without custom Rust flags")
    manifest = baseline.checked_manifest()
    source = baseline.source_identity()
    directory.mkdir(parents=True, exist_ok=False)
    collection = {"schema_version": 1, "purpose": "local correctness; timings are not performance evidence",
                  "source": source, "binary_sha256": sha256(binary.read_bytes()),
                  "environment": baseline.environment(), "build_command": "cargo build --release --locked --offline",
                  "manifest_sha256": sha256((SIMULATOR / "reference/manifest.json").read_bytes()),
                  "started_utc": baseline.now(), "workers": workers, "attempts": []}
    # Keep the verifier itself identifiable alongside the simulator source.
    collection["verifier_files_sha256"] = {
        str(path.relative_to(ROOT)): sha256(path.read_bytes())
        for path in (Path(__file__).resolve(), ROOT / "tools/baseline/main.py", ROOT / "tools/baseline/data.py")
    }
    for case in manifest["cases"]:
        if not case["golden"]:
            continue
        selections = [(backend, None, "ordinary") for backend in ("brute-force", "uniform-grid")]
        selections += [("uniform-grid", count, mode) for count in workers for mode in ("ordinary", "total", "stages", "replay")]
        for backend, count, mode in selections:
            name = f"{case['particles']:05}-{backend}-{count or 'serial'}-{mode}.json"
            if mode == "replay":
                original = directory / name.replace("-replay.json", "-ordinary.json")
                args = [str(binary), "replay", str(original), "--format", "json", "--quiet"]
            else:
                args = baseline.solver_args(binary, case, "warmup", backend)
                if count is not None:
                    args += ["--execution", "threaded", "--threads", str(count)]
                if mode in ("total", "stages"):
                    args += ["--measure"]
                if mode == "stages":
                    args += ["--stage-profile"]
            try:
                output = subprocess.run(args, cwd=SIMULATOR, stdin=subprocess.DEVNULL, capture_output=True, timeout=180)
            except subprocess.TimeoutExpired as error:
                output = subprocess.CompletedProcess(args, -1, error.stdout or b"", error.stderr or b"")
            except OSError as error:
                output = subprocess.CompletedProcess(args, -1, b"", str(error).encode())
            with (directory / name).open("xb") as stream:
                stream.write(output.stdout)
            execution = {"mode": "serial"} if count is None else {"mode": "threaded", "workers": count}
            attempt = {"file": name, "command": [str(Path(arg).relative_to(SIMULATOR)) if arg.startswith(str(SIMULATOR)+"/") else arg for arg in args],
                       "sha256": sha256(output.stdout), "reference": case["golden"],
                       "reference_sha256": case["golden_sha256"], "execution": execution,
                       "backend": f"{'serial' if count is None else 'threaded'}-{backend}-pbf-binary32-8-jacobi-v2",
                       "exit_code": output.returncode, "stderr": output.stderr.decode(errors="replace")}
            # Relative replay paths make commands portable between checkouts.
            attempt["command"] = [arg.replace(str(ROOT)+"/", "../") for arg in attempt["command"]]
            collection["attempts"].append(attempt)
    collection["finished_utc"] = baseline.now()
    if baseline.source_identity()["tree_sha256"] != source["tree_sha256"]:
        raise ValueError("simulator worktree changed during verification")
    baseline.write_json(directory / "collection.json", collection)
    result = report(directory)
    baseline.write_json(directory / "report.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("collect", "report"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--binary", type=Path, default=SIMULATOR / "target/release/maelstrom")
    parser.add_argument("--workers", type=int, nargs="+", default=[1, 2, 3, 7])
    args = parser.parse_args()
    try:
        directory = args.directory.resolve()
        if args.operation == "collect":
            result = collect(directory, args.binary.resolve(), args.workers)
        else:
            result = report(directory)
            if result != read_json(directory / "report.json"):
                raise ValueError("stored report differs from retained raw results")
        print(f"{len(result['comparisons'])} complete comparisons; exact agreement: {result['passed']}")
        return 0 if result["passed"] else 1
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(f"verification: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
