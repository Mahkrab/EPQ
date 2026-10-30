"""Check that recorded initial points satisfy the configured particle geometry."""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

from tools.performance.spatial_audit import frames


def check(directory):
    stream=frames(directory/"states.bin.gz")
    meta,_,step,p,_=next(stream);stream.close()
    if step!=0:raise ValueError("initial observation missing")
    upper=np.asarray(meta["upper"]);inset=meta["inset"]
    violation=float(max(0.,np.max(inset-p),np.max(p-(upper-inset))))
    nearest=float(cKDTree(p).query(p,k=2,workers=1)[0][:,1].min())
    result={"initial_collision_extent_violation_m":violation,
            "initial_minimum_separation_m":nearest,"distance_target_m":meta["contact"],
            "extent_pass":violation<=1e-12,"contact_pass":nearest>=meta["contact"]-1e-12,
            "centre":p.mean(axis=0).tolist(),"total_mass_kg":len(p)*meta["mass"]}
    result["initial_geometry_admissible"]=result["extent_pass"] and result["contact_pass"]
    (directory/"initial-geometry.json").write_text(json.dumps(result,indent=2)+"\n")
    return result


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("root",type=Path)
    args=parser.parse_args()
    rejected=[]
    for p in sorted((args.root/"runs").glob("*/collection.json")):
        if not check(p.parent)["initial_geometry_admissible"]:rejected.append(p.parent.name)
    (args.root/"initial-geometry-rejections.json").write_text(json.dumps({"rejected":rejected},indent=2)+"\n")
    print(rejected)
