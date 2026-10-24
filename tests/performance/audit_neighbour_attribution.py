"""Audit recorded stage durations using fixed independently inspected launch slots.

This does not import the collector's sequence builder or attribution function.
Compressed SQLite exports are restored only inside a temporary directory.
"""

import gzip
import json
import math
from pathlib import Path
import sqlite3
import tempfile
import statistics


def audit(root: Path) -> dict:
    checked = {}
    # Particle count: (production launches, diagnostic launches, count slot).
    for particles, slots in ((8000, (145, 147, 94)), (110592, (207, 209, 156))):
        summary = json.loads((root / str(particles) / "analysis.json").read_text())
        for variant, per_step in (("control", slots[0]), ("split", slots[1])):
            with tempfile.TemporaryDirectory() as directory:
                database = Path(directory) / "trace.sqlite"
                database.write_bytes(gzip.decompress((root / str(particles) / variant / "cuda.sqlite.gz").read_bytes()))
                with sqlite3.connect(database) as db:
                    rows = list(db.execute("SELECT start,end FROM CUPTI_ACTIVITY_KIND_KERNEL ORDER BY start"))
                    calls = db.execute("SELECT count(*) FROM CUPTI_ACTIVITY_KIND_RUNTIME a JOIN StringIds s ON a.nameId=s.id WHERE s.value='cuStreamSynchronize'").fetchone()[0]
            if len(rows) != per_step * 480 or calls != 24_481:
                raise ValueError("unexpected raw launch/completion count")
            offsets = {"4": slots[2], "12": slots[2] + 1}
            if variant == "split":
                offsets = {"4": slots[2], "15": slots[2] + 1, "12": slots[2] + 2, "14": slots[2] + 3}
            for first, last in ((1, 120), (121, 240), (241, 480)):
                claimed = summary[variant]["windows"][f"{first}-{last}"]["operations_device_s"]
                for operation, slot in offsets.items():
                    nanoseconds = sum(rows[step * per_step + slot][1] - rows[step * per_step + slot][0]
                                      for step in range(first - 1, last))
                    if not math.isclose(nanoseconds / 1e9, claimed[operation], rel_tol=1e-12, abs_tol=1e-12):
                        raise ValueError("claimed stage time differs from raw kernel intervals")
            checked[f"{particles}/{variant}"] = {"kernels": len(rows), "completions": calls,
                                                   "stage_windows_match_raw": True}
    return checked


def audit_compiler(root: Path) -> dict:
    """Recompute profile medians and compare physical JSON without collector code."""
    checked = {}
    physical = ("backend", "execution", "request", "completed_steps", "input", "steps",
                "checkpoints", "final_snapshot", "failures", "status")
    for campaign, sizes in (("original", (8000, 110592)), ("confirmation", (8000,))):
        summary = json.loads((root / campaign / "summary.json").read_text())
        for size in sizes:
            reference = None
            for variant in ("release", "thin"):
                totals = []
                for index in range(6):
                    name = "warmup" if index == 0 else f"sample-{index}"
                    path = root / campaign / str(size) / variant / name
                    process = json.loads((path / "process.json").read_text())
                    result = json.loads(gzip.decompress((path / "solver.json.gz").read_bytes()))
                    if (process["exit_code"] != 0 or process["timed_out"] or process["interrupted"]
                            or result["completed_steps"] != "480" or result["failures"]
                            or result["status"] not in ("completed", "completed_with_warnings")
                            or len(result["input"]["particles"]) != size):
                        raise ValueError("incomplete or different compiler comparison")
                    projection = json.dumps({key: result[key] for key in physical}, sort_keys=True)
                    if reference is None:
                        reference = projection
                    if reference != projection:
                        raise ValueError("physical JSON differs between compiler variants")
                    if index:
                        timings = result["measurements"]
                        if timings["mode"] != "total" or len(timings["steps"]) != 480:
                            raise ValueError("invalid primary timing boundary")
                        total = sum(step["total_s"] for step in timings["steps"])
                        if not math.isclose(total, summary["results"][str(size)][variant]["samples"][index - 1]["solver_s"], rel_tol=1e-12):
                            raise ValueError("reported solver total differs from raw steps")
                        totals.append(total)
                median = statistics.median(totals)
                # Python versions can accumulate binary64 totals a few ulps
                # differently; one picosecond is below the timer's resolution.
                if not math.isclose(median, summary["results"][str(size)][variant]["median_solver_s"], rel_tol=0, abs_tol=1e-12):
                    raise ValueError("reported median differs from raw samples")
                checked[f"{campaign}/{size}/{variant}"] = {"samples": 5, "warmups": 1,
                    "median_solver_s": median, "physical_json_agrees": True}
    return checked
