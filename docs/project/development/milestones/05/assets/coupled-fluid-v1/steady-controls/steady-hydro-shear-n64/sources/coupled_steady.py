# /// script
# dependencies = ["numpy==2.5.4", "scipy==1.18.1"]
# ///
"""Exact coupled hydrostatic/affine-shear controls with no moving interface."""
import argparse
from pathlib import Path
import numpy as np
from tools.performance.coupled_grid import Grid
from tools.performance.coupled_model import State
from tools.performance.coupled_reference import interface_fraction
from tools.performance.coupled_campaign import case


def run(root):
    folder=root/'steady-controls';folder.mkdir()
    for n in [32,64,128]:
        grid=Grid(n,n//2);a=interface_fraction(grid,lambda x:np.full_like(x,.05))
        u=np.broadcast_to(.1*(grid.y[:,None]/grid.ly-.5),a.shape).copy();zero=np.zeros_like(a)
        case(folder,f'steady-hydro-shear-n{n}',grid,State(a,u,zero,zero),.2,64,gravity=9.81)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);run(p.parse_args().root)
