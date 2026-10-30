# /// script
# dependencies = ["numpy==2.5.4", "scipy==1.18.1", "matplotlib==3.11.2"]
# ///
"""Summarise physical failures and retained controls without admitting performance."""
import argparse
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from tools.performance.coupled_audit import frames


def final(folder):
    for grid,meta,row,field in frames(folder):pass
    return grid,meta,row,field


def run(root):
    cases=[]
    for status in sorted(root.rglob('status.json')):
        folder=status.parent;assessment=folder/'assessment.json'
        if assessment.exists():
            a=json.loads(assessment.read_text());a['path']=str(folder.relative_to(root));cases.append(a)
    coll=[];time=[]
    base=root/'adaptive-collision'
    fields={n:final(base/f'collision-n{n}-cfl0.2')[3] for n in [32,64,128]}
    for coarse,fine in [(32,64),(64,128)]:
        a=fields[coarse][0];b=fields[fine][0].reshape(a.shape[0],2,a.shape[1],2).mean(axis=(1,3))
        old=json.loads((base/f'collision-n{coarse}-cfl0.2/assessment.json').read_text());new=json.loads((base/f'collision-n{fine}-cfl0.2/assessment.json').read_text())
        coll.append({'coarse':coarse,'fine':fine,'phase_L1_relative':float(np.sum(abs(a-b))/np.sum(b)),
            **{key+'_relative_change':abs(old[key]/new[key]-1) for key in ['height_max','spread_x_rms','spread_y_rms']}})
    ref=json.loads((base/'collision-n64-cfl0.05/assessment.json').read_text())
    for cfl in [.2,.1,.05]:
        a=json.loads((base/f'collision-n64-cfl{cfl}/assessment.json').read_text())
        time.append({'cfl':cfl,'energy_error':a['energy_drift_relative'],**{key+'_relative_to_finest_dt':abs(a[key]/ref[key]-1) for key in ['height_max','spread_x_rms','spread_y_rms']}})
    raw=json.loads((root/'raw-readback-final.json').read_text())
    result={'cases':cases,'collision_spatial_comparison':coll,'collision_time_comparison':time,
        'raw_cases_verified':raw['cases'],'raw_states_verified':raw['frames_verified'],
        'decision':'NO-GO for current coupled candidate, CUDA implementation and production qualification. Compatible pressure family is not rejected.',
        'coupled_physical_criteria_pass':False,'GPU_performance_admitted':False,'GPU_performance_measured':False,
        'throughput_measurements':None,'throughput_projections':None}
    (root/'assessment.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    fig,axes=plt.subplots(2,2,figsize=(11,8),layout='constrained')
    waves=[json.loads((root/'geometry-stable'/f'wave-midpoint-n{n}/assessment.json').read_text()) for n in [32,64,128]]
    axes[0,0].loglog([32,64,128],[100*a['frequency_relative_error'] for a in waves],'o-',label='Frequency')
    axes[0,0].loglog([32,64,128],[100*max(r.get('velocity_relative_error',0) for r in a['reference_samples']) for a in waves],'s-',label='Velocity L2 (worst quarter)')
    axes[0,0].axhline(1,color='black',linestyle=':');axes[0,0].set(xlabel='Horizontal cells, fixed physical geometry',ylabel='Reference error (%)',title='Correct wave timing does not ensure correct velocity');axes[0,0].legend(fontsize=8)
    for n in [32,64,128]:
        with np.load(root/'geometry-stable'/f'wave-midpoint-n{n}/wave-observations.npz') as data:
            axes[0,1].plot(data['time']/data['time'][-1],data['geometric_excess_energy']/data['reference_energy'],label=f'Nx={n}')
    axes[0,1].axhline(1,color='black',linestyle=':');axes[0,1].set(xlabel='Time / analytical wave period',ylabel='Mechanical wave energy / physical reference',title='Inviscid reference energy is constant');axes[0,1].legend(fontsize=8)
    controls=json.loads((root/'interface-pressure-control/results.json').read_text())['records'];offsets=[0.,.25,.5]
    for j,physical in enumerate([False,True]):
        selected=[next(a for a in controls if a['nx']==64 and a['rho_gas']==1.2 and a['a_over_H']==.001 and a['offset_cells']==o and a['physical_face_mass']==physical) for o in offsets]
        axes[1,0].bar(np.arange(3)+(j-.5)*.36,[100*a['acceleration_relative_error'] for a in selected],width=.36,label='Physical masses only' if physical else 'Averaged cell masses')
    axes[1,0].set_yscale('log');axes[1,0].axhline(1,color='black',linestyle=':');axes[1,0].set_xticks(range(3),['Cell face','Quarter cell','Cell centre']);axes[1,0].set(ylabel='Initial acceleration error (%)',title='A mass substitution is not a general interface repair');axes[1,0].legend(fontsize=8)
    selected={};case=base/'collision-n128-cfl0.2'
    for grid,meta,row,field in frames(case):
        if row['kind']=='midpoint':continue
        for target in [0.,.075,.15]:
            if target not in selected or abs(row['time']-target)<abs(selected[target][0]-target):selected[target]=(row['time'],field[0].copy())
    colors=['#1f77b4','#ff7f0e','#2ca02c']
    for color,(target,(t,alpha)) in zip(colors,selected.items()):
        axes[1,1].contour(grid.x,grid.y,alpha,levels=[.5],colors=[color],linewidths=1.5)
    axes[1,1].legend([Line2D([0],[0],color=c) for c in colors],[f't={t:.3f}s' for t in selected],fontsize=8)
    axes[1,1].set(xlabel='x (m)',ylabel='y (m)',title='Symmetric collision still loses 7.56% kinetic energy',xlim=(.03,.17),ylim=(.01,.09));axes[1,1].set_aspect('equal')
    fig.suptitle('Coupled finite-volume reference: physical qualification failed; no GPU throughput benchmark',fontsize=11)
    for extension in ['png','svg']:fig.savefig(root/('coupled-qualification.'+extension),dpi=160)
    plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);run(p.parse_args().root)
