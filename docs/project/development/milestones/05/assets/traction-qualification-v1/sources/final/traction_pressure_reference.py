# /// script
# dependencies = ["numpy==2.5.4"]
# ///
"""Measure pressure quadrature on an exactly volume-preserving sheared lattice.

Continuum density is unchanged and a pressure depending only on height has no
tangential gradient. This calculation has no timestep, PBF iterations, boundary
samples, viscosity or fitted coefficients.
"""
import argparse
import json
from pathlib import Path
import numpy as np


def lattice(spacing,support,shear):
    h=spacing*support;extent=int(np.ceil(3*support))
    axis=np.arange(-extent,extent+1)*spacing
    r=np.stack(np.meshgrid(axis,axis,axis,indexing='ij'),axis=-1).reshape(-1,3)
    r[:,0]+=shear*r[:,1];radius=np.linalg.norm(r,axis=1);r=r[radius<h];radius=radius[radius<h]
    t=1-radius/h;coefficient=21/(2*np.pi*h**3)
    rho=1000*spacing**3*np.sum(coefficient*t**4*(5-4*t))
    derivative=-20*coefficient/h**2*t[:,None]**3*r
    moment=-spacing**3*derivative.T@r
    return rho,moment


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('output',type=Path);a=parser.parse_args();records=[]
    for spacing in [.01,.005]:
        for support in [2,3,4,6,8]:
            base,_=lattice(spacing,support,0);samples=[]
            for shear in [0,.01,.05,.1,.2,.3,.5,.75,1.]:
                rho,moment=lattice(spacing,support,shear)
                samples.append({'shear':shear,'detF':1.,'constraint':float((rho-base)/1000),
                    'pressure_gradient_moment':moment.tolist(),
                    'tangential_over_normal_pressure_force':float(moment[0,1]/moment[1,1]),
                    'continuum_expected_moment':[[1,0,0],[0,1,0],[0,0,1]]})
            records.append({'spacing':spacing,'support_over_spacing':support,'bias_kg_m3':float(base-1000),'samples':samples})
    with a.output.open('x') as stream:json.dump({'reference':__doc__,'records':records},stream,indent=2);stream.write('\n')


if __name__=='__main__':main()
