"""Retain independent calibration runs and every-step energy ledgers durably.

No production source or prior evidence is mutated. The same immutable request
owns scheduled particle observations, complete stage work and executable identity.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from tools.performance.convergence_campaign import digest, persist, pin_binary


def compress(path: Path) -> dict:
    checksum=digest(path);size=path.stat().st_size
    destination=path.with_suffix(path.suffix+'.gz')
    with path.open('rb') as source,destination.open('xb') as output:
        with gzip.GzipFile(fileobj=output,mode='wb',mtime=0) as compressed:
            shutil.copyfileobj(source,compressed)
        output.flush();os.fsync(output.fileno())
    with gzip.open(destination,'rb') as source:
        if hashlib.file_digest(source,'sha256').hexdigest()!=checksum:raise ValueError('raw compression readback differs')
    path.unlink()
    return {'raw_sha256':checksum,'raw_bytes':size,'gzip_sha256':digest(destination)}


def run(root: Path,binary: Path,label: str, *,scene='collision',n=12,layers=1,dt=None,duration=6,
        iterations=8,boundary=True,inset=.5,threads=8,calibration='raw',wall_volume=False,
        nu=0.,contact=True,density=True,gravity=9.81,restart: Path|None=None,velocity_factor=1.,support=2.,viscosity_support=4.,mass_scheme="inherited",timeout=7200):
    root=root.resolve();directory=root/'runs'/label;directory.mkdir(parents=True,exist_ok=False)
    solver=pin_binary(binary.resolve());dt=dt if dt is not None else 1/240*6/n
    initial='-'
    if restart is not None:
        initial=str(directory/'initial.bin');shutil.copyfile(restart,initial)
    parameters=dict(scene=scene,n=n,layers=layers,dt=dt,duration=duration,iterations=iterations,
                    boundary=boundary,inset_fraction=inset,threads=threads,calibration=calibration,
                    wall_volume=wall_volume,nu=nu,contact=contact,density=density,gravity=gravity,
                    restart=restart is not None,velocity_factor=velocity_factor,support=support,viscosity_support=viscosity_support,mass_scheme=mass_scheme)
    ledger=directory/'ledger.jsonl'
    command=[str(solver),scene,str(n),str(layers),str(dt),str(duration),str(iterations),str(int(boundary)),str(inset),str(threads),calibration,str(int(wall_volume)),str(nu),str(int(contact)),str(int(density)),str(gravity),str(ledger),initial,str(velocity_factor),str(support),str(viscosity_support),mass_scheme]
    persist(directory/'request.json',{'parameters':parameters,'command':command,'solver_sha256':digest(solver),
            'protocol_sha256':digest(root/'protocol.json'),'started_utc':datetime.now(timezone.utc).isoformat(),
            'restart_sha256':digest(Path(initial)) if restart is not None else None})
    raw=directory/'states.bin';code=None;timed_out=False
    with raw.open('xb') as out,(directory/'stderr.txt').open('xb') as err:
        try:code=subprocess.run(command,stdout=out,stderr=err,timeout=timeout).returncode
        except subprocess.TimeoutExpired:timed_out=True
        for file in (out,err):file.flush();os.fsync(file.fileno())
    for path in (ledger,):
        if path.exists():
            with path.open('rb') as file:os.fsync(file.fileno())
    state=compress(raw)
    ledger_record=compress(ledger) if ledger.exists() else None
    metrics=json.loads((directory/'stderr.txt').read_text().splitlines()[-1]) if code==0 else None
    record=dict(state,exit_code=code,timed_out=timed_out,ledger=ledger_record,solver_metrics=metrics,
                finished_utc=datetime.now(timezone.utc).isoformat())
    persist(directory/'collection.json',record)
    print(label,code,metrics,flush=True)
    return record


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root',type=Path);parser.add_argument('binary',type=Path)
    parser.add_argument('phase',choices=['screen','spatial','temporal','viscosity'])
    args=parser.parse_args();root,binary=args.root,args.binary
    if args.phase=='screen':
        run(root,binary,'equivalence-n6',n=6,duration=.5)
        for scene in ('tank-valid','collision'):
            for calibration in ('raw','self','ratio'):
                run(root,binary,f'{scene}-{calibration}-n12',scene=scene,calibration=calibration)
        for calibration in ('raw','self'):
            run(root,binary,f'wall-volume-{calibration}-n12',calibration=calibration,wall_volume=True)
    elif args.phase=='spatial':
        for n in (6,18,24):
            for calibration in ('raw','self'):
                run(root,binary,f'collision-{calibration}-n{n}',n=n,calibration=calibration)
        for calibration in ('raw','self'):
            run(root,binary,f'tank-valid-{calibration}-n6',n=6,scene='tank-valid',calibration=calibration)
        for calibration in ('raw','self'):
            run(root,binary,f'flat-valid-{calibration}-n12',scene='flat-valid',calibration=calibration)
    elif args.phase=='temporal':
        for n in (12,18):
            for calibration in ('raw','self'):
                run(root,binary,f'halfdt-{calibration}-n{n}',n=n,dt=1/240*3/n,calibration=calibration)
                run(root,binary,f'iter16-{calibration}-n{n}',n=n,iterations=16,calibration=calibration)
    else:
        for nu in (1e-6,1e-3):
            for calibration in ('raw','self'):
                run(root,binary,f'viscosity-{nu}-{calibration}-n12',nu=nu,calibration=calibration)


if __name__=='__main__':main()
