"""Reconstruct the gradient trial without its collector or timing reporter.

Hashed raw process output owns the evidence. Exact physical records, including
signed zero, must agree before an independently summed duration is admitted.
"""

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import statistics

from tests.performance.audit_neighbour_bands import audit_trace


def read(directory: Path) -> tuple[dict, dict]:
    process = json.loads((directory / "process.json").read_bytes())
    compressed = (directory / "stdout.gz").read_bytes()
    raw = gzip.decompress(compressed)
    for data, name in ((compressed, "stdout_gzip_sha256"), (raw, "stdout_sha256"),
                       ((directory / "stderr.txt").read_bytes(), "stderr_sha256")):
        if hashlib.sha256(data).hexdigest() != process[name]:
            raise ValueError("raw process output hash differs")
    if process["exit_code"] != 0 or process["timed_out"] or process["interrupted"]:
        raise ValueError("unsuccessful process")
    return process, json.loads(raw)


def physical(result: dict, particles: int, revision: str) -> str:
    if (result["status"] not in ("completed", "completed_with_warnings") or result["failures"]
            or result["completed_steps"] != "480" or result["request"]["steps"] != "480"
            or result["metadata"]["debug_assertions"] or result["metadata"]["build_revision"] != revision
            or result["execution"] != {"mode": "cuda", "device": 0, "threads": 128}
            or len(result["input"]["particles"]) != particles
            or len(result["final_snapshot"]["particles"]) != particles
            or [row["completed_steps"] for row in result["steps"]] != [str(i) for i in range(1, 481)]):
        raise ValueError("different or incomplete physical request")
    value = dict(result)
    value.pop("measurements", None)
    value["metadata"] = dict(value["metadata"])
    value["metadata"].pop("build_revision")
    return json.dumps(value, sort_keys=True, allow_nan=False)


def duration(result: dict) -> float:
    timing = result["measurements"]
    if timing["schema_version"] != 1 or timing["mode"] != "total" or len(timing["steps"]) != 480:
        raise ValueError("different timing scope")
    values = [row["total_s"] for row in timing["steps"]]
    if (timing["failed_attempt_s"] is not None
            or any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0 for v in values)
            or any(row["stages"] is not None for row in timing["steps"])):
        raise ValueError("invalid or instrumented duration")
    return sum(values)


def close(actual: float, expected: float) -> None:
    if not math.isclose(actual, expected, rel_tol=0, abs_tol=1e-12):
        raise ValueError("reported quantity differs from raw samples")


def audit(root: Path, summary: dict | None = None) -> dict:
    if summary is None:
        summary = json.loads((root / "summary.json").read_bytes())
    identities = json.loads((root / "identities.json").read_bytes())
    experiment_path = root / "experiment.json"
    experiment = json.loads(experiment_path.read_bytes())["name"] if experiment_path.exists() else "gradient-reassessment"
    resident = experiment == "resident-state"
    identical = identities["control"]["fresh_ptx_sha256"] == identities["candidate"]["fresh_ptx_sha256"]
    if identical != resident:
        raise ValueError("wrong generated-code identity for this trial")
    checked = {}
    for label, particles in (("8000", 8000), ("110592", 110592), ("110592-effects", 110592)):
        reference = None
        totals, walls = {}, {}
        report = summary["workloads"][label]
        for variant, identity in identities.items():
            totals[variant], walls[variant] = [], []
            for index in range(6):
                name = "warmup" if index == 0 else f"sample-{index}"
                process, result = read(root / f"paired/{label}/{variant}/{name}")
                value = physical(result, particles, identity["revision"])
                if reference is None:
                    reference = value
                if value != reference:
                    raise ValueError("physical results or warning schedules differ")
                numerical = result["input"]["configuration"]["numerical"]
                enabled = label.endswith("-effects")
                if numerical["xsph_viscosity_enabled"] != enabled or numerical["vorticity_confinement_enabled"] != enabled:
                    raise ValueError("wrong fluid-effect workload")
                if index:
                    total = duration(result)
                    close(total, report["samples"][variant][index-1]["solver_s"])
                    close(process["wall_s"], report["samples"][variant][index-1]["invocation_s"])
                    totals[variant].append(total)
                    walls[variant].append(process["wall_s"])
                elif result.get("measurements") is not None:
                    raise ValueError("warm-up unexpectedly measured")
        for scope, values in (("solver", totals), ("invocation", walls)):
            original, candidate = values["control"], values["candidate"]
            claimed = report[scope]
            close(statistics.median(original), claimed["control_median_s"])
            close(statistics.median(candidate), claimed["candidate_median_s"])
            close(statistics.median(original) / statistics.median(candidate), claimed["median_speedup"])
            if claimed["faster_pairs"] != sum(b < a for a, b in zip(original, candidate, strict=True)):
                raise ValueError("reported faster-pair count differs")
            for index, (a, b) in enumerate(zip(original, candidate, strict=True)):
                close(a / b, claimed["pairs"][index]["speedup"])
        checked[label] = {"warmups": 2, "samples": 10, "exact_physical_agreement": True,
                          "control_solver_median_s": statistics.median(totals["control"]),
                          "candidate_solver_median_s": statistics.median(totals["candidate"])}
    for particles in (64, 216, 512, 1000, 1728, 4096, 8000):
        reference = None
        for variant, identity in identities.items():
            _, result = read(root / f"regression/{particles}/{variant}")
            value = physical(result, particles, identity["revision"])
            if reference is not None and value != reference:
                raise ValueError("regression physical results differ")
            reference = value
    traces = {}
    cooperative = experiment == "cooperative-sort"
    for variant in identities:
        directory = root / "timelines" / variant
        traces[variant] = audit_trace(directory, json.loads((directory / "windows.json").read_bytes()),
                                      row_sort=resident or (cooperative and variant == "candidate"),
                                      resident=resident and variant == "candidate")
    return {"paired_workloads": checked, "exact_regression_trajectories": 7,
            "independent_trace_checks": traces,
            "scope": "independent raw timing and physical-result reconstruction; no retention decision"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.directory.resolve()), indent=2, allow_nan=False))
