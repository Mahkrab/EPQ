"""Run the predeclared pressure-stage trials on the primary measurement device.

The executable and raw fields stay beside each trial. No system configuration is
changed. A failed subprocess keeps its command and diagnostics and stops admission.
"""
import argparse
import json
import math
from pathlib import Path
import subprocess
import time


def run(root,binary,audit_only=False):
    target=root/('gpu-audit' if audit_only else 'gpu');target.mkdir()
    cases=[('audit',(16,4,16),(.2,.05,.2),.002,3)] if audit_only else []
    if not audit_only:
        for name,shape,lengths in [('tank',(64,16,64),(.2,.05,.2)),('pool',(256,12,171),(1.2,.05625,.8)),('deep',(64,64,64),(.4,.4,.4))]:
            dt_limit=min(a/b for a,b in zip(lengths,shape));steps=math.ceil(.1/dt_limit)
            cases.append((name,shape,lengths,.1/steps,steps))
        cases.extend([('tank-halfdt',(64,16,64),(.2,.05,.2),.1/64,64),('tank-1s',(64,16,64),(.2,.05,.2),1/320,320)])
    for name,shape,lengths,dt,steps in cases:
        for trial in range(1 if audit_only else 3):
            order=['fft','pcg'] if trial%2==0 else ['pcg','fft']
            for solver in order:
                prefix=target/f'{name}-{solver}-{trial}'
                command=[str(binary),solver,*map(str,shape),*map(str,lengths),str(dt),str(steps),str(prefix),str(trial)]
                prefix.with_suffix('.command.json').write_text(json.dumps(command)+'\n')
                start=time.monotonic()
                with prefix.with_suffix('.json').open('x') as out,prefix.with_suffix('.stderr').open('x') as err:
                    result=subprocess.run(command,stdout=out,stderr=err,timeout=180,check=False)
                prefix.with_suffix('.process.json').write_text(json.dumps({'exit_code':result.returncode,'process_wall_s':time.monotonic()-start})+'\n')
                if result.returncode:raise RuntimeError(f'GPU trial failed: {prefix.name}')
                print(prefix.with_suffix('.json').read_text(),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path);parser.add_argument('--binary',type=Path,required=True);parser.add_argument('--audit-only',action='store_true');args=parser.parse_args();run(args.root,args.binary,args.audit_only)
