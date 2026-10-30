# /// script
# dependencies = ["numpy==2.5.4", "scipy==1.18.1", "matplotlib==3.11.2"]
# ///
"""Summarise all retained trials without dropping slow samples or failed grids."""
import argparse
import json
from pathlib import Path
import statistics
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def run(root):
    observations=json.loads((root/'verified/mathematics.json').read_text())['records']
    audit=json.loads((root/'gpu-assessment.json').read_text())
    if not audit['pass']:raise ValueError('GPU cost observations failed accuracy audit')
    groups={}
    for p in sorted((root/'gpu').glob('*.json')):
        if any(s in p.stem for s in ['command','process']):continue
        a=json.loads(p.read_text());case=p.stem.rsplit('-',2)[0];groups.setdefault((case,a['solver']),[]).append(a)
    costs=[]
    for (case,solver),rows in sorted(groups.items()):
        samples=[r['pressure_seconds_per_simulated_second'] for r in rows]
        costs.append({'case':case,'solver':solver,'samples_s_per_sim_s':samples,'median':statistics.median(samples),
            'min':min(samples),'max':max(samples),'dt':rows[0]['dt'],'steps':rows[0]['steps'],'shape':rows[0]['shape'],
            'iterations_min':min(min(r['iterations']) for r in rows),'iterations_max':max(max(r['iterations']) for r in rows),
            'setup_median_s':statistics.median(r['setup_s'] for r in rows)})
    spatial=[]
    for record in observations:
        if not record['candidate'].startswith('mac'):continue
        with np.load(root/'verified/mathematics'/(record['label']+'.npz')) as fields:
            mass=1000*fields['area']*fields['dual_distance']
            error=fields['projected_velocity']-fields['exact_velocity']
            impulse=fields['input_velocity']-fields['exact_velocity']
            relative=float(np.sqrt(np.sum(mass*error*error)/np.sum(mass*impulse*impulse)))
        spatial.append({'case':record['label'],'pressure_error':record['manufactured_pressure_error'],
            'velocity_error_relative_to_pressure_impulse':relative})
    results={'costs':costs,'spatial_impulse_errors':spatial,'gpu_audited_trials':len(audit['records']),
        'gpu_max_true_residual':max(r['relative_true_residual'] for r in audit['records']),
        'gpu_max_velocity_error_m_s':max(r['shear_velocity_max_error_m_s'] for r in audit['records']),
        'gpu_max_pressure_relative_error':max(r['relative_pressure_error'] for r in audit['records']),
        'gpu_max_energy_change_J':max(abs(r['kinetic_energy_change_J']) for r in audit['records']),
        'gpu_max_volume_rate_m3_s':max(abs(r['free_surface_volume_rate_m3_s']) for r in audit['records'])}
    (root/'assessment.json').write_text(json.dumps(results,indent=2)+'\n')
    fig,axes=plt.subplots(1,2,figsize=(10.5,4),layout='constrained')
    for name,label in [('mac','Bed + planar free surface'),('mac-periodic','Fully periodic')]:
        a=[r for r in observations if r['candidate']==name and r.get('fraction',1)==1]
        axes[0].loglog([r['shape'][1] for r in a],[100*r['manufactured_pressure_error'] for r in a],'o-',label=label)
    axes[0].axhline(1,color='black',linestyle=':',label='1% pressure gate');axes[0].set(xlabel='Vertical cells (fixed physical geometry)',ylabel='Continuum pressure L2 error (%)');axes[0].legend(fontsize=8)
    labels=['Small slab','Wide shallow slab','Deep column'];cases=['tank','pool','deep']
    for j,solver in enumerate(['fft','pcg']):
        entries=[next(r for r in costs if r['case']==c and r['solver']==solver) for c in cases]
        axes[1].bar([i+(j-.5)*.36 for i in range(3)],[r['median'] for r in entries],width=.36,label={'fft':'Restricted direct solve','pcg':'Jacobi PCG'}[solver])
    axes[1].set_yscale('log');axes[1].axhline(1,color='black',linestyle=':');axes[1].set_xticks(range(3),labels,fontsize=8);axes[1].set_ylabel('Pressure wall seconds / simulated second');axes[1].legend(fontsize=8)
    fig.suptitle('Isolated pressure feasibility; dynamic interface and particle transfer excluded',fontsize=10)
    for extension in ['svg','png']:fig.savefig(root/('feasibility.'+extension),dpi=170)
    plt.close(fig)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path);run(parser.parse_args().root)
