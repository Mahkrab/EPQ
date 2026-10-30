# /// script
# dependencies = ["matplotlib==3.11.2", "numpy==2.4.6"]
# ///
"""Plot retained physical references, not solver timing or backend agreement."""
import gzip
import json
from pathlib import Path
import struct
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def final_points(path):
    with gzip.open(path,"rb") as file:
        magic,n,w,_=struct.unpack("<4I",file.read(16))
        constants=struct.unpack("<7d",file.read(56))
        if magic==0x50424633:
            file.read(8)
        file.read(w*24)
        points=None
        while file.read(4):
            points=np.frombuffer(file.read(n*24),dtype="<f8").reshape((n,3)).copy()
            file.read(n*24)
    return points,constants


def main(root):
    runs=root/"runs"
    def summary(label):
        return json.loads((runs/label/"summary.json").read_text())
    fig,axes=plt.subplots(1,3,figsize=(12,3.8),constrained_layout=True)
    for name in ("qual-c2-hydro-dt120","qual-c2-hydro-dt240","qual-c2-hydro-dt480"):
        data=[json.loads(line) for line in (runs/name/"audit.jsonl").read_text().splitlines()]
        t=[r["time_s"] for r in data]
        axes[0].plot(t,[100*r["p95_compression"] for r in data],label=name.rsplit("-",1)[1])
        axes[1].plot(t,[r["centre"][1] for r in data])
        axes[2].plot(t,[r["kinetic_J_kg"] for r in data])
    axes[0].axhline(5,color="black",ls="--",lw=1)
    axes[1].axhline(data[0]["expected_depth_m"]/2,color="black",ls="--",lw=1)
    axes[2].axhline(.00125,color="black",ls="--",lw=1)
    axes[0].legend(fontsize=8)
    for ax,title,label in zip(axes,("Fresh p95 compression","Tank centroid","Residual motion"),("Compression (%)","Centroid y (m)","Kinetic energy (J/kg)")):
        ax.set(xlabel="Simulated time (s)",ylabel=label,title=title)
        ax.grid(alpha=.2)
    fig.savefig(root/"tank-convergence.png",dpi=180)
    plt.close(fig)
    fig,axes=plt.subplots(1,4,figsize=(13,3.8),constrained_layout=True)
    names=[("gradient-poly-low-eps-scale.5","Poly6; no distance constraint"),
           ("contact-iter128","Poly6; 128 passes + distance"),
           ("qual-c2-hydro-dt240","C2; eight passes"),
           ("extent-collision","Thin collision pool; finite extent")]
    for ax,(name,title) in zip(axes,names):
        points,c=final_points(runs/name/"states.bin.gz")
        H=len(points)*c[3]/(1000*c[4]*c[6])
        ax.scatter(points[:,0],points[:,1],s=3,alpha=.45)
        ax.axhline(H,color="red",ls="--",lw=1)
        ax.set(xlim=(0,c[4]),ylim=(0,max(.1,H*1.35)),xlabel="x (m)",title=title,aspect="equal")
    axes[0].set_ylabel("y (m)")
    fig.suptitle("Raw particle projections; red line: mass-derived flat-pool depth")
    fig.savefig(root/"particle-distribution.png",dpi=180)
    plt.close(fig)
    names=["resolution-hydro-thin1","resolution-hydro-thin2-retry","resolution-hydro-thin4","qual-c2-hydro-dt240"]
    data=[summary(name)["final"] for name in names]
    fig,ax=plt.subplots(figsize=(6,4),constrained_layout=True)
    ax.plot([d["expected_depth_m"]/.1 for d in data],[100*d["centroid_relative_error"] for d in data],"o-",label="Point-centre collision plane")
    d=summary("extent-hydro-thin1")["final"]
    ax.scatter([d["expected_depth_m"]/.1],[100*d["centroid_relative_error"]],marker="s",s=60,label="Half-spacing collision inset")
    ax.axhline(5,color="black",ls="--",lw=1)
    ax.set(xlabel="Mass-derived depth / kernel support radius",ylabel="Final centroid error (%)",title="Independent depth ladder at fixed numerical settings")
    ax.legend(fontsize=8)
    ax.grid(alpha=.2)
    fig.savefig(root/"depth-resolution.png",dpi=180)


if __name__=="__main__":
    main(Path(sys.argv[1]))
