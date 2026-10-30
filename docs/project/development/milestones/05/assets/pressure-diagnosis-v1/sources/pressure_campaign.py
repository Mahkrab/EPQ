# /// script
# dependencies = ["numpy==2.5.4", "scipy==1.18.1"]
# ///
"""Retain bounded manufactured pressure matrices and one-step native controls."""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import numpy as np
from tools.performance.pressure_operator import assemble,manufactured
from tools.performance.spatial_audit import frames


def write_json(path,value):
    with path.open('x') as stream:
        json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n');stream.flush();os.fsync(stream.fileno())


def operators(root):
    destination=root/'operators';destination.mkdir();records=[]
    cases=[]
    for closure in ['free','closed','periodic']:
        for n in [4,8,12,16,24,32]:
            for support in [2,3,4]:
                if closure=='periodic' and 2*support>=n:continue
                cases.append((n,support,.3,closure,0.))
    for n in [8,12,24]:
        for closure in ['free','closed','periodic']:
            cases.append((n,2,0.,closure,0.))
    for n in [9,13,25]:cases.append((n,2,.3,'periodic',0.))
    for support in [2,3,4,6,8]:cases.append((64,support,.3,'periodic',0.))
    for closure in ['free','fixed']:
        for phase in [0.,.37]:cases.append((8,2,.3,closure,phase))
    for n,support,gamma,closure,phase in dict.fromkeys(cases):
        label=f'{closure}-n{n}-q{support}-g{gamma}-phase{phase}'
        profile='periodic' if closure=='periodic' else 'mixed'
        op=assemble(n,support,gamma,closure,phase,profile=profile)
        metrics,raw=manufactured(op,gamma,closure,profile)
        metrics['label']=label;metrics['phase']=phase
        path=destination/(label+'.npz')
        with path.open('xb') as stream:np.savez_compressed(stream,**raw)
        metrics['raw_sha256']=hashlib.sha256(path.read_bytes()).hexdigest();records.append(metrics)
        print(label,'force/g',metrics['pressure_tangent_rms_over_g'],'exact loss',metrics['exact_projection_mode_loss'],flush=True)
    write_json(root/'operator-results.json',{'created_utc':datetime.now(timezone.utc).isoformat(),'records':records})


def initial(root,label,n,gamma,replay=None):
    dx=.05/n
    if replay is None:
        axis=(np.arange(4*n)+.5)*dx;y=(np.arange(n)+.5)*dx
        p=np.stack(np.meshgrid(axis,y,axis,indexing='ij'),axis=-1).reshape(-1,3)
        p[:,0]+=gamma*np.sin(np.pi*p[:,1]/.1)/(np.pi/.1);p[:,0]%=.2;v=np.zeros_like(p)
    else:
        samples=frames(replay)
        _,_,_,p,v=next(a for a in samples if abs(a[2]*a[0]['dt']-.2)<1e-9)
    path=root/(label+'.initial')
    with path.open('xb') as stream:stream.write(struct.pack('<I',len(p))+p.astype('<f8').tobytes()+v.astype('<f8').tobytes())
    return path


def native(root,binary,replay,prepare_only=False):
    destination=root/'native';destination.mkdir();cases=[]
    base=dict(n=4,gamma=.3,eps=.02,iterations=24,refresh=1,dt=1/480,support=2,gravity=0.,replay=None)
    cases.append(('base',base))
    for label,change in [('unstrained',{'gamma':0.}),('eps0',{'eps':0.}),('eps002',{'eps':.002}),('eps2',{'eps':.2}),
        ('one-iteration',{'iterations':1}),('96-iterations',{'iterations':96}),('halfdt',{'dt':1/960}),
        ('frozen',{'refresh':0}),('n8',{'n':8}),('n12',{'n':12}),('n12-q3',{'n':12,'support':3}),('n12-q4',{'n':12,'support':4})]:
        cases.append((label,{**base,**change}))
    actual={**base,'gamma':None,'gravity':9.81,'replay':str(replay)}
    cases += [('replay',actual),('replay-frozen',{**actual,'refresh':0}),('replay-eps0',{**actual,'eps':0.})]
    for label,parameters in cases:
        initial_path=initial(destination,label,parameters['n'],parameters['gamma'],Path(parameters['replay']) if parameters['replay'] else None)
        ledger=destination/(label+'.ledger');raw=destination/(label+'.raw')
        command=[str(binary.resolve()),'channel-mixed',str(parameters['n']),'0',str(parameters['dt']),str(parameters['dt']),str(parameters['iterations']),
            '1','.5','4','self','1','0','0','1',str(parameters['gravity']),str(ledger.resolve()),str(initial_path.resolve()),'1',str(parameters['support']),'2','geometric',str(parameters['eps']),str(parameters['refresh'])]
        write_json(destination/(label+'.request.json'),{'parameters':parameters,'command':command,'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'initial_sha256':hashlib.sha256(initial_path.read_bytes()).hexdigest(),'environment':{'OMP_WAIT_POLICY':'PASSIVE'}})
        if prepare_only:continue
        with raw.open('xb') as out,(destination/(label+'.stderr')).open('xb') as error:
            code=subprocess.run(command,stdout=out,stderr=error,env={**os.environ,'OMP_WAIT_POLICY':'PASSIVE'},check=False).returncode
            out.flush();os.fsync(out.fileno());error.flush();os.fsync(error.fileno())
        write_json(destination/(label+'.collection.json'),{'returncode':code,'raw_sha256':hashlib.sha256(raw.read_bytes()).hexdigest()})
        if code:raise RuntimeError(f'native pressure experiment failed: {label}; retained all output')
        print('completed',label,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=['operators','native','prepare-native']);parser.add_argument('root',type=Path);parser.add_argument('--binary',type=Path);parser.add_argument('--replay',type=Path);a=parser.parse_args()
    if a.mode=='operators':operators(a.root)
    else:
        if a.binary is None or a.replay is None:parser.error('native mode requires --binary and --replay')
        native(a.root,a.binary,a.replay,a.mode=='prepare-native')
