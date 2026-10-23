"""Check descriptive paired results independently of the reporting implementation."""

import math
import statistics

from .audit_compact import close


def validate(values: dict, reported: dict) -> None:
    if (type(reported.get("schema_version")) is not int or reported.get("schema_version") != 1 or reported.get("assessment_required") is not True
            or reported.get("decision_authority") != "documented_engineering_assessment"
            or set(reported) != {"schema_version", "assessment_required", "decision_authority", "workloads"}
            or set(reported["workloads"]) != set(values)):
        raise ValueError("evidence must leave retention to the written assessment")
    for name, sides in values.items():
        a, b = sides["control"], sides["candidate"]
        if len(a) != len(b) or len(a) < 2 or any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0 for v in [*a, *b]):
            raise ValueError("invalid timing pairs")
        claimed = reported["workloads"][name]
        expected_keys = {"pairs", "control_median_s", "candidate_median_s", "median_speedup",
                         "median_paired_speedup", "faster_pairs", "slower_pairs", "equal_pairs", "ranges_overlap"}
        if set(claimed) != expected_keys or len(claimed["pairs"]) != len(a):
            raise ValueError("evidence fields or sample count changed")
        ratios = []
        faster = slower = equal = 0
        for i in range(len(a)):
            row = claimed["pairs"][i]
            expected = {"control_s": a[i], "candidate_s": b[i], "saving_s": a[i] - b[i], "speedup": a[i] / b[i]}
            if set(row) != set(expected) or any(not close(v, row[k]) for k, v in expected.items()):
                raise ValueError("false or reordered paired observation")
            ratios.append(a[i] / b[i])
            faster += b[i] < a[i]
            slower += b[i] > a[i]
            equal += b[i] == a[i]
        medians = {"control_median_s": statistics.median(a), "candidate_median_s": statistics.median(b),
                   "median_speedup": statistics.median(a) / statistics.median(b),
                   "median_paired_speedup": statistics.median(ratios)}
        if any(not close(v, claimed[k]) for k, v in medians.items()):
            raise ValueError("false paired summary")
        overlap = not (max(a) < min(b) or max(b) < min(a))
        if (any(type(claimed[k]) is not int for k in ("faster_pairs", "slower_pairs", "equal_pairs"))
                or type(claimed["ranges_overlap"]) is not bool
                or (claimed["faster_pairs"], claimed["slower_pairs"], claimed["equal_pairs"], claimed["ranges_overlap"]) != (faster, slower, equal, overlap)):
            raise ValueError("false direction counts or range description")
