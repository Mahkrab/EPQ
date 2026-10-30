# /// script
# dependencies = ["numpy==2.5.4", "scipy==1.18.1"]
# ///
"""Separate timestep/solve error from spatial error and geometric cell motion."""
import argparse
import json
from pathlib import Path
import numpy as np
from tools.performance.feasible_pressure import mac,analytic_pressure
from tools.performance.feasible_volume import points,partition


def run(root):
    folder=root/'policy';folder.mkdir();records=[]
    grid=mac((32,8,32),fraction=.37)
    shear=np.where(grid.axis==0,.5*np.sin(2*np.pi*grid.position[:,2]/.2),0.)
    _,gradient=analytic_pressure(grid.position);force=gradient[np.arange(len(grid.axis)),grid.axis]/1000
    exact,_=analytic_pressure(grid.cells)
    for dt in [.004,.002,.001,.0005]:
        for tol in [1e-4,1e-6,1e-8,1e-10]:
            predicted=shear+dt*force;v,p,history=grid.project(predicted,dt,tolerance=tol)
            records.append({'dt':dt,'tolerance':tol,'iterations':len(history),'true_residual':float(history[-1]),
                'pressure_relative_error':float(np.linalg.norm(p-exact)/np.linalg.norm(exact)),
                'shear_relative_error':float(np.linalg.norm(v-shear)/np.linalg.norm(shear)),
                'energy_change_J':float(.5*np.sum(grid.mass*(v*v-predicted*predicted)))})
            np.savez_compressed(folder/f'dt{dt}-tol{tol}.npz',p=p,v=v,history=history,predicted=predicted)
    geometry=[]
    for n in [8,16,32]:
        sites=points(n,.1);initial,_=partition(sites)
        for strain in [1e-3,1e-5]:
            plus,_=partition(sites,np.array([[1,strain],[0,1.]]));minus,_=partition(sites,np.array([[1,-strain],[0,1.]]))
            rate=(plus-minus)/(2*strain*initial)
            geometry.append({'n':n,'strain':strain,'affine_fractional_volume_rate_rms':float(np.sqrt(np.mean(rate*rate)))})
            np.savez_compressed(folder/f'volume-n{n}-strain{strain}.npz',sites=sites,initial_area=initial,plus=plus,minus=minus,fractional_rate=rate)
    (root/'policy.json').write_text(json.dumps({'records':records,'geometry':geometry,'scope':'Static geometry pressure only; no advection temporal truncation tested.'},indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path);run(parser.parse_args().root)
