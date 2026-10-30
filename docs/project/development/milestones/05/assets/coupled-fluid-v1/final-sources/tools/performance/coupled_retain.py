"""Freeze coupled experiment sources and seal raw evidence with preservation guards."""
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
    count=0;size=0
    for line in (root/'SHA256SUMS').read_text().splitlines():
        expected,name=line.split('  ',1);path=root/name
        if not path.resolve().is_relative_to(root.resolve()):raise ValueError('manifest path outside root')
        if digest(path)!=expected:raise ValueError('evidence identity differs: '+name)
        count+=1;size+=path.stat().st_size
    return {'files_verified':count,'bytes_verified':size,'manifest_sha256':digest(root/'SHA256SUMS'),'all_match':True}


def freeze(root,repo):
    target=root/'final-sources';target.mkdir();records=[]
    paths=sorted((repo/'tools/performance').glob('coupled_*.py'))
    paths+=[repo/'tools/performance/feasible_pressure.py',repo/'tools/performance/__init__.py',repo/'tests/performance/test_coupled_fluid.py']
    for p in paths:
        rel=p.relative_to(repo);copy=target/rel;copy.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,copy)
        records.append({'source':str(rel),'snapshot':str(copy.relative_to(root)),'sha256':digest(p)})
    (root/'source-provenance.json').write_text(json.dumps({'base_heads':json.loads((root/'protocol.json').read_text())['base_heads'],
        'status':'Uncommitted standalone experimental snapshots, not Git history or production integration. Each case separately retains its actual earlier source version.','files':records},indent=2)+'\n')


def seal(root,repo):
    initial=json.loads((root/'initial-state.json').read_text());allowed={'docs/research/references.bib','docs/research/source-register.md','docs/project/development/milestones/05/performance-plan.md'}
    preserved=0;changed=[]
    for name,expected in initial['preexisting_source_sha256'].items():
        if digest(repo/name)!=expected:
            if name not in allowed:raise ValueError('pre-existing source changed: '+name)
            changed.append(name)
        else:preserved+=1
    states={}
    for name,relative in [('EPQ','.'),('Maelstrom','Maelstrom')]:
        path=repo/relative
        head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=path,text=True).strip()
        index=hashlib.sha256(subprocess.check_output(['git','ls-files','--stage'],cwd=path)).hexdigest()
        if head!=initial[name]['head'] or index!=initial[name]['index_sha256']:raise ValueError('repository history/index changed')
        states[name]={'head':head,'index_sha256':index}
    status=subprocess.check_output(['git','status','--short'],cwd=repo/'Maelstrom',text=True)
    if status!=initial['Maelstrom']['status']:raise ValueError('Maelstrom working state changed')
    for item in json.loads((root/'source-provenance.json').read_text())['files']:
        if digest(repo/item['source'])!=item['sha256'] or digest(root/item['snapshot'])!=item['sha256']:raise ValueError('final source snapshot differs')
    for path in root.rglob('input.json'):
        value=json.loads(path.read_text())
        for name,expected in value.get('source_sha256',{}).items():
            if digest(path.parent/'sources'/name)!=expected:raise ValueError('case source version differs')
    raw=json.loads((root/'raw-readback-final.json').read_text());assessment=json.loads((root/'assessment.json').read_text())
    if not raw['all_match'] or raw['cases']!=len(list(root.rglob('status.json'))):raise ValueError('raw-state readback missing/stale')
    if assessment['GPU_performance_admitted'] or assessment['GPU_performance_measured']:raise ValueError('unqualified performance admission')
    archives={name:verify(root.parent/name) for name in ['pressure-feasibility-v1','pressure-diagnosis-v1']}
    guard=json.loads((root.parent/'pressure-feasibility-v1/preservation.json').read_text())['native_sha256']
    for name,expected in guard.items():
        if digest(repo/'Maelstrom/native'/name)!=expected:raise ValueError('native production source differs')
    preservation={'repository_states':states,'preexisting_files_unchanged':preserved,'authorised_existing_document_additions':changed,
        'native_guards_verified':len(guard),'Maelstrom_working_state_unchanged':True,'prior_archives_local_readback':archives,
        'production_changes':False,'history_changes':False,'system_settings_changes':False,'GPU_benchmark_executed':False}
    (root/'preservation.json').write_text(json.dumps(preservation,indent=2)+'\n')
    excluded={'SHA256SUMS','local-readback.json','mirror-readback.json'}
    paths=[p for p in sorted(root.rglob('*')) if p.is_file() and p.relative_to(root).as_posix() not in excluded and '__pycache__' not in p.parts]
    with (root/'SHA256SUMS').open('w') as output:
        for p in paths:
            with p.open('rb') as stream:os.fsync(stream.fileno())
            output.write(digest(p)+'  '+p.relative_to(root).as_posix()+'\n')
        output.flush();os.fsync(output.fileno())
    (root/'local-readback.json').write_text(json.dumps(verify(root),indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('operation',choices=['freeze','seal','verify']);p.add_argument('root',type=Path);p.add_argument('--repo',type=Path);a=p.parse_args()
    if a.operation=='verify':print(json.dumps(verify(a.root),indent=2))
    else:
        if a.repo is None:p.error('--repo required')
        (freeze if a.operation=='freeze' else seal)(a.root,a.repo)
