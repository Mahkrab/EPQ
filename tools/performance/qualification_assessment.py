"""Apply predefined physical budgets without admitting centroid-only successes."""
from pathlib import Path
import argparse
import json
import math


def assess(root):
    protocol=json.loads((root/'protocol.json').read_text());c=protocol['criteria'];cases={}
    for f in sorted((root/'runs').glob('*/physical-summary.json')):
        parameters=json.loads((f.parent/'request.json').read_text())['parameters']
        if parameters['restart'] or parameters['duration']<6:continue
        d=json.loads(f.read_text());e=json.loads((f.parent/'energy-summary.json').read_text())
        rows=[json.loads(line) for line in (f.parent/'audit.jsonl').read_text().splitlines()];settled=[r for r in rows if 5-1e-9<=r['time_s']<=6+1e-9]
        checks={'centroid':d['settled_max_centroid_error']<=c['settled_centroid_relative_max'],
            'strict_calibration':d['settled_max_centroid_error']<=c['strict_calibration_centroid_relative_max'],
            'height':max(abs(r['height_relative_error']) for r in settled)<=c['settled_height_relative_max'],
            'volume':max(abs(r['field_volume']['0.5']['relative_volume_error']) for r in settled if 'field_volume' in r)<=c['settled_volume_relative_max'],
            'interparticle_density':d['settled_max_interparticle_error']<=c['settled_interparticle_field_p95_max'],
            'transient_density':d['max_p95_compression']<=c['sampled_transient_p95_compression_max'] and d['max_positive_density_error']<=c['sampled_transient_max_compression_max'],
            'separation':d['minimum_separation_fraction_dx']>=c['separation_fraction_dx_min'],
            'containment':max(r['boundary_violation_m'] for r in rows)<=c['plane_violation_m_max'],
            'quietness':e['windows']['settled']['maximum_K']<=c['settled_kinetic_J_kg_max'],
            'energy':e['every_step_max_energy_above_initial']<=c['energy_gain_J_kg_max'],
            'energy_accounting':max(e['maximum_identity_residuals'][key] for key in ['closure','gravity','checkpoint_K','checkpoint_U'])<=c['gravity_and_stage_closure_J_kg_max'],
            'impulse_accounting':max(e['maximum_identity_residuals'][key] for key in ['momentum_budget','density_internal_impulse','contact_impulse','viscous_impulse','viscous_angular'])<=c['isolated_impulse_m_s_max'],
            'viscous_dissipation':e['maximum_identity_residuals']['viscous_increase']<=c['viscous_energy_increase_J_kg_max']}
        cases[f.parent.name]={'parameters':parameters,'checks':checks,'all_checks_pass':all(checks.values()),
            'failed':[k for k,v in checks.items() if not v],'centroid_error':d['final']['centroid_relative_error'],
            'mean_centroid_m':d['settled_mean_centroid_m'],'settled_max_kinetic_J_kg':e['windows']['settled']['maximum_K']}
    pairs={}
    for prefix,numbers in [('collision-raw-n',[6,12,18,24]),('collision-self-n',[6,12,18,24]),('viscosity-0.001-self-n',[12,18,24]),('tank-valid-self-n',[6,12])]:
        labels=[prefix+str(n) for n in numbers]
        if not all(label in cases for label in labels):continue
        values=[cases[label]['centroid_error'] for label in labels]
        means=[cases[label]['mean_centroid_m'] for label in labels]
        pairs[prefix]={'labels':labels,'final_errors':values,'physical_errors_decrease':all(abs(b)<abs(a) for a,b in zip(values,values[1:])),
            'successive_mean_centroid_changes_m':[abs(b-a) for a,b in zip(means,means[1:])],
            'finest_two_strict_calibration_pass':all(cases[label]['checks']['strict_calibration'] for label in labels[-2:]),
            'finest_two_all_checks_pass':all(cases[label]['all_checks_pass'] for label in labels[-2:])}
    temporal={}
    comparisons=[]
    for n in [12,18]:
        for model in ['raw','self']:
            comparisons.append((f'collision-{model}-n{n}',[f'halfdt-{model}-n{n}',f'iter16-{model}-n{n}']))
    comparisons.append(('viscosity-0.001-self-n12',['halfdt-viscous-self-n12','iter16-viscous-self-n12']))
    budget=protocol['fixed_collision']['mass_kg']/1000/(1.2*.8)/2*c['strict_calibration_centroid_relative_max']
    for base,labels in comparisons:
        if base not in cases:continue
        for label in labels:
            if label not in cases:continue
            change=abs(cases[label]['mean_centroid_m']-cases[base]['mean_centroid_m'])
            temporal[label]={'base':base,'mean_centroid_change_m':change,'predefined_budget_m':budget,
                'change_within_budget':change<=budget,
                'changed_checks':[key for key,value in cases[base]['checks'].items() if cases[label]['checks'][key]!=value]}
    slab=json.loads((root/'slab-validation.json').read_text())['records']
    shallow=[r for r in slab if r['n']==24 and r['layers'] in [2,4] and '8000' in r['command']]
    material={'amplitude_budget':c['shear_decay_amplitude_relative_error_max'],
        'shallow_free_slip_errors':{str(r['layers']):r['mean_final_amplitude']/math.exp(-1)-1 for r in shallow},
        'shallow_free_slip_pass':all(abs(r['mean_final_amplitude']/math.exp(-1)-1)<=c['shear_decay_amplitude_relative_error_max'] for r in shallow)}
    if len(shallow)!=2:raise ValueError('missing independent shallow-viscosity references')
    result={'cases':cases,'spatial':pairs,'temporal':temporal,'viscosity_material_gate':material,'production_admitted':False,
            'admission_rule':'Passing an individual case is insufficient. Require spatial and temporal/iteration physical convergence for the same material model, correct conservation and independent viscosity validation in the operating geometry.'}
    (root/'assessment.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path)
    result=assess(parser.parse_args().root)
    print(json.dumps({k:v for k,v in result.items() if k!='cases'},indent=2))
