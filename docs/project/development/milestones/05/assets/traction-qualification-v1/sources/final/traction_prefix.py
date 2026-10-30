"""Read complete channel frames from a running or rejected raw observation file.

The hash identifies the exact assessed prefix. Trailing bytes remain untouched;
this reader neither repairs a file nor turns an incomplete run into a pass.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct


def screen(path,amplitude=.01,nu=.001):
    with path.open('rb') as stream:
        header=stream.read(104)
        if len(header)!=104:raise ValueError('incomplete channel header')
        magic,n,w,planned=struct.unpack('<4I',header[:16])
        if magic!=0x50424634 or not 0<n<=100000 or w>1000000:raise ValueError('invalid channel header')
        dt=struct.unpack('<d',header[16:24])[0];walls=stream.read(w*24)
        if len(walls)!=w*24:raise ValueError('incomplete wall samples')
        checksum=hashlib.sha256(header+walls);size=104+w*24;records=[]
        while True:
            data=stream.read(4+n*48)
            if len(data)!=4+n*48:break
            step=struct.unpack('<I',data[:4])[0]
            p=struct.unpack('<'+str(3*n)+'d',data[4:4+n*24]);v=struct.unpack('<'+str(3*n)+'d',data[4+n*24:])
            if not all(map(math.isfinite,p+v)):raise ValueError('nonfinite prefix observation')
            shape=[math.sin(math.pi*p[3*i+1]/.1) for i in range(n)]
            exact=math.exp(-nu*(math.pi/.1)**2*step*dt)
            l2=math.sqrt(sum((v[3*i]-amplitude*shape[i]*exact)**2+v[3*i+1]**2+v[3*i+2]**2 for i in range(n))/n)/(amplitude/math.sqrt(2))
            modal=sum(v[3*i]*shape[i] for i in range(n))/(amplitude*sum(t*t for t in shape))
            records.append({'step':step,'time_s':step*dt,'centroid_relative_error':sum(p[1::3])/n/.025-1,
                'L2_velocity_error_over_initial_rms':l2,'amplitude_relative_error':modal/exact-1,
                'axis_K_J_kg':[sum(v[3*i+k]**2 for i in range(n))/(2*n) for k in range(3)]})
            size+=len(data);checksum.update(data)
    if not records:raise ValueError('no complete observation frames')
    return {'planned_steps':planned,'complete_frames':len(records),'prefix_bytes':size,
        'prefix_sha256':checksum.hexdigest(),'unassessed_trailing_bytes':len(data),
        'criterion':'velocity L2 / initial RMS <= .05 at every assessed time',
        'failure_observed':any(r['L2_velocity_error_over_initial_rms']>.05 for r in records),
        'records':records,'reader_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('raw',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    with a.output.open('x') as stream:json.dump(screen(a.raw),stream,indent=2);stream.write('\n')


if __name__=='__main__':main()
