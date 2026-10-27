"""Reconstruct coordination costs directly from hashed process and probe records.

This reader does not call the collector's parser, metrics or summary functions.
Exact physical records and disjoint wall intervals precede opportunity estimates.
"""

import argparse
import csv
import json
import math
from pathlib import Path
import statistics

from tests.performance.audit_gradient_reassessment import read

NAMES = {
    "COORD_PREP": ("prepare_reserve", "prepare_pack", "prepare_upload"),
    "COORD_ROWS": ("bounds_cpu", "counts_download", "prefix_cpu", "membership_reserve", "offset_upload"),
    "COORD_STEP": ("cfl_download", "cfl_repack", "cfl_cpu", "prediction_download", "prediction_repack"),
}
BUNDLES = {
    "preparation": ("prepare_reserve", "prepare_pack", "prepare_upload"),
    "cfl": ("cfl_download", "cfl_repack", "cfl_cpu"),
    "bounds": ("prediction_download", "prediction_repack", "bounds_cpu"),
    "prefix": ("counts_download", "prefix_cpu", "membership_reserve", "offset_upload"),
}


def same(actual: float, expected: float) -> None:
    if not math.isclose(actual, expected, rel_tol=0, abs_tol=1e-10):
        raise ValueError("reported coordination quantity differs from raw data")


def physical(document: dict, particles: int, revision: str) -> str:
    if (document["completed_steps"] != "480" or document["request"]["steps"] != "480"
            or document["failures"] or document["status"] not in ("completed", "completed_with_warnings")
            or document["metadata"]["debug_assertions"] or document["metadata"]["build_revision"] != revision
            or document["execution"] != {"mode": "cuda", "device": 0, "threads": 128}
            or len(document["input"]["particles"]) != particles
            or [s["completed_steps"] for s in document["steps"]] != [str(i) for i in range(1, 481)]):
        raise ValueError("wrong or incomplete diagnostic request")
    value = dict(document)
    value.pop("measurements", None)
    value["metadata"] = dict(value["metadata"])
    value["metadata"].pop("build_revision")
    return json.dumps(value, sort_keys=True, allow_nan=False)


def audit(root: Path, summary: dict | None = None) -> dict:
    if summary is None:
        summary = json.loads((root / "summary.json").read_bytes())
    if summary.get("diagnostic_only") is not True:
        raise ValueError("instrumented observations cannot be primary timing evidence")
    identities = json.loads((root / "identities.json").read_bytes())
    if identities["control"]["fresh_ptx_sha256"] != identities["probe"]["fresh_ptx_sha256"]:
        raise ValueError("diagnostic changed native CUDA code")
    checked = {}
    for label, particles in (("8000", 8000), ("110592", 110592), ("110592-effects", 110592)):
        reported = summary["workloads"][label]
        reference = None
        warning_steps = None
        totals = {v: [] for v in identities}
        components = []
        for variant, identity in identities.items():
            for index in range(4):
                name = "warmup" if index == 0 else f"sample-{index}"
                directory = root / f"paired/{label}/{variant}/{name}"
                _, document = read(directory)
                value = physical(document, particles, identity["revision"])
                if reference is None:
                    reference = value
                    warning_steps = sum(s["warning"] for s in document["steps"])
                if value != reference:
                    raise ValueError("physical records or warning schedules differ")
                if index == 0:
                    if document.get("measurements") is not None:
                        raise ValueError("warmup unexpectedly measured")
                    continue
                timings = document["measurements"]
                if timings["schema_version"] != 1 or timings["mode"] != "total" or len(timings["steps"]) != 480 or timings["failed_attempt_s"] is not None:
                    raise ValueError("wrong diagnostic timer scope")
                durations = [r["total_s"] for r in timings["steps"]]
                if (any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0 for v in durations)
                        or any(r["stages"] is not None for r in timings["steps"])):
                    raise ValueError("invalid enclosing timer")
                total = sum(durations)
                totals[variant].append(total)
                if variant == "control":
                    same(total, reported["control_samples"][index-1]["solver_s"])
                    continue
                lines = [line for line in directory.joinpath("stderr.txt").read_text().splitlines() if line.startswith("COORD_")]
                if len(lines) != 1440:
                    raise ValueError("incomplete or duplicate probe records")
                rows = []
                for step in range(480):
                    row = {}
                    for group_index, (kind, names) in enumerate(NAMES.items()):
                        fields = next(csv.reader([lines[step*3 + group_index]]))
                        if fields[:3] != [kind, str(particles), str(step+1)] or len(fields) != len(names)+3:
                            raise ValueError("probe group, identity or step differs")
                        values = [float(v) for v in fields[3:]]
                        if any(not math.isfinite(v) or v < 0 for v in values):
                            raise ValueError("invalid raw component duration")
                        row.update(zip(names, values, strict=True))
                    if math.fsum(row.values()) > durations[step] + 1e-8:
                        raise ValueError("component intervals exceed their enclosing timer")
                    rows.append(row)
                measured = {key: math.fsum(row[key] for row in rows) for key in rows[0]}
                components.append(measured)
                claimed = reported["diagnostic_samples"][index-1]
                if claimed["primary_timing"] is not False:
                    raise ValueError("instrumented sample was relabelled as primary")
                same(total, claimed["solver_s"])
                for bundle, keys in BUNDLES.items():
                    same(math.fsum(measured[k] for k in keys), claimed["bundles_s"][bundle])
                for key, seconds in measured.items():
                    same(seconds, claimed["components_s"][key])
                    same(rows[0][key], claimed["first_step_s"][key])
                    for first, last in ((1, 120), (121, 240), (241, 480)):
                        same(math.fsum(r[key] for r in rows[first-1:last]), claimed["windows"][f"{first}-{last}"][key])
        control = statistics.median(totals["control"])
        probe = statistics.median(totals["probe"])
        same(control, reported["median_control_solver_s"])
        same(probe, reported["median_diagnostic_solver_s"])
        for key in components[0]:
            value = statistics.median(r[key] for r in components)
            same(value, reported["median_components_s"][key])
            same(value/probe, reported["component_fractions"][key])
        for bundle, keys in BUNDLES.items():
            value = statistics.median(math.fsum(sample[k] for k in keys) for sample in components)
            same(value, reported["median_bundles_s"][bundle])
            same(value/probe, reported["bundle_fractions"][bundle])
        if reported["warning_steps"] != warning_steps:
            raise ValueError("reported warning count differs")
        checked[label] = {"samples_per_variant": 3, "exact_physical_agreement": True,
                          "median_control_solver_s": control, "median_diagnostic_solver_s": probe,
                          "raw_component_sums_and_windows_checked": True}
    return {"diagnostic_only": True, "workloads": checked}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.directory.resolve()), indent=2, allow_nan=False))
