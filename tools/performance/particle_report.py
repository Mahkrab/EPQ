"""Recompute the particle campaign from retained frames, GPU logs and acceptances.

Ordinary paired throughput and synchronising timestamp profiles remain separate.
The report describes the evidence; the engineering assessment owns retention.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import statistics

from .live_report import campaign
from .particle_capacity import assess


def report(root: Path) -> dict:
    """Validate stored summaries and return the three independent evidence groups."""
    comparisons = {mode: campaign(root, mode, "indexed", mode)
                   for mode in ("low", "impostor", "adaptive")}
    gpu = []
    for count in (8000, 32000, 110592):
        for mode in ("indexed", "low", "impostor", "adaptive"):
            log = (root / f"gpu-{count}-{mode}" / "viewer.log").read_text(encoding="utf-8")
            values = [1000 * float(x) for x in re.findall(r"^GPU_DRAW_S (\S+)$", log, re.M)]
            primitives = re.findall(r"^PARTICLE_PRIMITIVES \w+ (\d+) (\d+)$", log, re.M)
            if not values or len(values) != len(primitives):
                raise ValueError(f"incomplete GPU timestamp profile: {count}/{mode}")
            # Exclude the terminal draw after completion, matching the original
            # component summary. Its timestamp remains in the raw log.
            values = values[:-1]
            if not values:
                raise ValueError(f"GPU profile contains no steady draws: {count}/{mode}")
            gpu.append(dict(count=count, renderer=mode, mean_ms=statistics.mean(values),
                            median_ms=statistics.median(values), samples=len(values),
                            submitted_triangles=sorted({int(x) for x, _ in primitives}),
                            mesh_levels=sorted({int(x) for _, x in primitives})))
    capacity = []
    for count in (35200, 38400, 40000):
        for pair in (1, 2, 3):
            sample = root / f"capacity-exact-{count}-p{pair}"
            result = assess(sample / "accepted.csv", 4800, 0.004166666883975267)
            stored = json.loads((sample / "capacity.json").read_text(encoding="utf-8"))
            if result != stored:
                raise ValueError(f"capacity summary disagrees: {sample.name}")
            capacity.append(dict(count=count, repeat=pair, **result))
    result = dict(comparison=comparisons, gpu_profiles=gpu, capacity=capacity)
    resumed = root / "post-resume"
    if (resumed / "capacity-summary.json").is_file():
        rows = json.loads((resumed / "capacity-summary.json").read_text(encoding="utf-8"))
        for row in rows:
            path = resumed / f'post-resume-capacity-{row["count"]}-p{row["repeat"]}'
            measured = assess(path / "accepted.csv", 4800, 0.004166666883975267)
            if dict(count=row["count"], repeat=row["repeat"], **measured) != row:
                raise ValueError(f"resumed capacity summary disagrees: {path.name}")
        result["post_resume_capacity"] = rows
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    try:
        result = report(args.root)
        (args.root / "assessment-data.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8")
        write_tables(args.root, result)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"particle report: {error}\n")


def write_tables(root: Path, result: dict) -> None:
    """Keep tabular units and the underlying evidence groups explicit."""
    lines = ["# Particle rendering measurements", "",
             "Medians of three ordinary alternating pairs, excluding warm-ups. GPU draw intervals come from separate synchronising profiles. These are primary-PC client-window measurements, not physical desktop FPS.", "",
             "## Indexed versus retained impostor", "",
             "| Particles | Metric | Indexed | Impostor |",
             "| ---: | --- | ---: | ---: |"]
    metrics = [("Surface presentations/s", "presentation_fps", 3),
               ("Mean interval, ms", "frame_mean_ms", 3),
               ("p95 interval, ms", "frame_p95_ms", 3),
               ("p99 interval, ms", "frame_p99_ms", 3),
               ("Simulated s/wall s", "simulated_s_per_wall_s", 4),
               ("Timesteps/s", "steps_s", 3),
               ("Complete CUDA solver call, ms/step", "solver_ms_per_step", 3),
               ("Complete launch/completion wall time, s", "complete_run_wall_s", 3),
               ("Process CPU, core equivalents", "cpu_core_equivalents", 3),
               ("Peak host RSS, KiB", "peak_rss_kib", 0)]
    for record in result["comparison"]["impostor"]:
        count = record["particles"]
        a, b = (record["variants"][mode] for mode in ("indexed", "impostor"))
        for label, key, digits in metrics:
            lines.append(f'| {count:,} | {label} | {a[key]["median"]:.{digits}f} | {b[key]["median"]:.{digits}f} |')
        for label, key in [("GPU utilisation, %", "utilization.gpu [%]"),
                           ("GPU memory, MiB", "memory.used [MiB]"),
                           ("SM clock, MHz", "clocks.current.sm [MHz]"),
                           ("Memory clock, MHz", "clocks.current.memory [MHz]")]:
            lines.append(f'| {count:,} | {label} | {a["telemetry"][key]:.2f} | {b["telemetry"][key]:.2f} |')
        for key in ("acquire_s", "prepare_s", "upload_s", "submit_s", "present_s", "redraw_s"):
            lines.append(f'| {count:,} | CPU {key[:-2]}, ms/frame | {a["cpu_frame_mean_ms"][key]:.4f} | {b["cpu_frame_mean_ms"][key]:.4f} |')
        draw = [next(r["mean_ms"] for r in result["gpu_profiles"]
                     if r["count"] == count and r["renderer"] == mode)
                for mode in ("indexed", "impostor")]
        lines.append(f'| {count:,} | GPU draw interval, ms/frame | {draw[0]:.4f} | {draw[1]:.4f} |')
    lines += ["", "CPU JSON stage keys retain `_s`; this table converts them to milliseconds. Upload is allocation/upload API wall time, not isolated DMA time. Submit includes encoding and error polling; present includes backpressure. These overlap GPU execution and must not be added to solver/GPU timings. CPU uses one logical core as 1.0. GPU readings are whole-device 200 ms samples, including background/desktop memory; utilisation is activity, not achieved occupancy.", "",
              "## All representation comparisons", "",
              "Each candidate has its own adjacent indexed controls. Ranges and individual paired effects remain in `comparison.json`.", "",
              "| Candidate | Particles | Indexed → candidate sim s/wall s | Paired physics ratios | GPU draw, ms/frame |",
              "| --- | ---: | ---: | --- | ---: |"]
    for mode, records in result["comparison"].items():
        for record in records:
            count = record["particles"]
            a, b = (record["variants"][m]["simulated_s_per_wall_s"]["median"] for m in ("indexed", mode))
            ratios = ", ".join(f'{p["simulation_speedup"]:.3f}×' for p in record["pairs"])
            draw = next(r["mean_ms"] for r in result["gpu_profiles"] if r["count"] == count and r["renderer"] == mode)
            lines.append(f'| {mode} | {count:,} | {a:.4f} → {b:.4f} | {ratios} | {draw:.4f} |')
    lines += ["", "## Every-one-second capacity qualification", "",
              "Each repeat computes all 4,800 timesteps (20.000001 simulated seconds). Exact acceptance timestamps cover every continuous full one-second window, including those between displayed observations. The clock starts after construction and before the first step, includes all solver calls and inter-step observation/rendering contention, and excludes construction and teardown CSV writing.", "",
              "| Particles | Repeat | Average sim s/wall s | Worst one-second steps | Worst one-second sim s | Qualifies |",
              "| ---: | ---: | ---: | ---: | ---: | --- |"]
    for row in result["capacity"]:
        lines.append(f'| {row["count"]:,} | {row["repeat"]} | {row["simulated_s_per_wall_s"]:.4f} | {row["minimum_steps_in_one_second"]} | {row["minimum_simulated_s_in_one_second"]:.6f} | {"yes" if row["qualifies"] else "no"} |')
    lines += ["", "The original campaign's highest verified count is **38,400**, 9.09% above 35,200. This is a measured lattice bracket with 1,600-particle layers, not an exact universal maximum. At 40,000 the overall mean passes, but repeat two contains only 237 steps in its worst second (0.9875 simulated seconds), so that count fails. The 41,600/48,000 short pilots cannot qualify capacity. At 110,592, 0.4729× real time requires approximately 2.11× further complete-viewer throughput."]
    if "post_resume_capacity" in result:
        lines += ["", "**The slower resumed session qualified only 28,800.** Its separate large-scene comparison still improved physics by 58.6%, from 0.2423 to 0.3842× real time. See [post-resume evidence](/docs/project/development/milestones/05/assets/particle-rendering-v1/post-resume/README.md). Do not treat 38,400 as a current guaranteed capacity or pool the sessions."]
    (root / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
