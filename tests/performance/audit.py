"""Independently recheck retained primary timings, component equality and capacity limits.

This reader deliberately does not import the collector or its report functions.
It checks original compressed JSON, not just stored pass flags or sample medians.
"""

from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import json
import math
from pathlib import Path
import statistics
import struct


def same(actual: object, expected: object) -> bool:
    if isinstance(actual, dict) and isinstance(expected, dict):
        return actual.keys() == expected.keys() and all(same(actual[k], expected[k]) for k in actual)
    if isinstance(actual, list) and isinstance(expected, list):
        return len(actual) == len(expected) and all(same(a, b) for a, b in zip(actual, expected))
    if type(actual) in (int, float) and type(expected) in (int, float):
        if not math.isfinite(actual) or not math.isfinite(expected):
            return False
        if type(actual) is int and type(expected) is int:
            return actual == expected
        return struct.pack("!f", actual) == struct.pack("!f", expected)
    return type(actual) is type(expected) and actual == expected


def physical(value: dict) -> dict:
    result = copy.deepcopy(value)
    for key in ("measurements", "backend", "execution"):
        result.pop(key, None)
    for key in ("backend", "run_id", "build_revision", "target_os", "target_arch", "debug_assertions", "device"):
        result["metadata"].pop(key, None)
    return result


def read(directory: Path) -> tuple[dict, dict]:
    process = json.loads((directory / "process.json").read_bytes())
    compressed = (directory / "stdout.gz").read_bytes()
    payload = gzip.decompress(compressed)
    for data, key in ((compressed, "stdout_gzip_sha256"), (payload, "stdout_sha256"),
                      ((directory / "stderr.txt").read_bytes(), "stderr_sha256")):
        if hashlib.sha256(data).hexdigest() != process[key]:
            raise ValueError("raw process evidence changed")
    return process, json.loads(payload)


def total(document: dict, mode: str) -> float:
    measured = document["measurements"]
    if measured["mode"] != mode or len(measured["steps"]) != int(document["completed_steps"]):
        raise ValueError("measurement scope differs")
    values = []
    for step in measured["steps"]:
        value = step["total_s"]
        if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
            raise ValueError("invalid elapsed time")
        if mode == "total" and step["stages"] is not None:
            raise ValueError("profile contamination in primary sample")
        if mode == "stages":
            if any(not math.isfinite(v) or v < 0 for v in step["stages"].values()):
                raise ValueError("invalid stage time")
            if sum(step["stages"].values()) > value + 1e-12:
                raise ValueError("stage overlap or inconsistent total")
        values.append(value)
    return math.fsum(values)


def audit(directory: Path, summary: Path) -> dict:
    report = json.loads(summary.read_bytes())
    rows = {(r["series"], r["particles"]): r for r in report["baseline"]}
    if len(rows) != 21:
        raise ValueError("baseline series/size matrix is incomplete")
    checked = 0
    for n in (64, 216, 512, 1000, 1728, 4096, 8000):
        _, reference = read(directory / f"baseline/serial-grid/{n:06}/warmup")
        for series in ("serial-grid", "threaded-grid", "cuda"):
            sample_totals = []
            complete = True
            for name in ("warmup", "sample-1", "sample-2", "sample-3", "profile"):
                path = directory / f"baseline/{series}/{n:06}/{name}"
                if not path.exists():
                    complete = False
                    continue
                process, document = read(path)
                admitted = (process["exit_code"] == 0 and not process["timed_out"]
                            and not process["interrupted"] and document["status"] == "completed"
                            and document["failures"] == [] and document["completed_steps"] == "480"
                            and not any(s["warning"] for s in document["steps"]))
                complete &= admitted
                if not admitted:
                    continue
                if document["request"] != {"steps": "480", "checkpoints": ["0", "1", "120", "240", "480"]}:
                    raise ValueError("baseline observation request changed")
                if not same(physical(document), physical(reference)):
                    raise ValueError("component comparison failed")
                checked += 1
                if name.startswith("sample"):
                    sample_totals.append(total(document, "total"))
                elif name == "profile":
                    total(document, "stages")
            primary = rows[series, n]["primary"]
            if complete and len(sample_totals) == 3:
                # Independent fsum and the collector's sequential accumulation
                # differ by binary64 rounding. This sub-nanosecond timing budget
                # does not relax any binary32 physical-component comparison.
                close = lambda a, b: math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-10)
                if (primary is None or len(primary["sample_totals_s"]) != 3
                        or not all(close(a, b) for a, b in zip(primary["sample_totals_s"], sample_totals))):
                    raise ValueError("reported primary samples differ")
                if not close(primary["median_solver_s"], statistics.median(sample_totals)):
                    raise ValueError("false median")
                if not close(primary["minimum_s"], min(sample_totals)) or not close(primary["maximum_s"], max(sample_totals)):
                    raise ValueError("false spread")
            elif primary is not None:
                raise ValueError("unclean or incomplete primary set was admitted")
    for row in report["capacity"]:
        n = row["particles"]
        decision = row["admission"]
        membership = n * ((n + 31) // 32) * 4
        slots = membership + 88 * n + 32 * (1 << (n - 1).bit_length()) + 96
        ceiling = min(6 * 1024 ** 3, decision["gpu_total_bytes"] * 3 // 5,
                      max(0, decision["gpu_free_bytes"] - 2 * 1024 ** 3))
        allowed = slots <= ceiling and decision["host_available_bytes"] >= 4 * 1024 ** 3
        if (decision["allocation_model"]["membership_bytes"] != membership
                or decision["allocation_model"]["total_slot_bytes"] != slots):
            raise ValueError("false membership estimate")
        if decision["gpu_ceiling_bytes"] != ceiling or decision["admitted"] != allowed:
            raise ValueError("false capacity admission")
        if not allowed and any(k in row for k in ("pilot", "core", "profile")):
            raise ValueError("unsafe capacity request executed")
        if "long_run_admission" in row:
            _, pilot = read(directory / f"capacity/{n:06}/pilot")
            predicted = total(pilot, "total") * 120
            long = row["long_run_admission"]
            if (long["ceiling_s"] != 90 or long["admitted"] != (predicted <= 90)
                    or not math.isclose(long["projected_480_step_s"], predicted, rel_tol=1e-12, abs_tol=1e-10)):
                raise ValueError("false pilot admission")
            if not long["admitted"] and any(k in row for k in ("core", "profile")):
                raise ValueError("impractical long request executed")
    return {"passed": True, "component_equal_baseline_attempts": checked,
            "verified_primary_rows": sum(r["primary"] is not None for r in rows.values()),
            "verified_capacity_decisions": len(report["capacity"])}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("summary", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.directory, args.summary), indent=2))
