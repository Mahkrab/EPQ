"""Compress raw pressure observations losslessly and seal verified evidence.

Packing keeps originals until a separately verified primary-original readback
authorises their local removal. Sealing includes source and analysis identities.
"""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path


def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def pack(root):
    records=[]
    for path in sorted((root/'native').iterdir()):
        if path.suffix not in ['.raw','.trace','.jac','.initial','.ledger']:continue
        target=Path(str(path)+'.gz')
        with path.open('rb') as source,target.open('xb') as output:
            with gzip.GzipFile(fileobj=output,mode='wb',mtime=0) as packed:
                while block:=source.read(1024*1024):packed.write(block)
            output.flush();os.fsync(output.fileno())
        with gzip.open(target,'rb') as stream:readback=hashlib.file_digest(stream,'sha256').hexdigest()
        checksum=digest(path)
        if readback!=checksum:raise ValueError('compression readback mismatch')
        records.append({'raw':str(path.relative_to(root)),'packed':str(target.relative_to(root)),
            'raw_bytes':path.stat().st_size,'raw_sha256':checksum,'gzip_sha256':digest(target)})
    with (root/'compression.json').open('x') as stream:json.dump({'records':records,'originals_removed':False},stream,indent=2);stream.write('\n')
    return {'files':len(records),'raw_bytes':sum(r['raw_bytes'] for r in records)}


def seal(root):
    receipt=json.loads((root/'original-readback.json').read_text())
    if not receipt['all_originals_match'] or receipt['compression_manifest_sha256']!=digest(root/'compression.json'):
        raise ValueError('primary original readback is missing or stale')
    if not json.loads((root/'reproduction-readback.json').read_text())['all_match']:
        raise ValueError('compressed observation reproduction failed')
    compression=json.loads((root/'compression.json').read_text())['records']
    for r in compression:
        p=root/r['packed']
        if digest(p)!=r['gzip_sha256']:raise ValueError('packed identity differs')
        with gzip.open(p,'rb') as stream:
            if hashlib.file_digest(stream,'sha256').hexdigest()!=r['raw_sha256']:raise ValueError('raw identity differs')
    for request in (root/'native').glob('*.request.json'):
        label=request.name.removesuffix('.request.json');r=json.loads(request.read_text());c=json.loads((root/'native'/(label+'.collection.json')).read_text())
        if c['returncode']!=0:raise ValueError('unsuccessful native case '+label)
        recorded=next(x['raw_sha256'] for x in compression if x['raw']=='native/'+label+'.raw')
        if c['raw_sha256']!=recorded:raise ValueError('native collection identity differs')
        execution=json.loads((root/'native'/(label+'.execution.json')).read_text())
        if execution['binary_sha256']!=r['binary_sha256']:raise ValueError('execution binary differs')
        initial=next(x['raw_sha256'] for x in compression if x['raw']=='native/'+label+'.initial')
        if initial!=r['initial_sha256']:raise ValueError('initial-array identity differs')
    verified=json.loads((root/'verified-operators/operator-results.json').read_text())['records']
    for r in verified:
        if digest(root/'verified-operators/operators'/(r['label']+'.npz'))!=r['raw_sha256']:raise ValueError('operator identity differs')
    readback={'packed_streams':len(compression),'packed_raw_hashes_verified':True,'native_requests':len(list((root/'native').glob('*.request.json'))),
        'native_pressure_iterations':sum(json.loads(p.read_text())['parameters']['iterations'] for p in (root/'native').glob('*.request.json')),
        'unique_verified_geometries':len(verified),'operator_hashes_verified':True,
        'report_sha256':digest(root.parent.parent/'pressure-projection-diagnosis.md')}
    with (root/'readback.json').open('x') as stream:json.dump(readback,stream,indent=2);stream.write('\n')
    files=sorted(p for p in root.rglob('*') if p.is_file() and p.name not in ['SHA256SUMS','mirror-readback.json'])
    with (root/'SHA256SUMS').open('x') as stream:
        for path in files:stream.write(digest(path)+'  '+path.relative_to(root).as_posix()+'\n')
    for path in [*files,root/'SHA256SUMS']:
        with path.open('rb') as stream:os.fsync(stream.fileno())
    for directory in sorted([root,*[p for p in root.rglob('*') if p.is_dir()]],reverse=True):
        descriptor=os.open(directory,os.O_RDONLY)
        try:os.fsync(descriptor)
        finally:os.close(descriptor)
    return {'files':len(files),'bytes':sum(p.stat().st_size for p in files),**readback}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['pack','seal']);p.add_argument('root',type=Path);a=p.parse_args();print(json.dumps(pack(a.root) if a.mode=='pack' else seal(a.root),indent=2))
