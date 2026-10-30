"""Seal standalone feasibility sources and verify evidence without altering history.

Checksums cover raw arrays and observations, not a claim of physical correctness.
The independent mirror receipt is deliberately outside the manifest it verifies.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def verify(root):
    checked=[]
    for line in (root/'SHA256SUMS').read_text().splitlines():
        expected,name=line.split('  ',1);path=root/name
        if not path.resolve().is_relative_to(root.resolve()):raise ValueError('manifest path outside evidence root')
        if digest(path)!=expected:raise ValueError(f'evidence mismatch: {name}')
        checked.append(name)
    return {'files_verified':len(checked),'manifest_sha256':digest(root/'SHA256SUMS'),'all_match':True}


def seal(root,repo):
    sources=root/'sources';sources.mkdir();records=[]
    paths=sorted((repo/'tools/performance').glob('feasible_*'))+[repo/'tests/performance/test_feasible_pressure.py']
    for name in ['tools/__init__.py','tools/performance/__init__.py','tests/__init__.py','tests/performance/__init__.py']:
        if (repo/name).is_file():paths.append(repo/name)
    for path in paths:
        if not path.is_file():continue
        relative=path.relative_to(repo);target=sources/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
        records.append({'source':str(relative),'snapshot':str(target.relative_to(root)),'sha256':digest(path)})
    protocol=json.loads((root/'protocol.json').read_text());initial=json.loads((root/'initial-state.json').read_text())
    heads={'EPQ':subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),'Maelstrom':subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo/'Maelstrom',text=True).strip()}
    if heads!=protocol['base_heads']:raise ValueError('repository HEAD changed')
    state=subprocess.check_output(['git','status','--short'],cwd=repo/'Maelstrom',text=True)
    if state!=initial['Maelstrom_status']:raise ValueError('Maelstrom working state changed')
    prior=root.parent/'pressure-diagnosis-v1';native={}
    for name,r in json.loads((prior/'environment-and-preservation.json').read_text())['native_source_identities'].items():
        native[name]=digest(repo/'Maelstrom/native'/name)
        if native[name]!=r['sha256']:raise ValueError('production native source changed: '+name)
    preservation={'heads':heads,'native_sha256':native,'Maelstrom_status_unchanged':True,'Maelstrom_status':state,'prior_archive':verify(prior),'production_changes':False,'history_changes':False,'system_setting_changes':False}
    (root/'preservation.json').write_text(json.dumps(preservation,indent=2)+'\n')
    (root/'source-provenance.json').write_text(json.dumps({'base_heads':heads,'status':'Uncommitted standalone experimental snapshots; not a Git checkpoint or production integration.','files':records},indent=2)+'\n')
    excluded={'SHA256SUMS','local-readback.json','mirror-readback.json'}
    files=[p for p in sorted(root.rglob('*')) if p.is_file() and p.relative_to(root).as_posix() not in excluded and '__pycache__' not in p.parts]
    for p in files:
        with p.open('rb') as stream:os.fsync(stream.fileno())
    with (root/'SHA256SUMS').open('w') as stream:
        for p in files:stream.write(digest(p)+'  '+p.relative_to(root).as_posix()+'\n')
        stream.flush();os.fsync(stream.fileno())
    (root/'local-readback.json').write_text(json.dumps(verify(root),indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('operation',choices=['seal','verify']);parser.add_argument('root',type=Path);parser.add_argument('--repo',type=Path);args=parser.parse_args()
    if args.operation=='seal':
        if args.repo is None:parser.error('--repo required to seal')
        seal(args.root,args.repo)
    else:print(json.dumps(verify(args.root),indent=2))
