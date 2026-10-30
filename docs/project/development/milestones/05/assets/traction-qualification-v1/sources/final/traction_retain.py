"""Verify native observations before sealing a durable experiment manifest."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import struct
from tools.performance.traction_prefix import screen


def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def observations(path,complete):
    with gzip.open(path,'rb') as stream:
        raw=stream.read(104)
        if len(raw)!=104:raise ValueError('truncated native header')
        magic,n,w,planned=struct.unpack('<4I',raw[:16])
        if magic!=0x50424634 or not 0<n<=100000 or w>1000000:raise ValueError('invalid native header')
        if len(stream.read(w*24))!=w*24:raise ValueError('truncated wall support')
        steps=[];trailing=0
        while True:
            block=stream.read(4+n*48)
            if not block:break
            if len(block)!=4+n*48:trailing=len(block);break
            steps.append(struct.unpack('<I',block[:4])[0])
        if not steps or steps[0]!=0 or any(b<=a for a,b in zip(steps,steps[1:])):raise ValueError('unordered observation steps')
        if complete and (trailing or steps[-1]!=planned):raise ValueError('incomplete successful observation stream')
    return {'particles':n,'planned_steps':planned,'scheduled_observations':len(steps),'last_observation_step':steps[-1],'trailing_bytes':trailing}


def retain(root):
    records=[]
    for path in sorted((root/'coupled').glob('*.collection.json')):
        label=path.name.removesuffix('.collection.json');collection=json.loads(path.read_text());complete=collection['returncode']==0
        for key,suffix in [('raw','.raw'),('ledger','.ledger')]:
            packed=root/'coupled'/(label+suffix+'.gz');expected=collection[key]
            if digest(packed)!=expected['gzip_sha256']:raise ValueError('packed checksum differs: '+label+key)
            with gzip.open(packed,'rb') as stream:
                if hashlib.file_digest(stream,'sha256').hexdigest()!=expected['raw_sha256']:raise ValueError('raw readback differs: '+label+key)
            unpacked=root/'coupled'/(label+suffix)
            if unpacked.exists() and digest(unpacked)!=expected['raw_sha256']:raise ValueError('retained uncompressed bytes differ')
        obs=observations(root/'coupled'/(label+'.raw.gz'),complete)
        with gzip.open(root/'coupled'/(label+'.ledger.gz'),'rt') as stream:
            lines=stream.read().splitlines(keepends=True)
        valid=[];truncated=False
        for i,line in enumerate(lines):
            try:valid.append(json.loads(line))
            except json.JSONDecodeError:
                if complete or i!=len(lines)-1:raise
                truncated=True
        if any(r['step']!=i+1 for i,r in enumerate(valid)):raise ValueError('ledger step gap')
        if complete and (len(valid)!=obs['planned_steps'] or truncated):raise ValueError('incomplete successful ledger')
        records.append({'label':label,'complete':complete,**obs,'complete_ledger_records':len(valid),'truncated_ledger_tail':truncated})
    rejection=json.loads((root/'coupled/mirror-mixed-n8-h4.rejection.json').read_text())
    raw=root/'coupled/mirror-mixed-n8-h4.raw'
    with raw.open('rb') as stream:
        if hashlib.sha256(stream.read(rejection['prefix_bytes'])).hexdigest()!=rejection['prefix_sha256']:raise ValueError('rejected prefix differs')
    final_prefix=screen(raw)
    result={'records':records,'completed_runs':sum(r['complete'] for r in records),'rejected_prefixes':sum(not r['complete'] for r in records),
        'complete_run_observations':sum(r['scheduled_observations'] for r in records if r['complete']),
        'complete_run_accepted_steps':sum(r['complete_ledger_records'] for r in records if r['complete']),
        'rejected_final_prefix':final_prefix,'rejected_failure_prefix_hash_verified':True,
        'report_sha256':digest(root.parent.parent/'viscosity-traction.md')}
    with (root/'readback.json').open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    excluded={'SHA256SUMS','mirror-readback.json'}
    files=sorted(p for p in root.rglob('*') if p.is_file() and p.name not in excluded)
    with (root/'SHA256SUMS').open('x') as stream:
        for path in files:stream.write(digest(path)+'  '+path.relative_to(root).as_posix()+'\n')
    for path in [*files,root/'SHA256SUMS']:
        with path.open('rb') as stream:os.fsync(stream.fileno())
    for directory in sorted([root,*[p for p in root.rglob('*') if p.is_dir()]],reverse=True):
        descriptor=os.open(directory,os.O_RDONLY)
        try:os.fsync(descriptor)
        finally:os.close(descriptor)
    return {'files':len(files),'bytes':sum(p.stat().st_size for p in files),'completed_runs':result['completed_runs'],'rejected_prefixes':result['rejected_prefixes']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);a=p.parse_args();print(json.dumps(retain(a.root),indent=2))
