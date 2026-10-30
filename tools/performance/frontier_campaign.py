"""Measure full production steps and retain matched native quality trajectories.

Run on the primary PC from its durable experimental root. Audits and builds are
separate phases, never concurrent with admitted production timing. Native clocks
are retained for diagnostics but never used as production throughput samples.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import time

LAYOUT=struct.Struct('<4I12fd2IQ2f')


def f32(x):return struct.unpack('<f',struct.pack('<f',x))[0]


def state_bytes(particles):
    return b''.join(struct.pack('<3f',*(p[field][axis] for axis in 'xyz')) for field in ['position_m','velocity_m_s'] for p in particles)


def encode(document):
    value=document['input'];config=value['configuration'];model=config['numerical'];derived=config['derived'];n=len(value['particles'])
    h=f32(derived['support_radius_m']);r=f32(derived['artificial_pressure_reference_separation_m']);h2=f32(h*h);h4=f32(h2*h2);h8=f32(h4*h4);term=f32(h2-f32(r*r))
    coefficient=f32(315/f32(f32(64*f32(3.141592653589793))*f32(h*h8)));reference=f32(coefficient*f32(term*f32(term*term)))
    settings=LAYOUT.pack(n,1<<(n-1).bit_length(),len(value['planes']),0,model['fixed_timestep_s'],h,derived['normalised_rest_density_per_m3'],derived['relaxation_per_m2'],derived['artificial_pressure_strength_m2'] if model['artificial_pressure_enabled'] else 0,reference,model['artificial_pressure_exponent'],model['correction_scale'],derived['particle_mass_kg'],*(model['external_acceleration_m_s2'][k] for k in 'xyz'),.125,0,0,0,0,0)
    return settings+state_bytes(value['particles'])+b''.join(struct.pack('<4f',*(p['normal'][k] for k in 'xyz'),p['offset_m']) for p in value['planes'])


def invoke(command,out,err,timeout=300):
    start=time.monotonic()
    with out.open('xb') as stdout,err.open('xb') as stderr:
        try:
            p=subprocess.run(command,stdout=stdout,stderr=stderr,timeout=timeout,check=False);code=p.returncode;failure=None
        except subprocess.TimeoutExpired:
            code=None;failure='timeout'
    return {'command':list(map(str,command)),'exit_code':code,'failure':failure,'process_wall_s':time.monotonic()-start}


def run_case(root,scene,policy,label=None,duration=None,observe=True):
    definitions=json.loads((root/'scenes.json').read_text());d=definitions[scene];duration=d['duration'] if duration is None else duration
    steps=round(duration/policy['dt']);folder=root/'runs'/(label or f'{scene}--{policy["id"]}');folder.mkdir(parents=True,exist_ok=True)
    if (folder/'metrics.json').exists():return json.loads((folder/'metrics.json').read_text())
    binary=root/'target/release/maelstrom'
    command=[str(binary),'run',str(root/'scenes'/(scene+'.toml')),'--backend','cuda','--refine-timestep','1','--steps',str(steps),'--measure','--format','json','--unpaced','--quiet']
    for name,key in [('fixed_timestep_s','dt'),('solver_iterations','iterations'),('correction_scale','scale'),('relaxation_scale','epsilon')]:command+=['--set',f'{name}={policy[key]}']
    request={'scene':scene,'policy':policy,'duration':duration,'steps':steps,'production_binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest()}
    (folder/'request.json').write_text(json.dumps(request,indent=2)+'\n')
    if (folder/'production.process.json').exists():record=json.loads((folder/'production.process.json').read_text())
    else:
        record=invoke(command,folder/'production.json',folder/'production.stderr');(folder/'production.process.json').write_text(json.dumps(record,indent=2)+'\n')
    if not (folder/'production.json').stat().st_size:return {'completed':False,'label':folder.name,'process':record}
    document=json.loads((folder/'production.json').read_text());model=document['input']['configuration']['numerical'];derived=document['input']['configuration']['derived']
    # Serde intentionally omits the unit correction scale in legacy records.
    model.setdefault('correction_scale',1.0)
    for name,key in [('fixed_timestep_s','dt'),('solver_iterations','iterations'),('correction_scale','scale'),('relaxation_scale','epsilon')]:
        if f32(model[name])!=f32(policy[key]):raise ValueError('resolved independent control differs: '+name)
    raw_input=encode(document);(folder/'input.bin').write_bytes(raw_input)
    n=len(document['input']['particles']);(folder/'initial.bin').write_bytes(state_bytes(document['input']['particles']))
    final=state_bytes(document['final_snapshot']['particles']);(folder/'production-final.bin').write_bytes(final)
    production_s=sum(s['total_s'] for s in document['measurements']['steps']);actual_time=int(document['completed_steps'])*model['fixed_timestep_s']
    result={'label':folder.name,'scene':scene,'policy':policy,'particles':n,'completed':record['exit_code']==0 and document['status'] in ('completed','completed_with_warnings') and int(document['completed_steps'])==steps,
        'production_solver_s':production_s,'simulated_s':actual_time,'cost_s_per_sim_s':production_s/max(actual_time,1e-30),
        'CFL_warning_steps':sum(s['warning'] for s in document['steps']),'steps':int(document['completed_steps']),
        'resolved_numerical':model,'resolved_derived':derived,'input_sha256':hashlib.sha256(raw_input).hexdigest(),'final_sha256':hashlib.sha256(final).hexdigest(),'native_endpoint_equal':None}
    original=folder/'production.json';checksum=hashlib.sha256(original.read_bytes()).hexdigest()
    with original.open('rb') as inp,gzip.GzipFile(filename=str(original)+'.gz',mode='xb',mtime=0) as out:
        while block:=inp.read(1024*1024):out.write(block)
    with gzip.open(str(original)+'.gz','rb') as f:
        if hashlib.file_digest(f,'sha256').hexdigest()!=checksum:raise ValueError('JSON compression readback failed')
    result['production_json_sha256']=checksum;original.unlink()
    if result['completed'] and observe:
        cadence=max(1,round(.125/model['fixed_timestep_s']))
        native=[str(root/'frontier-driver'),str(folder/'input.bin'),str(steps),str(policy['iterations']),'checked',str(folder/'state'),'1','0',str(cadence)]
        response=invoke(native,folder/'native.json',folder/'native.stderr');(folder/'native.process.json').write_text(json.dumps(response,indent=2)+'\n')
        result['native_exit_code']=response['exit_code']
        if response['exit_code']==0:
            result['native_endpoint_equal']=hashlib.sha256((folder/f'state-{steps}.bin').read_bytes()).hexdigest()==result['final_sha256']
            if not result['native_endpoint_equal']:raise ValueError('quality replay differs from production endpoint: '+folder.name)
    (folder/'metrics.json').write_text(json.dumps(result,indent=2)+'\n');print(folder.name,result['completed'],result['cost_s_per_sim_s'],flush=True)
    return result


def run(root,group):
    rows=json.loads((root/'policies.json').read_text())
    if group=='pilot':return run_case(root,'resolved',rows[0],label='admission-resolved',duration=.25)
    if group=='screen':
        for policy in rows:
            for scene in ['resolved','hydro','collision','surface','shear']:run_case(root,scene,policy)
    elif group=='large':
        selection=json.loads((root/'large-selection.json').read_text())
        for policy in selection:run_case(root,'large',policy,duration=1.)
    else:raise ValueError('unknown group')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('group',choices=['pilot','screen','large']);a=p.parse_args();run(a.root.resolve(),a.group)
