"""Read component probes without promoting instrumented runs to primary timings.

The diagnostic overlay emits one CUDA/host pair per completed step. Ordinary
physical outputs and the existing total timer independently bound those probes.
"""

from __future__ import annotations

import math
import statistics

from .arithmetic import require_sample
from .assessment import paired


COMPONENTS = ("velocity_reconstruction", "position_download", "velocity_download",
              "particle_reconstruction", "particle_validation", "plane_validation", "commit")


def probes(stderr: str, particles: int, steps: int) -> list[dict[str, float]]:
    """Reject incomplete, reordered or non-finite component observations."""
    if any(type(v) is not int or v < 1 for v in (particles, steps)):
        raise ValueError("positive particle and step counts are required")
    result = []
    pending = None
    for line in stderr.splitlines():
        if not line.startswith("ACCEPT_"):
            continue
        fields = line.split(",")
        if fields[0] == "ACCEPT_CUDA" and len(fields) == 6:
            if pending is not None or int(fields[1]) != particles:
                raise ValueError("duplicate or wrong-particle CUDA probe")
            pending = [float(v) for v in fields[2:]]
        elif fields[0] == "ACCEPT_HOST" and len(fields) == 5:
            if pending is None or int(fields[1]) != len(result) + 1:
                raise ValueError("missing CUDA probe or out-of-order host step")
            values = pending + [float(v) for v in fields[2:]]
            if any(not math.isfinite(v) or v < 0 for v in values):
                raise ValueError("invalid component duration")
            result.append(dict(zip(COMPONENTS, values, strict=True)))
            pending = None
        else:
            raise ValueError("unknown or malformed acceptance probe")
    if pending is not None or len(result) != steps:
        raise ValueError("incomplete acceptance probe sequence")
    return result


def diagnostic(process: dict, document: dict, reference: dict, revision: str,
               stderr: str, particles: int) -> dict:
    """Validate physical work and keep per-component timing inside the whole step."""
    measured = require_sample(process, document, reference, revision)
    rows = probes(stderr, particles, 480)
    for row, step in zip(rows, document["measurements"]["steps"], strict=True):
        if math.fsum(row.values()) > step["total_s"] + 1e-8:
            raise ValueError("component intervals exceed the observed solver step")
    windows = {}
    for first, last in ((1, 120), (121, 240), (241, 480)):
        windows[f"{first}-{last}"] = {name: math.fsum(row[name] for row in rows[first-1:last]) for name in COMPONENTS}
    return {"solver_s": measured["solver_s"], "components_s": {name: math.fsum(row[name] for row in rows) for name in COMPONENTS},
            "windows": windows, "primary_timing": False}


def diagnostic_summary(samples: list[dict]) -> dict:
    """Use all three diagnostic samples when bounding a candidate's opportunity."""
    if len(samples) != 3:
        raise ValueError("three diagnostic samples are required")
    total = statistics.median(s["solver_s"] for s in samples)
    components = {name: statistics.median(s["components_s"][name] for s in samples) for name in COMPONENTS}
    return {"primary_timing": False, "samples": samples, "median_solver_s": total,
            "median_components_s": components, "plane_fraction_of_median_solver": components["plane_validation"] / total,
            "assessment_required": True}


def historical_diagnostic_summary(samples: list[dict]) -> dict:
    """Reproduce the former opportunity cutoff for an archived investigation."""
    result = diagnostic_summary(samples)
    result.pop("assessment_required")
    result["plane_candidate_admitted"] = result["median_components_s"]["plane_validation"] >= 0.1 * result["median_solver_s"]
    return result


def screen(control: list[float], candidate: list[float]) -> dict:
    """Report the exploratory pairs without an automatic continuation veto."""
    if len(control) != 3 or len(candidate) != 3:
        raise ValueError("three timing pairs are required for this screen")
    return {"performance_evidence": paired(control, candidate), "assessment_required": True,
            "primary_qualification": False}


def historical_screen(control: list[float], candidate: list[float]) -> dict:
    """Reproduce the superseded screening rule for archived observations."""
    if any(len(values) != 3 or any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0 for v in values)
           for values in (control, candidate)):
        raise ValueError("three positive finite durations per screen variant are required")
    ratio = statistics.median(control) / statistics.median(candidate)
    return {"admitted": ratio >= 1.05 and max(candidate) < min(control), "solver_speedup": ratio,
            "control_s": control, "candidate_s": candidate, "primary_qualification": False}
