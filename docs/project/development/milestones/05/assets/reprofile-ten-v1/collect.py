from pathlib import Path
import json,hashlib,tarfile,shutil,subprocess
w=Path('/tmp/maelstrom-reprofile11-20261028');out=w/'retained';out.mkdir();sha=lambda b:hashlib.sha256(b).hexdigest()
old=Path('/tmp/maelstrom-orchestration-20261028/retained');(out/'control.patch').write_bytes((old/'control.patch').read_bytes()+(old/'candidate.patch').read_bytes());shutil.copyfile(old/'candidate-diagnostic.patch',out/'diagnostic.patch')
control=json.loads((w/'control-source.json').read_text())
for v in ['trial-0','candidate']:
 source=json.loads((w/(v+'-source.json')).read_text());parts=[]
 for n in sorted(source.keys()|control.keys()):
  if source.get(n)==control.get(n):continue
  p=subprocess.run(['diff','-u','--label','a/'+n,'--label','b/'+n,str(w/'control'/n),str(w/v/n)],capture_output=True);assert p.returncode==1;parts.append(p.stdout)
 (out/(v+'.patch')).write_bytes(b''.join(parts))
for v in ['control','diagnostic','trial-0','candidate']:shutil.copyfile(w/(v+'-source.json'),out/(v+'-source.json'))
members={};counts={}
def files(folder):return [p for p in (w/folder).rglob('*') if p.is_file() and p.name!='activity-incomplete.sqlite']
def pack(name,paths):
 count=0
 def scrub(info):info.uid=info.gid=0;info.uname=info.gname='';return info
 with tarfile.open(out/name,'w:xz',preset=6) as a:
  for p in sorted(set(paths)):
   n=p.relative_to(w).as_posix();assert n not in members;members[n]=sha(p.read_bytes());a.add(p,arcname=n,recursive=False,filter=scrub);count+=1
 counts[name]=count;print(name,count,flush=True)
pack('observations.tar.xz',sum([files(f) for f in ['initial','measurements','verification/regression','final-profiles','clean-profiles']],[]))
pack('investigation.tar.xz',files('trial-results')+files('cache-results')+[p for p in w.iterdir() if p.is_file() and (p.suffix in ['.py','.cpp','.md','.log','.json'] or p.name.startswith('ncu.')) and p.name!='collect.py' and p.name not in ['control-source.json','diagnostic-source.json','trial-0-source.json','candidate-source.json','trial-cache-source.json']])
pack('verification.tar.xz',[p for p in files('verification') if 'regression' not in p.relative_to(w/'verification').parts]+files('device-checks'))
(out/'files-sha256.json').write_text(json.dumps(members,indent=2)+'\n');(out/'archive-members.json').write_text(json.dumps(counts,indent=2)+'\n')
for n in ['independent-audit.json','clean-audit.json','resources.json','gpu-stages.json','clean-analysis.json','protocol.md','collect.py']:
 shutil.copyfile(w/n,out/n)
print('complete',len(members),flush=True)
