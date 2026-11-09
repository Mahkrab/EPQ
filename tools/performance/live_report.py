"""Describe retained live-viewer pairs without making a retention decision.

Warm-ups and failed pilots remain in the evidence directory but are excluded from
paired medians. GPU readings are whole-device samples, not process occupancy.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics as stats

from .live_viewer import summarise


def reading(sample: Path) -> dict:
    record = json.loads((sample / "summary.json").read_text(encoding="utf-8"))
    recomputed = summarise(sample / "frames.csv")
    for key, value in recomputed.items():
        if record[key] != value:
            raise ValueError(f"stored frame summary disagrees: {sample.name}: {key}")
    with (sample / "gpu.csv").open(encoding="utf-8",newline="") as stream:
        rows = list(csv.DictReader(stream, skipinitialspace=True))
    # Exclude startup and shutdown when those readings are available.
    rows = [row for row in rows if record["start_unix_s"] <=
            datetime.strptime(row["timestamp"], "%Y/%m/%d %H:%M:%S.%f").replace(tzinfo=timezone.utc).timestamp() <= record["end_unix_s"]]
    telemetry = {}
    for key in rows[0] if rows else ():
        if key == "timestamp" or key == "pstate":
            continue
        try:
            values = [float(row[key]) for row in rows]
        except ValueError:
            telemetry[key] = None
        else:
            telemetry[key] = dict(mean=stats.mean(values), median=stats.median(values),
                                  minimum=min(values), maximum=max(values), samples=len(values))
    return dict(record, telemetry=telemetry)


def campaign(root: Path, name: str, before: str, after: str) -> list[dict]:
    results = []
    for count in (8000,32000,110592):
        samples = {variant: [reading(root / f"{name}-{count}-p{pair}-{variant}")
                             for pair in (1,2,3)] for variant in (before,after)}
        pairs = []
        for a,b in zip(samples[before],samples[after]):
            pairs.append(dict(complete_speedup=a["complete_run_wall_s"]/b["complete_run_wall_s"],
                              simulation_speedup=b["simulated_s_per_wall_s"]/a["simulated_s_per_wall_s"]))
        metrics = ("presentation_fps","frame_mean_ms","frame_p95_ms","frame_p99_ms","frame_max_ms",
                   "simulated_s_per_wall_s","steps_s","solver_ms_per_step","snapshot_ms_per_step",
                   "complete_run_wall_s","cpu_core_equivalents","peak_rss_kib","virtual_kib")
        summaries = {}
        for variant, values in samples.items():
            summaries[variant] = {key:dict(median=stats.median(v[key] for v in values),
                minimum=min(v[key] for v in values),maximum=max(v[key] for v in values)) for key in metrics}
            summaries[variant]["cpu_frame_mean_ms"] = {key:stats.median(v["cpu_frame_mean_ms"][key] for v in values)
                for key in values[0]["cpu_frame_mean_ms"]}
            summaries[variant]["telemetry"] = {key:stats.median(v["telemetry"][key]["mean"] for v in values)
                for key in values[0]["telemetry"] if all(v["telemetry"].get(key) is not None for v in values)}
            summaries[variant]["stutters_over_33ms"] = sum(v["stutters_over_33ms"] for v in values)
            summaries[variant]["stutters_over_50ms"] = sum(v["stutters_over_50ms"] for v in values)
        results.append(dict(particles=count, variants=summaries,pairs=pairs))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root",type=Path)
    args = parser.parse_args()
    try:
        result = dict(indexed=campaign(args.root,"indexed","baseline","indexed"),
                      buffers=campaign(args.root,"buffers","indexed","buffers"))
        (args.root / "comparison.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    except (OSError,ValueError,KeyError) as error:
        parser.exit(1,f"live viewer report: {error}\n")


if __name__ == "__main__":
    main()
