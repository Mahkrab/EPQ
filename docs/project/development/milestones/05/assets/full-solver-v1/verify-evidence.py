"""Check retained members and reconstruct every source export without a mutable checkout."""
from pathlib import Path
import json,hashlib,tarfile,tempfile,subprocess,shutil,io,sys
assets=Path(sys.argv[1]);repo=Path(sys.argv[2]);sha=lambda b:hashlib.sha256(b).hexdigest();members=json.loads((assets/'files-sha256.json').read_text());seen={};archives={}
for p in sorted(assets.glob('*.tar.xz')):
 count=0
 with tarfile.open(p) as arc:
  for member in arc:
   assert member.isfile() and not Path(member.name).is_absolute() and '..' not in Path(member.name).parts;data=arc.extractfile(member).read();assert sha(data)==members[member.name];assert member.name not in seen;seen[member.name]=p.name;count+=1
 archives[p.name]=dict(sha256=sha(p.read_bytes()),members=count,bytes=p.stat().st_size)
assert set(seen)==set(members)
(assets/'archive-readback.json').write_text(json.dumps(dict(verified_members=len(seen),archives=archives,all_member_hashes_match=True,private_registry_hives_and_native_profiler_reports_excluded=True),indent=2)+'\n')
results={};base='1e0085926d05c42949bb76b55d177d42a1f8f94f'
with tempfile.TemporaryDirectory(prefix='maelstrom-source-readback-') as temp:
 temp=Path(temp);control=temp/'control';control.mkdir();p=subprocess.run(['git','-C',str(repo),'archive',base],capture_output=True,check=True)
 with tarfile.open(fileobj=io.BytesIO(p.stdout)) as arc:arc.extractall(control,filter='data')
 def patch(tree,name):
  command=['patch','--batch','--forward','-p1','-i',str((assets/(name+'.patch')).resolve())];p=subprocess.run(command,cwd=tree,capture_output=True);assert p.returncode==0,(name,p.stdout,p.stderr)
 def check(tree,name):
  manifest=json.loads((assets/(name+'-source.json')).read_text());actual={p.relative_to(tree).as_posix():sha(p.read_bytes()) for p in tree.rglob('*') if p.is_file()};assert actual==manifest,(name,set(actual)^set(manifest));results[name]=dict(files=len(actual),all_hashes_match=True)
 patch(control,'control');check(control,'control')
 for name in ['diagnostic','candidate','trial-0','candidate-prequalification']:
  target=temp/name;shutil.copytree(control,target);patch(target,name);check(target,name)
 for name,parent in [('candidate-diagnostic','candidate'),('trial-verification','trial-0')]:
  target=temp/name;shutil.copytree(temp/parent,target);patch(target,name);check(target,name)
(assets/'source-reconstruction.json').write_text(json.dumps(dict(base_commit=base,exports=results),indent=2)+'\n');print('verified',len(seen),'members;',results)
