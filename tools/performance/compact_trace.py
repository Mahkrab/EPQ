"""Reconcile compact-row CUDA traces and their tracked allocation peaks.

The row-count transfer and fill launch are additional measured work, not removed
host synchronisation. Traced allocation peaks do not include all driver memory.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import sqlite3
import sys

from .capture import digest
from .timeline import LABELS, union


def completion_count(particles: int, steps: int, layout: str, *, allocation_calls: int | None = None) -> int:
    """Model only explicit stream completions; kernel count is unchanged by batching."""
    if type(particles) is not int or type(steps) is not int or particles < 1 or steps < 1 or layout not in ("compact", "bitset", "compact-batched", "compact-diagnostic", "compact-atomic", "compact-stages", "compact-reserved"):
        raise ValueError("positive particles/steps and a known storage layout are required")
    bits = (particles - 1).bit_length()
    passes = bits * (bits + 1) // 2
    base = 135 if layout != "bitset" else 128
    if layout == "compact-reserved":
        if type(allocation_calls) is not int or allocation_calls < 1:
            raise ValueError("reservation traces need observed allocation calls including initial diagnostics")
        # Nineteen reservations per nonempty step; real growth retains a wait.
        # One allocation belongs to initial diagnostics, not storage growth.
        return (base + min(passes, 1) - 53 - 32 - 19) * steps + allocation_calls
    if layout == "compact-diagnostic":
        return (base + min(passes, 1) - 53) * steps
    if layout == "compact-atomic":
        return (base + min(passes, 1) - 53) * steps + 1
    if layout == "compact-stages":
        return (base + min(passes, 1) - 53 - 32) * steps + 1
    return (base + (min(passes, 1) if layout == "compact-batched" else passes)) * steps


def analyse(directory: Path, particles: int, steps: int, layout: str = "compact", *,
            entry_names: tuple[str, ...] | None = None) -> dict:
    if entry_names is not None and (len(entry_names) != 13 or any(not isinstance(n, str) or not n for n in entry_names)):
        raise ValueError("thirteen non-empty solver entry names are required")
    database = directory / "cuda.sqlite"
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        kernels = list(connection.execute("SELECT * FROM CUPTI_ACTIVITY_KIND_KERNEL ORDER BY start"))
        apis = list(connection.execute("SELECT a.*,s.value AS name FROM CUPTI_ACTIVITY_KIND_RUNTIME a JOIN StringIds s ON s.id=a.nameId ORDER BY a.start"))
        copies = list(connection.execute("SELECT * FROM CUPTI_ACTIVITY_KIND_MEMCPY ORDER BY start"))
        memsets = list(connection.execute("SELECT * FROM CUPTI_ACTIVITY_KIND_MEMSET ORDER BY start")) if layout in ("compact-atomic", "compact-stages", "compact-reserved") else []
        allocations = list(connection.execute("SELECT * FROM CUDA_GPU_MEMORY_USAGE_EVENTS ORDER BY start"))
        memory_names = {r["id"]: r["label"] for r in connection.execute("SELECT * FROM ENUM_CUDA_DEV_MEM_EVENT_OPER")}
        kernel_names = dict(connection.execute("SELECT id,value FROM StringIds"))
    finally:
        connection.close()
    bits = (particles - 1).bit_length()
    compact = layout != "bitset"
    sequence = [0, 1, 2] + [3] * (bits * (bits + 1) // 2) + ([4, 12] if compact else [4]) + list(range(5, 11)) * 8 + [11]
    staged = layout in ("compact-stages", "compact-reserved")
    diagnostic = layout in ("compact-diagnostic", "compact-atomic", "compact-stages", "compact-reserved")
    if layout == "compact-diagnostic":
        sequence = [item for operation in sequence for item in ((operation, 14) if operation not in (2, 3) else (operation,))]
    launches = [r for r in apis if r["name"] == "cuLaunchKernel"]
    syncs = [r for r in apis if r["name"] == "cuStreamSynchronize"]
    allocation_calls = sum(r["name"].startswith("cuMemAlloc") for r in apis)
    expected_completions = completion_count(particles, steps, layout,
        allocation_calls=allocation_calls if layout == "compact-reserved" else None)
    if len(kernels) != len(sequence) * steps or len(launches) != len(kernels):
        raise ValueError("compact trace launch sequence differs")
    if len(syncs) != expected_completions:
        raise ValueError("compact trace completion count differs")
    reset = None
    if layout in ("compact-atomic", "compact-stages", "compact-reserved"):
        resets = [r for r in apis if r["name"] == "cuMemsetD8Async"]
        reset_bytes = 32 if staged else 8
        if len(resets) != 1 or len(memsets) != 1 or memsets[0]["bytes"] != reset_bytes:
            raise ValueError("diagnostic reset count/bytes differ")
        reset = {"calls": 1, "bytes": reset_bytes}
    groups = defaultdict(lambda: {"calls": 0, "device_ns": 0, "launch_to_next_ns": 0})
    start, stop = launches[0]["start"], syncs[-1]["end"]
    for index, (kernel, launch) in enumerate(zip(kernels, launches, strict=True)):
        operation = sequence[index % len(sequence)]
        if kernel["correlationId"] != launch["correlationId"]:
            raise ValueError("compact kernel correlation differs")
        expected_name = "first_error" if operation == 14 else entry_names[operation] if entry_names is not None else "solver"
        if diagnostic and kernel_names[kernel["shortName"]] != expected_name:
            raise ValueError("diagnostic kernel identity differs")
        lanes = 128 if operation == 14 else (1 << bits) if operation in (2, 3) else particles
        if kernel["blockX"] != 128 or kernel["gridX"] != (lanes + 127) // 128:
            raise ValueError("compact launch dimensions differ")
        row = groups[operation]
        row["calls"] += 1
        row["device_ns"] += kernel["end"] - kernel["start"]
        row["launch_to_next_ns"] += (launches[index+1]["start"] if index+1 < len(launches) else stop) - launch["start"]
    transfers = {}
    specification = [(1, "host_to_device", 4, 32 * particles + 104),
                     (2, "device_to_host", 26 if staged else 58, 56 * particles + 432 if diagnostic else 268 * particles + 8)] if compact else [
                     (1, "host_to_device", 3, 24 * particles + 96),
                     (2, "device_to_host", 56, 256 * particles)]
    for kind, name, count, size in specification:
        rows = [r for r in copies if r["copyKind"] == kind]
        if len(rows) != count * steps or sum(r["bytes"] for r in rows) != size * steps:
            raise ValueError("compact transfer counts/bytes differ")
        transfers[name] = {"calls": len(rows), "bytes": sum(r["bytes"] for r in rows)}
    live = peak = 0
    for row in allocations:
        label = memory_names[row["memoryOperationType"]]
        if label not in ("Allocation", "Deallocation"):
            raise ValueError("unsupported memory event")
        live += row["bytes"] if label == "Allocation" else -row["bytes"]
        peak = max(peak, live)
    intervals = [(max(start, r["start"]), min(stop, r["end"])) for r in [*kernels, *copies, *memsets]
                 if r["end"] > start and r["start"] < stop]
    busy = union(intervals)
    return {"particles": particles, "steps": steps, "layout": layout, "primary_timing": False,
            "sqlite_sha256": digest(database.read_bytes()), "kernel_count": len(kernels), "completion_count": len(syncs),
            **({"allocation_calls_including_diagnostics": allocation_calls} if layout == "compact-reserved" else {}),
            "window_s": (stop-start)/1e9, "device_busy_union_s": busy/1e9, "idle_gap_s": (stop-start-busy)/1e9,
            "tracked_allocation_peak_bytes": peak, "memory_scope": "traced allocations including transient growth/module constants, not total driver/context memory",
            "transfers": transfers,
            **({"diagnostic_reset": reset} if reset is not None else {}),
            "operations": [{"operation": op, "name": "first-error" if op==14 else "neighbour-count" if compact and op==4 else "neighbour-fill-sort" if op==12 else LABELS[op],
                            "calls": v["calls"], "device_s": v["device_ns"]/1e9,
                            "launch_to_next_s": v["launch_to_next_ns"]/1e9} for op,v in sorted(groups.items())]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--particles", type=int, required=True)
    parser.add_argument("--steps", type=int, required=True)
    parser.add_argument("--layout", choices=("compact", "bitset", "compact-batched", "compact-diagnostic", "compact-atomic", "compact-stages", "compact-reserved"), default="compact")
    args = parser.parse_args()
    try:
        print(json.dumps(analyse(args.directory, args.particles, args.steps, args.layout), indent=2))
    except (OSError, ValueError, KeyError, sqlite3.Error) as error:
        print(f"Compact trace: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
