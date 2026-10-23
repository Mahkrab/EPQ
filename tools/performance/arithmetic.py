"""Compare bounded solver changes at coordination-heavy and larger workloads.

The larger workload retains known CFL warnings. Exact agreement admits a timing
comparison with its control, not a claim of independently qualified fluid quality.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import statistics
import sys

from tools.cuda.compare import compare
from .assessment import evidence
from .capture import load_attempt
from .compact import attempt, verify
from .report import metrics
from .sort_batch import report as coordination_report


def summarise(samples: list[dict]) -> dict:
    """Retain a complete five-run set, including any slow sample."""
    values = [sample["solver_s"] for sample in samples]
    if len(values) != 5 or any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0 for v in values):
        raise ValueError("five positive finite solver durations are required")
    return {"samples": samples, "median_solver_s": statistics.median(values),
            "minimum_s": min(values), "maximum_s": max(values), "standard_deviation_s": statistics.stdev(values)}


def historical_decision(primary: dict, larger: dict) -> dict:
    """Reproduce the superseded rule only when explicitly replaying old reports."""
    gains = {}
    no_regression = True
    for label, workload in (("8000", primary), ("110592", larger)):
        control, candidate = (summarise(workload[v]["samples"]) for v in ("control", "candidate"))
        gains[label] = (control["median_solver_s"] / candidate["median_solver_s"] >= 1.05
                        and candidate["maximum_s"] < control["minimum_s"])
        no_regression &= candidate["median_solver_s"] <= control["median_solver_s"] * 1.03
    return {"retained": no_regression and any(gains.values()), "clear_gain": gains,
            "both_median_regressions_at_most_three_percent": no_regression,
            "policy": "at least 1.05x with non-overlapping five-sample ranges at one declared size; neither median regresses by more than 3%"}


def require_sample(process: dict, document: dict | None, reference: dict, revision: str,
                   *, kind: str = "sample") -> dict:
    """Admit identical completed work, retaining the reference's warning policy."""
    if (process["exit_code"] != 0 or process["timed_out"] or process["interrupted"]
            or document is None or document["status"] != reference["status"]
            or document["status"] not in ("completed", "completed_with_warnings")
            or document["failures"] or document["completed_steps"] != "480"
            or document["execution"] != {"mode": "cuda", "device": 0, "threads": 128}
            or document["metadata"]["build_revision"] != revision or document["metadata"]["debug_assertions"]
            or not compare(reference, document, exact=True)["passed"]):
        raise ValueError("incomplete, different or unqualified arithmetic comparison sample")
    return metrics(process, document, kind)


def collect(root: Path) -> None:
    """Collect the separately declared 110,592-particle pairs sequentially."""
    campaign = json.loads((root / "campaign.json").read_bytes())
    if campaign["experiment"] not in ("gradient-prefix-v1", "reserve-reuse-v1", "power-tables-v1", "acceptance-inline-v1"):
        raise ValueError("unknown paired solver experiment")
    scene = Path(campaign["baseline_directory"]) / "inputs/scenes/capacity-block-48.toml"
    _, reference = load_attempt(root / "previous/110592")
    for name in ("warmup", *(f"sample-{i}" for i in range(1, 6))):
        index = 0 if name == "warmup" else int(name.rsplit("-", 1)[1])
        for variant in (("control", "candidate") if index % 2 else ("candidate", "control")):
            label = f"paired-large/{variant}/{name}"
            attempt(root, campaign, label, variant, scene, 110592, observation=False,
                    kind="warmup" if name == "warmup" else "sample", reference=reference)
            process, document = load_attempt(root / label)
            require_sample(process, document, reference, campaign["implementations"][variant]["revision"],
                           kind="warmup" if name == "warmup" else "sample")
    verify(root, campaign)


def report(root: Path, *, historical_policy: bool = False) -> dict:
    """Validate samples and report evidence; the written assessment decides retention."""
    campaign = json.loads((root / "campaign.json").read_bytes())
    if campaign["experiment"] not in ("gradient-prefix-v1", "reserve-reuse-v1", "power-tables-v1", "acceptance-inline-v1"):
        raise ValueError("unknown paired solver experiment")
    result = coordination_report(root)
    _, reference = load_attempt(root / "previous/110592")
    result["paired_large"] = {}
    for variant in ("control", "candidate"):
        samples = []
        for index in range(1, 6):
            process, document = load_attempt(root / f"paired-large/{variant}/sample-{index}")
            samples.append(require_sample(process, document, reference, campaign["implementations"][variant]["revision"]))
        result["paired_large"][variant] = summarise(samples)
    result["paired_large_solver_speedup"] = result["paired_large"]["control"]["median_solver_s"] / result["paired_large"]["candidate"]["median_solver_s"]
    if historical_policy:
        result["decision"] = historical_decision(result["primary"], result["paired_large"])
    else:
        result["performance_evidence"] = evidence(result["primary"], result["paired_large"])
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("collect", "report"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--historical-policy", action="store_true",
                        help="reproduce the superseded automatic decision in an old report")
    args = parser.parse_args()
    if args.historical_policy and args.operation != "report":
        parser.error("--historical-policy applies only to report")
    try:
        if args.operation == "collect":
            collect(args.directory.resolve())
        else:
            print(json.dumps(report(args.directory.resolve(), historical_policy=args.historical_policy), indent=2, allow_nan=False))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Arithmetic comparison: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
