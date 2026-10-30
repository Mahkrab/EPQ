# /// script
# dependencies = ["numpy==2.5.4", "scipy==1.18.1"]
# ///
"""Check every native pressure action against independent layer derivatives."""
from __future__ import annotations
import argparse
import gzip
import json
from pathlib import Path
import struct
import numpy as np
from tools.performance.pressure_operator import assemble
from tools.performance.spatial_audit import frames
from tools.performance.traction_audit import periodic_density
from tools.performance.qualification_audit import calibration_constants
from tools.performance.pressure_campaign import write_json


def binary_stream(path):
    if path.exists():return gzip.open(path,'rb') if path.suffix=='.gz' else path.open('rb')
    packed=Path(str(path)+'.gz')
    if packed.exists():return gzip.open(packed,'rb')
    raise FileNotFoundError(path)


def trace(path):
    with binary_stream(path) as stream:
        header=stream.read(60)
        if len(header)!=60:raise ValueError('truncated pressure trace header')
        magic,n,iterations=struct.unpack('<3I',header[:12]);parameters=struct.unpack('<6d',header[12:])
        if magic!=0x50524431 or not 0<n<=100000 or iterations>128:raise ValueError('invalid pressure trace')
        for iteration in range(iterations):
            block=stream.read(n*64)
            if len(block)!=n*64:raise ValueError('truncated pressure iteration')
            a=np.frombuffer(block,dtype='<f8');p=a[:3*n].reshape(n,3);c=a[3*n:4*n];load=a[4*n:5*n];correction=a[5*n:].reshape(n,3)
            yield parameters,iteration,p.copy(),c.copy(),load.copy(),correction.copy()
        if stream.read(1):raise ValueError('unexpected trace tail')


def layer_coordinates(p,ny,dx):
    nx=4*ny;rows=p.reshape(nx,ny,nx,3);x=(np.arange(nx)+.5)*dx
    phase=rows[:,:,:,0]-x[:,None,None]
    shifts=np.angle(np.mean(np.exp(2j*np.pi*phase/.2),axis=(0,2)))*.2/(2*np.pi)
    result=np.column_stack((shifts,rows[:,:,:,1].mean(axis=(0,2)),np.zeros(ny)))
    return result


