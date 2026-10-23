"""Independently check component bounds and the preliminary performance screen."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics

from .audit import physical, read, same, total
from .audit_compact import close, completed
from .audit_assessment import validate as validate_evidence


def audit_diagnosis(root: Path) -> dict:
    summary = json.loads((root / "summary.json").read_bytes())
    identity = json.loads((root / "identity.json").read_bytes())
    names = ("velocity_reconstruction", "position_download", "velocity_download",
             "particle_reconstruction", "particle_validation", "plane_validation", "commit")
    fractions = {}
    for n in (8000, 110592):
        _, reference = read(root / f"references/{n}")
        samples = []
        for label in ("warmup", "sample-1", "sample-2", "sample-3"):
            path = root / str(n) / label
            process, document = read(path)
            completed(process, document, 480, warnings=True)
            if (document["metadata"]["build_revision"] != identity["revision"]
                    or document["execution"] != {"mode": "cuda", "device": 0, "threads": 128}
                    or not same(physical(reference), physical(document))):
                raise ValueError("diagnostic work differs")
            observations = []
            first = None
            for line in (path / "stderr.txt").read_text().splitlines():
                if not line.startswith("ACCEPT_"):
                    continue
                cells = line.split(",")
                if cells[0] == "ACCEPT_CUDA" and len(cells) == 6:
                    if first is not None or int(cells[1]) != n:
                        raise ValueError("bad CUDA probe sequence")
                    first = list(map(float, cells[2:]))
                elif cells[0] == "ACCEPT_HOST" and len(cells) == 5:
                    if first is None or int(cells[1]) != len(observations) + 1:
                        raise ValueError("bad host probe sequence")
                    row = first + list(map(float, cells[2:]))
                    if any(not math.isfinite(v) or v < 0 for v in row):
                        raise ValueError("bad duration")
                    observations.append(row)
                    first = None
                else:
                    raise ValueError("unknown probe format")
            if len(observations) != 480 or first is not None:
                raise ValueError("incomplete probe sequence")
            if label == "warmup":
                continue
            duration = total(document, "total")
            if any(math.fsum(row) > step["total_s"] + 1e-8
                   for row, step in zip(observations, document["measurements"]["steps"], strict=True)):
                raise ValueError("probe intervals exceed whole step")
            components = dict(zip(names, (math.fsum(row[i] for row in observations) for i in range(7)), strict=True))
            claimed = summary[str(n)]["samples"][len(samples)]
            if not close(duration, claimed["solver_s"]) or any(not close(v, claimed["components_s"][k]) for k, v in components.items()):
                raise ValueError("false component or solver totals")
            for first_step, last_step in ((1, 120), (121, 240), (241, 480)):
                for i, name in enumerate(names):
                    value = math.fsum(row[i] for row in observations[first_step-1:last_step])
                    if not close(value, claimed["windows"][f"{first_step}-{last_step}"][name]):
                        raise ValueError("false component window")
            samples.append((duration, components))
        if len(summary[str(n)]["samples"]) != 3:
            raise ValueError("diagnostic samples removed")
        whole = statistics.median(s[0] for s in samples)
        medians = {name: statistics.median(s[1][name] for s in samples) for name in names}
        claimed = summary[str(n)]
        if (not close(whole, claimed["median_solver_s"])
                or any(not close(v, claimed["median_components_s"][k]) for k, v in medians.items())
                or not close(medians["plane_validation"] / whole, claimed["plane_fraction_of_median_solver"])):
            raise ValueError("false diagnostic bound")
        if "plane_candidate_admitted" in claimed:
            if claimed["plane_candidate_admitted"] != (medians["plane_validation"] >= 0.1 * whole):
                raise ValueError("false historical diagnostic admission")
        elif claimed.get("assessment_required") is not True:
            raise ValueError("diagnostic evidence requires a written assessment")
        fractions[str(n)] = medians["plane_validation"] / whole
    return {"passed": True, "exact_diagnostic_runs": 8, "plane_fractions": fractions}


def validate_screen(values: dict, summary: dict) -> None:
    if "performance_evidence" in summary:
        if "admitted" in summary or summary.get("assessment_required") is not True or summary.get("primary_qualification") is not False:
            raise ValueError("a screen cannot decide continuation")
        validate_evidence({"screen": values}, {"schema_version": 1, "assessment_required": True,
            "decision_authority": "documented_engineering_assessment", "workloads": {"screen": summary["performance_evidence"]}})
        return
    for variant in ("control", "candidate"):
        if len(summary[variant + "_s"]) != 3 or any(not close(a, b) for a, b in zip(values[variant], summary[variant + "_s"], strict=True)):
            raise ValueError("false or filtered screen samples")
    ratio = statistics.median(values["control"]) / statistics.median(values["candidate"])
    expected = ratio >= 1.05 and max(values["candidate"]) < min(values["control"])
    if not close(ratio, summary["solver_speedup"]) or summary["admitted"] != expected or summary["primary_qualification"] is not False:
        raise ValueError("false screen decision")


def audit_screen(root: Path, reference: Path) -> dict:
    summary = json.loads((root / "summary.json").read_bytes())
    implementations = json.loads((root / "implementations.json").read_bytes())
    _, canonical = read(reference)
    values = {}
    for variant in ("control", "candidate"):
        values[variant] = []
        for label in ("warmup", "sample-1", "sample-2", "sample-3"):
            process, document = read(root / variant / label)
            completed(process, document, 480, warnings=True)
            if (document["metadata"]["build_revision"] != implementations[variant]["revision"]
                    or document["execution"] != {"mode": "cuda", "device": 0, "threads": 128}
                    or not same(physical(canonical), physical(document))):
                raise ValueError("screen work differs")
            if label != "warmup":
                values[variant].append(total(document, "total"))
    validate_screen(values, summary)
    result = {"passed": True, "exact_screen_runs": 8, "raw_solver_s": values}
    result.update({"historical_admitted": summary["admitted"]} if "admitted" in summary else {"assessment_required": True})
    return result


def validate_confirmation(values: dict, summary: dict) -> dict:
    """Check new evidence or reproduce the explicitly historical decision."""
    for name in ("primary", "paired_large"):
        for variant in ("control", "candidate"):
            durations = values[name][variant]
            if len(durations) != 5 or any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0 for v in durations):
                raise ValueError("confirmation requires five positive finite samples")
            claimed = summary[name][variant]
            if len(claimed["samples"]) != 5 or any(not close(a, b["solver_s"]) for a, b in zip(durations, claimed["samples"], strict=True)):
                raise ValueError("confirmation samples differ or were filtered")
            expected = {"median_solver_s": statistics.median(durations), "minimum_s": min(durations),
                        "maximum_s": max(durations), "standard_deviation_s": statistics.stdev(durations)}
            if any(not close(v, claimed[k]) for k, v in expected.items()):
                raise ValueError("false confirmation statistics")
    if "performance_evidence" in summary:
        if "decision" in summary:
            raise ValueError("a machine report cannot also decide retention")
        validate_evidence({"8000" if k == "primary" else "110592": v for k, v in values.items()}, summary["performance_evidence"])
        return {"assessment_required": True}
    gains = {}
    regressions = []
    for name in ("primary", "paired_large"):
        control, candidate = (values[name][v] for v in ("control", "candidate"))
        gains["8000" if name == "primary" else "110592"] = statistics.median(control) / statistics.median(candidate) >= 1.05 and max(candidate) < min(control)
        regressions.append(statistics.median(candidate) > statistics.median(control) * 1.03)
    expected = not any(regressions) and any(gains.values())
    claimed = summary["decision"]
    if (claimed["retained"] != expected or claimed["clear_gain"] != gains
            or claimed["both_median_regressions_at_most_three_percent"] != (not any(regressions))):
        raise ValueError("false confirmation retention decision")
    return {"retained": expected, "clear_gain": gains}


def audit_confirmation(root: Path, original: Path) -> dict:
    summary = json.loads((root / "summary.json").read_bytes())
    identity = json.loads((root / "identity.json").read_bytes())
    campaign = json.loads((original / "campaign.json").read_bytes())
    if (identity["implementations"] != campaign["implementations"]
            or hashlib.sha256((original / "summary.json").read_bytes()).hexdigest() != identity["original_summary_sha256"]
            or hashlib.sha256((root / "protocol.md").read_bytes()).hexdigest() != identity["protocol_sha256"]):
        raise ValueError("confirmation changed its protocol or original implementation identity")
    values = {}
    for name, relative in (("primary", "controls/008000"), ("paired_large", "previous/110592")):
        _, reference = read(original / relative)
        values[name] = {}
        for variant in ("control", "candidate"):
            values[name][variant] = []
            for label in ("warmup", *(f"sample-{i}" for i in range(1, 6))):
                process, document = read(root / name / variant / label)
                completed(process, document, 480, warnings=True)
                if (document["metadata"]["build_revision"] != identity["implementations"][variant]["revision"]
                        or document["metadata"]["debug_assertions"]
                        or document["execution"] != {"mode": "cuda", "device": 0, "threads": 128}
                        or not same(physical(reference), physical(document))):
                    raise ValueError("confirmation work differs")
                if label != "warmup":
                    values[name][variant].append(total(document, "total"))
    result = {"passed": True, "exact_confirmation_runs": 24, "raw_solver_s": values}
    result["performance_evidence_checked" if "performance_evidence" in summary else "independently_derived_decision"] = validate_confirmation(values, summary)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    result = {"diagnosis": audit_diagnosis(args.root / "diagnosis"),
              "screen": audit_screen(args.root / "screen", args.root / "diagnosis/references/110592")}
    if (args.root / "confirmation").exists():
        result["confirmation"] = audit_confirmation(args.root / "confirmation", args.root)
    print(json.dumps(result, indent=2))
