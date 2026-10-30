# /// script
# dependencies = ["numpy==2.5.4", "scipy==1.18.1"]
# ///
"""Independently check retained GPU fields, residuals and physical invariants.

The continuum spatial tests live in the mathematical campaign. The known pressure
here is an algebraic manufactured field for auditing GPU implementations of that
accepted operator; it is not a second continuum validation of the same stencil.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from tools.performance.feasible_pressure import mac


def audit(path,cpu=False):
    meta=json.loads(path.read_text());nx,ny,nz=meta['shape'];lx,H,lz=meta['lengths'];hx,hy,hz=lx/nx,H/ny,lz/nz
    def load(field):
        a=np.fromfile(path.with_name(path.stem+'-'+field+'.f64'),dtype='<f8')
        if a.size!=nx*ny*nz or not np.isfinite(a).all():raise ValueError('invalid GPU field')
        return a.reshape(ny,nz,nx)
    vx,vy,vz,p,b,truth=[load(f) for f in ['vx','vy','vz','p','rhs','truth']]
    y=(np.arange(ny)+.5)/ny;z=(np.arange(nz)+.5)/nz;x=(np.arange(nx)+.5)/nx
    zz,yy,xx=np.meshgrid(z,y,x,indexing='ij');xx=xx.transpose(1,0,2);yy=yy.transpose(1,0,2);zz=zz.transpose(1,0,2)
    independent=1000*9.81*H*(1-yy)
    for k in range(1,9):independent+=20/k**2*np.cos(2*np.pi*k*xx)*np.sin(2*np.pi*(k%3+1)*zz)*np.cos(np.pi*(k%4+.5)*yy)
    truth_error=float(np.max(np.abs(truth-independent)))
    Ap=(2*p-np.roll(p,1,2)-np.roll(p,-1,2))/hx**2+(2*p-np.roll(p,1,1)-np.roll(p,-1,1))/hz**2
    yp=2*p-np.roll(p,1,0)-np.roll(p,-1,0);yp[0]=p[0]-p[1];yp[-1]=3*p[-1]-p[-2];Ap+=yp/hy**2
    div=(vx-np.roll(vx,1,2))/hx+(vz-np.roll(vz,1,1))/hz;incoming=np.roll(vy,1,0);incoming[0]=0;div+=(vy-incoming)/hy
    shear=np.broadcast_to(.5*np.sin(2*np.pi*z)[None,:,None],p.shape)
    mass=1000*hx*hy*hz;ymass=np.full(p.shape,mass);ymass[-1]*=.5
    energy_after=.5*(mass*np.sum(vx*vx+vz*vz)+np.sum(ymass*vy*vy));energy_before=.5*mass*np.sum(shear*shear)
    result={'case':path.stem,'relative_true_residual':float(np.linalg.norm(Ap-b)/np.linalg.norm(b)),
        'relative_pressure_error':float(np.linalg.norm(p-truth)/np.linalg.norm(truth)),
        'independent_input_pressure_max_error_Pa':truth_error,
        'shear_velocity_max_error_m_s':float(max(np.max(abs(vx-shear)),np.max(abs(vy)),np.max(abs(vz)))),
        'divergence_max_s_inv':float(np.max(np.abs(div))),
        'kinetic_energy_change_J':float(energy_after-energy_before),
        'horizontal_momentum_impulse_kg_m_s':[float(mass*np.sum(vx-shear)),float(mass*np.sum(vz))],
        'free_surface_volume_rate_m3_s':float(hx*hz*vy[-1].sum()),
        'pressure_seconds_per_simulated_second':meta['pressure_seconds_per_simulated_second']}
    if cpu:
        grid=mac((nx,ny,nz),meta['lengths'])
        convert=lambda a:a.transpose(2,0,1).ravel()
        pc=convert(truth);baseline=np.where(grid.axis==0,.5*np.sin(2*np.pi*grid.position[:,2]/lz),0.)
        _,reference,_=grid.project(baseline+meta['dt']*grid.gradient(pc),meta['dt'])
        result['independent_sparse_CPU_pressure_relative_error']=float(np.linalg.norm(convert(p)-reference)/np.linalg.norm(reference))
    result['pass']=bool(result['relative_true_residual']<1e-8 and result['relative_pressure_error']<1e-8 and truth_error<1e-9 and result['shear_velocity_max_error_m_s']<1e-8 and result['divergence_max_s_inv']<1e-6 and abs(result['kinetic_energy_change_J'])<1e-8 and max(map(abs,result['horizontal_momentum_impulse_kg_m_s']))<1e-9 and abs(result['free_surface_volume_rate_m3_s'])<1e-9)
    if cpu:result['pass']&=result['independent_sparse_CPU_pressure_relative_error']<1e-8
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('folder',type=Path);parser.add_argument('--cpu',action='store_true');args=parser.parse_args()
    results=[audit(p,args.cpu) for p in sorted(args.folder.glob('*.json')) if not any(s in p.stem for s in ['command','process'])]
    if not results:raise ValueError('no GPU trials')
    print(json.dumps({'records':results,'pass':all(r['pass'] for r in results)},indent=2,allow_nan=False))
    if not all(r['pass'] for r in results):raise SystemExit(1)
