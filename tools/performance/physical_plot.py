# /// script
# dependencies = ["matplotlib==3.11.2", "numpy==2.4.6"]
# ///
"""Plot independent numerical health and hydrostatic particle projections."""
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main(evidence: Path, states: Path) -> None:
    data = json.loads((evidence / "validate.json").read_text())
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), constrained_layout=True)
    for policy, label in (("baseline", "Production policy"), ("strong", "Scale 1"),
                          ("clamp-low-eps", "Compression only; εh²=2"),
                          ("clamp-coarse", "Compression only; coarser")):
        value = data["110592-"+policy]
        values = sorted((int(k.rsplit("-",1)[1])*value["parameters"]["dt"],h)
                        for k,h in value["health"].items())
        axes[0].plot([t for t,_ in values], [h["positive_density_error"]["p95"]*100 for _,h in values], label=label)
        axes[1].scatter(value["metrics"]["solver_s"]/5,
                        max(h["positive_density_error"]["p95"]*100 for _,h in values),label=label)
    axes[0].set(xlabel="Simulated time (s)",ylabel="p95 over-compression (%)",title="110,592 particles: fresh density audit")
    axes[1].set(xlabel="Checked replay seconds / simulated second",ylabel="Worst sampled p95 compression (%)",title="Exploratory cost; separate from production API")
    for ax in axes:
        ax.axhline(5,color="black",ls="--",lw=1)
        ax.grid(alpha=.2)
    axes[0].legend(fontsize=8)
    fig.savefig(evidence/"density-cost.png",dpi=170)
    plt.close(fig)
    fig, axes = plt.subplots(1,5,figsize=(15,4),constrained_layout=True)
    cases = [("signed",2400),("strong",2400),("clamp240",1200),("clamp480",2400),("clamp960",4800)]
    for ax,(label,step) in zip(axes,cases):
        points = np.fromfile(states/f"hydro-{label}-{step}.bin",dtype="<f4")[:3200*3].reshape((-1,3))
        ax.scatter(points[:,0],points[:,1],s=1,alpha=.3)
        ax.axhline(.3961278915,color="red",ls="--",lw=1)
        ax.set(xlim=(0,1),ylim=(0,.85),xlabel="x (m)",title=label,aspect="equal")
    axes[0].set_ylabel("y (m)")
    fig.suptitle("Tank at 5 s; all particles projected in x/y. Red: mass-derived depth")
    fig.savefig(evidence/"hydrostatic-projections.png",dpi=170)


if __name__ == "__main__":
    main(Path(sys.argv[1]),Path(sys.argv[2]))