def sparse_check(path,n,ny,load,actual):
    reduced=np.zeros((ny,3*ny));diag=np.zeros(ny);action=np.zeros((n,3));c=[];nx=4*ny
    directions=np.sin(np.arange(n*3).reshape(n,3)*.123)
    directional=[]
    with binary_stream(path) as stream:
        if struct.unpack('<I',stream.read(4))[0]!=n:raise ValueError('Jacobian count differs')
        dtype=np.dtype([('target','<u4'),('g','<f8',(3,))])
        for i in range(n):
            value,multiplier,count=struct.unpack('<ddI',stream.read(20));c.append(value)
            block=stream.read(28*count)
            if len(block)!=28*count:raise ValueError('truncated sparse Jacobian')
            row=np.frombuffer(block,dtype=dtype);targets=row['target'];g=row['g'];layer=(i//nx)%ny
            target_layer=(targets//nx)%ny
            for k in range(3):reduced[layer,k::3]+=np.bincount(target_layer,weights=g[:,k],minlength=ny)/(nx*nx)
            diag[layer]+=np.sum(g*g)/(nx*nx)
            np.add.at(action,targets,.5*multiplier*g)
            directional.append(float(np.sum(g*directions[targets])))
            if abs(multiplier-load[i])>1e-14:raise ValueError('trace and sparse multiplier differ')
        if stream.read(1):raise ValueError('unexpected sparse Jacobian tail')
    return reduced,diag,np.array(c),np.array(directional),float(np.max(np.abs(action-actual)))


def point_constraints(p,h,mass):
    ghost=p[p[:,1]<h].copy();ghost[:,1]*=-1
    rho=periodic_density(p,p,h,mass)+periodic_density(ghost,p,h,mass)
    bias,_=calibration_constants(mass,h,'self')
    return (rho-bias)/1000-1


def audit(root,destination=None):
    output=root if destination is None else destination;output.mkdir(parents=True,exist_ok=True)
    records=[];directory=root/'native';derived=output/'native-audits';derived.mkdir()
    for request_path in sorted(directory.glob('*.request.json')):
        label=request_path.name.removesuffix('.request.json');request=json.loads(request_path.read_text());par=request['parameters'];ny=par['n'];nx=4*ny;dx=.05/ny
        raw=directory/(label+'.raw');raw=raw if raw.exists() else Path(str(raw)+'.gz')
        observations=list(frames(raw))
        if len(observations)!=2 or observations[-1][2]!=1:raise ValueError('native request is not a complete one-step experiment')
        p0,v0=observations[0][3:];pf,vf=observations[-1][3:];arrays=list(trace(directory/(label+'.ledger.trace')))
        first=arrays[0];p=first[2];C=first[3];load=first[4];corr=first[5]
        Jr,diag,Cs,directional,action_error=sparse_check(directory/(label+'.ledger.jac'),len(p),ny,load,corr)
        max_action_error=0.;max_C_error=0.;max_J_error=0.;max_diag_error=0.;history=[]
        initial_graph=None
        for constants,it,positions,c,multipliers,delta in arrays:
            coordinates=layer_coordinates(positions,ny,dx)
            op=assemble(ny,par['support'],0,'free',layer_positions=coordinates,frozen_edges=initial_graph if not par['refresh'] else None)
            if it==0:initial_graph=op.edges
            rowC=c.reshape(nx,ny,nx).mean(axis=(0,2));rowLoad=multipliers.reshape(nx,ny,nx).mean(axis=(0,2))
            rowDelta=delta.reshape(nx,ny,nx,3).mean(axis=(0,2))
            predicted_delta=(.5*op.jacobian.T@rowLoad).reshape(ny,3)
            max_action_error=max(max_action_error,float(np.max(np.abs(rowDelta-predicted_delta))))
            max_C_error=max(max_C_error,float(np.max(np.abs(rowC-op.constraint))))
            if it==0:
                max_J_error=float(np.max(np.abs(Jr-op.jacobian)));max_diag_error=float(np.max(np.abs(diag-op.full_row_norm2)))
            shape=np.sin(np.pi*p0[:,1]/.1)
            history.append({'iteration':it,'p95_compression_before':float(np.quantile(np.maximum(c,0),.95)),
                'tangential_mode_correction_m':float(np.dot(shape,delta[:,0])/np.dot(shape,shape)),
                'maximum_pressure_correction_m':float(np.linalg.norm(delta,axis=1).max())})
        shape=np.sin(np.pi*p0[:,1]/.1);normalization=float(np.dot(shape,shape))
        tangent_displacement=pf[:,0]-p0[:,0]
        tangent_displacement-=np.rint(tangent_displacement/.2)*.2
        # Net tangential position change includes only free advection and pressure;
        # all viscosity/contact are disabled and plane correction is normal.
        pressure_displacement=tangent_displacement-v0[:,0]*par['dt']
        mode_delta=float(np.dot(shape,pressure_displacement)/normalization)
        finalC=point_constraints(pf,par['support']*dx,1000*dx**3)
        result={'label':label,'parameters':par,'initial_p95_compression':float(np.quantile(np.maximum(C,0),.95)),
            'final_p95_compression':float(np.quantile(np.maximum(finalC,0),.95)),
            'pressure_mode_displacement_m':mode_delta,'pressure_mode_velocity_change_m_s':mode_delta/par['dt'],
            'pressure_tangent_displacement_rms_m':float(np.sqrt(np.mean(pressure_displacement**2))),
            'net_pressure_tangent_displacement_mean_m':float(np.mean(pressure_displacement)),
            'manufactured_shear_displacement_fraction_removed':-mode_delta/(par['gamma']/(np.pi/.1)) if par['gamma'] else None,
            'sparse_native_action_error_m':action_error,'reduced_native_action_error_m':max_action_error,
            'reduced_constraint_error':max_C_error,'reduced_J_error_per_m':max_J_error,
            'reduced_diagonal_error_per_m2':max_diag_error,'history':history}
        if label in ['base','replay']:
            direction=np.sin(np.arange(p.size).reshape(p.shape)*.123);epsilon=dx*1e-6
            finite=(point_constraints(p+epsilon*direction,par['support']*dx,1000*dx**3)-point_constraints(p-epsilon*direction,par['support']*dx,1000*dx**3))/(2*epsilon)
            result['native_directional_finite_difference_error_per_m']=float(np.max(np.abs(finite-directional)))
            np.savez_compressed(derived/(label+'-finite-difference.npz'),p=p,C_native=Cs,direction=direction,finite=finite,native_directional=directional)
        np.savez_compressed(derived/(label+'.npz'),native_reduced_J=Jr,native_row_norm2=diag,initial_positions=p0,final_positions=pf,
            pressure_displacement=pressure_displacement,final_constraint=finalC)
        write_json(derived/(label+'.json'),result);records.append(result)
        print(label,'velocity correction',result['pressure_mode_velocity_change_m_s'],'C',result['final_p95_compression'],'action error',max_action_error,flush=True)
    write_json(output/'native-results.json',{'records':records})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path);parser.add_argument('--destination',type=Path);a=parser.parse_args();audit(a.root,a.destination)
