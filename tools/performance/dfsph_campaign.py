"""Bounded DFSPH runs, retaining physical states and complete workload traces.

Inputs are copied from the previous fixed-geometry PBF frontier. New compression
and boundary controls are explicit. Builds, physical audits and timed runs remain
separate phases on the primary PC.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import time


def invoke(command,folder,env=None,timeout=600):
    folder.mkdir(parents=True,exist_ok=False);start=time.monotonic()
    with (folder/'stdout.json').open('xb') as out,(folder/'stderr.txt').open('xb') as err:
        try:p=subprocess.run(list(map(str,command)),stdout=out,stderr=err,env=env,timeout=timeout,check=False);code=p.returncode;failure=None
        except subprocess.TimeoutExpired:code=None;failure='timeout'
    value={'command':list(map(str,command)),'exit_code':code,'failure':failure,'process_wall_s':time.monotonic()-start}
    (folder/'process.json').write_text(json.dumps(value,indent=2)+'\n');return value


def prepare(root,previous):
    inputs=root/'inputs';inputs.mkdir(exist_ok=False)
    names=['resolved','hydro','collision','surface','shear','large'];scenes=json.loads((previous/'scenes.json').read_text())
    for name in names:shutil.copyfile(previous/'runs'/(name+'--production')/'input.bin',inputs/(name+'.bin'))
    data=bytearray((inputs/'resolved.bin').read_bytes());n=struct.unpack_from('<I',data)[0]
    for i in range(n):
        p=struct.unpack_from('<3f',data,96+12*i);v=tuple(-1*(p[k]-(.675 if k!=1 else .875)) for k in range(3));struct.pack_into('<3f',data,96+12*n+12*i,*v)
    # Header acceleration is irrelevant to DFSPH's explicit gravity arguments,
    # but clearing it also makes the recorded compression input self-describing.
    struct.pack_into('<3f',data,52,0,0,0);(inputs/'compression.bin').write_bytes(data)
    scenes['compression']={**scenes['resolved'],'gravity':False,'duration':2.}
    (root/'scenes.json').write_text(json.dumps(scenes,indent=2)+'\n')
    policies=[{'id':f'cubic-{rate}-e01','dt':1/rate,'density_percent':.1,'divergence_percent':.1,'kernel':'cubic','support':.1} for rate in [120,240,480]]
    policies+=[{'id':'cubic-240-e001','dt':1/240,'density_percent':.01,'divergence_percent':.1,'kernel':'cubic','support':.1},{'id':'cubic-120-e05','dt':1/120,'density_percent':.5,'divergence_percent':.1,'kernel':'cubic','support':.1}]
    (root/'policies.json').write_text(json.dumps(policies,indent=2)+'\n')
    (root/'input-identities.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs.iterdir()},indent=2)+'\n')


def run_case(root,scene,policy,duration=None,label=None):
    folder=root/'runs'/(label or f'{scene}--{policy["id"]}')
    if (folder/'metrics.json').exists():return json.loads((folder/'metrics.json').read_text())
    d=json.loads((root/'scenes.json').read_text())[scene];duration=(.2 if scene=='shear' else 2.) if duration is None else duration;steps=round(duration/policy['dt'])
    folder.parent.mkdir(exist_ok=True);prefix=folder/'state';binary=root/'dfsph-gpu'
    args=[binary,root/'inputs'/(scene+'.bin'),policy['dt'],steps,','.join(map(str,d['upper'])),'0,-9.81,0' if d['gravity'] else '0,0,0',policy['density_percent'],policy['divergence_percent'],prefix,1/60,.025 if scene not in ['shear','compression'] else 0,'solid' if scene not in ['shear','compression'] else 'none']
    if policy.get('kernel')=='wendland':args+=['wendland',policy['support']]
    if 'jacobi_weight' in policy:args+=[policy['jacobi_weight']]
    process=invoke(args,folder);result={'scene':scene,'policy':policy,'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'process':process,'completed':process['exit_code']==0}
    if result['completed']:
        result['measurement']=json.loads((folder/'stdout.json').read_text());m=result['measurement'];result['cost_s_per_sim_s']=(m['solver_s']+m['observation_s'])/m['simulated_s']
    (folder/'metrics.json').write_text(json.dumps(result,indent=2)+'\n');print(folder.name,result['completed'],result.get('cost_s_per_sim_s'),flush=True);return result


def campaign(root,phase):
    policies=json.loads((root/'policies.json').read_text())
    if phase=='screen':
        for policy in policies:
            for scene in ['hydro','compression','resolved','collision','surface','shear']:run_case(root,scene,policy)
    elif phase=='large':
        for policy in json.loads((root/'selection.json').read_text()):run_case(root,'large',policy,duration=5.)
    elif phase=='extend':
        for policy in json.loads((root/'selection.json').read_text()):
            for scene in ['hydro','resolved','collision','surface']:run_case(root,scene,policy,duration=5.,label=f'long-{scene}--{policy["id"]}')
    else:raise ValueError('unknown campaign phase')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('phase',choices=['prepare','screen','large','extend']);p.add_argument('--previous',type=Path);a=p.parse_args()
    if a.phase=='prepare':
        if a.previous is None:p.error('--previous required')
        prepare(a.root.resolve(),a.previous.resolve())
    else:campaign(a.root.resolve(),a.phase)
