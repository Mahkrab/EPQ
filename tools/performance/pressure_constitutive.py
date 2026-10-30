# /// script
# dependencies = ["numpy==2.5.4", "scipy==1.18.1"]
# ///
"""Test the pressure constraint's artificial shear modulus without fitting it.

The kernel Hessian on an infinite, affinely sheared lattice predicts the
long-wave pressure force in a different periodic sinusoidal manufactured map.
An incompressible fluid has zero pressure work for either isochoric map.
"""
import argparse
from pathlib import Path
import numpy as np
from tools.performance.pressure_operator import assemble,kernel_and_gradient
from tools.performance.pressure_campaign import write_json


def curvature(support,dx=.01):
    h=support*dx;axis=np.arange(-int(np.ceil(support))-1,int(np.ceil(support))+2)*dx
    points=np.stack(np.meshgrid(axis,axis,axis,indexing='ij'),axis=-1).reshape(-1,3)
    radius=np.linalg.norm(points,axis=1);valid=(radius>0)&(radius<h);r=points[valid];radius=radius[valid];t=1-radius/h
    coefficient=21/(2*np.pi*h**3)
    hessian_xx=-20*coefficient/h**2*(t**3-3*t**2*r[:,0]**2/(h*radius))
    value=float(dx**3*np.sum(hessian_xx*r[:,1]**2))
    base=kernel_and_gradient(points,h,dx**3)[0].sum();samples=[]
    for shear in [-.1,-.01,-.001,0.,.001,.01,.1]:
        p=points.copy();p[:,0]+=shear*p[:,1]
        samples.append({'shear':shear,'C_minus_rest':float(kernel_and_gradient(p,h,dx**3)[0].sum()-base)})
    epsilon=.001
    fd=(samples[2]['C_minus_rest']+samples[4]['C_minus_rest'])/epsilon**2
    return {'support':support,'dimensionless_shear_curvature':value,'finite_difference_curvature':float(fd),
        'G_at_mean_hydrostatic_Pa':value*(1000*9.81*.05/2),'samples':samples}


def run(root):
    folder=root/'constitutive';folder.mkdir();coefficients=[curvature(q) for q in [2,3,4,6,8]];records=[]
    for q,n in [(2,12),(2,24),(2,32),(2,64),(3,32),(3,64),(4,32),(4,64)]:
        op=assemble(n,q,.001,'periodic',profile='periodic');b=next(r['dimensionless_shear_curvature'] for r in coefficients if r['support']==q)
        pressure_over_rho=9.81*.05;actual=-(op.jacobian.T@np.full(n,pressure_over_rho)).reshape(n,3)[:,0]
        k=2*np.pi/.05;predicted=-pressure_over_rho*b*k*k*op.positions[:,0]
        error=float(np.linalg.norm(actual-predicted)/np.linalg.norm(predicted))
        record={'layers':n,'support':q,'gamma':.001,'curvature_from_independent_affine_lattice':b,
            'predicted_force_L2_relative_error':error,'measured_over_predicted_mode_force':float(np.dot(actual,predicted)/np.dot(predicted,predicted))}
        records.append(record);np.savez_compressed(folder/f'n{n}-q{q}.npz',positions=op.positions,J=op.jacobian,actual_ax=actual,predicted_ax=predicted)
        print(q,n,'predicted/observed relative error',error,flush=True)
    write_json(root/'constitutive-results.json',{'derivation':'C_affine(gamma)=C0+.5*b*gamma^2+O(gamma^4). Pressure potential density P*C therefore adds artificial shear modulus G=P*b. Its long-wave constant-P acceleration is ax=(P/rho)*b*d2S/dy2. b is independently computed from the C2 Hessian, never fitted to sinusoidal force or coupled data.','coefficients':coefficients,'records':records})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);run(p.parse_args().root)
