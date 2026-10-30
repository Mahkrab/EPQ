# /// script
# dependencies = ["numpy==2.5.4", "scipy==1.18.1"]
# ///
"""Finite differences check the reflected pressure constraint's actual Jacobian."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import numpy as np
from tools.performance.qualification_audit import calibration_constants
from tools.performance.spatial_audit import frames, kernel


def constraints(p,dx):
    ghost=p[p[:,1]<2*dx].copy();ghost[:,1]*=-1
    images=np.concatenate([p,ghost]);d=p[:,None,:]-images[None,:,:]
    d[:,:,[0,2]]-=np.rint(d[:,:,[0,2]]/.2)*.2
    bias,_=calibration_constants(1000*dx**3,2*dx,'self')
    return (1000*dx**3*np.sum(kernel(np.linalg.norm(d,axis=2),2*dx),axis=1)-bias)/1000-1


def run(root,binary):
    root.mkdir(parents=True,exist_ok=True);dx=.0125;ny=4
    p=np.stack(np.meshgrid((np.arange(16)+.5)*dx,(np.arange(4)+.5)*dx,(np.arange(16)+.5)*dx,indexing='ij'),axis=-1).reshape(-1,3)
    p[:,0]+=.1*p[:,1];p[:,0]%=.2;p[:,1]+=.001
    p+=.015*dx*np.sin(np.arange(p.size).reshape(p.shape)*1.234)
    p[:,[0,2]]%=.2
    initial=root/'initial.bin';initial.write_bytes(struct.pack('<I',len(p))+p.astype('<f8').tobytes()+np.zeros_like(p).tobytes())
    ledger=root/'pressure.ledger';raw=root/'states.raw'
    command=[str(binary.resolve()),'channel-mixed',str(ny),'0',str(1/480),str(1/480),'1','1','0','1','self','1','0','0','1','0',str(ledger.resolve()),str(initial.resolve()),'1','2','2','geometric']
    with raw.open('xb') as output,(root/'stderr.txt').open('x') as error:subprocess.run(command,stdout=output,stderr=error,check=True,env={**os.environ,'OMP_WAIT_POLICY':'PASSIVE'})
    with (root/'pressure.ledger.jac').open('rb') as stream:
        n=struct.unpack('<I',stream.read(4))[0]
        if n!=len(p):raise ValueError('Jacobian particle count differs')
        c=[];multipliers=[];rows=[]
        for _ in range(n):
            constraint,multiplier,count=struct.unpack('<ddI',stream.read(20));row=[]
            for _ in range(count):
                target,*gradient=struct.unpack('<I3d',stream.read(28));row.append((target,np.array(gradient)))
            c.append(constraint);multipliers.append(multiplier);rows.append(row)
        if stream.read(1):raise ValueError('unexpected Jacobian trailing bytes')
    c=np.array(c);field_error=float(np.max(np.abs(c-constraints(p,dx))))
    derivative_errors=[];epsilon=dx*1e-6
    for phase in [.123,.789,1.234]:
        direction=np.sin(np.arange(p.size).reshape(p.shape)*phase)
        expected=(constraints(p+epsilon*direction,dx)-constraints(p-epsilon*direction,dx))/(2*epsilon)
        observed=np.array([sum(np.dot(g,direction[j]) for j,g in row) for row in rows])
        derivative_errors.append(float(np.max(np.abs(observed-expected))))
    tangent=max(abs(sum(g[k] for _,g in row)) for row in rows for k in [0,2])
    correction=np.zeros_like(p)
    for multiplier,row in zip(multipliers,rows):
        for j,g in row:correction[j]+=.5*multiplier*g
    final=list(frames(raw))[-1][3];action_error=float(np.max(np.abs(final-p-correction)))
    result={'command':command,'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),
        'density_absolute_error':field_error,'maximum_directional_derivative_errors_per_m':derivative_errors,
        'maximum_tangential_gradient_sum_per_m':tangent,'native_action_error_m':action_error,
        'epsilon_m':epsilon,'reference':'Independent point-kernel sum and central finite differences; three arbitrary directions include self-mirror, cross-target and normal ghost derivatives. Sheared and jittered volume sampling, no time evolution/viscosity/contact.'}
    with (root/'result.json').open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    if field_error>1e-12 or max(derivative_errors)>1e-5 or tangent>1e-10 or action_error>1e-12:raise ValueError('pressure Jacobian check failed')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path);parser.add_argument('binary',type=Path);a=parser.parse_args();print(json.dumps(run(a.root,a.binary),indent=2))
