"""Check raw sort-batch evidence without trusting collector assessments or totals."""

import argparse
import json
from pathlib import Path
import statistics

from .audit import physical, read, same, total
from .audit_compact import close, completed


def audit(root: Path, summary: dict) -> dict:
    campaign = json.loads((root / "campaign.json").read_bytes())
    experiment = campaign["experiment"]
    if experiment not in ("sort-batch-v1", "diagnostic-v1", "diagnostic-atomic-v1", "stage-batch-v1") or summary["experiment"] != experiment:
        raise ValueError("unknown or mismatched coordination experiment")
    extra_bytes = 0 if experiment == "sort-batch-v1" else 32 if experiment == "stage-batch-v1" else 8
    if campaign.get("diagnostic_bytes", 0) != extra_bytes:
        raise ValueError("false persistent diagnostic allocation")
    comparisons = 0
    for count in (64, 216, 512, 1000, 1728, 4096, 8000):
        _, reference = read(root / f"controls/{count:06}")
        for kind in ("warmup", "profile"):
            process, document = read(root / f"regression/{count:06}/{kind}")
            completed(process, document, 480)
            if not same(physical(reference), physical(document)):
                raise ValueError("regression physical bits differ")
            if kind == "profile":
                total(document, "stages")
            comparisons += 1
    _, reference = read(root / "controls/008000")
    medians = {}
    for variant in ("control", "candidate"):
        values = []
        for name in ("warmup", *(f"sample-{i}" for i in range(1, 6))):
            process, document = read(root / f"paired/{variant}/{name}")
            completed(process, document, 480)
            if document["execution"] != {"mode": "cuda", "device": 0, "threads": 128}:
                raise ValueError("resource selection differs")
            if document["metadata"]["build_revision"] != campaign["implementations"][variant]["revision"]:
                raise ValueError("source revision differs")
            if not same(physical(reference), physical(document)):
                raise ValueError("paired physical bits differ")
            if name != "warmup":
                values.append(total(document, "total"))
            comparisons += 1
        claimed = summary["primary"][variant]
        medians[variant] = statistics.median(values)
        for expected, key in ((statistics.median(values), "median_solver_s"), (min(values), "minimum_s"),
                              (max(values), "maximum_s"), (statistics.stdev(values), "standard_deviation_s")):
            if not close(expected, claimed[key]):
                raise ValueError("false paired timing summary")
    if not close(medians["control"] / medians["candidate"], summary["paired_solver_speedup"]):
        raise ValueError("false paired speedup")
    if "confirmation" in summary:
        if summary["confirmation_policy"]["samples"] != list(range(6, 11)):
            raise ValueError("confirmation sample schedule differs")
        for variant in ("control", "candidate"):
            values = []
            p, d = read(root / f"confirmation/{variant}/warmup"); completed(p, d, 480)
            if not same(physical(reference), physical(d)):
                raise ValueError("confirmation warmup differs")
            comparisons += 1
            for i in range(6, 11):
                p, d = read(root / f"confirmation/{variant}/sample-{i}"); completed(p, d, 480)
                if d["execution"] != {"mode": "cuda", "device": 0, "threads": 128} or d["metadata"]["build_revision"] != campaign["implementations"][variant]["revision"]:
                    raise ValueError("confirmation resources or revision differ")
                if not same(physical(reference), physical(d)):
                    raise ValueError("confirmation physical bits differ")
                values.append(total(d, "total")); comparisons += 1
            initial = [total(read(root / f"paired/{variant}/sample-{i}")[1], "total") for i in range(1, 6)]
            for name, durations in (("confirmation", values), ("combined", initial + values)):
                claimed = summary[name][variant]
                if len(claimed["samples"]) != len(durations):
                    raise ValueError("confirmation or combined samples were removed")
                for actual, key in ((statistics.median(durations), "median_solver_s"), (min(durations), "minimum_s"),
                                     (max(durations), "maximum_s"), (statistics.stdev(durations), "standard_deviation_s")):
                    if not close(actual, claimed[key]):
                        raise ValueError("false confirmation or combined timing")
        for name in ("confirmation", "combined"):
            if not close(summary[name]["control"]["median_solver_s"] / summary[name]["candidate"]["median_solver_s"], summary[f"{name}_solver_speedup"]):
                raise ValueError("false confirmation or combined speedup")
    pilots = trajectories = 0
    for n in (8000, 32768, 110592, 262144, 512000):
        directory = root / f"capacity/{n:06}"
        admission = json.loads((directory / "admission.json").read_bytes())
        expected = 88*n + 32*(1 << (n-1).bit_length()) + 96 + 8*(n+1) + 744*n + extra_bytes
        ceiling = min(6*1024**3, admission["gpu_total"]*3//5, max(0, admission["gpu_free"]-2*1024**3))
        if admission["initial_lattice_estimate_bytes"] != expected or admission["ceiling_bytes"] != ceiling:
            raise ValueError("false capacity admission estimate")
        if not admission["admitted"]:
            if (directory / "pilot").exists():
                raise ValueError("unadmitted pilot executed")
            continue
        p, reference = read(directory / "cpu-pilot"); completed(p, reference, 4)
        p, document = read(directory / "pilot"); completed(p, document, 4)
        if not same(physical(reference), physical(document)):
            raise ValueError("independent capacity pilot differs")
        pilots += 1
        decision = json.loads((directory / "long-run-admission.json").read_bytes())
        projected = total(document, "total")*120
        if not close(projected, decision["projected_480_step_s"]) or decision["admitted"] != (projected <= 90):
            raise ValueError("false long-run admission")
        if (directory / "core").exists():
            if not decision["admitted"]:
                raise ValueError("unadmitted trajectory executed")
            p, document = read(directory / "core"); completed(p, document, 480, warnings=True)
            _, previous = read(root / f"previous/{n:06}")
            if not same(physical(previous), physical(document)):
                raise ValueError("complete capacity trajectory or warnings differ")
            total(document, "total")
            trajectories += 1
    return {"passed": True, "exact_observation_rich_comparisons": comparisons,
            "exact_independent_capacity_pilots": pilots, "exact_complete_capacity_comparisons": trajectories}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("summary", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.directory, json.loads(args.summary.read_bytes())), indent=2))
