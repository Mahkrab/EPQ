# /// script
# dependencies = ["numpy==2.5.4", "scipy==1.18.1"]
# ///
"""Reproduce one complete rejected wave case with the final standalone sources."""
import argparse
import json
from pathlib import Path
import numpy as np
from tools.performance.coupled_grid import Grid
from tools.performance.coupled_campaign import initial,case
from tools.performance.coupled_reference import wave_frequency
from tools.performance.coupled_audit import frames,assess


def run(root):
    folder=root/'reproduction';folder.mkdir();grid=Grid(32,16);T=2*np.pi/wave_frequency(grid,.05)
    case(folder,'wave-midpoint-n32',grid,initial(grid,'wave'),T,256,gravity=9.81)
    current=folder/'wave-midpoint-n32';original=root/'geometry-stable/wave-midpoint-n32'
    state0=next(reversed([(r,a) for _,_,r,a in frames(original) if r['kind']=='accepted']))[1]
    state1=next(reversed([(r,a) for _,_,r,a in frames(current) if r['kind']=='accepted']))[1]
    difference=np.max(abs(state1-state0),axis=(1,2))
    receipt={'fields':['alpha','u','v','p'],'maximum_absolute_differences':difference.tolist(),
        'limits':[1e-9,1e-9,1e-9,1e-6],'physical_acceptance_unchanged':True,
        'interpretation':'Reproducibility tolerances, not physical pass thresholds. The reproduced wave must still fail its original gates.'}
    result=assess(current);receipt['reproduced_physical_pass']=result['physical_pass']
    receipt['reproduction_pass']=bool(np.all(difference<np.array(receipt['limits'])) and not result['physical_pass'])
    (folder/'readback.json').write_text(json.dumps(receipt,indent=2)+'\n')
    if not receipt['reproduction_pass']:raise ValueError('wave reproduction differs')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);run(p.parse_args().root)
