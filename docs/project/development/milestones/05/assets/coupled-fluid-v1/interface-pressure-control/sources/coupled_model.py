# /// script
# dependencies = ["numpy==2.5.4", "scipy==1.18.1"]
# ///
"""Minimal two-fluid Euler coupling with explicit, separately auditable stages.

Material volume and staggered momentum use the same mass fluxes. The midpoint
variant changes time integration only; it does not alter phase reconstruction,
pressure compatibility, material properties or boundary conditions.
"""
from dataclasses import dataclass
import numpy as np
from tools.performance.coupled_transport import phase_transport,momentum_rate


@dataclass
class State:
    alpha:np.ndarray
    u:np.ndarray
    v:np.ndarray
    p:np.ndarray
    time:float=0.


def stage(state,adv_u,adv_v,dt,grid,gravity=0.,method='geometric',order=0,force_alpha=None):
    alpha,mx,my=phase_transport(state.alpha,adv_u,adv_v,dt,grid,method,order)
    rx0,ry0=grid.face_density(state.alpha);rx1,ry1=grid.face_density(alpha)
    du,dv=momentum_rate(adv_u,adv_v,mx,my,grid)
    pu=rx0*state.u+dt*du;pv=ry0*state.v+dt*dv
    ut=pu/rx1;vt=pv/ry1
    if not grid.periodic_y:vt[-1]=0
    old=grid.diagnostics(state.alpha,state.u,state.v,gravity)
    transported=grid.diagnostics(alpha,ut,vt,gravity)
    force_ry=ry1 if force_alpha is None else grid.face_density(force_alpha)[1]
    predicted_v=vt-dt*gravity*force_ry/ry1
    if not grid.periodic_y:predicted_v[-1]=0
    forced=grid.diagnostics(alpha,ut,predicted_v,gravity)
    u,v,p,projection=grid.project(alpha,ut,predicted_v,dt)
    final=grid.diagnostics(alpha,u,v,gravity)
    phi=np.broadcast_to(np.cos((2 if grid.periodic_y else 1)*np.pi*grid.y[:,None]/grid.ly),u.shape)
    projection['null_shear_impulse']=float(grid.volume*np.sum(rx1*phi*(u-ut)))
    ledger={'dt':dt,'transport_kinetic_change':transported['kinetic']-old['kinetic'],
        'transport_momentum_x_change':transported['momentum_x']-old['momentum_x'],
        'transport_momentum_y_change':transported['momentum_y']-old['momentum_y'],
        'body_kinetic_change':forced['kinetic']-transported['kinetic'],
        'material_potential_change':final['potential']-old['potential'],
        'mechanical_energy_change':final['kinetic']+final['potential']-old['kinetic']-old['potential'],
        'material_volume_change':final['liquid_volume']-old['liquid_volume'],'projection':projection,'final':final}
    return State(alpha,u,v,p,state.time+dt),ledger


def step(state,dt,grid,gravity=0.,method='geometric',integrator='midpoint',order=0):
    if integrator=='euler':
        after,record=stage(state,state.u,state.v,dt,grid,gravity,method,order)
        return after,[('accepted',after,record)]
    if integrator!='midpoint':raise ValueError('unknown coupling integrator')
    middle,first=stage(state,state.u,state.v,dt/2,grid,gravity,method,order)
    after,second=stage(state,middle.u,middle.v,dt,grid,gravity,method,order,middle.alpha)
    return after,[('midpoint',middle,first),('accepted',after,second)]
