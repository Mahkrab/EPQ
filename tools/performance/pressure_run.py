"""Execute prepared pressure-only requests on the primary PC using stdlib only."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess


def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main(root,binary):
    for request_path in sorted(root.glob('*.request.json')):
        label=request_path.name.removesuffix('.request.json');request=json.loads(request_path.read_text());command=request['command'].copy()
        if digest(binary)!=request['binary_sha256']:raise ValueError('native binary differs from prepared source build')
        initial=root/Path(command[17]).name
        if digest(initial)!=request['initial_sha256']:raise ValueError('initial observation identity differs')
        command[0]=str(binary.resolve());command[16]=str((root/(label+'.ledger')).resolve());command[17]=str(initial.resolve())
        raw=root/(label+'.raw');stderr=root/(label+'.stderr');execution=root/(label+'.execution.json')
        if any(p.exists() for p in [raw,stderr,execution,Path(command[16])]):raise FileExistsError('refusing to replace experiment '+label)
        with execution.open('x') as stream:json.dump({'command':command,'binary_sha256':digest(binary),'started_utc':datetime.now(timezone.utc).isoformat(),'environment':{'OMP_WAIT_POLICY':'PASSIVE'}},stream,indent=2)
        with raw.open('xb') as out,stderr.open('xb') as error:
            code=subprocess.run(command,stdout=out,stderr=error,env={**os.environ,'OMP_WAIT_POLICY':'PASSIVE'},check=False).returncode
            out.flush();os.fsync(out.fileno());error.flush();os.fsync(error.fileno())
        with (root/(label+'.collection.json')).open('x') as stream:json.dump({'returncode':code,'raw_sha256':digest(raw)},stream,indent=2)
        if code:raise RuntimeError('pressure-only request failed: '+label)
        print('completed',label,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('binary',type=Path);a=p.parse_args();main(a.root,a.binary)
