"""Retain isolated channel requests, failed prefixes and checked raw streams.

Each label is exclusive. A completed collection includes both compressed and
uncompressed hashes; a failed process keeps its observations for diagnosis.
"""
import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def persist(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n');stream.flush();os.fsync(stream.fileno())


def compress(path):
    target=path.with_suffix(path.suffix+'.gz')
    with path.open('rb') as source, target.open('xb') as destination:
        with gzip.GzipFile(fileobj=destination, mode='wb', mtime=0) as packed:
            while block:=source.read(1024*1024):packed.write(block)
        destination.flush();os.fsync(destination.fileno())
    with gzip.open(target, 'rb') as stream:
        readback=hashlib.file_digest(stream, 'sha256').hexdigest()
    checksum=digest(path)
    if checksum!=readback:raise ValueError('compressed readback differs')
    return {'raw_sha256':checksum, 'gzip_sha256':digest(target), 'raw_bytes':path.stat().st_size}


def run(root, binary, label, ny, amplitude=.01, gravity=9.81, dt=1/480,
        duration=1.0125, iterations=24, threads=4, boundary=True, density=True,
        nu=.001, mode='channel-mixed', pressure_support=2, restart=None):
    if not label or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-.' for c in label):
        raise ValueError('label must be a simple lower-case filename')
    root.mkdir(parents=True, exist_ok=True);base=root/label
    ledger=Path(str(base)+'.ledger');raw=Path(str(base)+'.raw');stderr=Path(str(base)+'.stderr')
    parameters={k:v for k,v in locals().copy().items() if k in
        ['ny','amplitude','gravity','dt','duration','iterations','threads','boundary','density','nu','mode','pressure_support']}
    command=[str(binary.resolve()),mode,str(ny),str(amplitude),str(dt),str(duration),str(iterations),
        str(int(boundary)),'.5',str(threads),'self','1',str(nu),'1',str(int(density)),str(gravity),str(ledger.resolve()),str(restart.resolve()) if restart else '-','1',str(pressure_support),'2','geometric']
    if any(p.exists() for p in [raw,ledger,stderr,Path(str(base)+'.request.json')]):
        raise FileExistsError(f'experiment already exists: {label}')
    persist(Path(str(base)+'.request.json'),{'parameters':parameters,'command':command,
        'binary_sha256':digest(binary),'started_utc':datetime.now(timezone.utc).isoformat(),
        'restart_sha256':digest(restart) if restart else None,
        'environment':{'OMP_WAIT_POLICY':'PASSIVE'}})
    started=time.perf_counter()
    with raw.open('xb') as out,stderr.open('xb') as err:
        code=subprocess.run(command, stdout=out, stderr=err,
            env={**os.environ,'OMP_WAIT_POLICY':'PASSIVE'}, check=False).returncode
        out.flush();os.fsync(out.fileno());err.flush();os.fsync(err.fileno())
    record={'returncode':code,'elapsed_s':time.perf_counter()-started,'raw':compress(raw)}
    if ledger.exists():record['ledger']=compress(ledger)
    persist(Path(str(base)+'.collection.json'), record)
    if code:raise RuntimeError(f'experiment failed ({code}); retained {label}')
    return record


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root',type=Path);parser.add_argument('binary',type=Path);parser.add_argument('label')
    parser.add_argument('--ny',type=int,required=True)
    for name,default in [('amplitude',.01),('gravity',9.81),('dt',1/480),('duration',1.0125),('nu',.001)]:
        parser.add_argument('--'+name,type=float,default=default)
    parser.add_argument('--iterations',type=int,default=24);parser.add_argument('--threads',type=int,default=4)
    parser.add_argument('--pressure-support',type=float,default=2)
    parser.add_argument('--restart',type=Path)
    parser.add_argument('--mode',default='channel-mixed',choices=['channel-mixed','channel-horizontal','channel-rest'])
    args=vars(parser.parse_args());print(json.dumps(run(**args),indent=2))


if __name__=='__main__':main()
