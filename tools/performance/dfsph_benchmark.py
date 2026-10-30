"""Alternate complete production-PBF and rejected DFSPH trajectory timings.

These measurements compare workloads, not an equivalent-accuracy speedup: neither
model passes the combined physical criteria. Quality collection and CPU audits
must have finished before starting this phase.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import struct
if __package__:
    from .dfsph_campaign import invoke
else:
    from dfsph_campaign import invoke


def benchmark(root,previous):
    outputs=[]
    for scene,duration in [('resolved',2.),('large',5.)]:
        for repeat in range(6):
            for method in (['pbf','dfsph'] if repeat%2==0 else ['dfsph','pbf']):
                folder=root/'benchmark'/f'{scene}--r{repeat}--{method}';folder.parent.mkdir(exist_ok=True)
                if folder.exists():raise ValueError('benchmark output already exists')
                if method=='pbf':
                    binary=previous/'target/release/maelstrom';steps=round(duration*480)
                    command=[binary,'run',previous/'scenes'/(scene+'.toml'),'--backend','cuda','--refine-timestep','1','--steps',steps,'--measure','--format','json','--unpaced','--quiet','--set','fixed_timestep_s=0.0020833333333333333','--set','solver_iterations=8','--set','correction_scale=0.0625','--set','relaxation_scale=20']
                else:
                    binary=root/'dfsph-gpu';steps=round(duration*240);definitions=json.loads((root/'scenes.json').read_text())[scene]
                    command=[binary,root/'inputs'/(scene+'.bin'),1/240,steps,','.join(map(str,definitions['upper'])),'0,-9.81,0',.1,.1,folder/'state','benchmark',.025,'solid']
                process=invoke(command,folder,timeout=180)
                if process['exit_code']!=0:raise ValueError('benchmark execution failed '+folder.name)
                result=json.loads((folder/'stdout.json').read_text());sha=hashlib.sha256(binary.read_bytes()).hexdigest()
                if method=='pbf':
                    if int(result['completed_steps'])!=steps:raise ValueError('incomplete PBF trajectory')
                    model=result['input']['configuration']['numerical'];solver=sum(x['total_s'] for x in result['measurements']['steps']);observations=0;simulated=steps*model['fixed_timestep_s']
                    final=b''.join(struct.pack('<3f',*(p[field][axis] for axis in 'xyz')) for field in ['position_m','velocity_m_s'] for p in result['final_snapshot']['particles'])
                    (folder/'final.bin').write_bytes(final);fingerprint=hashlib.sha256(final).hexdigest();warnings=sum(t['warning'] for t in result['steps']);extra={'iterations':steps*8,'iterations_per_sim_s':steps*8/simulated}
                else:
                    solver=result['solver_s'];observations=result['observation_s'];simulated=result['simulated_s'];fingerprint=hashlib.sha256((folder/f'state-{steps}.bin').read_bytes()).hexdigest();warnings=None;extra={k:result[k] for k in ['density_iterations','divergence_iterations','fluid_row_entry_visits','cap_steps','boundary_particles']}
                    expected=root/'runs'/(scene+'--cubic-240-e01')
                    if fingerprint!=hashlib.sha256((expected/f'state-{steps}.bin').read_bytes()).hexdigest():raise ValueError('timed trajectory differs from qualification state')
                raw=(folder/'stdout.json').read_bytes();(folder/'stdout.json.gz').write_bytes(gzip.compress(raw,mtime=0))
                if gzip.decompress((folder/'stdout.json.gz').read_bytes())!=raw:raise ValueError('benchmark raw compression mismatch')
                (folder/'stdout.json').unlink()
                row={'scene':scene,'repeat':repeat,'warmup':repeat==0,'method':method,'simulated_s':simulated,'solver_s':solver,'observation_s':observations,'cost_s_per_sim_s':(solver+observations)/simulated,'binary_sha256':sha,'endpoint_sha256':fingerprint,'CFL_warning_steps':warnings,'process':process,**extra};outputs.append(row)
                (folder/'measurement.json').write_text(json.dumps(row,indent=2)+'\n');print(folder.name,row['cost_s_per_sim_s'],flush=True)
    (root/'benchmark-results.json').write_text(json.dumps(outputs,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('previous',type=Path);a=p.parse_args();benchmark(a.root.resolve(),a.previous.resolve())
