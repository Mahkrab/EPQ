# /// script
# dependencies = ["numpy==2.5.4", "scipy==1.18.1"]
# ///
"""Retain complete coupled states and stage ledgers, including failed prefixes.

Each case has an exclusive directory and a source snapshot. State streams contain
consecutive lossless NumPy arrays inside gzip, with frame times/kinds in JSONL.
The campaign is a physical reference calculation; its instrumented CPU time is
not a throughput measurement.
"""
import argparse
from dataclasses import asdict
import gzip
import hashlib
import json
import math
from pathlib import Path
import shutil
import time
import numpy as np
from tools.performance.coupled_grid import Grid
from tools.performance.coupled_model import State,step
from tools.performance.coupled_reference import circle_fraction,interface_fraction,wave_frequency,wave_reference,height_mode
from tools.performance.coupled_transport import phase_transport,momentum_rate,geometric_potential,reconstruction,rectangle_fraction


def snapshot(folder):
    sources=folder/'sources';sources.mkdir();records={}
    for p in sorted(Path(__file__).parent.glob('coupled_*.py')):
        shutil.copyfile(p,sources/p.name);records[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
    return records


def public_grid(grid):return {key:getattr(grid,key) for key in ['nx','ny','lx','ly','periodic_y','rho_liquid','rho_gas']}


def case(root,label,grid,state,duration,steps,gravity=0.,integrator='midpoint',method='geometric',transport_only=False,speed=.1,shear=0.,wave_depth=.05,adaptive_cfl=None):
    folder=root/label;folder.mkdir();metadata={'label':label,'grid':public_grid(grid),'duration':duration,'steps':steps,'dt':duration/steps,'adaptive_cfl':adaptive_cfl,'gravity':gravity,'integrator':integrator,'interface_method':method,'transport_only':transport_only,'speed':speed,'shear':shear,'source_sha256':snapshot(folder)}
    (folder/'input.json').write_text(json.dumps(metadata,indent=2)+'\n')
    frames=gzip.GzipFile(filename=str(folder/'states.npy.gz'),mode='xb',mtime=0)
    ledger=(folder/'frames.jsonl').open('x');rejected=(folder/'rejected-steps.jsonl').open('x');start=time.monotonic();count=0
    def write(kind,current,record):
        nonlocal count
        field=np.stack([current.alpha,current.u,current.v,current.p]);np.save(frames,field,allow_pickle=False)
        diag=grid.diagnostics(current.alpha,current.u,current.v,gravity);diag['geometric_potential']=geometric_potential(current.alpha,grid,gravity)
        entry={'frame':count,'kind':kind,'time':current.time,'diagnostics':diag,'stage':record}
        if gravity:entry['height_mode']=height_mode(grid,current.alpha,wave_depth)
        ledger.write(json.dumps(entry,allow_nan=False)+'\n');ledger.flush();count+=1
    base_dt=duration/steps;write('initial',state,None);i=0
    try:
        while state.time<duration*(1-1e-14):
            if i>=10000:raise ValueError('bounded accepted-step limit reached')
            dt=min(base_dt,duration-state.time)
            if adaptive_cfl:
                rate=abs(state.u).max()/grid.hx+abs(state.v).max()/grid.hy
                dt=min(dt,adaptive_cfl/max(rate,1e-30))
            if transport_only:
                u=np.full_like(state.alpha,speed);v=np.broadcast_to(shear*np.sin(2*np.pi*(grid.x-speed*(state.time+dt/2))/grid.lx),u.shape).copy()
                alpha,_,_=phase_transport(state.alpha,u,v,dt,grid,method,i)
                state=State(alpha,u,v,np.zeros_like(alpha),state.time+dt);write('accepted',state,None)
            else:
                for retry in range(12):
                    try:
                        after,stages=step(state,dt,grid,gravity,method,integrator,i);break
                    except ValueError as exc:
                        if adaptive_cfl is None or 'CFL' not in str(exc):raise
                        rejected.write(json.dumps({'time':state.time,'dt':dt,'retry':retry,'reason':str(exc)})+'\n');rejected.flush();dt/=2
                else:raise ValueError('bounded CFL retry limit reached')
                state=after
                for kind,s,record in stages:write(kind,s,record)
            if i%64==0:print(label,i+1,'/',steps,flush=True)
            i+=1
        status={'completed':True,'accepted_steps':i,'frames':count,'instrumented_CPU_wall_s':time.monotonic()-start}
    except (ValueError,FloatingPointError,ArithmeticError) as exc:
        status={'completed':False,'frames':count,'error':str(exc),'instrumented_CPU_wall_s':time.monotonic()-start}
    finally:frames.close();ledger.close();rejected.close()
    (folder/'status.json').write_text(json.dumps(status,indent=2)+'\n');print(label,status,flush=True)
    return status


def initial(grid,kind):
    zero=np.zeros((grid.ny,grid.nx))
    if kind in ['translation','shear']:
        alpha=circle_fraction(grid,[(.07,.05)],.018);u=np.full_like(alpha,.1)
        v=np.broadcast_to((.01 if kind=='shear' else 0)*np.sin(2*np.pi*grid.x/grid.lx),u.shape).copy()
    elif kind=='wave':
        alpha,u,v,_=wave_reference(grid,.05,.00005,0.)
    elif kind=='collision':
        alpha=circle_fraction(grid,[(.065,.05),(.135,.05)],.02)
        x=np.arange(grid.nx+1)*grid.hx;y=np.arange(grid.ny+1)*grid.hy
        psi=.2/(2*np.pi/grid.ly)*np.sin(2*np.pi*x[None,:]/grid.lx)*np.sin(2*np.pi*(y[:,None]-.05)/grid.ly)
        u=(psi[1:,1:]-psi[:-1,1:])/grid.hy;v=-(psi[1:,1:]-psi[1:,:-1])/grid.hx;v[-1]=0
    else:raise ValueError('unknown initial state')
    return State(alpha,u,v,zero)


def operators(root):
    folder=root/'operators';folder.mkdir();records=[];source=snapshot(folder)
    for n in [16,32,64]:
        grid=Grid(2*n,n);rho=grid.rho_liquid
        for fraction in [0.,.25,.5,.75]:
            depth=.05+fraction*grid.hy
            a=interface_fraction(grid,lambda x:np.full_like(x,depth));u=np.zeros_like(a);v=np.full_like(a,-9.81*.002);v[-1]=0
            outu,outv,p,record=grid.project(a,u,v,.002)
            exact=np.where(grid.y[:,None]<depth,grid.rho_gas*9.81*(grid.ly-depth)+rho*9.81*(depth-grid.y[:,None]),grid.rho_gas*9.81*(grid.ly-grid.y[:,None]))
            exact=np.broadcast_to(exact,a.shape).copy();exact-=exact.mean()
            # Pressure values outside the mixed cell are independent continuum
            # point samples; the mixed-cell error is reported separately.
            bulk=(a>.999999)|(a<.000001)
            bed=float((p[0]+.5*grid.hy*rho*9.81).mean());lid=float((p[-1]-.5*grid.hy*grid.rho_gas*9.81).mean())
            weight=9.81*grid.volume*grid.density(a).sum()
            result={'ny':n,'fraction':fraction,'pressure_error':float(np.linalg.norm((p-exact)[bulk])/np.linalg.norm(exact[bulk])),
                'hydrostatic_speed_max':float(max(abs(outu).max(),abs(outv).max())),
                'force_relative_error':float(abs((bed-lid)*grid.lx/weight-1)),**record}
            label=f'hydro-n{n}-fraction{fraction}';np.savez_compressed(folder/(label+'.npz'),alpha=a,u=outu,v=outv,p=p,exact=exact);records.append(result)
    # Deliberately mismatch material and momentum mass fluxes in one control.
    grid=Grid(32,16,periodic_y=True);a=circle_fraction(grid,[(.07,.05)],.018);u=np.full_like(a,.1);v=np.zeros_like(a);dt=.005
    b,mx,my=phase_transport(a,u,v,dt,grid);rx,ry=grid.face_density(a);rx1,ry1=grid.face_density(b)
    for consistent in [True,False]:
        du,dv=momentum_rate(u,v,mx if consistent else rx*u,my if consistent else ry*v,grid)
        ut=(rx*u+dt*du)/rx1;vt=(ry*v+dt*dv)/ry1
        np.savez_compressed(folder/f'mass-flux-consistent{consistent}.npz',alpha=a,after_alpha=b,u=ut,v=vt)
        records.append({'mass_flux_consistent':consistent,'uniform_velocity_error_max':float(max(abs(ut-.1).max(),abs(vt).max()))})
    (folder/'results.json').write_text(json.dumps({'records':records,'source_sha256':source},indent=2)+'\n')


def run(root,group):
    root.mkdir(exist_ok=True)
    if group=='operators':operators(root);return
    if group=='transport':
        for method in ['muscl','geometric']:
            for n in [32,64,128]:
                grid=Grid(n,n//2,periodic_y=True);s=initial(grid,'translation')
                case(root,f'translation-{method}-n{n}',grid,s,2.,5*n,method=method,transport_only=True)
        return
    if group=='shear':
        for n in [32,64,128]:
            grid=Grid(n,n//2,periodic_y=True)
            case(root,f'shear-geometric-n{n}',grid,initial(grid,'shear'),2.,5*n,shear=.01)
        return
    if group=='wave':
        for n in [32,64,128]:
            grid=Grid(n,n//2);T=2*np.pi/wave_frequency(grid,.05)
            case(root,f'wave-midpoint-n{n}',grid,initial(grid,'wave'),T,8*n,gravity=9.81)
        return
    if group=='time':
        grid=Grid(64,32);T=2*np.pi/wave_frequency(grid,.05)
        for factor in [4,16]:case(root,f'wave-midpoint-n64-steps{factor*64}',grid,initial(grid,'wave'),T,factor*64,gravity=9.81)
        case(root,'wave-euler-n64',grid,initial(grid,'wave'),T,8*64,gravity=9.81,integrator='euler')
        return
    if group=='collision':
        for n in [32,64,128]:
            grid=Grid(n,n//2);dt=.2*min(grid.hx,grid.hy)/.2;steps=math.ceil(.15/dt)
            case(root,f'collision-midpoint-n{n}',grid,initial(grid,'collision'),.15,steps)
        return
    raise ValueError('unknown campaign group')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('group',choices=['operators','transport','shear','wave','time','collision']);a=p.parse_args();run(a.root,a.group)
