# /// script
# dependencies = ["numpy==2.5.4", "scipy==1.18.1", "matplotlib==3.11.2"]
# ///
"""Plot measured calibration convergence, closed energy budgets and viscosity tests."""
import argparse
import gzip
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def main(root):
    def summary(label):return json.loads((root/'runs'/label/'physical-summary.json').read_text())
    def ledger(label):
        with gzip.open(root/'runs'/label/'ledger.jsonl.gz','rt') as f:return [json.loads(line) for line in f]
    fig,axes=plt.subplots(1,2,figsize=(10,3.8),constrained_layout=True)
    for prefix,label in [('collision-raw-n','Raw calibration'),('collision-self-n','Physical-rest site correction'),('viscosity-0.001-self-n','Site correction; viscous model')]:
        data=[summary(prefix+str(n)) for n in (6,12,18,24) if (root/'runs'/(prefix+str(n))/'physical-summary.json').exists()]
        x=[d['final']['nominal_layers'] for d in data]
        axes[0].plot(x,[100*d['final']['centroid_relative_error'] for d in data],'o-',label=label)
        axes[1].plot(x,[100*d['settled_max_interparticle_error'] for d in data],'o-',label=label)
    for y in [-1,1]:axes[0].axhline(y,color='black',ls=':',lw=1)
    axes[1].axhline(10,color='black',ls='--',label='Declared field limit')
    for ax in axes:ax.set_xlabel('Independent physical depth / nominal spacing');ax.grid(alpha=.2)
    axes[0].set_ylabel('Final signed centroid error (%)');axes[0].legend(fontsize=7)
    axes[1].set_ylabel('Worst settled interparticle field error (%)');axes[1].legend(fontsize=7)
    fig.savefig(root/'calibration-spatial.png',dpi=180);plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(13,3.8),constrained_layout=True)
    for name,label in [('collision-raw-n12','Raw; nu=0'),('collision-self-n12','Corrected; nu=0'),('viscosity-1e-06-self-n12','Corrected; nu=1e-6'),('viscosity-0.001-self-n12','Corrected; nu=1e-3')]:
        rows=ledger(name);axes[0].plot([r['time'] for r in rows],[r['accepted']['K'] for r in rows],label=label,lw=1)
    rows=ledger('tail-extended-raw-n12');axes[0].plot([5+r['time'] for r in rows],[r['accepted']['K'] for r in rows],color='tab:blue',lw=1,label='Raw extended from t=5')
    axes[0].axhline(.00125,color='black',ls='--');axes[0].set(xlabel='Physical time (s)',ylabel='Kinetic energy (J/kg)',yscale='log',ylim=(1e-6,10));axes[0].legend(fontsize=6)
    rows=[r for r in ledger('collision-raw-n12') if r['time']>=5-1e-9];t=[r['time'] for r in rows];initial=rows[0]['accepted']
    for key,label in [('K','K change'),('U','U change')]:axes[1].plot(t,[r['accepted'][key]-initial[key] for r in rows],label=label)
    axes[1].plot(t,[r['accepted']['K']+r['accepted']['U']-initial['K']-initial['U'] for r in rows],label='Accepted total E change',color='black')
    axes[1].set(xlabel='Physical time (s)',ylabel='Energy change since t=5 (J/kg)');axes[1].legend(fontsize=7)
    e=json.loads((root/'runs/collision-raw-n12/energy-summary.json').read_text())['windows']['settled'];work=e['phase_work']
    gravity=sum(r['prediction']['K']+r['prediction']['U']-r['initial']['K']-r['initial']['U'] for r in rows[1:])
    values=[gravity]+[work[name]['dK']+work[name]['dU'] for name in ['density','plane','contact']]+[e['net_energy_change']]
    axes[2].bar(['Gravity\nprediction','Density','Plane','Contact','Accepted\nnet'],values)
    axes[2].set_ylabel('Signed mechanical work, t=5 to 6 (J/kg)');axes[2].tick_params(axis='x',labelsize=7)
    for ax in axes:ax.grid(alpha=.2)
    fig.savefig(root/'motion-energy.png',dpi=180);plt.close(fig)
    diagnostics=json.loads((root/'diagnostic-summary.json').read_text())['internal_pressure_momentum']
    fig,axes=plt.subplots(1,3,figsize=(12,3.8),constrained_layout=True)
    denominators=[240,480,960];dt=1/np.array(denominators)
    for model,label in [('raw','Raw site convention'),('self','Physical-rest correction')]:
        final=[diagnostics[f'{model}-{d}']['final_kinetic_J_kg'] for d in denominators]
        angular=[100*diagnostics[f'{model}-{d}']['angular_relative_drift'] for d in denominators]
        displacement=[ledger(f'internal-{model}-{d}')[0]['density']['max_displacement'] for d in denominators]
        axes[0].loglog(dt,final,'o-',label=label)
        axes[1].loglog(dt,np.array(displacement)*1000,'o-',label=label)
        axes[2].loglog(dt,angular,'o-',label=label)
    axes[0].axhline(ledger('internal-raw-240')[0]['initial']['K'],color='black',ls='--',label='Initial K')
    for ax in axes:ax.set_xlabel('Time step (s)');ax.grid(alpha=.2);ax.legend(fontsize=7)
    axes[0].set_ylabel('Final K after 0.05 s (J/kg)');axes[1].set_ylabel('Maximum pressure correction (mm)');axes[1].set_title('First step, maximum over Jacobi passes');axes[2].set_ylabel('Unforced angular-momentum drift (%)')
    fig.savefig(root/'initial-pressure-energy.png',dpi=180);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(10,3.8),constrained_layout=True)
    records=json.loads((root/'shear-support-validation.json').read_text())['records']
    for support in [2,3,4]:
        points=[r for r in records if r['support_ratio']==support and r['nu']==.001 and r['steps']==8000]
        axes[0].plot([r['n'] for r in points],[100*r['relative_error'] for r in points],'o-',label=f'Support / spacing = {support}')
    slab=json.loads((root/'slab-spatial-convergence.json').read_text())['records']
    axes[1].plot([r['layers'] for r in slab],[100*r['relative_error'] for r in slab],'o-',label='Fixed L=0.6 m, H=0.05 m')
    for ax in axes:ax.axhline(5,color='black',ls='--');ax.grid(alpha=.2);ax.legend(fontsize=8);ax.set_ylabel('Shear-decay amplitude error (%)')
    axes[0].set(xlabel='Cells per periodic wavelength',title='Bulk validation');axes[1].set(xlabel='Particle layers at fixed physical slab depth',title='Free-slip slab, viscosity support = 4 spacings')
    axes[1].set_xscale('log',base=2);axes[1].set_xticks([2,4,8,16,32],labels=['2','4','8','16','32']);axes[1].minorticks_off()
    fig.savefig(root/'viscosity-qualification.png',dpi=180);plt.close(fig)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path);main(parser.parse_args().root)
