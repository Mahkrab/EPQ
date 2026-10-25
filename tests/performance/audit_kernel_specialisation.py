"""Recompute paired totals and named-kernel costs without the collection helpers.

Physical JSON remains exact. The timing tolerance only accommodates binary64
accumulation differences between Python versions and is below clock resolution.
"""

import gzip
import json
import math
from pathlib import Path
import sqlite3
import statistics
import tempfile

NAMES = ("accelerate", "predict", "build_cells", "sort_cells", "count_neighbours",
         "validate_distances", "multipliers", "corrections", "validate_density",
         "apply_corrections", "project_planes", "reconstruct_velocity", "fill_neighbours")


def document(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_bytes())
    return json.loads(gzip.decompress(path.with_suffix(path.suffix + ".gz").read_bytes()))


def physical(result: dict) -> str:
    keys = ("backend", "execution", "request", "completed_steps", "input", "steps",
            "checkpoints", "final_snapshot", "failures", "status")
    if (result["completed_steps"] != "480" or result["failures"]
            or result["status"] not in ("completed", "completed_with_warnings")
            or result["execution"] != {"mode": "cuda", "device": 0, "threads": 128}
            or result["metadata"]["debug_assertions"]):
        raise ValueError("different or incomplete physical work")
    return json.dumps({key: result[key] for key in keys}, sort_keys=True)


def audit(root: Path, *, shared_search: bool) -> dict:
    summary = document(root / "paired-summary.json")
    checked = {}
    for size in (8000, 110592):
        reference = None
        for variant in ("control", "candidate"):
            totals = []
            for index in range(6):
                label = "warmup" if index == 0 else f"sample-{index}"
                directory = root / f"paired/{size}/{variant}/{label}"
                process, result = document(directory / "process.json"), document(directory / "solver.json")
                if process["exit_code"] != 0 or process["timed_out"] or process["interrupted"]:
                    raise ValueError("unsuccessful sample")
                value = physical(result)
                if reference is None:
                    reference = value
                if value != reference or len(result["input"]["particles"]) != size:
                    raise ValueError("paired physical values differ")
                if index:
                    timing = result["measurements"]
                    if timing["mode"] != "total" or len(timing["steps"]) != 480:
                        raise ValueError("wrong timing scope")
                    total = sum(step["total_s"] for step in timing["steps"])
                    reported = summary[str(size)][variant]["samples"][index - 1]["solver_s"]
                    if not math.isclose(total, reported, rel_tol=0, abs_tol=1e-12):
                        raise ValueError("reported total differs from raw steps")
                    totals.append(total)
            median = statistics.median(totals)
            if not math.isclose(median, summary[str(size)][variant]["median_solver_s"], rel_tol=0, abs_tol=1e-12):
                raise ValueError("reported median differs from raw samples")
            checked[f"{size}/{variant}"] = {"samples": 5, "warmups": 1, "median_solver_s": median}
    for size in (64, 216, 512, 1000, 1728, 4096, 8000):
        if physical(document(root / f"regression/{size}/control/solver.json")) != physical(document(root / f"regression/{size}/candidate/solver.json")):
            raise ValueError("regression trajectory differs")
    for folder, size in (("timelines", 110592), ("small-timelines", 8000)):
        if not (root / folder).exists():
            continue
        claimed = document(root / ("trace-summary.json" if size == 110592 else "small-trace-summary.json"))
        passes = [0, 1, 2] + [3] * (153 if size == 110592 else 91) + [4, 12] + list(range(5, 11)) * 8 + [11]
        for variant in ("control", "candidate"):
            path = root / f"{folder}/{variant}/cuda.sqlite"
            with tempfile.TemporaryDirectory() as temporary:
                if not path.exists():
                    restored = Path(temporary) / "trace.sqlite"
                    restored.write_bytes(gzip.decompress(path.with_suffix(".sqlite.gz").read_bytes()))
                    path = restored
                with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as db:
                    rows = list(db.execute("SELECT k.start,k.end,k.correlationId,s.value FROM CUPTI_ACTIVITY_KIND_KERNEL k JOIN StringIds s ON k.shortName=s.id ORDER BY k.start"))
                    launches = list(db.execute("SELECT a.correlationId FROM CUPTI_ACTIVITY_KIND_RUNTIME a JOIN StringIds s ON a.nameId=s.id WHERE s.value=? ORDER BY a.start", ("cuLaunchKernel",)))
                    syncs = db.execute("SELECT count(*) FROM CUPTI_ACTIVITY_KIND_RUNTIME a JOIN StringIds s ON a.nameId=s.id WHERE s.value=?", ("cuStreamSynchronize",)).fetchone()[0]
                    transfers = list(db.execute("SELECT copyKind,count(*),sum(bytes) FROM CUPTI_ACTIVITY_KIND_MEMCPY GROUP BY copyKind ORDER BY copyKind"))
            if len(rows) != 480 * len(passes) or len(launches) != len(rows) or syncs != 24_481:
                raise ValueError("changed raw launch/completion model")
            if transfers != [(1, 1920, 480 * (32 * size + 104)), (2, 12480, 480 * (56 * size + 432))]:
                raise ValueError("changed transfers")
            for i, (start, end, correlation, name) in enumerate(rows):
                operation = passes[i % len(passes)]
                expected = "solver" if variant == "control" else "solver_shared" if shared_search and operation in (2, 3, 4, 12) else "solver_" + NAMES[operation]
                if correlation != launches[i][0] or name != expected or end <= start:
                    raise ValueError("wrong kernel or launch correlation")
            for first, last in ((1, 120), (121, 240), (241, 480)):
                totals = {str(op): 0 for op in range(13)}
                for i in range((first - 1) * len(passes), last * len(passes)):
                    totals[str(passes[i % len(passes)])] += rows[i][1] - rows[i][0]
                reported = claimed[variant]["windows"][f"{first}-{last}"]["operations_device_s"]
                if any(not math.isclose(ns / 1e9, reported[op], rel_tol=0, abs_tol=1e-12) for op, ns in totals.items()):
                    raise ValueError("reported component durations differ")
            checked[f"{folder}/{variant}"] = {"kernels": len(rows), "completions": syncs,
                "identity_and_component_windows_match_raw": True}
    checked["seven_regression_trajectories_exact"] = True
    return checked
