# /// script
# dependencies = ["numpy==2.5.4", "scipy==1.18.1"]
# ///
"""Compare native particle acceleration with an independent Fourier operator."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import numpy as np
from tools.performance.traction_operator import edge_matrix


def main(root,binary):
    destination=root/'native-operator';destination.mkdir(exist_ok=True);records=[]
    for mode,layers,L in [('horizontal-natural',2,.6),('horizontal-natural',4,.2),('horizontal-slip',4,.2),('vertical-slip',8,.2),('vertical-noslip',8,.2),('vertical-mixed',4,.2),('vertical-mixed',8,.2)]:
        label=f'{mode}-{layers}-{L}';raw=destination/(label+'.bin');command=[str(binary.resolve()),str(layers),mode,str(L),'2',str(raw.resolve()),'4']
        metrics=json.loads(subprocess.check_output(command,text=True))
        payload=raw.read_bytes();n=int.from_bytes(payload[:4],'little');arrays=np.frombuffer(payload[4:],dtype='<f8').reshape(3,n,3);p,v,a=arrays
        H=.05;dx=H/layers;upper=lower='natural';ky=kz=0
        if mode.startswith('horizontal'):kz=2*np.pi/L
        if mode=='horizontal-slip':lower=upper='slip'
        if mode=='vertical-slip':lower=upper='slip';ky=np.pi/H
        if mode=='vertical-noslip':lower=upper='noslip';ky=np.pi/H
        if mode=='vertical-mixed':lower='noslip';ky=np.pi/(2*H)
        matrix,conditions=edge_matrix(layers,dx,2,0,kz,lower,upper,.001)
        profile=np.ones(layers) if kz else (np.cos(ky*(np.arange(layers)+.5)*dx) if mode=='vertical-slip' else np.sin(ky*(np.arange(layers)+.5)*dx))
        initial=np.zeros(3*layers,dtype=complex);initial[::3]=profile
        expected=(-matrix@initial).reshape(layers,3)
        yi=np.rint(p[:,1]/dx-.5).astype(int)
        predicted=(expected[yi]*np.exp(1j*kz*p[:,2])[:,None]).imag if kz else expected[yi].real
        difference=float(np.max(np.abs(a-predicted)));closure=abs(metrics['power']+metrics['v_dot_a'])
        if difference>1e-9 or closure>1e-9:raise ValueError(f'native operator disagreement {label}: {difference} {closure}')
        records.append({'label':label,'command':command,'raw_sha256':hashlib.sha256(payload).hexdigest(),'metrics':metrics,'maximum_acceleration_difference':difference,'dissipation_closure':closure})
        print(label,'difference',difference,'power',metrics['power'],flush=True)
    (root/'native-operator-checks.json').write_text(json.dumps({'records':records},indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path);parser.add_argument('binary',type=Path);a=parser.parse_args();main(a.root,a.binary)
