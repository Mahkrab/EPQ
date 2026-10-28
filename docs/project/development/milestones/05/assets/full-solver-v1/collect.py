"""Retain raw bounded observations and sanitised activities, never machine registry data."""
from pathlib import Path
import tarfile,json,hashlib,shutil
w=Path('/tmp/maelstrom-fullprofile-20261028');out=w/'retained';out.mkdir();members={};archives={}
def files(folder):return [p for p in (w/folder).rglob('*') if p.is_file() and p.name not in ['activity-incomplete.sqlite','cpu-incomplete.sqlite']]
def scrub(info):info.uid=info.gid=0;info.uname=info.gname='';return info
def pack(name,paths):
 count=0
 with tarfile.open(out/name,'w:xz',preset=6) as arc:
  for p in sorted(set(paths)):
   if p.is_file():
    rel=p.relative_to(w).as_posix();assert not rel.startswith('/') and '..' not in Path(rel).parts;members[rel]=hashlib.sha256(p.read_bytes()).hexdigest();arc.add(p,arcname=rel,recursive=False,filter=scrub);count+=1
 archives[name]=count;print(name,count,flush=True)
def names(values):return [w/n for n in values]
pack('observations.tar.xz',files('measurements')+files('inputs')+files('final-profiles')+names(['measure.py','final-profile.py','final-profile-resume.py','audit.py','analyse-candidate.py','candidate-cpu-analysis.py','queue-analysis.py','candidate-analysis.json','candidate-cpu-analysis.json','queue-analysis.json','regression-summary.json','measurement-progress.log','final-profile-progress.log','final-profile-resume-progress.log','audit-progress.log','audit-2-progress.log','audit-3-progress.log']))
pack('investigation.tar.xz',files('baseline')+files('profiles')+files('trial-results')+names(['baseline.py','profile.py','profile-resume.py','profile-resume2.py','analyse.py','analysis.json','cpu-analysis.py','cpu-analysis.json','make-diagnostic.py','make-candidate-diagnostic.py','trial.py','trial-final-binding.json','trial-tests.log','trial-build.log','plane-tests.log','plane-tests-2.log','control-build.log','diagnostic-build.log','candidate-diagnostic-build.log','baseline-progress.log','profile-progress.log','profile-resume-progress.log','profile-resume2-progress.log','trial-progress.log','prepare-evidence.py','prepare-evidence-progress.log']))
pack('verification.tar.xz',files('verification-initial')+files('verification')+files('postcheck')+files('device-checks')+files('device-checks-2')+files('local-verification')+names(['verify.py','postcheck.py','resources.cpp','device-checks.py','device-checks-2.py','candidate-release.log','candidate-release-isolated.log','candidate-gpu.log','candidate-build.log','verification-progress.log','verification-2-progress.log','device-checks-progress.log','device-checks-2-progress.log','postcheck-progress.log']))
pack('tooling.tar.xz',files('tooling')+files('counter-check')+files('boundary')+files('boundary-final')+names(['counter-check.py','counter-check-progress.log','tooling.py','tooling-progress.log','driver-boundary.cpp','boundary.py','boundary-final.py','build-boundary.py','boundary-build.json','boundary-build-progress.log','boundary-progress.log','boundary-final-progress.log','registry-recovery-verification.json','perf-install.stdout','perf-install.stderr','mingw-install.stdout','mingw-install.stderr','sanitizer-configured.json','sanitizer-configured.stdout','sanitizer-configured.stderr','ncu-first.stdout','ncu-first.stderr','ncu-root.stdout','ncu-root.stderr','ncu-configured.stdout','ncu-configured.stderr'])+[p for p in w.glob('boundary-build-*') if p.suffix in ['.stdout','.stderr']])
(out/'files-sha256.json').write_text(json.dumps(members,indent=2)+'\n');(out/'archive-members.json').write_text(json.dumps(archives,indent=2)+'\n')
root=['control-source.json','candidate-source.json','control.patch','candidate.patch','protocol.md','containment-proof.md','evidence-notes.json','independent-audit.json','rollback-profiling-settings.ps1','collect.py']
for v in ['diagnostic','candidate-diagnostic','trial-0','trial-verification','candidate-prequalification']:root += [v+'-source.json',v+'.patch']
for n in root:shutil.copyfile(w/n,out/n)
print('members',len(members),flush=True)
