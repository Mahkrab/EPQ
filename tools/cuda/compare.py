"""Compare complete simulator records under reference-comparison-v1.

Particle arrays remain available: hashes cannot establish tolerance acceptance.
Run with two result paths; stdout is a disagreement report and exit 1 rejects it.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import gzip
import json
import math
import re
from pathlib import Path
import struct
import sys

from tools.baseline.data import require_exact

LIMITS = {"position_m": 1e-5, "velocity_m_s": 0.005,
          "maximum_speed_m_s": 0.005, "seconds": 1e-6,
          "mean_error": 1e-4, "maximum_error": 1e-4}


def binary32(value: object) -> float:
    """Restore the finite binary32 number carried by a JSON round trip."""
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError("comparison requires finite binary32 numbers")
    result = struct.unpack("!f", struct.pack("!f", value))[0]
    if not math.isfinite(result):
        raise ValueError("number exceeds binary32")
    return result


def _difference(expected: object, actual: object, limit: float, exact: bool) -> dict:
    expected, actual = binary32(expected), binary32(actual)
    error = abs(actual - expected)
    same = struct.pack("!f", expected) == struct.pack("!f", actual)
    return {"expected": expected, "actual": actual, "absolute_error": error,
            "limit": 0.0 if exact else limit, "exact": same,
            "passed": same if exact else error <= limit}


def _context(document: dict) -> dict:
    return {"backend": document.get("backend"), "execution": document.get("execution", {"mode": "serial"}),
            "metadata": document.get("metadata"), "measurements_present": "measurements" in document}


def _structure(document: dict) -> dict:
    value = copy.deepcopy(document)
    value.pop("measurements", None)
    value.pop("execution", None)
    value.pop("backend")
    for key in ("backend", "run_id", "build_revision", "target_os", "target_arch", "debug_assertions", "device"):
        value["metadata"].pop(key, None)
    return value


def compare(reference: dict, candidate: dict, *, exact: bool = False) -> dict:
    """Check every observation, preserving structural obligations and worst errors.

    Malformed or incomplete records fail before numerical acceptance. Exact mode
    also rejects signed-zero changes and is required for unchanged arithmetic.
    """
    report = {"policy": "reference-comparison-v1", "exact_required": exact,
              "reference": _context(reference), "candidate": _context(candidate),
              "structural_mismatches": [], "snapshots": [], "audits": [], "cfl": [],
              "first_divergent_checkpoint": None, "first_divergent_step": None, "passed": False}
    try:
        for name, document in (("reference", reference), ("candidate", candidate)):
            if type(document["schema_version"]) is not int or document["schema_version"] != 1:
                raise ValueError(f"{name}: unsupported result schema")
            if document["status"] not in ("completed", "completed_with_warnings") or document["failures"]:
                raise ValueError(f"{name}: incomplete or failed request")
            count = int(document["request"]["steps"])
            if str(count) != document["completed_steps"] or len(document["steps"]) != count:
                raise ValueError(f"{name}: accepted work differs from request")
            if [step["completed_steps"] for step in document["steps"]] != [str(i) for i in range(1, count + 1)]:
                raise ValueError(f"{name}: diagnostic sequence is incomplete")
            checkpoints = document["request"]["checkpoints"]
            if [item["snapshot"]["completed_steps"] for item in document["checkpoints"]] != checkpoints:
                raise ValueError(f"{name}: checkpoint sequence differs from request")
            if [int(step) for step in checkpoints] != sorted(set(int(step) for step in checkpoints)):
                raise ValueError(f"{name}: checkpoints are duplicated or unordered")
            if any(int(step) < 0 or int(step) > count for step in checkpoints):
                raise ValueError(f"{name}: checkpoint outside request")
            if document["final_snapshot"]["completed_steps"] != str(count):
                raise ValueError(f"{name}: final state is incomplete")
            if document["metadata"]["backend"] != document["backend"]:
                raise ValueError(f"{name}: backend metadata is inconsistent")
        r, c = _structure(reference), _structure(candidate)
        # Structure is compared before any numerical budgets are considered.
        pairs = [(a["snapshot"], b["snapshot"], f"checkpoint:{a['snapshot']['completed_steps']}")
                 for a, b in zip(r["checkpoints"], c["checkpoints"], strict=True)]
        pairs.append((r["final_snapshot"], c["final_snapshot"], "final"))
        for a, b, label in pairs:
            if len(a["particles"]) != len(reference["input"]["particles"]) or len(b["particles"]) != len(a["particles"]):
                raise ValueError(f"{label}: particle count differs from input")
            identities = [p["identity"] for p in a["particles"]]
            if identities != [p["identity"] for p in reference["input"]["particles"]]:
                raise ValueError(f"{label}: particle identities differ from input")
            for x, y in zip(a["particles"], b["particles"], strict=True):
                for quantity in ("position_m", "velocity_m_s"):
                    for axis in ("x", "y", "z"):
                        binary32(x[quantity][axis]); binary32(y[quantity][axis])
                        x[quantity][axis] = y[quantity][axis] = "numerically compared"
        for a, b in zip(r["checkpoints"], c["checkpoints"], strict=True):
            if a["density"] is None or b["density"] is None:
                raise ValueError("required audit is unavailable")
            for metric in ("mean_error", "maximum_error"):
                if a["density"]["sample_count"] == b["density"]["sample_count"] == 0:
                    if a["density"][metric] is not None or b["density"][metric] is not None:
                        raise ValueError("empty audit must have unavailable metrics")
                else:
                    binary32(a["density"][metric]); binary32(b["density"][metric])
                    a["density"][metric] = b["density"][metric] = "numerically compared"
        for a, b in zip(r["steps"], c["steps"], strict=True):
            for key in ("maximum_speed_m_s",):
                binary32(a[key]); binary32(b[key]); a[key] = b[key] = "numerically compared"
            if a["cfl_limit"]["kind"] == b["cfl_limit"]["kind"] == "finite":
                binary32(a["cfl_limit"]["seconds"]); binary32(b["cfl_limit"]["seconds"])
                a["cfl_limit"]["seconds"] = b["cfl_limit"]["seconds"] = "numerically compared"
        require_exact(c, r)
    except (KeyError, TypeError, ValueError, OverflowError, struct.error) as error:
        report["structural_mismatches"].append(str(error))
        step = re.search(r"result\.steps\[(\d+)\]", str(error))
        if step and int(step[1]) < len(reference.get("steps", [])):
            report["first_divergent_step"] = reference["steps"][int(step[1])]["completed_steps"]
        return report

    pairs = [(a["snapshot"], b["snapshot"], a["snapshot"]["completed_steps"])
             for a, b in zip(reference["checkpoints"], candidate["checkpoints"], strict=True)]
    pairs.append((reference["final_snapshot"], candidate["final_snapshot"], "final"))
    for a, b, label in pairs:
        row = {"checkpoint": label, "particles": len(a["particles"]), "passed": True}
        for quantity in ("position_m", "velocity_m_s"):
            errors = []
            for x, y in zip(a["particles"], b["particles"], strict=True):
                for axis in ("x", "y", "z"):
                    diff = _difference(x[quantity][axis], y[quantity][axis], LIMITS[quantity], exact)
                    errors.append((diff["absolute_error"], x["identity"], axis, diff))
            worst = max(errors, key=lambda item: (item[0], not item[3]["exact"]), default=None)
            row[quantity] = {"components": len(errors), "maximum_absolute_error": worst[0] if worst else 0.0,
                             "rms_error": math.sqrt(sum(e[0] ** 2 for e in errors) / len(errors)) if errors else 0.0,
                             "worst_identity": worst[1] if worst else None, "worst_axis": worst[2] if worst else None,
                             "worst_values": worst[3] if worst else None,
                             "limit": 0.0 if exact else LIMITS[quantity],
                             "exact_components": sum(e[3]["exact"] for e in errors),
                             "passed": all(e[3]["passed"] for e in errors)}
            row["passed"] &= row[quantity]["passed"]
        report["snapshots"].append(row)
        if not row["passed"] and report["first_divergent_checkpoint"] is None:
            report["first_divergent_checkpoint"] = label
    for a, b in zip(reference["checkpoints"], candidate["checkpoints"], strict=True):
        report["audits"].append({"checkpoint": a["snapshot"]["completed_steps"],
            "sample_count": a["density"]["sample_count"],
            "metrics": {key: _difference(a["density"][key], b["density"][key], LIMITS[key], exact)
                        for key in ("mean_error", "maximum_error") if a["density"][key] is not None}})
        if any(not diff["passed"] for diff in report["audits"][-1]["metrics"].values()):
            checkpoint = a["snapshot"]["completed_steps"]
            previous = report["first_divergent_checkpoint"]
            if previous is None or int(checkpoint) < int(reference["completed_steps"] if previous == "final" else previous):
                report["first_divergent_checkpoint"] = checkpoint
    for a, b in zip(reference["steps"], candidate["steps"], strict=True):
        report["cfl"].append({"step": a["completed_steps"], "warning": a["warning"],
            "speed": _difference(a["maximum_speed_m_s"], b["maximum_speed_m_s"], LIMITS["maximum_speed_m_s"], exact),
            "limit": _difference(a["cfl_limit"]["seconds"], b["cfl_limit"]["seconds"], LIMITS["seconds"], exact)
                     if a["cfl_limit"]["kind"] == "finite" else None})
    report["passed"] = (all(row["passed"] for row in report["snapshots"])
                        and all(diff["passed"] for row in report["audits"] for diff in row["metrics"].values())
                        and all(row["speed"]["passed"] and (row["limit"] is None or row["limit"]["passed"])
                                for row in report["cfl"]))
    mismatching_steps = [row["step"] for row in report["cfl"]
                        if not row["speed"]["passed"] or (row["limit"] is not None and not row["limit"]["passed"])]
    report["first_divergent_step"] = mismatching_steps[0] if mismatching_steps else None
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--exact", action="store_true", help="require identical binary32 bits")
    args = parser.parse_args()
    try:
        raw = [gzip.decompress(path.read_bytes()) if path.suffix == ".gz" else path.read_bytes()
               for path in (args.reference, args.candidate)]
        documents = [json.loads(value) for value in raw]
        if any(not isinstance(value, dict) for value in documents):
            raise ValueError("result documents must be JSON objects")
        report = compare(*documents, exact=args.exact)
        report["files_sha256"] = {key: hashlib.sha256(value).hexdigest()
                                  for key, value in zip(("reference", "candidate"), raw, strict=True)}
        print(json.dumps(report, indent=2, allow_nan=False))
        return 0 if report["passed"] else 1
    except (OSError, ValueError, TypeError, EOFError) as error:
        print(f"CUDA comparison: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
