# /// script
# dependencies = ["numpy==2.5.4", "scipy==1.18.1"]
# ///
"""Diagnose collisions with a valid evolving-velocity CFL policy.

The original fixed-step failures remain separate. This changes timestep selection
only; it does not damp velocities or alter the pressure/interface formulation.
"""
import argparse
import math
from pathlib import Path
from tools.performance.coupled_grid import Grid
from tools.performance.coupled_campaign import initial,case


def run(root):
    folder=root/'adaptive-collision';folder.mkdir()
    for n,cfl in [(32,.2),(64,.2),(128,.2),(64,.1),(64,.05)]:
        grid=Grid(n,n//2);steps=math.ceil(.15/(.2*min(grid.hx,grid.hy)/.2))
        case(folder,f'collision-n{n}-cfl{cfl}',grid,initial(grid,'collision'),.15,steps,adaptive_cfl=cfl)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);run(p.parse_args().root)
