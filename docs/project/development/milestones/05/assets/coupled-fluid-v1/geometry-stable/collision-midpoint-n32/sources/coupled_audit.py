# /// script
# dependencies = ["numpy==2.5.4", "scipy==1.18.1"]
# ///
"""Read complete saved coupled states and assess predefined physical observables.

References use analytic material maps and continuum two-fluid potentials. Every
stage's energy and pressure work remain visible, even when a final scalar passes.
"""
import argparse
import gzip
import json
from pathlib import Path
import numpy as np
from scipy.optimize import minimize_scalar
from tools.performance.coupled_grid import Grid
from tools.performance.coupled_reference import circle_fraction,wave_frequency,wave_reference


def frames(folder):
    meta=json.loads((folder/'input.json').read_text());grid=Grid(**meta['grid'])
    with gzip.open(folder/'states.npy.gz','rb') as stream,(folder/'frames.jsonl').open() as ledger:
        for line in ledger:
            row=json.loads(line);field=np.load(stream,allow_pickle=False)
            if field.shape!=(4,grid.ny,grid.nx) or field.dtype!=np.float64 or not np.isfinite(field).all():raise ValueError('invalid retained state')
            yield grid,meta,row,field
        if stream.read(1):raise ValueError('unindexed state bytes')


def assess(folder):
    rows=[];initial=None;last=None;snapshots=[];maxima={k:0. for k in ['mass_relative','volume_relative','momentum_x_relative','momentum_y_relative','phase_bounds','divergence_dt','pressure_residual','projection_energy_increase','null_shear_impulse_relative']}
    times=[];modes=[];energies=[]
    for grid,meta,row,field in frames(folder):
        diag=row['diagnostics'];alpha,u,v,p=field
        if initial is None:
            initial=diag;first=field.copy();scale=max(diag['mass']*max(diag['velocity_max'],.001),1e-20)
        for name,key in [('mass_relative','mass'),('volume_relative','liquid_volume')]:maxima[name]=max(maxima[name],abs(diag[key]/initial[key]-1))
        for axis in ['x','y']:maxima['momentum_'+axis+'_relative']=max(maxima['momentum_'+axis+'_relative'],abs(diag['momentum_'+axis]-initial['momentum_'+axis])/scale)
        maxima['phase_bounds']=max(maxima['phase_bounds'],max(0,-diag['alpha_min'],diag['alpha_max']-1))
        if row['stage']:
            proj=row['stage']['projection'];maxima['divergence_dt']=max(maxima['divergence_dt'],proj['divergence_dt_max']);maxima['pressure_residual']=max(maxima['pressure_residual'],proj['relative_residual'])
            maxima['projection_energy_increase']=max(maxima['projection_energy_increase'],proj['projection_energy_change']/max(initial['kinetic'],1e-12))
            maxima['null_shear_impulse_relative']=max(maxima['null_shear_impulse_relative'],abs(proj['null_shear_impulse'])/scale)
        if row['kind']=='midpoint':continue
        times.append(row['time']);energies.append(diag['kinetic']);last=field.copy();last_row=row;rows.append(row)
        if 'height_mode' in row:modes.append(row['height_mode'][0])
        if meta['gravity']:
            # Retain quarter-period states for independent velocity/pressure checks.
            for f in [.25,.5,.75,1.]:
                target=meta['duration']*f
                if abs(row['time']-target)<=meta['dt']/2+1e-12:snapshots.append((row,field.copy()))
    status=json.loads((folder/'status.json').read_text());result={'case':folder.name,'completed':status['completed'],'accepted_frames':len(rows),'maxima':maxima}
    result['fundamental_pass']=bool(maxima['mass_relative']<1e-10 and maxima['volume_relative']<1e-10 and maxima['momentum_x_relative']<1e-9 and (not grid.periodic_y or maxima['momentum_y_relative']<1e-9) and maxima['phase_bounds']<1e-10 and maxima['divergence_dt']<1e-8 and maxima['pressure_residual']<1e-8 and maxima['null_shear_impulse_relative']<1e-8)
    alpha,u,v,p=last;t=last_row['time']
    if folder.name.startswith(('translation','shear')):
        shear=meta['shear'];exact=circle_fraction(grid,[(.07,.05)],.018,t,meta['speed'],shear)
        result['interface_L1_relative']=float(np.sum(abs(alpha-exact))/np.sum(exact))
        exactu=np.full_like(u,meta['speed']);exactv=np.broadcast_to(shear*np.sin(2*np.pi*(grid.x-meta['speed']*t)/grid.lx),u.shape)
        rx,ry=grid.face_density(exact);weights=grid.pack(rx,ry);dv=grid.pack(u-exactu,v-exactv)
        result['velocity_relative_error']=float(np.sqrt(np.dot(weights*dv,dv)/max(np.dot(weights*grid.pack(exactu,exactv),grid.pack(exactu,exactv)),1e-30)))
        if shear:
            phi=np.sin(2*np.pi*(grid.x-meta['speed']*t)/grid.lx)
            result['shear_mode_amplitude_error']=float(abs(2*np.mean(v*phi)/shear-1))
        result['energy_drift_relative']=float(max(abs(np.asarray(energies)/energies[0]-1))) if energies[0]>0 else 0.
        result['physical_pass']=bool(result['fundamental_pass'] and status['completed'] and result['interface_L1_relative']<.01 and result['velocity_relative_error']<.01 and result.get('shear_mode_amplitude_error',0)<.01 and result['energy_drift_relative']<.01)
        np.savez_compressed(folder/'independent-final-reference.npz',alpha=exact,u=exactu,v=exactv)
    elif folder.name.startswith('wave'):
        omega=wave_frequency(grid,.05);a0=.00005*np.sinc(1/grid.nx);times=np.asarray(times);modes=np.asarray(modes)
        def fit(w):
            matrix=np.column_stack([np.cos(w*times),np.sin(w*times),np.ones_like(times)])
            coefficients=np.linalg.lstsq(matrix,modes,rcond=None)[0]
            return float(np.mean((matrix@coefficients-modes)**2)),coefficients
        optimum=minimize_scalar(lambda w:fit(w)[0],bounds=(.5*omega,1.5*omega),method='bounded',options={'xatol':1e-12});_,coeff=fit(optimum.x)
        result.update({'frequency_relative_error':float(abs(optimum.x/omega-1)),'amplitude_relative_error':float(abs(np.linalg.norm(coeff[:2])/a0-1)),
            'initial_phase_cycles_error':float(abs(np.arctan2(-coeff[1],coeff[0]))/(2*np.pi)),
            'waveform_max_relative_error':float(np.max(abs(modes-a0*np.cos(omega*times)))/a0)})
        mean_depth=initial['liquid_volume']/grid.lx;minimum=9.81*grid.lx*(grid.rho_gas*grid.ly**2+(grid.rho_liquid-grid.rho_gas)*mean_depth**2)/2
        reference_energy=(grid.rho_liquid-grid.rho_gas)*9.81*grid.lx*.00005**2/4
        excess=np.array([r['diagnostics']['kinetic']+r['diagnostics']['geometric_potential']-minimum for r in rows])
        centre_excess=np.array([r['diagnostics']['kinetic']+r['diagnostics']['potential']-minimum for r in rows])
        result['wave_energy_drift_relative']=float(np.max(abs(excess/reference_energy-1)))
        result['initial_geometric_energy_error']=float(excess[0]/reference_energy-1)
        result['initial_cell_centre_energy_error']=float(centre_excess[0]/reference_energy-1)
        references=[]
        for index,(r,field) in enumerate(snapshots):
            ar,ur,vr,pr,ru,rv=wave_reference(grid,.05,.00005,r['time'],with_density=True);_,uu,vv,pp=field
            vel_scale=max(abs(np.sin(omega*r['time'])),1e-12)
            weight=grid.pack(ru,rv);target=grid.pack(ur,vr);error=grid.pack(uu-ur,vv-vr)
            sample={'time':r['time']}
            if vel_scale>.5:
                sample['velocity_relative_error']=float(np.sqrt(np.dot(weight*error,error)/np.dot(weight*target,target)))
                sample['sampled_reference_kinetic_energy_bias']=float(.5*grid.volume*np.dot(weight*target,target)/reference_energy-np.sin(omega*r['time'])**2)
            pp=pp-pp.mean(axis=1,keepdims=True);pr=pr-pr.mean(axis=1,keepdims=True)
            if abs(np.cos(omega*r['time']))>.5:sample['pressure_perturbation_relative_error']=float(np.linalg.norm(pp-pr)/np.linalg.norm(pr))
            references.append(sample)
            np.savez_compressed(folder/f'independent-reference-{index}.npz',alpha=ar,u=ur,v=vr,p=pr,face_density_u=ru,face_density_v=rv)
        result['reference_samples']=references
        result['physical_pass']=bool(result['fundamental_pass'] and status['completed'] and max(result[k] for k in ['frequency_relative_error','amplitude_relative_error','initial_phase_cycles_error','wave_energy_drift_relative'])<.01 and max((s.get('velocity_relative_error',0) for s in references),default=1)<.01 and max((s.get('pressure_perturbation_relative_error',0) for s in references),default=1)<.01)
        np.savez_compressed(folder/'wave-observations.npz',time=times,amplitude=modes,geometric_excess_energy=excess,cell_centre_excess_energy=centre_excess,reference_energy=reference_energy,exact_amplitude=a0*np.cos(omega*times))
    elif folder.name.startswith('collision'):
        mask=np.flip(alpha,axis=1);height=grid.hy*np.sum(alpha,axis=0)
        total=alpha.sum();xc=(alpha*grid.x[None,:]).sum()/total;yc=(alpha*grid.y[:,None]).sum()/total
        result.update({'energy_drift_relative':float(max(abs(np.asarray(energies)/energies[0]-1))),
            'symmetry_L1_relative':float(np.sum(abs(alpha-mask))/total),'centroid_x':float(xc),'centroid_y':float(yc),
            'height_max':float(height.max()),'spread_x_rms':float(np.sqrt((alpha*(grid.x[None,:]-xc)**2).sum()/total)),
            'spread_y_rms':float(np.sqrt((alpha*(grid.y[:,None]-yc)**2).sum()/total))})
        result['physical_pass']=bool(result['fundamental_pass'] and status['completed'] and result['energy_drift_relative']<.01 and result['symmetry_L1_relative']<.01)
    (folder/'assessment.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--pattern',default='*');args=p.parse_args()
    for folder in sorted(args.root.glob(args.pattern)):
        if (folder/'status.json').exists():print(json.dumps(assess(folder),allow_nan=False),flush=True)
