"""Audit retained trajectories independently after GPU timing has finished.

The volume observable is a particle-support union, not an interface reconstruction.
Its resolution sensitivity is retained explicitly; it cannot certify a free surface
by itself. Historical formulation failures remain outside this practical screen.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
if __package__:
    from .frontier_campaign import invoke
else:
    from frontier_campaign import invoke


def repair(root):
    """Recover warning-completed trajectories without repeating production clocks."""
    for folder in sorted((root/'runs').iterdir()):
        if not (folder/'metrics.json').exists():continue
        m=json.loads((folder/'metrics.json').read_text())
        if m['native_endpoint_equal'] is True:continue
        with gzip.open(folder/'production.json.gz') as f:d=json.load(f)
        record=json.loads((folder/'production.process.json').read_text())
        m['completed']=record['exit_code']==0 and d['status'] in ('completed','completed_with_warnings') and int(d['completed_steps'])==json.loads((folder/'request.json').read_text())['steps']
        if m['completed']:
            command=[str(root/'frontier-driver'),str(folder/'input.bin'),str(m['steps']),str(m['policy']['iterations']),'checked',str(folder/'state'),'1','0',str(max(1,round(.125/m['resolved_numerical']['fixed_timestep_s'])))]
            response=invoke(command,folder/'native.json',folder/'native.stderr')
            (folder/'native.process.json').write_text(json.dumps(response,indent=2)+'\n')
            m['native_exit_code']=response['exit_code']
            m['native_endpoint_equal']=response['exit_code']==0 and hashlib.sha256((folder/f'state-{m["steps"]}.bin').read_bytes()).hexdigest()==m['final_sha256']
            if not m['native_endpoint_equal']:raise ValueError('endpoint mismatch '+folder.name)
        (folder/'metrics.json').write_text(json.dumps(m,indent=2)+'\n')


def audit(root):
    scenes=json.loads((root/'scenes.json').read_text());invariants={};summaries=[]
    for folder in sorted((root/'runs').iterdir()):
        if not (folder/'metrics.json').exists():continue
        m=json.loads((folder/'metrics.json').read_text());scene=scenes[m['scene']];model=m['resolved_numerical'];d=m['resolved_derived']
        fixed_model={k:v for k,v in model.items() if k not in ['fixed_timestep_s','solver_iterations','correction_scale','relaxation_scale']}
        fixed_derived={k:v for k,v in d.items() if k!='relaxation_per_m2'}
        data=(folder/'input.bin').read_bytes();key={'numerical':fixed_model,'derived':fixed_derived,'initial_and_planes_sha256':hashlib.sha256(data[96:]).hexdigest()}
        previous=invariants.setdefault(m['scene'],key)
        if key!=previous:raise ValueError('unrelated physical inputs changed '+folder.name)
        if not m['native_endpoint_equal']:continue
        records=[]
        states=[p for p in folder.glob('state-*.bin') if p.stem.split('-')[-1].isdigit()]
        for path in [folder/'initial.bin']+sorted(states,key=lambda p:int(p.stem.split('-')[-1])):
            out=folder/(path.stem+'.audit.json')
            if not out.exists():
                command=[str(root/'frontier-quality'),str(path),str(m['particles']),str(d['support_radius_m']),str(d['normalised_rest_density_per_m3']),str(d['particle_mass_kg']),str(model['external_acceleration_m_s2']['y']),str(model['particle_spacing_m']),','.join(map(str,scene['upper'])),str(folder/'initial.bin'),str(model['particle_spacing_m']/2)]
                value=subprocess.run(command,capture_output=True,text=True,check=True)
                out.write_text(value.stdout)
            a=json.loads(out.read_text());a['step']=0 if path.stem=='initial' else int(path.stem.split('-')[-1]);a['time_s']=a['step']*model['fixed_timestep_s'];records.append(a)
        initial=records[0];last=records[-1];dx=model['particle_spacing_m'];physical=last['physical_volume']
        row={'label':folder.name,'scene':m['scene'],'policy':m['policy'],'cost_s_per_sim_s':m['cost_s_per_sim_s'],'CFL_warning_steps':m['CFL_warning_steps'],'observations':len(records),
             'p95_compression_peak':max(a['p95_compression'] for a in records),'max_compression_peak':max(a['max_compression'] for a in records),
             'min_separation_over_dx':min(a['min_separation']/dx for a in records),'energy_excess_peak':max(a['mechanical_excess_relative'] for a in records),
             'volume_error_peak':max(abs(a['occupied_support_volume']/physical-1) for a in records),
             'final':last,'initial':initial,'completed':m['completed'],'stability':all(a['coincidences']==0 and a['boundary_violation']<=1e-6 for a in records)}
        gates={'density':row['p95_compression_peak']<=.05 and row['max_compression_peak']<=.25,
               'stability':row['stability'] and row['min_separation_over_dx']>=.5,'energy':row['energy_excess_peak']<=.1,'volume_proxy':row['volume_error_peak']<=.1}
        if m['scene']=='hydro':
            height=physical/(scene['upper'][0]*scene['upper'][2]);row['hydro_reference_height']=height;row['hydro_centroid_error']=abs(last['com'][1]/(height/2)-1);gates['hydro']=row['hydro_centroid_error']<=.1
        if m['scene']=='shear':gates['shear']=abs(last['shear_projection']-1)<=.2
        row['sampled_gates']=gates;row['sampled_practical_pass']=all(gates.values());summaries.append(row)
        (folder/'quality.json').write_text(json.dumps({'summary':row,'observations':records},indent=2)+'\n')
        print(folder.name,'rho',round(100*row['p95_compression_peak'],2),'volume',round(100*row['volume_error_peak'],2),'E',round(row['energy_excess_peak'],3),gates,flush=True)
    (root/'physical-invariants.json').write_text(json.dumps(invariants,indent=2)+'\n')
    (root/'frontier.json').write_text(json.dumps(summaries,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('phase',choices=['repair','audit']);a=p.parse_args();(repair if a.phase=='repair' else audit)(a.root.resolve())
