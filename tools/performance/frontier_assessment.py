"""Describe timestep/iteration changes and empirical cost/density frontiers.

These derived comparisons preserve the raw practical decisions. Nondominance is
only a description of the sampled policies, never an acceptance or retention rule.
"""
import argparse
import json
from pathlib import Path


def assess(root):
    rows=json.loads((root/'frontier.json').read_text())
    screen=[r for r in rows if not r['label'].startswith(('long-','admission'))]
    by={(r['scene'],r['policy']['id']):r for r in screen}
    ids=['dt-0.008333333333333333','anchor','dt-0.0020833333333333333','dt-0.0010416666666666667']
    convergence=[]
    for scene in ['resolved','hydro','collision','surface','shear']:
        for coarse,fine in zip(ids,ids[1:]):
            a,b=by[scene,coarse],by[scene,fine];x,y=a['final'],b['final']
            relative=lambda key:abs(x[key]-y[key])/max(abs(y[key]),1e-30)
            convergence.append({'scene':scene,'coarse':coarse,'fine':fine,
                'centroid_y_relative_change':abs(x['com'][1]-y['com'][1])/max(abs(y['com'][1]),1e-30),
                'occupied_volume_relative_change':relative('occupied_support_volume'),
                'height_relative_change':relative('height_max'),
                'kinetic_energy_relative_change':relative('kinetic_J_kg'),
                'shear_projection_change_over_initial_mode':abs(x['shear_projection']-y['shear_projection']) if scene=='shear' else None,
                'note':'Bulk lengths/volume use the finer value; shear uses initial unit amplitude. Near-zero kinetic-energy denominators require inspecting absolute raw energies.'})
    frontiers={}
    for scene in ['resolved','hydro','collision','surface','shear','large']:
        subset=[r for r in screen if r['scene']==scene]
        frontiers[scene]=[r['label'] for r in subset if not any(q['cost_s_per_sim_s']<=r['cost_s_per_sim_s'] and q['p95_compression_peak']<=r['p95_compression_peak'] and (q['cost_s_per_sim_s']<r['cost_s_per_sim_s'] or q['p95_compression_peak']<r['p95_compression_peak']) for q in subset)]
    iterations=[{k:by[scene,policy][k] for k in ['scene','policy','cost_s_per_sim_s','p95_compression_peak','energy_excess_peak','final']} for scene in ['resolved','hydro','shear'] for policy in ['iterations-2','iterations-4','anchor','iterations-16']]
    result={'timestep':convergence,'iteration_controls':iterations,'sampled_cost_density_nondominated':frontiers,'warning':'No cost/density Pareto point is thereby physically qualified.'}
    (root/'convergence.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);assess(p.parse_args().root)
