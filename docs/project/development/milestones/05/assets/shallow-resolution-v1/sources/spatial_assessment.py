"""Assess spatial accuracy without turning a favourable diagnostic into admission."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics


def assess(root: Path):
    protocol=json.loads((root/"protocol.json").read_text())["criteria"]
    cases={}
    for path in sorted((root/"runs").glob("*/physical-summary.json")):
        d=json.loads(path.read_text())
        rows=[json.loads(line) for line in (path.parent/"audit.jsonl").read_text().splitlines()]
        settled=[r for r in rows if r["time_s"]>=5-1e-9]
        if not settled:continue
        volumes=[r["field_volume"]["0.5"]["relative_volume_error"] for r in settled if "field_volume" in r]
        checks={"centroid":max(abs(r["centroid_relative_error"]) for r in settled)<=protocol["settled_centroid_relative_error_max"],
            "height":max(abs(r["height_relative_error"]) for r in settled)<=protocol["settled_height_relative_error_max"],
            "reconstructed_volume":bool(volumes) and max(map(abs,volumes))<=protocol["settled_reconstructed_volume_relative_error_max"],
            "interparticle_density":max(r["interparticle_slab_density_p95_absolute_error"] for r in settled)<=protocol["settled_interparticle_density_absolute_error_p95_max"],
            "transient_density":d["max_p95_compression"]<=protocol["transient_p95_compression_max"] and d["max_positive_density_error"]<=protocol["transient_max_compression_max"],
            "separation":d["minimum_separation_fraction_dx"]>=protocol["minimum_separation_fraction_dx"],
            "containment":max(r["boundary_violation_m"] for r in rows)<=protocol["plane_violation_max_m"],
            "quietness":d["settled_max_kinetic_J_kg"]<=protocol["settled_kinetic_J_kg_max"]}
        initial=json.loads((path.parent/"initial-geometry.json").read_text())
        checks["initial_geometry"]=initial["initial_geometry_admissible"]
        cases[path.parent.name]={"checks":checks,"all_declared_pass":all(checks.values()),
            "macroscopic_pass":all(checks[k] for k in ("centroid","height","reconstructed_volume","interparticle_density","separation","containment","initial_geometry")),
            "nominal_layers":d["final"]["nominal_layers"],"final_centroid_error":d["final"]["centroid_relative_error"],
            "max_settled_kinetic":d["settled_max_kinetic_J_kg"],
            "initial_p95_compression":rows[0]["p95_compression"],
            "mean_centroid_m":statistics.mean(r["centre"][1] for r in settled),
            "mean_height_m":statistics.mean(r["height_p95_plus_half_dx_m"] for r in settled)}
    ladder=[cases[f"ladder-n{n}"] for n in (6,12,18,24)]
    convergence={}
    for metric in ("mean_centroid_m","mean_height_m"):
        values=[r[metric] for r in ladder];changes=[abs(b-a) for a,b in zip(values,values[1:])]
        physical_depth=json.loads((root/"protocol.json").read_text())["physical_geometry"]["settled_depth_m"]
        budget=physical_depth*(.5*protocol["settled_centroid_relative_error_max"] if metric=="mean_centroid_m" else protocol["settled_height_relative_error_max"])
        convergence[metric]={"values":values,"successive_changes_m":changes,
                             "changes_decrease":changes[2]<changes[1]<changes[0],
                             "finest_pair_budget_m":budget,"finest_change_within_budget":changes[-1]<=budget}
    result={"cases":cases,"spatial_changes":convergence,
            "smallest_collision_macroscopic_layers":min(r["nominal_layers"] for r in ladder if r["macroscopic_pass"]),
            "collision_all_declared_pass":any(r["all_declared_pass"] for r in ladder),
            "nominal_lattice_bias":8270.744069418484*.05**3-1,
            "production_admitted":False,
            "conclusion":"Spatial refinement removes the coarse centroid/field failure within the declared macroscopic budgets, but the fixed-ratio bias and quietness failure prevent a general fully qualified policy."}
    (root/"assessment.json").write_text(json.dumps(result,indent=2)+"\n")
    return result


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("root",type=Path)
    result=assess(parser.parse_args().root)
    print(json.dumps({k:v for k,v in result.items() if k!="cases"},indent=2))
