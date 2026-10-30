"""Keep operator admission and full-model physical qualification separate."""
import argparse
import json
from pathlib import Path


def operator_assessment(root):
    source=json.loads((root/'edge-strain-screen.json').read_text())
    result=[]
    for r in source['records']:
        windows={}
        for limit in [1,2]:
            samples=[s for s in r['samples'] if s['time']<=limit*r['decay_time']+1e-9]
            amp=max(abs(s['amplitude']/s['analytic_amplitude']-1) for s in samples)
            l2=max(s['L2_error_over_initial'] for s in samples)
            traction=0.
            if r['force_expected_initial']:
                traction=max(abs(s['force_per_kg'][0]/(r['force_expected_initial']*s['analytic_amplitude'])-1) for s in samples)
            windows[str(limit)]={'maximum_amplitude_relative_error':amp,'maximum_velocity_L2_over_initial':l2,
                'maximum_traction_relative_error':traction,'rate_relative_error_at_tau':r['rate_relative_error'],
                'pass':amp<=.05 and l2<=.05 and traction<=.05 and abs(r['rate_relative_error'])<=.05}
        result.append({'mode':r['mode'],'layers':r['layers'],'L':r['L'],'H':r['H'],'windows_in_e_folds':windows})
    return result


def coupled_assessment(root):
    result=[]
    for path in sorted((root/'audits-final').glob('*.audit.json')):
        data=json.loads(path.read_text());s=data['summary'];records=data['records'];U=s['parameters']['amplitude']
        gates={'density_p95':s['maximum_p95_compression']<=.05,'density_maximum':s['maximum_compression']<=.25,
            'separation':s['minimum_separation_over_dx']>=.5-1e-12,
            'planes':s['maximum_plane_violation']<=1e-6,
            'centroid':s['maximum_abs_centroid_error']<=.01,
            'energy_budget':s['energy_maxima']['energy_budget']<=1e-9,
            'viscous_energy_budget':s['energy_maxima']['viscous_identity']<=1e-9,
            'viscous_energy_sign':s['energy_maxima']['viscous_increase']<=1e-12,
            'hydrostatic_height':max(abs(r['height_relative_error']) for r in records)<=.1,
            'mass':all(abs(r['mass_kg']-2)<1e-12 for r in records)}
        # The 10% interparticle-field screen comes from the preserved preceding
        # study. It is deliberately independent of particle-site compression.
        gates['legacy_interparticle_field']=max(v['p95_absolute_relative_error'] for r in records for v in r['interparticle_density'].values())<=.1
        volumes=[v for r in records if 'field_volume' in r for v in r['field_volume']['thresholds'].values()]
        gates['independent_volume']=bool(volumes) and max(abs(v['relative_volume_error']) for v in volumes)<=.1
        if U:
            gates['modal_amplitude']=max(abs(r['amplitude_relative_error']) for r in records)<=.05
            gates['velocity_L2']=s['max_L2_velocity_error']<=.05
            gates['decay_rate']=s['decay_rate_relative_error'] is not None and abs(s['decay_rate_relative_error'])<=.05
            if 'wall_viscous_impulse_relative_error' in s:gates['wall_traction']=s['wall_viscous_impulse_relative_error']<=.05
        result.append({'label':s['label'],'gates':gates,'failed_gates':[k for k,v in gates.items() if not v],
            'legacy_quietness':s['legacy_quietness_pass'],'summary':s,
            'complete_physical_regime_qualified':False,
            'scope':'Separate reference case; no collision qualification or two-finest combined settled qualification implied.'})
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);a=p.parse_args()
    report={'operator':operator_assessment(a.root),'coupled':coupled_assessment(a.root),
        'rejected_prefix':json.loads((a.root/'coupled/mirror-mixed-n8-h4.rejection.json').read_text()),
        'production_qualification_ready':False,
        'decision':'Reject this full PBF candidate for gravity-supported viscous free-surface flows. Isolated viscosity/traction regimes pass within stated windows; no combined physically acceptable operating regime is established.',
        'original_results':'Earlier studies and every original threshold remain unchanged; five-second quietness is reported separately, not converted to a physical-accuracy pass.'}
    with (a.root/'assessment.json').open('x') as stream:json.dump(report,stream,indent=2,allow_nan=False);stream.write('\n')


if __name__=='__main__':main()
