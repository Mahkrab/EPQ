# /// script
# dependencies = ["numpy==2.5.4", "scipy==1.18.1"]
# ///
"""Test a variational Newtonian strain operator against exact channel modes.

Only real fluid cells enter the dissipation quadrature. Mirror velocities
constrain solid traction; free surfaces retain the natural weak boundary term.
The Hermitian adjoint is formed explicitly, so physical and time errors remain
separate from implementation and energy-sign mistakes.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
from scipy.linalg import eigh


def mirror(index, count, lower, upper):
    sign=np.ones(3);coordinate=np.ones(3)
    for _ in range(16):
        if 0<=index<count:return index,sign,coordinate
        bc=lower if index<0 else upper
        if bc=='natural':return None
        if bc not in ('slip','noslip'):raise ValueError('unknown boundary')
        sign*=np.array([1,-1,1]) if bc=='slip' else -1
        coordinate[1]*=-1
        index=-index-1 if index<0 else 2*count-index-1
    raise ValueError('too many mirror images')


def gradient(count,dx,support,kx,kz,lower,upper,details=False):
    q=int(np.ceil(support));h=support*dx
    axis=np.arange(-q,q+1)
    integer=np.stack(np.meshgrid(axis,axis,axis,indexing='ij'),axis=-1).reshape((-1,3))
    r=integer*dx;radius=np.linalg.norm(r,axis=1);valid=(radius>0)&(radius<h)
    integer,r,radius=integer[valid],r[valid],radius[valid]
    # The common kernel coefficient cancels in the moment correction.
    weight=(1-radius/h)**3
    g=np.zeros((9*count,3*count),dtype=complex);conditions=[];neighbours=[]
    for i in range(count):
        rows=[];moment=np.zeros((3,3))
        for off,rr,w in zip(integer,r,weight):
            mapped=mirror(i+int(off[1]),count,lower,upper)
            if mapped is None:continue
            rows.append((rr,w,mapped));moment+=w*np.outer(rr,rr)
        values=np.linalg.eigvalsh(moment)
        if values[0]<=0 or values[-1]/values[0]>1e6:raise ValueError('rank-deficient velocity gradient')
        conditions.append(float(values[-1]/values[0]));inverse=np.linalg.inv(moment)
        local=[]
        for rr,w,(j,sign,coordinate) in rows:
            b=inverse@(w*rr);local.append((rr,b,j,sign,coordinate));phase=np.exp(1j*(kx*rr[0]+kz*rr[2]))
            for component in range(3):
                for derivative in range(3):
                    row=9*i+3*component+derivative
                    g[row,3*j+component]+=b[derivative]*sign[component]*phase
                    g[row,3*i+component]-=b[derivative]
        neighbours.append(local)
    strain=(g+g.reshape(count,3,3,3*count).swapaxes(1,2).reshape(9*count,3*count))/2
    return (g,strain,conditions,neighbours) if details else (g,strain,conditions)


def edge_matrix(count,dx,support,kx,kz,lower,upper,nu):
    g,d,conditions,neighbours=gradient(count,dx,support,kx,kz,lower,upper,details=True)
    matrix=np.zeros((3*count,3*count),dtype=complex)
    for i,local in enumerate(neighbours):
        weights=np.array([(1-np.linalg.norm(rr)/(support*dx))**4*(1+4*np.linalg.norm(rr)/(support*dx)) for rr,_,_,_,_ in local]);weights/=weights.sum()
        for weight,(rr,b,j,sign,coordinate) in zip(weights,local):
            phase=np.exp(1j*(kx*rr[0]+kz*rr[2]));r2=np.dot(rr,rr)
            own=g[9*i:9*i+9].reshape(3,3,3*count)
            neighbour=g[9*j:9*j+9].reshape(3,3,3*count)*sign[:,None,None]*coordinate[None,:,None]*phase
            average=(own+neighbour)/2
            difference=np.zeros((3,3*count),dtype=complex)
            for component in range(3):difference[component,3*j+component]+=phase*sign[component];difference[component,3*i+component]-=1
            residual=difference-np.einsum('abk,b->ak',average,rr)
            edge=average+np.einsum('ak,b->abk',residual,rr/r2)
            strain=((edge+edge.swapaxes(0,1))/2).reshape(9,3*count)
            matrix+=2*nu*weight*(strain.conj().T@strain)
    return matrix,conditions


def evaluate(layers,mode,support=2,nu=.001,H=.05,L=.2,method='edge'):
    dx=H/layers;y=(np.arange(layers)+.5)*dx
    if mode=='horizontal-natural':lower=upper='natural';kz=2*np.pi/L;ky=0;profile=np.ones(layers)
    elif mode=='horizontal-slip':lower=upper='slip';kz=2*np.pi/L;ky=0;profile=np.ones(layers)
    elif mode=='vertical-slip':lower=upper='slip';kz=0;ky=np.pi/H;profile=np.cos(ky*y)
    elif mode=='vertical-noslip':lower=upper='noslip';kz=0;ky=np.pi/H;profile=np.sin(ky*y)
    elif mode=='vertical-mixed':lower='noslip';upper='natural';kz=0;ky=np.pi/(2*H);profile=np.sin(ky*y)
    else:raise ValueError('unknown mode')
    if method=='edge':matrix,condition=edge_matrix(layers,dx,support,0,kz,lower,upper,nu)
    elif method=='nodal':
        g,d,condition=gradient(layers,dx,support,0,kz,lower,upper);matrix=2*nu*d.conj().T@d
    else:raise ValueError('unknown strain quadrature')
    values,vectors=eigh(matrix);rate=nu*(ky*ky+kz*kz);duration=1/rate
    initial=np.zeros(3*layers,dtype=complex);initial[::3]=profile
    coefficients=vectors.conj().T@initial;samples=[]
    for time in np.linspace(0,2*duration,41):
        velocity=vectors@(np.exp(-values*time)*coefficients)
        expected=initial*np.exp(-rate*time)
        amplitude=float(np.vdot(initial,velocity).real/np.vdot(initial,initial).real)
        acceleration=-matrix@velocity
        samples.append({'time':float(time),'velocity_real':velocity.real.tolist(),'velocity_imag':velocity.imag.tolist(),
            'amplitude':amplitude,'analytic_amplitude':float(np.exp(-rate*time)),
            'L2_error_over_initial':float(np.linalg.norm(velocity-expected)/np.linalg.norm(initial)),
            'kinetic_per_amplitude_squared':float(np.vdot(velocity,velocity).real/(2*layers)),
            'force_per_kg':acceleration.reshape(layers,3).mean(axis=0).real.tolist()})
    final=samples[20];amplitude=final['amplitude'];observed_rate=-np.log(amplitude)/duration
    if mode in ['vertical-noslip','vertical-mixed']:
        exact_mean=2/np.pi;force_expected=-rate*exact_mean
        force_observed=float((-matrix@initial)[::3].mean().real)
        traction_error=abs(force_observed-force_expected)/abs(force_expected)
    else:force_expected=force_observed=traction_error=0.
    return {'method':method,'layers':layers,'mode':mode,'support':support,'nu':nu,'H':H,'L':L,'dx':dx,'decay_time':duration,
        'max_condition':max(condition),'min_eigenvalue':float(values[0]),'max_eigenvalue':float(values[-1]),
        'amplitude_relative_error_at_tau':amplitude/np.exp(-1)-1,'rate_relative_error':observed_rate/rate-1,
        'L2_over_initial_at_tau':final['L2_error_over_initial'],'traction_relative_error_initial':traction_error,
        'force_expected_initial':force_expected,'force_observed_initial':force_observed,'samples':samples}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('output',type=Path);args=parser.parse_args()
    records=[]
    for mode in ['horizontal-natural','horizontal-slip','vertical-slip','vertical-noslip','vertical-mixed']:
        for layers in [2,4,8,12,16,24]:
            r=evaluate(layers,mode);records.append(r)
            print(mode,layers,'amplitude',round(r['amplitude_relative_error_at_tau'],5),'rate',round(r['rate_relative_error'],5),'traction',round(r['traction_relative_error_initial'],5),flush=True)
    import hashlib
    with args.output.open('x') as f:json.dump({'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'records':records},f,indent=2);f.write('\n')


if __name__=='__main__':main()
