"""Join raw quality, work counters and paired timings without deciding adoption."""
import argparse
import json
from pathlib import Path
import statistics
import csv

if __package__:
    from .numerical_work import write_json
else:
    from numerical_work import write_json


def paired(rows):
    """Preserve matched repeats and keep the two control series separate."""
    results = []
    for scene in ("resolved", "large"):
        for candidate in ("half-rate", "half-iterations"):
            group = [r for r in rows if r["scene"] == scene and r["candidate"] == candidate
                     and not r["warmup"]]
            repeats = {}
            for row in group:
                modes = repeats.setdefault(row["repeat"], {})
                if row["policy"] in modes:
                    raise ValueError("duplicate paired sample")
                modes[row["policy"]] = row["cost_s_per_sim_s"]
            if set(repeats) != set(range(1, 6)) or any(set(p) != {"production", candidate} for p in repeats.values()):
                raise ValueError("five complete paired repeats are required")
            controls = [repeats[k]["production"] for k in sorted(repeats)]
            values = [repeats[k][candidate] for k in sorted(repeats)]
            ratios = [a/b for a, b in zip(controls, values)]
            results.append(dict(scene=scene, candidate=candidate, control_samples=controls,
                                candidate_samples=values, paired_speedups=ratios,
                                control_median=statistics.median(controls),
                                candidate_median=statistics.median(values),
                                speedup_ratio_of_medians=statistics.median(controls)/statistics.median(values),
                                slower_pairs=sum(r < 1 for r in ratios),
                                simulated_seconds_per_wall_second=1/statistics.median(values)))
    return results


def assess(root):
    plan = json.loads((root/"matrix-plan.json").read_text())
    fresh = json.loads((root/"frontier.json").read_text())
    by_label = {row["label"]: row for row in fresh}
    work = {(r["scene"], r["policy"]["id"]): r
            for r in json.loads((root/"workload-results.json").read_text())}
    traces = {(r["scene"], r["policy"]["id"]): r
              for r in json.loads((root/"trace-results.json").read_text())}
    matrix = []
    for row in plan:
        policy = row["policy"]
        key = row["scene"], policy["id"]
        quality = row["summary"] if "reused_from" in row else by_label[f'{row["scene"]}--{policy["id"]}']
        w, trace = work[key], traces[key]
        matrix.append(dict(scene=row["scene"], hz=round(1/policy["dt"]), iterations=policy["iterations"],
                           reused="reused_from" in row, policy=policy, quality=quality,
                           actual_steps=w["steps"], simulated_s=w["simulated_s"],
                           jacobi_iterations_per_sim_s=w["jacobi_iterations"]/w["simulated_s"],
                           neighbour_entries_per_sim_s=w["counted_neighbour_entries"]/w["simulated_s"],
                           jacobi_entry_visits_per_sim_s=w["derived_jacobi_entry_visits"]/w["simulated_s"],
                           self_density_visits_per_sim_s=w["derived_self_density_visits"]/w["simulated_s"],
                           kernels_per_sim_s=trace["kernel_count"]/trace["simulated_s"],
                           traced_kernel_s_per_sim_s=trace["kernel_execution_s"]/trace["simulated_s"],
                           ordinary_solver_s_per_sim_s=quality["cost_s_per_sim_s"]))
    result = dict(matrix=matrix,
                  sustained=paired(json.loads((root/"sustained-results.json").read_text())),
                  long_quality=[r for r in fresh if r["label"].startswith("long-")],
                  residual_opportunity=json.loads((root/"residual-results.json").read_text()),
                  sustained_work=[r for r in work.values()
                                  if r["policy"]["id"] in ("production", "half-rate", "half-iterations")],
                  note="Reused screen clocks, fresh screen clocks and fresh paired sustained clocks are separate evidence. Residual opportunity is not an adaptive speedup.")
    write_json(root/"assessment.json", result)
    flat = []
    for row in matrix:
        quality = row["quality"]
        flat.append({**{k: v for k, v in row.items() if k not in ("quality", "policy")},
                     **{k: quality[k] for k in ("p95_compression_peak", "max_compression_peak",
                                                "min_separation_over_dx", "volume_error_peak",
                                                "energy_excess_peak", "CFL_warning_steps", "stability")}})
    with (root/"matrix.csv").open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=list(flat[0]))
        writer.writeheader()
        writer.writerows(flat)
    for row in result["sustained"]:
        print(row["scene"], row["candidate"], row["candidate_median"], row["speedup_ratio_of_medians"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    assess(parser.parse_args().root.resolve())
