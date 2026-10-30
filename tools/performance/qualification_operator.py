# /// script
# dependencies = ["numpy==2.5.4"]
# ///
"""Separate slab stencil error from time integration using matrix exponentials.

This independently forms the Fourier-reduced operator from the analytic C2
radial derivative, rather than importing the native pair routine or fitting
an effective viscosity. Its exponential is an exact discrete-time reference.
"""
import argparse
import json
from pathlib import Path
import numpy as np


def check(root):
    records=json.loads((root/'slab-spatial-convergence.json').read_text())['records'];checks=[]
    for r in records:
        n,layers=r['n'],r['layers'];dx=.6/n;h=4*dx;nu=.001
        axis=np.arange(-4,5)*dx
        xyz=np.stack(np.meshgrid(axis,axis,axis,indexing='ij'),axis=-1).reshape((-1,3))
        radii=np.linalg.norm(xyz,axis=1);valid=(radii>0)&(radii<h);xyz=xyz[valid];radii=radii[valid]
        derivative=-20*(21/(2*np.pi*h**3))*radii/h**2*(1-radii/h)**3
        weights=-10*nu*dx**3*derivative/radii*xyz[:,0]**2/radii**2
        offsets=np.rint(xyz[:,1]/dx).astype(int)
        matrix=np.zeros((layers,layers))
        for y in range(layers):
            for dy in range(-4,5):
                other=y+dy
                if not 0<=other<layers:continue
                mask=offsets==dy
                matrix[y,other]+=np.sum(weights[mask]*np.cos(2*np.pi*xyz[mask,2]/.6))
                matrix[y,y]-=np.sum(weights[mask])
        values,vectors=np.linalg.eigh(matrix);dt=r['dt'];time=r['samples'][-1]['time'];steps=round(time/dt)
        initial=vectors.T@np.ones(layers)
        exact=vectors@(np.exp(values*time)*initial)
        euler=vectors@((1+dt*values)**steps*initial)
        observed=np.array(r['samples'][-1]['amplitudes'])
        checks.append({'n':n,'layers':layers,'euler_eigenvalue_radius':float(np.max(np.abs(1+dt*values))),
            'native_vs_independent_euler_max':float(np.max(np.abs(observed-euler))),
            'native_vs_exact_discrete_operator_max':float(np.max(np.abs(observed-exact))),
            'exact_discrete_operator_physical_amplitude_error':float(exact.mean()/np.exp(-1)-1)})
    if any(r['euler_eigenvalue_radius']>1 or r['native_vs_independent_euler_max']>1e-9 for r in checks):raise ValueError('slab stencil/time integration verification failed')
    (root/'slab-independent-matrix-checks.json').write_text(json.dumps(checks,indent=2)+'\n')
    print(json.dumps(checks,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path);check(parser.parse_args().root)
