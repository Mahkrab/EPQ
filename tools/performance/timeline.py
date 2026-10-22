"""Attribute the recorded CUDA sequence without adding overlapping host/device clocks.

Operation labels are admitted only when every launch matches the source-derived
sequence. GPU memory events describe traced allocations, not total driver memory.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import sqlite3
import sys

from .capture import digest, write_json
from .contract import allocation, operations

LABELS = ("acceleration", "prediction", "cell-keys", "bitonic-sort", "membership-build",
          "active-distance-validation", "density-and-multipliers", "correction",
          "physical-density-validation", "candidate-positions", "plane-projection", "velocity-reconstruction")


def union(intervals: list[tuple[int, int]]) -> int:
    """Measure covered nanoseconds once even when activities overlap."""
    covered = 0
    end = None
    for start, stop in sorted(intervals):
        if stop < start:
            raise ValueError("negative timeline interval")
        if end is None or start >= end:
            covered += stop - start
        elif stop > end:
            covered += stop - end
        end = max(end, stop) if end is not None else stop
    return covered


def analyse(directory: Path, steps: int) -> dict:
    """Reconcile kernel/copy/completion counts against the exact 8,000-particle request."""
    manifest = json.loads((directory / "files.json").read_bytes())
    for relative, expected in manifest.items():
        target = (directory / relative).resolve()
        if not target.is_relative_to(directory.resolve()) or digest(target.read_bytes()) != expected:
            raise ValueError("raw timeline file changed")
    database = directory / "cuda.sqlite"
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        kernels = list(connection.execute("SELECT * FROM CUPTI_ACTIVITY_KIND_KERNEL ORDER BY start"))
        api = list(connection.execute("SELECT a.*, s.value AS name FROM CUPTI_ACTIVITY_KIND_RUNTIME a JOIN StringIds s ON s.id=a.nameId ORDER BY a.start"))
        copies = list(connection.execute("SELECT * FROM CUPTI_ACTIVITY_KIND_MEMCPY ORDER BY start"))
        memory = list(connection.execute("SELECT * FROM CUDA_GPU_MEMORY_USAGE_EVENTS ORDER BY start"))
        copy_names = {row["id"]: row["label"] for row in connection.execute("SELECT * FROM ENUM_CUDA_MEMCPY_OPER")}
        memory_names = {row["id"]: row["label"] for row in connection.execute("SELECT * FROM ENUM_CUDA_DEV_MEM_EVENT_OPER")}
    finally:
        connection.close()
    model = operations(8000)
    sequence = [0, 1, 2] + [3] * model["sort_passes"] + [4] + list(range(5, 11)) * 8 + [11]
    launches = [row for row in api if row["name"] == "cuLaunchKernel"]
    if len(kernels) != len(sequence) * steps or len(launches) != len(kernels):
        raise ValueError("recorded launch count does not match the solver sequence")
    if any(kernel["correlationId"] != launch["correlationId"] for kernel, launch in zip(kernels, launches, strict=True)):
        raise ValueError("kernel and host launch correlation differs")
    if any(row["blockX"] != 128 or row["blockY"] != 1 or row["blockZ"] != 1
           or row["gridX"] != (64 if sequence[index % len(sequence)] in (2, 3) else 63)
           or row["gridY"] != 1 or row["gridZ"] != 1 for index, row in enumerate(kernels)):
        raise ValueError("unexpected launch shape")
    syncs = [row for row in api if row["name"] == "cuStreamSynchronize"]
    if len(syncs) != model["solver_wrapper_completions_per_step"] * steps:
        raise ValueError("recorded stream completion count differs from the corrected model")
    copy_rows = {}
    for kind in sorted({row["copyKind"] for row in copies}):
        values = [row for row in copies if row["copyKind"] == kind]
        copy_rows[copy_names[kind]] = {"calls": len(values), "bytes": sum(row["bytes"] for row in values),
                                     "device_s": sum(row["end"] - row["start"] for row in values) / 1e9}
    if (sum(row["bytes"] for row in copies if row["copyKind"] == 1) != model["upload_bytes_per_step"] * steps
            or sum(row["bytes"] for row in copies if row["copyKind"] == 2) != model["download_bytes_per_step"] * steps):
        raise ValueError("recorded transfer volume differs from source model")
    start = launches[0]["start"]
    end = syncs[-1]["end"]
    window = end - start
    by_operation = defaultdict(lambda: {"launches": 0, "device_ns": 0, "launch_to_next_ns": 0})
    for index, (kernel, launch) in enumerate(zip(kernels, launches, strict=True)):
        operation = sequence[index % len(sequence)]
        next_start = launches[index + 1]["start"] if index + 1 < len(launches) else end
        row = by_operation[operation]
        row["launches"] += 1
        row["device_ns"] += kernel["end"] - kernel["start"]
        row["launch_to_next_ns"] += next_start - launch["start"]
    intervals = [(max(start, row["start"]), min(end, row["end"])) for row in [*kernels, *copies]
                 if row["end"] > start and row["start"] < end]
    busy = union(intervals)
    api_rows = []
    for name in sorted({row["name"] for row in api}):
        values = [row for row in api if row["name"] == name]
        api_rows.append({"name": name, "calls": len(values),
                         "inclusive_host_s": sum(row["end"] - row["start"] for row in values) / 1e9})
    live = peak = 0
    for row in memory:
        label = memory_names[row["memoryOperationType"]]
        if label == "Allocation":
            live += row["bytes"]
        elif label == "Deallocation":
            live -= row["bytes"]
        else:
            raise ValueError("unsupported memory event")
        peak = max(peak, live)
    result = {"steps": steps, "primary_timing": False, "kernel_count": len(kernels),
              "completion_count": len(syncs), "source_models_verified": True,
              "model_correction": "initial derivation omitted three upload-internal reservation calls; observed 219 completions per step, not 216",
              "window": "first solver launch submission through final stream completion; first uploads/allocation precede this window",
              "window_s": window / 1e9, "device_busy_union_s": busy / 1e9,
              "device_idle_gap_s": (window - busy) / 1e9,
              "api_inclusive_host": api_rows, "copies": copy_rows,
              "maximum_registers_per_thread": max(row["registersPerThread"] for row in kernels),
              "maximum_local_memory_per_thread": max(row["localMemoryPerThread"] for row in kernels),
              "tracked_allocation_peak_bytes": peak, "requested_solver_slot_bytes": allocation(8000)["total_slot_bytes"],
              "memory_scope": "traced allocations, including module constants; excludes untraced driver/context working set",
              "operations": [{"operation": key, "name": LABELS[key], "launches": row["launches"],
                              "device_s": row["device_ns"] / 1e9,
                              "launch_to_next_s": row["launch_to_next_ns"] / 1e9}
                             for key, row in sorted(by_operation.items())]}
    if sum(row["launch_to_next_ns"] for row in by_operation.values()) != window:
        raise ValueError("host transaction windows do not partition the traced interval")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--steps", type=int, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = analyse(args.directory.resolve(), args.steps)
        if args.output:
            write_json(args.output, result)
        else:
            print(json.dumps(result, indent=2))
    except (OSError, ValueError, KeyError, sqlite3.Error) as error:
        print(f"Timeline analysis: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
