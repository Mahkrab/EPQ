"""Exercise bounded prototype input rejection without changing production APIs."""
import argparse
import json
from pathlib import Path
import struct
if __package__:
    from .dfsph_campaign import invoke
else:
    from dfsph_campaign import invoke


def validate(root):
    folder=root/'validation';folder.mkdir(exist_ok=False);original=(root/'inputs/hydro.bin').read_bytes();cases=[]
    for name,offset,value,expected in [('zero-count',0,0,'bounded particles'),('wrong-support',20,.2,'0.1 m support'),('nan-position',96,float('nan'),'nonfinite input')]:
        raw=bytearray(original);struct.pack_into('<I' if name=='zero-count' else '<f',raw,offset,value);path=folder/(name+'.bin');path.write_bytes(raw);cases.append((name,path,None,expected))
    truncated=folder/'truncated.bin';truncated.write_bytes(original[:-1]);cases.append(('truncated',truncated,None,'byte count differs'))
    cases.append(('nan-dt',root/'inputs/hydro.bin','nan','invalid numerical policy'))
    results=[]
    for name,path,timestep,expected in cases:
        destination=folder/name;command=[root/'dfsph-gpu',path,timestep or 1/240,1,'1,1,1','0,-9.81,0',.1,.1,destination/'unused','benchmark',.025,'solid']
        process=invoke(command,destination,timeout=10);stderr=(destination/'stderr.txt').read_text()
        if process['exit_code']!=1 or expected not in stderr:raise ValueError('input rejection differs '+name)
        results.append({'case':name,'exit_code':1,'expected_error':expected,'passed':True})
    (root/'validation-results.json').write_text(json.dumps(results,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);validate(p.parse_args().root.resolve())
