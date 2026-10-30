"""Seal raw experimental evidence in bounded archives and verify every member.

Build trees stay in the durable experiment directory. The seal contains inputs,
observations, failed attempts, logs and exact experiment sources, with a source
commit and binary hashes sufficient to distinguish every measured executable.
"""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile


def verify(folder):
    manifest=json.loads((folder/'manifest.json').read_text());actual={}
    for item in manifest['archives']:
        path=folder/item['name']
        if path.stat().st_size!=item['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('archive bytes differ '+path.name)
        with tarfile.open(path,'r:gz') as archive:
            for member in archive:
                with archive.extractfile(member) as f:
                    if member.name in actual:raise ValueError('duplicate raw member')
                    actual[member.name]={'bytes':member.size,'sha256':hashlib.file_digest(f,'sha256').hexdigest(),'archive':path.name}
    expected={f['name']:{k:v for k,v in f.items() if k!='name'} for f in manifest['files']}
    if actual!=expected:raise ValueError('raw observations differ from manifest')
    return {'archives':len(manifest['archives']),'files':len(actual),'raw_bytes':sum(x['bytes'] for x in actual.values())}


def seal(root,destination):
    destination.mkdir(exist_ok=False)
    excluded={'target','production-source','residency-source','__pycache__','retained','source','build'}
    files=[p for p in sorted(root.rglob('*')) if p.is_file() and not any(k in excluded for k in p.relative_to(root).parts) and p.name not in ['frontier-driver','frontier-quality','frontier-dfsph','dfsph-quality'] and not p.name.endswith('.tar.gz')]
    groups=[];group=[];size=0
    for p in files:
        if group and size+p.stat().st_size>64*1024*1024:groups.append(group);group=[];size=0
        group.append(p);size+=p.stat().st_size
    if group:groups.append(group)
    manifest={'format':'pbf-frontier-raw-seal-v1','archives':[],'files':[]}
    for i,paths in enumerate(groups):
        path=destination/f'observations-{i:03d}.tar.gz';expected={}
        with tarfile.open(path,'w:gz',compresslevel=6) as archive:
            for p in paths:
                name=p.relative_to(root).as_posix();sha=hashlib.sha256(p.read_bytes()).hexdigest();expected[name]=sha
                archive.add(p,arcname=name,recursive=False);manifest['files'].append({'name':name,'bytes':p.stat().st_size,'sha256':sha,'archive':path.name})
        actual={}
        with tarfile.open(path,'r:gz') as archive:
            for m in archive:
                if not m.isfile():raise ValueError('unexpected archive member')
                with archive.extractfile(m) as f:actual[m.name]=hashlib.file_digest(f,'sha256').hexdigest()
        if actual!=expected:raise ValueError('raw archive readback failed '+path.name)
        manifest['archives'].append({'name':path.name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'members':len(actual)})
        print(path.name,path.stat().st_size,len(actual),flush=True)
    (destination/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('destination',type=Path,nargs='?');p.add_argument('--verify',action='store_true');a=p.parse_args()
    if a.verify:print(json.dumps(verify(a.root.resolve())))
    elif a.destination is None:p.error('destination required when sealing')
    else:seal(a.root.resolve(),a.destination.resolve())
