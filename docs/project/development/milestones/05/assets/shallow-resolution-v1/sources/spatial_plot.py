# /// script
# dependencies = ["numpy==2.5.4", "scipy==1.18.1", "matplotlib==3.11.2"]
# ///
"""Plot spatial errors and the remaining distinction between shape and quietness."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from tools.performance.spatial_audit import frames


def main(root):
    def load(label):return json.loads((root/"runs"/label/"physical-summary.json").read_text())
    data=[load(f"ladder-n{n}") for n in (6,12,18,24)]
    layers=[d["final"]["nominal_layers"] for d in data]
    fig,axes=plt.subplots(1,3,figsize=(12,3.6),constrained_layout=True)
    axes[0].plot(layers,[100*d["final"]["centroid_relative_error"] for d in data],"o-",label="Centroid, signed")
    axes[0].plot(layers,[100*d["final"]["height_relative_error"] for d in data],"s-",label="p95 height proxy, signed")
    axes[0].axhline((8270.744069418484*.05**3-1)*100,color="black",ls=":",label="Lattice calibration bias")
    axes[1].plot(layers,[100*d["settled_max_interparticle_error"] for d in data],"o-",label="Interparticle field error")
    axes[1].plot(layers,[100*d["max_p95_compression"] for d in data],"s-",label="Particle p95 compression")
    axes[1].axhline(10,color="black",ls="--")
    axes[2].plot(layers,[d["settled_max_kinetic_J_kg"] for d in data],"o-")
    axes[2].axhline(.00125,color="black",ls="--",label="Declared quietness limit")
    for ax in axes:
        ax.set_xlabel("Physical depth / nominal spacing")
        ax.grid(alpha=.2)
        ax.legend(fontsize=7)
    axes[0].set_ylabel("Geometric error (%)")
    axes[1].set_ylabel("Density error (%)")
    axes[2].set_ylabel("Maximum settled kinetic energy (J/kg)")
    fig.savefig(root/"spatial-errors.png",dpi=180);plt.close(fig)
    fig,axes=plt.subplots(4,1,figsize=(9,7),sharex=True,sharey=True,constrained_layout=True)
    for ax,n in zip(axes,(6,12,18,24)):
        for final_frame in frames(root/"runs"/f"ladder-n{n}"/"states.bin.gz"):
            pass
        meta,_,step,p,_=final_frame
        depth=meta["count"]*meta["mass"]/1000/(meta["upper"][0]*meta["upper"][2])
        ax.scatter(p[:,0],1000*p[:,1],s=2,alpha=.25,label="Particle centres, all z projected")
        ax.axhline(1000*depth,color="black",ls="--",label="Independent uniform depth")
        ax.axhline(1000*depth/2,color="black",ls=":",label="Independent centroid")
        ax.axhline(1000*p[:,1].mean(),color="orange",label="Particle centroid")
        ax.set(ylabel="y (mm)",ylim=(0,100),title=f"Spacing {1000*meta['dx']:.2f} mm; t={step*meta['dt']:.1f} s")
        ax.grid(alpha=.2)
    axes[0].legend(fontsize=6,ncol=2);axes[-1].set_xlabel("x (m); marker size does not represent particle extent")
    fig.savefig(root/"settled-projections.png",dpi=180);plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(12,3.8),constrained_layout=True)
    for prefix,marker,label in (("depth-L","o","Inset-consistent floor(L) strata"),("ceil-L","s","Inset-consistent ceil(L) strata")):
        records=[]
        for layers in (1,1.25,1.5,2,2.5,3,3.75,4):
            corrected=root/"runs"/f"valid-{prefix}{layers}"/"physical-summary.json"
            original=root/"runs"/f"{prefix}{layers}"/"physical-summary.json"
            path=corrected if corrected.exists() else original
            if not path.exists():continue
            initial=json.loads((path.parent/"initial-geometry.json").read_text())
            if not initial["initial_geometry_admissible"]:continue
            records.append(json.loads(path.read_text()))
        records.sort(key=lambda d:d["final"]["nominal_layers"])
        x=[d["final"]["nominal_layers"] for d in records]
        axes[0].plot(x,[abs(d["final"]["centroid_relative_error"])*100 for d in records],marker+"-",label=label)
        axes[1].plot(x,[abs(d["final"]["height_relative_error"])*100 for d in records],marker+"-",label=label)
        axes[2].plot(x,[d["settled_max_interparticle_error"]*100 for d in records],marker+"-",label=label)
    for ax,limit,title in zip(axes,(5,10,10),("Centroid","Height proxy","Interparticle density")):
        ax.axhline(limit,color="black",ls="--");ax.set(xlabel="Physical depth / nominal spacing",ylabel="Error (%)",title=title);ax.grid(alpha=.2)
    axes[0].legend(fontsize=7)
    fig.savefig(root/"depth-controls.png",dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(6,4),constrained_layout=True)
    for n in (6,12):
        names=[f"inset0-n{n}",f"inset0.25-n{n}",f"ladder-n{n}"]
        ax.plot([0,.25,.5],[load(name)["final"]["centroid_relative_error"]*100 for name in names],"o-",label=f"n={n}; wall density on")
        ax.scatter([.5],[load(f"no-wall-n{n}")["final"]["centroid_relative_error"]*100],marker="x",s=70,label=f"n={n}; wall density off")
    ax.axhline(5,color="black",ls=":");ax.axhline(-5,color="black",ls=":")
    ax.set(xlabel="Collision inset / spacing",ylabel="Signed centroid error (%)",title="Inset and wall support are separate controls")
    ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.savefig(root/"boundary-controls.png",dpi=180);plt.close(fig)
    if (root/"cost-summary.json").exists():
        costs=json.loads((root/"cost-summary.json").read_text())
        fig,ax=plt.subplots(figsize=(6,4),constrained_layout=True)
        x=[costs[str(n)]["median_solver_s"] for n in (6,12,18,24)]
        y=[abs(d["final"]["centroid_relative_error"])*100 for d in data]
        ax.plot(x,y,"o-")
        for a,b,n in zip(x,y,(432,3456,11664,27648)):ax.annotate(str(n),(a,b),xytext=(5,5),textcoords="offset points")
        ax.axhline(5,color="black",ls="--");ax.set_xscale("log")
        ax.set(xlabel="CPU solver seconds / first 0.5 simulated seconds",ylabel="Six-second centroid error (%)",title="Primary PC, eight workers; separate accuracy and cost runs")
        ax.grid(alpha=.2);fig.savefig(root/"accuracy-cost.png",dpi=180)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("root",type=Path)
    main(parser.parse_args().root)
