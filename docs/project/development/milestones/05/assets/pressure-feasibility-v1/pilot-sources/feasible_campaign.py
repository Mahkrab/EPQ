# /// script
# dependencies = ["numpy==2.5.4", "scipy==1.18.1"]
# ///
"""Retain mathematical candidate screens before pressure-stage timing admission."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from tools.performance.feasible_pressure import mac,metrics
from tools.performance.feasible_volume import volume_screen,wls_screen


def run(root):
    folder=root/'mathematics';folder.mkdir();results=[]
    for n in [4,8,12,16]:
        for fraction in [1.,.37,.1]:
            grid=mac((4*n,n,4*n),fraction=fraction);s,a=metrics(grid);label=f'mac-n{n}-fraction{fraction}'
            with (folder/(label+'.npz')).open('xb') as f:np.savez_compressed(f,**a)
            s.update({'candidate':'mac','label':label,'fraction':fraction});results.append(s);print(label,s,flush=True)
    for n in [4,8,12]:
        s,a=metrics(mac((4*n,n,4*n),kind='periodic'));label=f'mac-periodic-n{n}'
        with (folder/(label+'.npz')).open('xb') as f:np.savez_compressed(f,**a)
        s.update({'candidate':'mac-periodic','label':label});results.append(s);print(label,s,flush=True)
    for n in [8,16,32]:
        for jitter in [0.,.1]:
            for name,function in [('unweighted-volume',volume_screen),('wls-adjoint',wls_screen)]:
                s,a=function(n,jitter);label=f'{name}-n{n}-jitter{jitter}'
                with (folder/(label+'.npz')).open('xb') as f:np.savez_compressed(f,**a)
                s.update({'candidate':name,'label':label});results.append(s);print(label,s,flush=True)
    with (root/'mathematics.json').open('x') as f:json.dump({'records':results,'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('feasible_*.py')}},f,indent=2,allow_nan=False);f.write('\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);run(p.parse_args().root)
