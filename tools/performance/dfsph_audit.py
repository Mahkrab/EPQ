"""Independently audit DFSPH states; residuals are never physical acceptance.

Current-position cubic or Wendland quadrature includes the recorded solid sample
volumes. The support-cube volume stays a labelled geometric proxy. Every sampled
small-scene state is inspected; rejected large runs use a declared subset.
"""
import argparse
import json
import math
from pathlib import Path
import struct
import subprocess


def load_trace(path):
    records=[];errors=[]
    def nonfinite(value):raise ValueError('nonfinite JSON number: '+value)
    for number,line in enumerate(path.read_text().splitlines(),1):
        if not line:continue
        try:records.append(json.loads(line,parse_constant=nonfinite))
        except (json.JSONDecodeError,ValueError) as error:errors.append({'line':number,'error':str(error)})
    return records,errors


def audit(root,correct_compression=False):
    scenes=json.loads((root/'scenes.json').read_text());results=[]
    for folder in sorted((root/'runs').iterdir()):
        if not (folder/'metrics.json').exists():continue
        metadata=json.loads((folder/'metrics.json').read_text());scene=metadata['scene'];policy=metadata['policy'];definition=scenes[scene]
        if correct_compression and scene!='compression':
            results.append(json.loads((folder/'quality.json').read_text())['summary']);continue
        n=struct.unpack_from('<I',(root/'inputs'/(scene+'.bin')).read_bytes())[0]
        states=sorted([p for p in folder.glob('state-*.bin') if p.stem.split('-')[-1].isdigit()],key=lambda p:int(p.stem.split('-')[-1]))
        records=[];unsupported=[];reader=root/('quality-wendland' if policy.get('kernel')=='wendland' else 'quality-cubic')
        if correct_compression:reader=reader.with_name(reader.name+'-unbounded')
        last=int(states[-1].stem.split('-')[-1]) if states else 0
        for path in states:
            step=int(path.stem.split('-')[-1])
            if scene=='large' and step>10 and step!=last and step%max(1,round(.125/policy['dt'])):continue
            if correct_compression:
                raw=path.read_bytes();position_max=max(abs(v) for p in struct.iter_unpack('<3f',raw[:n*12]) for v in p)
                if position_max>math.ldexp(.025,40):
                    # Exploded controls still have independently measurable
                    # energy, but cannot support cell/volume quadrature at this
                    # coordinate precision. Never turn missing geometry into a pass.
                    kinetic=sum(float(v)*v for p in struct.iter_unpack('<3f',raw[n*12:]) for v in p)/(2*n)
                    unsupported.append({'step':step,'position_abs_max':position_max,'kinetic_J_kg':kinetic,'reason':'outside representable unbounded-volume domain'});continue
            out=path.with_suffix('.unbounded.audit.json' if correct_compression else '.audit.json')
            if not out.exists():
                command=[str(reader),str(path),str(n),str(policy.get('support',.1)),'8000','.125','-9.81' if definition['gravity'] else '0','.05',','.join(map(str,definition['upper'])),str(folder/'state-0.bin'),'.025',str(folder/'state-boundary.bin')]
                process=subprocess.run(command,capture_output=True,text=True,check=True);out.write_text(process.stdout)
            value=json.loads(out.read_text());value['step']=step;value['time_s']=step*policy['dt'];records.append(value)
        traces,trace_errors=load_trace(folder/'state.jsonl')
        if trace_errors:(folder/'trace-errors.json').write_text(json.dumps(trace_errors,indent=2)+'\n')
        if not records:continue
        first,last=records[0],records[-1];volume=last['physical_volume'];wall_contacts=sum(t['wall_contacts'] for t in traces)
        r={'label':folder.name,'scene':scene,'policy':policy,'particles':n,'completed':metadata['completed'],'cost_s_per_sim_s':metadata.get('cost_s_per_sim_s'),
           'p95_compression_peak':max(a['p95_compression'] for a in records),'maximum_compression_peak':max(a['max_compression'] for a in records),
           'min_separation_over_dx':min(a['min_separation']/.05 for a in records),'volume_proxy_error_peak':max(abs(a['occupied_support_volume']/volume-1) for a in records),
           'energy_excess_peak':max(a['mechanical_excess_relative'] for a in records),'wall_contacts':wall_contacts,'wall_energy_loss_J_kg':sum(t['wall_energy_loss_J_kg'] for t in traces),
           'density_iterations':sum(t['density_iterations'] for t in traces),'divergence_iterations':sum(t['divergence_iterations'] for t in traces),
           'cap_steps':sum(t['density_iterations']==100 or t['divergence_iterations']==100 for t in traces),'initial':first,'final':last,'observations':len(records),'transient_density_scope':'all retained60Hz states for small scenes; first10 steps, .125s aligned states and final for rejected large candidates'}
        r['unsupported_spatial_states']=unsupported
        if unsupported:
            r['volume_proxy_error_peak']=None
            r['energy_excess_peak']=max(r['energy_excess_peak'],max((v['kinetic_J_kg']-first['kinetic_J_kg'])/max(first['kinetic_J_kg'],1e-30) for v in unsupported))
        t=sum(t['dt'] for t in traces);r['iterations_per_sim_s']=(r['density_iterations']+r['divergence_iterations'])/max(t,1e-30);r['density_iterations_per_sim_s']=r['density_iterations']/max(t,1e-30);r['divergence_iterations_per_sim_s']=r['divergence_iterations']/max(t,1e-30)
        r['row_sweeps_per_sim_s']=sum(x['row_sweeps'] for x in traces)/max(t,1e-30);r['max_cfl_dx']=max((x['dt']*x['max_speed']/.05 for x in traces),default=0)
        r['trace_errors']=trace_errors
        r['unconverged_steps']=sum(t['density_residual_mean']>policy['density_percent']*.01 or t['divergence_residual_mean']>policy['divergence_percent']*.01/t['dt'] for t in traces)
        contains=lambda a:True if correct_compression else a['boundary_violation']<1e-6
        gates={'completed':r['completed'] and not trace_errors,'density':r['p95_compression_peak']<=.05 and r['maximum_compression_peak']<=.25,
               'stability':not unsupported and all(a['coincidences']==0 and contains(a) for a in records) and r['min_separation_over_dx']>=.5,
               'energy':r['energy_excess_peak']<=.1,'volume_proxy':r['volume_proxy_error_peak'] is not None and r['volume_proxy_error_peak']<=.1}
        if scene=='hydro':
            refheight=volume/(definition['upper'][0]*definition['upper'][2]);r['hydro_reference_height']=refheight;r['hydro_centroid_error']=abs(last['com'][1]/(.5*refheight)-1);gates['hydro']=r['hydro_centroid_error']<=.1
        if scene=='shear':r['shear_amplitude_error']=abs(last['shear_projection']-1);gates['shear']=r['shear_amplitude_error']<=.2
        r['gates']=gates;r['sampled_practical_pass']=all(gates.values());results.append(r)
        if correct_compression:r['domain_note']='Unbounded wall-free compression: union volume is not clipped to the observation box; box excursions are not wall violations. Original diagnostic and acceptance outcome retained separately.'
        (folder/('quality-corrected.json' if correct_compression else 'quality.json')).write_text(json.dumps({'summary':r,'observations':records},indent=2)+'\n')
        print(folder.name,'rho%',round(r['p95_compression_peak']*100,2),'sep',round(r['min_separation_over_dx'],3),'volume%',None if r['volume_proxy_error_peak'] is None else round(r['volume_proxy_error_peak']*100,1),'E',round(r['energy_excess_peak'],3),gates,flush=True)
    (root/('quality-results-corrected.json' if correct_compression else 'quality-results.json')).write_text(json.dumps(results,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--correct-compression',action='store_true');a=p.parse_args();audit(a.root.resolve(),a.correct_compression)
