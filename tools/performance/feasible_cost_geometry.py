# /// script
# dependencies = ["numpy==2.5.4", "scipy==1.18.1"]
# ///
"""Apply the continuum pressure gates to each proposed cost geometry before timing."""
import argparse
import json
from pathlib import Path
import numpy as np
from tools.performance.feasible_pressure import mac,metrics


def run(root):
    folder=root/'cost-geometry';folder.mkdir();records=[]
    cases=[('tank',(64,16,64),(.2,.05,.2)),('pool',(256,12,171),(1.2,.05625,.8)),('deep',(64,64,64),(.4,.4,.4))]
    for name,shape,lengths in cases:
        result,arrays=metrics(mac(shape,lengths));result['name']=name
        if result['manufactured_pressure_error']>=.01 or result['hydrostatic_pressure_relative']>=.01 or result['shear_preservation_relative']>=1e-10:
            raise ValueError(f'cost geometry failed physical admission: {name}')
        np.savez_compressed(folder/(name+'.npz'),**arrays);records.append(result)
    (root/'cost-geometry-admission.json').write_text(json.dumps({'records':records,'pass':True},indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path);run(parser.parse_args().root)
