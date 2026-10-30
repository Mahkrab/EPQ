# /// script
# dependencies = ["numpy==2.5.4", "scipy==1.18.1"]
# ///
"""Freeze transport and isolate interface geometry in pressure acceleration.

The counterfactual uses independently integrated physical staggered masses. It is
not a coupled fix: those masses would need their own consistent transport fluxes.
Only the mass supplied to the unchanged compatible pressure projection differs.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from numpy.polynomial.legendre import leggauss
from tools.performance.coupled_grid import Grid
from tools.performance.coupled_reference import interface_fraction,wave_frequency,wave_reference
from tools.performance.coupled_campaign import snapshot


class PrescribedFaceMass(Grid):
    def face_density(self,alpha):return self.physical_faces


def fields(grid,depth,amplitude):
    nodes,weights=leggauss(24);k=2*np.pi/grid.lx;omega=wave_frequency(grid,depth);H=grid.ly
    def component(axis):
        xc=grid.x+(.5*grid.hx if axis==0 else 0);yc=grid.y+(.5*grid.hy if axis==1 else 0)
        x=xc[None,:,None]+grid.hx/2*nodes;lo=yc[:,None,None]-grid.hy/2;hi=lo+grid.hy
        eta=depth+amplitude*np.cos(k*x);cut=np.minimum(hi,np.maximum(lo,eta));rw,ra=grid.rho_liquid,grid.rho_gas
        rho=np.sum((rw*(cut-lo)+ra*(hi-cut))*weights,axis=2)/(2*grid.hy)
        if axis==0:
            water=amplitude*omega**2/k/np.sinh(k*depth)*(np.sinh(k*cut)-np.sinh(k*lo))*np.sin(k*x)
            air=-amplitude*omega**2/k/np.sinh(k*(H-depth))*(np.sinh(k*(H-cut))-np.sinh(k*(H-hi)))*np.sin(k*x)
        else:
            water=-amplitude*omega**2/k/np.sinh(k*depth)*(np.cosh(k*cut)-np.cosh(k*lo))*np.cos(k*x)
            air=amplitude*omega**2/k/np.sinh(k*(H-depth))*(np.cosh(k*(H-hi))-np.cosh(k*(H-cut)))*np.cos(k*x)
        acceleration=np.sum((rw*water+ra*air)*weights,axis=2)/(2*grid.hy*rho)
        if axis==1 and not grid.periodic_y:acceleration[-1]=0;rho[-1]=ra
        return rho,acceleration
    rx,ax=component(0);ry,ay=component(1)
    return (rx,ry),(ax,ay)


def run(root):
    folder=root/'interface-pressure-control';folder.mkdir();source=snapshot(folder);records=[]
    configs=[(n,1.2,.001,0.) for n in [32,64,128]]+[(64,r,.001,0.) for r in [12.,120.]]+[(64,1.2,.0001,0.)]+[(64,1.2,.001,f) for f in [.25,.5]]
    for n,gas,relative_amplitude,offset in configs:
        original=Grid(n,n//2,rho_gas=gas);depth=.05+offset*original.hy;amplitude=relative_amplitude*depth
        alpha=interface_fraction(original,lambda x:depth+amplitude*np.cos(2*np.pi*x/original.lx))
        physical,expected=fields(original,depth,amplitude);zero=np.zeros_like(alpha);predicted=np.full_like(alpha,-9.81*.001);predicted[-1]=0
        reference=original.pack(*expected);weights=original.pack(*physical)*original.volume
        old_density=original.face_density(alpha);false_gas=[]
        for old,new in zip(old_density,physical):false_gas.append(float(np.max(np.where(new<gas*(1+1e-10),old/gas-1,0))))
        _,_,_,exact_p=wave_reference(original,depth,amplitude,0.)
        for geometric in [False,True]:
            grid=PrescribedFaceMass(n,n//2,rho_gas=gas) if geometric else original
            if geometric:grid.physical_faces=physical
            u,v,p,ledger=grid.project(alpha,zero,predicted,.001)
            computed=grid.pack(u,v)/.001;error=computed-reference
            active_y=np.r_[np.broadcast_to(grid.y[:,None],alpha.shape).ravel(),np.broadcast_to((grid.y+grid.hy/2)[:,None],alpha.shape).ravel()[grid.vkeep]]
            bulk=abs(active_y-depth)>2*grid.hy
            fluct=p-p.mean(axis=1,keepdims=True);exact_fluct=exact_p-exact_p.mean(axis=1,keepdims=True)
            result={'nx':n,'rho_gas':gas,'a_over_H':relative_amplitude,'offset_cells':offset,'physical_face_mass':geometric,
                'acceleration_relative_error':float(np.sqrt(np.dot(weights*error,error)/np.dot(weights*reference,reference))),
                'bulk_acceleration_relative_error':float(np.sqrt(np.dot(weights[bulk]*error[bulk],error[bulk])/np.dot(weights[bulk]*reference[bulk],reference[bulk]))),
                'pressure_perturbation_relative_error':float(np.linalg.norm(fluct-exact_fluct)/np.linalg.norm(exact_fluct)),
                'false_gas_face_density_relative_excess':false_gas,'pressure_record':ledger}
            label=f'n{n}-gas{gas}-a{relative_amplitude}-offset{offset}-geometric{geometric}'
            np.savez_compressed(folder/(label+'.npz'),alpha=alpha,u=u,v=v,p=p,exact_p=exact_p,exact_ax=expected[0],exact_ay=expected[1],physical_rx=physical[0],physical_ry=physical[1],old_rx=old_density[0],old_ry=old_density[1])
            records.append(result);print(result,flush=True)
    (folder/'results.json').write_text(json.dumps({'records':records,'source_sha256':source,'coupled_candidate':False},indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);run(p.parse_args().root)
