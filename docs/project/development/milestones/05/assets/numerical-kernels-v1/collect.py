from pathlib import Path
import json,hashlib,tarfile,shutil,subprocess
w=Path('/tmp/maelstrom-numerical-20261028');out=w/'retained';out.mkdir();sha=lambda b:hashlib.sha256(b).hexdigest()
shutil.copyfile(Path('/tmp/maelstrom-reprofile11-20261028/retained/control.patch'),out/'control.patch')
control=json.loads((w/'control-source.json').read_text())
for v in ['trial-0','trial-1','trial-2','trial-3','trial-4','candidate']:
 source=json.loads((w/(v+'-source.json')).read_text());parts=[]
 for n in sorted(source.keys()|control.keys()):
  if source.get(n)==control.get(n):continue
  a=w/'control'/n;b=w/v/n
  args=['diff','-u','--label','a/'+n if a.exists() else '/dev/null','--label','b/'+n if b.exists() else '/dev/null',str(a) if a.exists() else '/dev/null',str(b) if b.exists() else '/dev/null'];p=subprocess.run(args,capture_output=True);assert p.returncode==1;parts.append(p.stdout)
 (out/(v+'.patch')).write_bytes(b''.join(parts))
root=['control-source.json','trial-0-source.json','trial-1-source.json','trial-2-source.json','trial-3-source.json','trial-4-source.json','candidate-source.json','independent-audit.json','gpu-stages.json','resources.json','exploratory-summary.json','microbenchmark.json','qualification-counts.json','post-source-check.json','protocol.md','collect.py']
for n in root:shutil.copyfile(w/n,out/n)
(w/'setup-failures.md').write_text('''# Retained setup failures
The first trial-3 generator copied control into trial-3 but referred to trial-2/native/solver.cu when extracting the original correction body. It raised ValueError: substring not found before writing the edited source. The corrected generator uses trial-3 and overwrites only its own private export.

The initial trial-3 target symlink referred to a nonexistent old target. Cargo exited 101: failed to create directory .../target-trial-3; Not a directory (os error 20). The task-owned link was corrected to an existing previous task target. No timing sample was collected from either setup failure.

The first aggregate resource query reached candidate before candidate.ptx existed and exited 2 from the probe's file-open check. resources-progress.log retains the assertion. Production PTX was generated explicitly, and resources-retry-progress.log plus resources.json record the completed query. No measurements ran until this succeeded.

Nsight Compute returned ERR_NVGPUCTRPERM on the fresh one-step attempt. The command, exit 1, raw stdout/stderr hashes and output are in preflight. No privileged settings were changed. This is not a hardware-counter pass.
''')
members={};counts={}
def files(folder):return [p for p in (w/folder).rglob('*') if p.is_file()]
def pack(name,paths):
 def scrub(info):info.uid=info.gid=0;info.uname=info.gname='';return info
 paths=sorted(set(paths));count=0
 with tarfile.open(out/name,'w:xz',preset=6) as archive:
  for p in paths:
   n=p.relative_to(w).as_posix();assert n not in members;members[n]=sha(p.read_bytes());archive.add(p,arcname=n,recursive=False,filter=scrub);count+=1
 counts[name]=count;print(name,count,flush=True)
pack('observations.tar.xz',sum([files(f) for f in ['trial-results','trial1-results','trial2-results','trial3-results','trial4-results','trial-profiles','measurements','final-profiles','verification/regression']],[]))
pack('verification.tar.xz',[p for p in files('verification') if 'regression' not in p.relative_to(w/'verification').parts]+files('device-checks')+files('supplement')+files('postcheck'))
pack('inputs.tar.xz',files('inputs'))
pack('investigation.tar.xz',files('assembly')+files('preflight')+[p for p in w.iterdir() if p.is_file() and p.name not in root and p.suffix in ['.py','.cpp','.cu','.rs','.md','.log','.json','.stdout','.stderr','.ptx']])
(out/'files-sha256.json').write_text(json.dumps(members,indent=2)+'\n');(out/'archive-members.json').write_text(json.dumps(counts,indent=2)+'\n');print('complete',len(members),flush=True)
