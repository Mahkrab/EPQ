"""Bounded longer trajectories and matched device-ownership measurements."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
if __package__:
    from .frontier_campaign import invoke, run_case
else:
    from frontier_campaign import invoke, run_case


def extend(root):
    policies=json.loads((root/'policies.json').read_text())
    selected=['production','anchor','iterations-2','dt-0.008333333333333333','dt-0.0020833333333333333']
    for p in policies:
        if p['id'] not in selected:continue
        for scene in ['resolved','hydro','collision','surface']:
            run_case(root,scene,p,label=f'long-{scene}--{p["id"]}',duration=5.)
    for p in policies:
        if p['id'] in ['production','dt-0.008333333333333333','iterations-2']:
            run_case(root,'large',p,label=f'long-large--{p["id"]}',duration=5.)


def resident(root,sustained=False):
    binary=root/'target/release/examples/frontier_resident';results=[]
    cases=['resolved--production','hydro--production','collision--production','surface--production','shear--production','large--production','large--dt-0.008333333333333333','large--iterations-2']
    if sustained:cases=['long-large--production']
    folder=root/('residency-sustained' if sustained else 'residency');folder.mkdir(exist_ok=True)
    for case in cases:
        source=root/'runs'/case;m=json.loads((source/'metrics.json').read_text())
        record=folder/(case+'.input.json')
        with gzip.open(source/'production.json.gz','rb') as f:record.write_bytes(f.read())
        response=invoke([str(binary),str(record),'1','check','0',str(folder/'unused.bin')],folder/(case+'.checks.json'),folder/(case+'.checks.stderr'))
        (folder/(case+'.checks.process.json')).write_text(json.dumps(response,indent=2)+'\n')
        if response['exit_code']!=0:raise ValueError('cancellation/retry checks failed '+case)
        if not sustained and case not in ['resolved--production','large--production','large--dt-0.008333333333333333','large--iterations-2']:continue
        for cadence in ([max(1,round(1/(60*m['policy']['dt'])))] if sustained else [0,max(1,round(1/(60*m['policy']['dt']))) ]):
            for repeat in range(6):
                for mode in (['normal','device'] if repeat%2==0 else ['device','normal']):
                    name=f'{case}--obs{cadence}--r{repeat}--{mode}';snapshot=folder/(name+'.bin')
                    command=[str(binary),str(record),str(m['steps']),mode,str(cadence),str(snapshot)]
                    response=invoke(command,folder/(name+'.json'),folder/(name+'.stderr'))
                    (folder/(name+'.process.json')).write_text(json.dumps(response,indent=2)+'\n')
                    if response['exit_code']!=0:raise ValueError('resident run failed '+name)
                    value=json.loads((folder/(name+'.json')).read_text());sha=hashlib.sha256(snapshot.read_bytes()).hexdigest()
                    if sha!=m['final_sha256']:raise ValueError('resident endpoint differs '+name)
                    value.update(case=case,repeat=repeat,warmup=repeat==0,endpoint_equal=True,simulated_s=m['simulated_s'],cost_s_per_sim_s=(value['solver_s']+value['observation_s'])/m['simulated_s'],binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest());results.append(value)
                    print(name,value['cost_s_per_sim_s'],flush=True)
    (root/('sustained-residency-results.json' if sustained else 'residency-results.json')).write_text(json.dumps(results,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('phase',choices=['extend','resident','sustained']);a=p.parse_args()
    if a.phase=='extend':extend(a.root.resolve())
    else:resident(a.root.resolve(),sustained=a.phase=='sustained')
