"""Read back every raw particle stream and energy-ledger byte before reporting."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from tools.performance.spatial_retain import verify


def retain(root):
    result=verify(root);ledgers={}
    protocol_hash=hashlib.sha256((root/'protocol.json').read_bytes()).hexdigest()
    for path in sorted((root/'runs').glob('*/collection.json')):
        d=json.loads(path.read_text());request=json.loads((path.parent/'request.json').read_text())
        if request['protocol_sha256']!=protocol_hash:raise ValueError('request protocol differs')
        if request['restart_sha256'] is not None:
            with (path.parent/'initial.bin').open('rb') as source:
                if hashlib.file_digest(source,'sha256').hexdigest()!=request['restart_sha256']:raise ValueError('restart input differs')
        record=d['ledger'];f=path.parent/'ledger.jsonl.gz'
        if record is None:
            ledgers[path.parent.name]={'present':False};continue
        with f.open('rb') as source:
            if hashlib.file_digest(source,'sha256').hexdigest()!=record['gzip_sha256']:raise ValueError('compressed ledger differs')
        checksum=hashlib.sha256();count=0;size=0
        with gzip.open(f,'rb') as source:
            for line in source:
                checksum.update(line);size+=len(line);row=json.loads(line);count+=1
                if row['step']!=count:raise ValueError('ledger step sequence differs')
        if checksum.hexdigest()!=record['raw_sha256'] or size!=record['raw_bytes']:raise ValueError('raw ledger differs')
        if d['exit_code']==0 and count!=d['solver_metrics']['completed_steps']:raise ValueError('incomplete ledger')
        ledgers[path.parent.name]={'present':True,'raw_sha256':record['raw_sha256'],'gzip_sha256':record['gzip_sha256'],'raw_bytes':size,'steps':count}
    result['ledgers']=ledgers;result['total_ledger_steps']=sum(r.get('steps',0) for r in ledgers.values())
    result['total_ledger_raw_bytes']=sum(r.get('raw_bytes',0) for r in ledgers.values())
    result['all_ledger_checksums_and_steps_valid']=True
    (root/'readback.json').write_text(json.dumps(result,indent=2)+'\n')
    print({k:v for k,v in result.items() if k not in ('runs','ledgers')})
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path)
    retain(parser.parse_args().root)
