"""Validate timing evidence independently, preserving explicitly historical decisions."""

import argparse
import json
from pathlib import Path
import statistics

from .audit import physical, read, same, total
from .audit_compact import close, completed
from .audit_sort_batch import audit as audit_small_and_capacity
from .audit_assessment import validate as validate_evidence


def validate_claims(stats: dict, summary: dict) -> dict:
    """Check statistics and either new evidence or the original historical decision."""
    for variant in ("control", "candidate"):
        claimed = summary["paired_large"][variant]
        if len(claimed["samples"]) != 5:
            raise ValueError("large paired samples were removed")
        for value, key in zip(stats[variant]["values"], claimed["samples"], strict=True):
            if not close(value, key["solver_s"]):
                raise ValueError("false individual large-sample timing")
        for key in ("median_solver_s", "minimum_s", "maximum_s", "standard_deviation_s"):
            if not close(stats[variant][key], claimed[key]):
                raise ValueError("false large paired timing summary")
    ratio = stats["control"]["median_solver_s"] / stats["candidate"]["median_solver_s"]
    if not close(ratio, summary["paired_large_solver_speedup"]):
        raise ValueError("false large paired speedup")
    if "performance_evidence" in summary:
        if "decision" in summary:
            raise ValueError("a machine report cannot also decide retention")
        values = {"8000": {v: [s["solver_s"] for s in summary["primary"][v]["samples"]]
                           for v in ("control", "candidate")},
                  "110592": {v: stats[v]["values"] for v in ("control", "candidate")}}
        validate_evidence(values, summary["performance_evidence"])
        return {"assessment_required": True}
    # Historical reports retain their original rule and decision verbatim.
    clear = {}
    regressions = []
    for label, workload in (("8000", summary["primary"]), ("110592", stats)):
        a, b = workload["control"], workload["candidate"]
        clear[label] = a["median_solver_s"] / b["median_solver_s"] >= 1.05 and b["maximum_s"] < a["minimum_s"]
        regressions.append(b["median_solver_s"] > a["median_solver_s"] * 1.03)
    expected = not any(regressions) and any(clear.values())
    claimed = summary["decision"]
    if (claimed["retained"] != expected or claimed["clear_gain"] != clear
            or claimed["both_median_regressions_at_most_three_percent"] != (not any(regressions))):
        raise ValueError("false retain/reject decision")
    return {"retained": expected, "clear_gain": clear}


def audit(root: Path, summary: dict) -> dict:
    result = audit_small_and_capacity(root, summary)
    campaign = json.loads((root / "campaign.json").read_bytes())
    if campaign["experiment"] not in ("gradient-prefix-v1", "reserve-reuse-v1", "power-tables-v1", "acceptance-inline-v1", "neighbour-bands-v1"):
        raise ValueError("unknown paired solver campaign")
    _, reference = read(root / "previous/110592")
    stats = {}
    comparisons = 0
    for variant in ("control", "candidate"):
        values = []
        for name in ("warmup", *(f"sample-{i}" for i in range(1, 6))):
            process, document = read(root / f"paired-large/{variant}/{name}")
            completed(process, document, 480, warnings=True)
            if document["execution"] != {"mode": "cuda", "device": 0, "threads": 128}:
                raise ValueError("large paired resource selection differs")
            if document["metadata"]["build_revision"] != campaign["implementations"][variant]["revision"]:
                raise ValueError("large paired source identity differs")
            if not same(physical(reference), physical(document)):
                raise ValueError("large paired physical observations or warnings differ")
            if name != "warmup":
                values.append(total(document, "total"))
            comparisons += 1
        stats[variant] = {"values": values, "median_solver_s": statistics.median(values),
                          "minimum_s": min(values), "maximum_s": max(values),
                          "standard_deviation_s": statistics.stdev(values)}
    checked = validate_claims(stats, summary)
    result.update(exact_large_paired_comparisons=comparisons, large_raw_statistics=stats)
    result["performance_evidence_checked" if "performance_evidence" in summary else "independently_derived_decision"] = checked
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("summary", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.directory, json.loads(args.summary.read_bytes())), indent=2))
