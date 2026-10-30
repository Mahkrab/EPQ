"""Summarise physical failures and total work without treating timing as accuracy."""
import argparse
import csv
import json
from pathlib import Path
import statistics


def assess(root,corrected=False):
    quality_path=root/('quality-results-corrected.json' if corrected else 'quality-results.json')
    quality=json.loads(quality_path.read_text());timings=json.loads((root/'benchmark-results.json').read_text());pbf=json.loads((root/'pbf-workload-results.json').read_text());summary={'timing':[],'workload':[],'convergence':[],'quality_source':quality_path.name}
    for scene in ['resolved','large']:
        for method in ['pbf','dfsph']:
            samples=[x['cost_s_per_sim_s'] for x in timings if x['scene']==scene and x['method']==method and not x['warmup']]
            summary['timing'].append({'scene':scene,'method':method,'median':statistics.median(samples),'min':min(samples),'max':max(samples),'samples':samples,'accuracy_equivalent':False})
        a=next(x for x in pbf if x['scene']==scene);t=a['simulated_s']
        summary['workload'].append({'scene':scene,'method':'pbf','iterations_per_sim_s':a['jacobi_iterations']/t,'row_sweeps_per_sim_s':a['row_sweeps']/t,'row_entry_visits_per_sim_s':a['row_entry_visits']/t,'search_passes_per_sim_s':a['search_passes']/t})
        b=next(x for x in timings if x['scene']==scene and x['method']=='dfsph');t=b['simulated_s'];steps=round(t*240)
        summary['workload'].append({'scene':scene,'method':'dfsph-cubic','density_iterations_per_sim_s':b['density_iterations']/t,'divergence_iterations_per_sim_s':b['divergence_iterations']/t,'iterations_per_sim_s':(b['density_iterations']+b['divergence_iterations'])/t,'row_sweeps_per_sim_s':(5*steps+2*(b['density_iterations']+b['divergence_iterations']))/t,'row_entry_visits_per_sim_s':b['fluid_row_entry_visits']/t,'search_passes_per_sim_s':2*steps/t})
    for scene in ['hydro','compression','collision','surface']:
        rows=[next(x for x in quality if x['label']==scene+'--cubic-'+str(rate)+'-e01') for rate in [120,240,480]]
        summary['convergence'].append({'scene':scene,'states':[{'rate':1/x['policy']['dt'],'p95_compression_peak':x['p95_compression_peak'],'min_separation_over_dx':x['min_separation_over_dx'],'volume_proxy_error_peak':x['volume_proxy_error_peak'],'hydro_centroid_error':x.get('hydro_centroid_error'),'final_centroid':x['final']['com']} for x in rows]})
    summary['physical_trajectories']=len(quality);summary['coupled_policies_passed']=[]
    screens=[x for x in quality if not x['label'].startswith('long-') and x['scene']!='large']
    for policy in sorted({x['policy']['id'] for x in screens}):
        subset=[x for x in screens if x['policy']['id']==policy]
        if {x['scene'] for x in subset}=={'hydro','compression','resolved','collision','surface','shear'} and all(x['sampled_practical_pass'] for x in subset):summary['coupled_policies_passed'].append(policy)
    summary['written_assessment_required']='Physical screens and workload comparisons describe the measured prototype; they do not make an automatic production-integration decision.'
    (root/('assessment-corrected.json' if corrected else 'assessment.json')).write_text(json.dumps(summary,indent=2)+'\n')
    columns=['label','scene','particles','completed','cost_s_per_sim_s','p95_compression_peak','maximum_compression_peak','min_separation_over_dx','volume_proxy_error_peak','energy_excess_peak','iterations_per_sim_s','row_sweeps_per_sim_s','cap_steps','unconverged_steps','sampled_practical_pass']
    with (root/('physical-results-corrected.csv' if corrected else 'physical-results.csv')).open('w') as out:
        writer=csv.DictWriter(out,fieldnames=columns);writer.writeheader();writer.writerows({k:x.get(k) for k in columns} for x in quality)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--corrected',action='store_true');a=p.parse_args();assess(a.root.resolve(),a.corrected)
