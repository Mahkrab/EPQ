"""Apply the declared physical gates without deriving a performance decision."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def observations(directory: Path) -> list[dict]:
    path=directory/"readback-audit.jsonl"
    if not path.exists():
        path=directory/"audit.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def assess(root: Path) -> dict:
    protocol=json.loads((root/"protocol.json").read_text())["criteria"]
    cases={}
    for path in sorted((root/"runs").glob("*/summary.json")):
        summary=json.loads(path.read_text())
        records=observations(path.parent)
        if summary["exit_code"]!=0 or not records:
            cases[path.parent.name]={"completed":False,"numerically_admitted":False}
            continue
        transient=protocol["all_checkpoints"]
        checks={
            "compression_p95":max(r["p95_compression"] for r in records)<=transient["p95_positive_density_error_max"],
            "compression_tail":max(r["max_compression"] for r in records)<=transient["max_positive_density_error_max"],
            "separation":min(r["minimum_separation_m"] for r in records)>=transient["minimum_separation_m"],
            "containment":max(r["boundary_violation_m"] for r in records)<=transient["boundary_violation_m_max"],
            "energy":max(r["mechanical_J_kg"]-records[0]["mechanical_J_kg"] for r in records)<=transient["mechanical_energy_increase_J_kg_max"],
        }
        settled=[r for r in records if 5<=r["time_s"]<=6]
        final=records[-1]
        metrics={"worst_p95_compression":max(r["p95_compression"] for r in records),
                 "final_centroid_error":final["centroid_relative_error"],
                 "final_surface_error":final["surface_relative_error"],
                 "minimum_separation_m":min(r["minimum_separation_m"] for r in records),
                 "expected_depth_m":final["expected_depth_m"]}
        if settled:
            hydro=protocol["hydrostatic"]
            checks.update(centroid=max(r["centroid_relative_error"] for r in settled)<=hydro["centroid_relative_error_max"],
                          surface=max(r["surface_relative_error"] for r in settled)<=hydro["p95_height_plus_half_spacing_relative_error_max"],
                          settled_motion=max(r["kinetic_J_kg"] for r in settled)<=hydro["settled_kinetic_J_kg_max"])
            bulk=[r["bulk_p95_absolute_error"] for r in settled if r["bulk_count"]]
            if bulk:
                checks["bulk_density"]=max(bulk)<=hydro["bulk_absolute_density_error_p95_max"]
            metrics.update(mean_settled_centroid_m=sum(r["centre"][1] for r in settled)/len(settled),
                           mean_settled_surface_m=sum(r["surface_height_m"] for r in settled)/len(settled),
                           max_settled_kinetic_J_kg=max(r["kinetic_J_kg"] for r in settled),
                           bulk_observations=len(bulk))
        cases[path.parent.name]={"completed":True,"checks":checks,"metrics":metrics,
                                "numerically_admitted":bool(settled) and all(checks.values())}
    convergence={}
    groups={"timestep":[f"qual-c2-hydro-dt{k}" for k in (120,240,480)],
            "iterations":["primary-c2-hydro-iter8","primary-c2-hydro-iter32","primary-c2-hydro-iter128-retry2"]}
    bounds=protocol["convergence"]
    for label,names in groups.items():
        if not all(n in cases and cases[n]["completed"] and "mean_settled_centroid_m" in cases[n]["metrics"] for n in names):
            convergence[label]={"complete":False}
            continue
        results={}
        for metric,bound in (("mean_settled_centroid_m",bounds["centroid_change_m_max"]),
                             ("mean_settled_surface_m",bounds["surface_height_change_m_max"])):
            values=[cases[n]["metrics"][metric] for n in names]
            changes=[abs(values[k+1]-values[k]) for k in range(2)]
            results[metric]={"values":values,"changes_m":changes,"within_bound":max(changes)<=bound,
                             "decreasing":changes[1]<changes[0]}
        convergence[label]={"complete":True,"results":results,
                            "passed":all(r["within_bound"] and r["decreasing"] for r in results.values())}
    originally_required=["qual-c2-hydro-dt240","qual-c2-fall","qual-c2-collision"]
    combined=all(cases.get(n,{}).get("numerically_admitted",False) for n in originally_required)
    combined=combined and all(c.get("passed",False) for c in convergence.values())
    result={"cases":cases,"convergence":convergence,"combined_original_scene_gate":combined,
            "cost_campaign_authorised_by_physical_gate":combined,
            "production_change_admitted":False,
            "note":"Bulk tests without interior samples are unavailable, not evidence of bulk accuracy. Snapshot gates are not continuous-time bounds."}
    (root/"assessment.json").write_text(json.dumps(result,indent=2)+"\n")
    return result


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root",type=Path)
    result=assess(parser.parse_args().root)
    print(json.dumps({k:v for k,v in result.items() if k!="cases"},indent=2))
