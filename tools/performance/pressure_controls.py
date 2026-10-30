# /// script
# dependencies = ["numpy==2.5.4", "scipy==1.18.1"]
# ///
"""Reproduce the small-strain, neighbour and multiplier attribution controls."""
import argparse
import gzip
import json
from pathlib import Path
import numpy as np
from tools.performance.pressure_operator import assemble,manufactured
from tools.performance.pressure_audit import trace,layer_coordinates
from tools.performance.pressure_campaign import write_json


def run(root,output,legacy):
    output.mkdir(parents=True,exist_ok=True);folder=output/'gauge-and-neighbours';folder.mkdir();records=[]
    for n in [12,24]:
        initial=assemble(n,2,0,'periodic',profile='periodic')
        for gamma in [.001,.01,.1,.3]:
            full=assemble(n,2,gamma,'periodic',profile='periodic')
            frozen=assemble(n,2,gamma,'periodic',profile='periodic',frozen_edges=initial.edges)
            for name,op in [('refreshed',full),('frozen-at-zero',frozen)]:
                s,a=manufactured(op,gamma,'periodic',profile='periodic')
                s.update({'graph':name,'positive_constraints':int(np.sum(op.constraint>0)),'constraint_mean':float(op.constraint.mean())})
                active=op.jacobian[op.constraint>0];_,sv,right=np.linalg.svd(active,full_matrices=False);keep=sv>1e-12*sv[0];u=a['velocity'].ravel()
                s['positive_constraint_projection_loss']=float(np.sum((right[keep]@u)**2)/np.dot(u,u))
                epsilon=op.dx*1e-6;direction=np.zeros_like(op.positions);direction[:,0]=np.sin(np.arange(n)*.123);direction[:,1]=np.cos(np.arange(n)*.345)
                values=[]
                for sign in [1,-1]:values.append(assemble(n,2,gamma,'periodic',profile='periodic',frozen_edges=initial.edges if name=='frozen-at-zero' else None,layer_positions=op.positions+sign*epsilon*direction).constraint)
                finite=(values[0]-values[1])/(2*epsilon)
                s['layer_J_finite_difference_error_per_m']=float(np.max(np.abs(finite-op.jacobian@direction.ravel())))
                with (folder/f'n{n}-g{gamma}-{name}.npz').open('xb') as stream:np.savez_compressed(stream,**a,FD=finite,direction=direction)
                records.append(s)
    write_json(output/'gauge-and-neighbour-results.json',{'records':records,'note':'Zero-mean row equation removal is an offline attribution control, not an implemented replacement. Positive constraints are explicitly counted; at q2 all periodic manufactured rows are compression-active.'})
    decompositions=[]
    for label in ['base','replay','n12']:
        par=json.loads((root/'native'/(label+'.request.json')).read_text())['parameters'];n=par['n'];nx=4*n;dx=.05/n;phi=np.sin(np.pi*(np.arange(n)+.5)*dx/.1);den=phi@phi;parts=[]
        for _,iteration,p,c,load,delta in trace(root/'native'/(label+'.ledger.trace')):
            op=assemble(n,par['support'],0,'free',layer_positions=layer_coordinates(p,n,dx));force=(.5*op.jacobian.T@np.full(n,float(load.mean()))).reshape(n,3)
            actual=delta.reshape(nx,n,nx,3).mean((0,2));total=float(phi@actual[:,0]/den/par['dt']);constant=float(phi@force[:,0]/den/par['dt'])
            parts.append({'iteration':iteration,'total_pressure_mode_delta_v':total,'constant_multiplier_component':constant,'nonconstant_multiplier_component':total-constant})
        decompositions.append({'label':label,'pressure_mode_delta_v':sum(p['total_pressure_mode_delta_v'] for p in parts),'constant_multiplier_component':sum(p['constant_multiplier_component'] for p in parts),'nonconstant_multiplier_component':sum(p['nonconstant_multiplier_component'] for p in parts),'records':parts})
    write_json(output/'multiplier-attribution.json',{'records':decompositions,'interpretation':'An algebraic force decomposition of the unchanged native pressure step. Removing the mean would change free-surface pressure/normal traction and is NOT proposed as a solver fix.'})
    steps=list(trace(root/'native/replay.ledger.trace'));dt=1/480
    mean_pressure=-1000*.5*sum(float(s[4].mean()) for s in steps)/dt**2
    write_json(output/'replay-pressure-scale.json',{'effective_mean_pressure_Pa':mean_pressure,'hydrostatic_continuum_mean_Pa':1000*9.81*.05/2,'definition':'-rho*correction_scale*sum_iteration(mean(lambda))/dt^2. Pressure scale only; individual Jacobians evolve within step.','note':'Not used to fit the independent kernel shear curvature or sinusoidal manufactured-force prediction.'})
    if legacy is not None:
        with gzip.open(legacy/'coupled/modal-mixed-n4-g9.81.ledger.gz','rt') as stream:old=[json.loads(s) for s in stream][96]
        index=np.arange(1024);y=((index//16)%4+.5)*.0125;shape=np.sin(np.pi*y/.1)
        measured=sum(float(shape@s[5][:,0]/1024/dt) for s in steps);expected=old['reconstructed']['modal_projection']-old['prediction']['modal_projection']
        write_json(output/'retained-failure-replay.json',{'retained_source_step':97,'retained_time_start':.2,'native_pressure_only_modal_change':measured,'prior_complete_model_pressure_modal_change':expected,'absolute_difference':abs(measured-expected),'interpretation':'New pressure-only replay reproduces the actual failing full-model pressure stage; preceding viscosity is in initial state but disabled during this step; contact had no activity. Instrumentation association, not a physical correctness oracle.'})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path);parser.add_argument('output',type=Path);parser.add_argument('--legacy',type=Path);a=parser.parse_args();run(a.root,a.output,a.legacy)
