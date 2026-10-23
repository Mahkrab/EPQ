"""Describe paired performance evidence without deciding whether code should stay.

The written assessment owns that decision. These quantities preserve every pair
and expose variability, including regressions that a favourable median can hide.
"""

import math
import statistics


def paired(control: list[float], candidate: list[float]) -> dict:
    """Compare complete ordered pairs; ranges are descriptive, not admission tests.

    ``median_speedup`` divides the two workload medians; ``median_paired_speedup``
    is the median of the individual pair ratios. Neither is an uncertainty interval.
    """
    if len(control) != len(candidate) or len(control) < 2:
        raise ValueError("at least two complete timing pairs are required")
    if any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0
           for values in (control, candidate) for v in values):
        raise ValueError("positive finite durations are required")
    rows = [{"control_s": a, "candidate_s": b, "saving_s": a - b, "speedup": a / b}
            for a, b in zip(control, candidate, strict=True)]
    return {"pairs": rows, "control_median_s": statistics.median(control),
            "candidate_median_s": statistics.median(candidate),
            "median_speedup": statistics.median(control) / statistics.median(candidate),
            "median_paired_speedup": statistics.median(row["speedup"] for row in rows),
            "faster_pairs": sum(b < a for a, b in zip(control, candidate)),
            "slower_pairs": sum(b > a for a, b in zip(control, candidate)),
            "equal_pairs": sum(b == a for a, b in zip(control, candidate)),
            "ranges_overlap": max(min(control), min(candidate)) <= min(max(control), max(candidate))}


def evidence(primary: dict, larger: dict) -> dict:
    """Summarise each workload separately for a reasoned engineering assessment."""
    workloads = {}
    for name, workload in (("8000", primary), ("110592", larger)):
        control = [sample["solver_s"] for sample in workload["control"]["samples"]]
        candidate = [sample["solver_s"] for sample in workload["candidate"]["samples"]]
        workloads[name] = paired(control, candidate)
    return {"schema_version": 1, "assessment_required": True,
            "decision_authority": "documented_engineering_assessment",
            "workloads": workloads}
