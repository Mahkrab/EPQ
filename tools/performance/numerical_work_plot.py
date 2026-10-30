# /// script
# dependencies = ["matplotlib==3.11.2"]
# ///
"""Export measured workload trade-offs and central slices of retained particles."""
import argparse
import json
from pathlib import Path
import struct

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def plot(root):
    result = json.loads((root/"assessment.json").read_text())
    rows = [r for r in result["matrix"] if r["scene"] == "large"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), layout="constrained")
    for hz, colour in ((120, "tab:blue"), (240, "tab:orange"), (480, "tab:green")):
        group = sorted((r for r in rows if r["hz"] == hz), key=lambda r: r["iterations"])
        axes[0].plot([r["iterations"] for r in group],
                     [r["ordinary_solver_s_per_sim_s"] for r in group], "o-", color=colour, label=f"{hz} Hz")
        axes[1].plot([r["ordinary_solver_s_per_sim_s"] for r in group],
                     [100*r["quality"]["p95_compression_peak"] for r in group], "o-", color=colour)
        for r in group:
            axes[1].annotate(str(r["iterations"]),
                             (r["ordinary_solver_s_per_sim_s"], 100*r["quality"]["p95_compression_peak"]),
                             xytext=(3, 4), textcoords="offset points", fontsize=8)
    axes[0].axhline(1, color="grey", ls=":")
    axes[0].set(xlabel="Jacobi iterations per step", ylabel="Wall s / simulated s",
                title="110,592 particles: independent scheduling axes", xticks=[2, 3, 4, 8])
    axes[0].legend()
    axes[1].axhline(5, color="black", ls="--", label="5% compression screen")
    axes[1].set(xlabel="Wall s / simulated s", ylabel="Peak sampled p95 compression (%)",
                title="Single-run screen; labels show iteration counts", yscale="log")
    axes[1].legend()
    fig.savefig(root/"workload-frontier.png", dpi=180)
    fig.savefig(root/"workload-frontier.svg")
    plt.close(fig)

    visual = root/"visual-inputs.json"
    if not visual.exists():
        return
    cases = json.loads(visual.read_text())
    fig, axes = plt.subplots(len(cases), 3, figsize=(11, 9), layout="constrained", sharex=True, sharey=True)
    for row, case in enumerate(cases):
        for col, frame in enumerate(case["frames"]):
            data = (root/frame["path"]).read_bytes()
            count = case["particles"]
            if len(data) != count*24:
                raise ValueError("visual snapshot size differs")
            points = list(struct.iter_unpack("<3f", data[:count*12]))
            selected = [p for p in points if abs(p[2]-1.375) <= .0375]
            axis = axes[row, col]
            axis.scatter([p[0] for p in selected], [p[1] for p in selected], s=2, c="tab:blue", linewidths=0)
            axis.set(xlim=(0, 2.8), ylim=(0, 3), aspect="equal", title=f'{case["name"]}, {frame["time_s"]:g} s')
            if col == 0:
                axis.set_ylabel("y (m)")
            if row == len(cases)-1:
                axis.set_xlabel("x (m)")
    fig.suptitle("Retained 110,592-particle trajectories: central 0.075 m slice\n"
                 "Same geometry and particle identities; these pictures do not establish physical acceptance.")
    fig.savefig(root/"particle-slices.png", dpi=180)
    fig.savefig(root/"particle-slices.svg")
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    plot(parser.parse_args().root.resolve())
