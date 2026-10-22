"""Keep the original diagnostic comparison and its confirmation visibly separate.

The confirmation was declared after observing a small, variable initial gain. All
samples remain in the descriptive combined summary; none replaces an earlier run.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import statistics
import sys

from tools.cuda.compare import compare
from .capture import load_attempt
from .compact import qualified
from .report import metrics
from .sort_batch import report


def summarise(samples: list[dict]) -> dict:
    """Summarise a complete five- or ten-run set without filtering its spread."""
    if len(samples) not in (5, 10):
        raise ValueError("a complete five- or ten-sample set is required")
    values = [s["solver_s"] for s in samples]
    if any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0 for v in values):
        raise ValueError("invalid solver duration")
    return {"samples": samples, "median_solver_s": statistics.median(values),
            "minimum_s": min(values), "maximum_s": max(values), "standard_deviation_s": statistics.stdev(values)}


def analyse(root: Path) -> dict:
    result = report(root)
    campaign = json.loads((root / "campaign.json").read_bytes())
    policy = json.loads((root / "confirmation-policy.json").read_bytes())
    if campaign["experiment"] != "diagnostic-atomic-v1" or policy["samples"] != list(range(6, 11)):
        raise ValueError("unknown diagnostic confirmation")
    _, reference = load_attempt(root / "controls/008000")
    result.update(confirmation_policy=policy, confirmation={}, combined={})
    for variant in ("control", "candidate"):
        samples = []
        for index in range(6, 11):
            process, document = load_attempt(root / f"confirmation/{variant}/sample-{index}")
            if not qualified(process, document, particles=8000, steps=480, observation=True,
                             revision=campaign["implementations"][variant]["revision"]) or not compare(reference, document, exact=True)["passed"]:
                raise ValueError("unclean or physically different confirmation sample")
            samples.append(metrics(process, document, "sample"))
        result["confirmation"][variant] = summarise(samples)
        result["combined"][variant] = summarise([*result["primary"][variant]["samples"], *samples])
    for name in ("confirmation", "combined"):
        result[f"{name}_solver_speedup"] = result[name]["control"]["median_solver_s"] / result[name]["candidate"]["median_solver_s"]
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(analyse(args.directory.resolve()), indent=2, allow_nan=False))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Diagnostic report: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
