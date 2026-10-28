from pathlib import Path
import subprocess,json,time,hashlib
w=Path('/tmp/maelstrom-fullprofile-20261028');records=[]
for name,args in [('ordinary',['nsys','profile','--gpu-metrics-devices=help']),('wsl-root',['/mnt/c/Windows/System32/wsl.exe','--user','root','--exec','/opt/nvidia/nsight-systems/2026.1.3/target-linux-x64/nsys','profile','--gpu-metrics-devices=help'])]:
 t=time.monotonic();p=subprocess.run(args,capture_output=True,timeout=60);records.append(dict(name=name,command=args,exit=p.returncode,wall_s=time.monotonic()-t,stdout=p.stdout.decode(),stderr=p.stderr.decode(),stdout_sha256=hashlib.sha256(p.stdout).hexdigest(),stderr_sha256=hashlib.sha256(p.stderr).hexdigest()));assert b'Insufficient privilege' in p.stdout+p.stderr
(w/'nsys-counter-check.json').write_text(json.dumps(records,indent=2)+'\n')
