# /// script
# dependencies = ["numpy==2.5.4", "scipy==1.18.1"]
# ///
"""Check restart identity and unforced momentum using recorded particle arrays."""
import argparse
import gzip
import json
from pathlib import Path
import numpy as np
from tools.performance.spatial_audit import frames


def inspect(root):
    equivalence={};internal={};checkpoints={}
    for model in ['raw','self']:
        source=list(frames(root/'runs'/f'collision-{model}-n12'/'states.bin.gz'))
        reference=[r for r in source if r[2]*r[0]['dt']>=5-1e-9]
        restarted=list(frames(root/'runs'/f'tail-full-{model}-n12'/'states.bin.gz'))
        if len(reference)!=len(restarted):raise ValueError('restart observation count differs')
        difference=max(float(np.max(np.abs(a[k]-b[k]))) for a,b in zip(reference,restarted) for k in [3,4])
        equivalence[model]={'maximum_position_or_velocity_difference':difference,'exactly_identical':difference==0,'observations':len(reference)}
        if difference>1e-10:raise ValueError('restart trajectory differs')
        for denominator,passes in [(240,8),(480,8),(960,8),(480,16)]:
            suffix=f'{denominator}'+('-iter16' if passes==16 else '')
            directory=root/'runs'/f'internal-{model}-{suffix}'
            if not (directory/'collection.json').exists():continue
            observations=list(frames(directory/'states.bin.gz'));first,last=observations[0],observations[-1]
            initial=np.cross(first[3],first[4]).mean(axis=0);final=np.cross(last[3],last[4]).mean(axis=0)
            with gzip.open(directory/'ledger.jsonl.gz','rt') as f:rows=[json.loads(line) for line in f]
            pressure=np.sum([r['density']['angular_impulse_per_kg'] for r in rows],axis=0)
            plane=sum(r['plane']['active_particle_stages'] for r in rows)
            internal[f'{model}-{suffix}']={'initial_angular_per_kg':initial.tolist(),'final_angular_per_kg':final.tolist(),
                'angular_relative_drift':float(np.linalg.norm(final-initial)/np.linalg.norm(initial)),
                'mean_velocity_drift':float(np.linalg.norm(last[4].mean(axis=0)-first[4].mean(axis=0))),
                'pressure_angular_sum_vs_observed':float(np.max(np.abs(final-initial-pressure))),
                'plane_particle_stages':plane,'final_kinetic_J_kg':float(np.mean(np.sum(last[4]**2,axis=1))/2)}
            if plane or internal[f'{model}-{suffix}']['mean_velocity_drift']>1e-10:raise ValueError('unforced momentum reference violated')
    for label,origin in [('collision-raw-n12',0),('tail-extended-raw-n12',5)]:
        with gzip.open(root/'runs'/label/'ledger.jsonl.gz','rt') as f:
            for line in f:
                r=json.loads(line);physical=origin+r['time']
                if any(abs(physical-target)<1e-9 for target in [5,6,8,10,12]):checkpoints[str(round(physical))]={'K':r['accepted']['K'],'U':r['accepted']['U']}
    result={'restart_equivalence':equivalence,'internal_pressure_momentum':internal,'raw_extended_physical_checkpoints':checkpoints}
    (root/'diagnostic-summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path);inspect(parser.parse_args().root)
