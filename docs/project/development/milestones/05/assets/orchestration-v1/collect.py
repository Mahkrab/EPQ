"""Retain bounded observations and sanitised activities, excluding native report metadata."""
from pathlib import Path
import tarfile,json,hashlib,shutil
w=Path('/tmp/maelstrom-orchestration-20261028');out=w/'retained';out.mkdir();members={};catalog={}
def files(folder):return [p for p in (w/folder).rglob('*') if p.is_file() and p.name not in ['activity-incomplete.sqlite']]
def names(values):return [w/n for n in values]
def scrub(info):info.uid=info.gid=0;info.uname=info.gname='';return info
def pack(name,paths):
 count=0
 with tarfile.open(out/name,'w:xz',preset=6) as arc:
  for p in sorted(set(paths)):
   if p.is_file():
    rel=p.relative_to(w).as_posix();assert rel not in members;members[rel]=hashlib.sha256(p.read_bytes()).hexdigest();arc.add(p,arcname=rel,recursive=False,filter=scrub);count+=1
 catalog[name]=count;print(name,count,flush=True)
pack('observations.tar.xz',files('measurements')+files('inputs')+files('final-profiles')+files('verification/regression')+names(['measure.py','final-profile.py','audit.py','summaries.py','boundary-analysis.py','binding-analysis.py','boundary-analysis.json','final-control-cpu.py','final-candidate-cpu.py','final-control-analyse.py','final-candidate-analyse.py','final-queue-analysis.py','final-control-analysis.json','final-candidate-analysis.json','final-control-cpu-analysis.json','final-candidate-cpu-analysis.json','final-queue-analysis.json','overhead-summary.json','measurement-progress.log','final-profile-progress.log','audit-progress.log','audit-final-progress.log','audit-readback-progress.log']))
pack('investigation.tar.xz',files('initial')+files('trial-results')+files('micro')+files('graph-micro')+files('mirror-micro')+files('mirror-micro2')+files('all-apis')+names(['initial.py','cpu-analysis.py','analyse.py','queue-analysis.py','analysis.json','cpu-analysis.json','queue-analysis.json','micro.py','readback-boundary.cpp','graph-micro.py','graph-micro-resume.py','graph-boundary.cpp','micro-api-analysis.py','micro-api-analysis.json','mirror-micro.py','mirror-micro2.py','mirror-probe.cpp','mirror-probe-kernel.cu','trial.py','trial-final-binding.json','all-apis.py','binding-probe.cpp','binding-analysis.json','initial-progress.log','micro-progress.log','graph-micro-progress.log','graph-micro-resume-progress.log','mirror-micro-progress.log','mirror-micro2-progress.log','trial-progress.log','all-apis-progress.log','selection.md','control-build.log','diagnostic-build.log','candidate-diagnostic-build.log','trial-tests.log','trial-native.log','trial-build.log','prepare-evidence.py','prepare-evidence-progress.log','make-candidate-diagnostic.py']))
pack('verification.tar.xz',[p for p in files('verification') if 'regression' not in p.relative_to(w/'verification').parts]+files('device-checks')+files('local-verification')+files('postcheck')+files('tooling')+names(['verify.py','device-checks.py','postcheck.py','resources.cpp','tooling.py','local-check.py','cpu-counters.json','verification-progress.log','device-checks-progress.log','postcheck-progress.log','tooling-progress.log']))
(out/'files-sha256.json').write_text(json.dumps(members,indent=2)+'\n');(out/'archive-members.json').write_text(json.dumps(catalog,indent=2)+'\n')
root=['control-source.json','candidate-source.json','control.patch','candidate.patch','protocol.md','selection.md','mirror-proof.md','evidence-notes.json','initial-state.json','independent-audit.json','collect.py']
for v in ['diagnostic','candidate-diagnostic','trial-0']:root += [v+'-source.json',v+'.patch']
for n in root:shutil.copyfile(w/n,out/n)
print('members',len(members),flush=True)
