# /// script
# dependencies = ["numpy==2.5.4", "scipy==1.18.1"]
# ///
"""Recompute conservation and pressure budgets directly from every raw state.

This reader does not trust the recorded diagnostic values or use the solver's
incidence matrix to check divergence and integrated pressure forces.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from tools.performance.coupled_audit import frames


def recompute(grid,field):
    alpha,u,v,_=field;rho=grid.rho_gas+(grid.rho_liquid-grid.rho_gas)*alpha
    rx=(rho+np.roll(rho,-1,axis=1))/2;ry=(rho+np.roll(rho,-1,axis=0))/2
    active_v=v if grid.periodic_y else v[:-1];active_ry=ry if grid.periodic_y else ry[:-1]
    previous_v=np.roll(v,1,axis=0)
    if not grid.periodic_y:
        if np.max(abs(v[-1]))>1e-14:raise ValueError('impermeable lid velocity failed')
        previous_v[0]=0
    divergence=(u-np.roll(u,1,axis=1))/grid.hx+(v-previous_v)/grid.hy
    return {'liquid_volume':float(grid.hx*grid.hy*alpha.sum()),'mass':float(grid.hx*grid.hy*rho.sum()),
        'momentum_x':float(grid.hx*grid.hy*np.sum(rx*u)),'momentum_y':float(grid.hx*grid.hy*np.sum(active_ry*active_v)),
        'kinetic':float(.5*grid.hx*grid.hy*(np.sum(rx*u*u)+np.sum(active_ry*active_v*active_v))),
        'divergence_max':float(abs(divergence).max()),'alpha_min':float(alpha.min()),'alpha_max':float(alpha.max())}


def validate(grid,field,record):
    values=recompute(grid,field)
    for key,value in values.items():
        if not np.isclose(value,record[key],atol=2e-12,rtol=2e-10):raise ValueError('raw diagnostic mismatch: '+key)
    return values


def check(folder):
    count=0;maximum=0.;base=None;accepted=0;middle_alpha=None;force_maximum=0.
    for grid,meta,row,field in frames(folder):
        raw=validate(grid,field,row['diagnostics']);count+=1;stage=row['stage']
        if base is None:base=raw;continue
        if stage:
            deltaK=raw['kinetic']-base['kinetic'];accounted=stage['transport_kinetic_change']+stage['body_kinetic_change']+stage['projection']['projection_energy_change']
            error=abs(deltaK-accounted);maximum=max(maximum,error)
            if error>2e-11:raise ValueError('kinetic budget mismatch')
            dt=stage['dt'];p=field[3];pressure_x=-dt*grid.hy*np.sum(np.roll(p,-1,axis=1)-p)
            pressure_y=0. if grid.periodic_y else -dt*grid.hx*np.sum(p[-1]-p[0])
            for axis,value in [('x',pressure_x),('y',pressure_y)]:
                if abs(value-stage['projection']['pressure_impulse_'+axis])>2e-11:raise ValueError('pressure force budget mismatch')
            if abs(raw['momentum_x']-base['momentum_x']-stage['transport_momentum_x_change']-pressure_x)>2e-11:raise ValueError('horizontal momentum budget mismatch')
            force_alpha=middle_alpha if row['kind']=='accepted' and meta['integrator']=='midpoint' else field[0]
            force_rho=grid.rho_gas+(grid.rho_liquid-grid.rho_gas)*force_alpha
            force_ry=.5*(force_rho+np.roll(force_rho,-1,axis=0))
            if not grid.periodic_y:force_ry=force_ry[:-1]
            body_y=-meta['gravity']*dt*grid.hx*grid.hy*force_ry.sum()
            error=abs(raw['momentum_y']-base['momentum_y']-stage['transport_momentum_y_change']-body_y-pressure_y);force_maximum=max(force_maximum,error)
            if error>2e-11:raise ValueError('vertical force budget mismatch')
        if row['kind']=='midpoint':middle_alpha=field[0].copy()
        if row['kind']=='accepted':base=raw;accepted+=1
    status=json.loads((folder/'status.json').read_text())
    if count!=status['frames']:raise ValueError('state count differs from status')
    if status['completed'] and (accepted!=status['accepted_steps'] or abs(row['time']-meta['duration'])>1e-12):raise ValueError('completed horizon differs from status')
    return {'case':str(folder),'frames_verified':count,'kinetic_budget_max_abs_error':maximum,'force_budget_max_abs_error':force_maximum,'all_match':True}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);args=p.parse_args()
    result=[check(status.parent) for status in sorted(args.root.rglob('status.json'))]
    print(json.dumps({'records':result,'cases':len(result),'frames_verified':sum(r['frames_verified'] for r in result),'all_match':all(r['all_match'] for r in result)},indent=2))
