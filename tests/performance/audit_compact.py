"""Check the storage experiment from raw output, independently of its collector.

Physical components use binary32 equality, including signed zero. Only binary64
timing accumulation has a sub-nanosecond reconciliation budget.
"""

import argparse
import json
import math
from pathlib import Path
import statistics
import struct

from tests.performance.audit import physical, read, same, total


def close(left, right):
    return math.isclose(left, right, abs_tol=1e-10, rel_tol=1e-12)


def completed(process, result, steps, warnings=False):
    if (process['exit_code'] != 0 or process['timed_out'] or process['interrupted']
            or result['status'] not in (('completed', 'completed_with_warnings') if warnings else ('completed',))
            or result['failures'] or result['completed_steps'] != str(steps)
            or [s['completed_steps'] for s in result['steps']] != [str(i) for i in range(1, steps+1)]):
        raise ValueError('incomplete or failed experiment work')
    if not warnings and any(s['warning'] for s in result['steps']):
        raise ValueError('warning-bearing primary work')


def audit(root: Path, summary_path: Path) -> dict:
    summary = json.loads(summary_path.read_bytes())
    campaign = json.loads((root/'campaign.json').read_bytes())
    comparisons = 0
    for count in [64,216,512,1000,1728,4096,8000]:
        _, reference = read(root/f'controls/{count:06}')
        for kind in ['warmup','profile']:
            p,d = read(root/f'regression/{count:06}/{kind}')
            completed(p,d,480)
            if not same(physical(reference),physical(d)):
                raise ValueError('regression components differ')
            comparisons += 1
    _, reference = read(root/'controls/008000')
    for variant in ['bitset','compact']:
        values=[]
        for name in ['warmup',*[f'sample-{i}' for i in range(1,6)]]:
            p,d=read(root/f'paired/{variant}/{name}')
            completed(p,d,480)
            if d['execution'] != {'mode':'cuda','device':0,'threads':128}:
                raise ValueError('primary resource selection differs')
            if d['metadata']['build_revision'] != campaign['implementations'][variant]['revision']:
                raise ValueError('primary source identity differs')
            if not same(physical(reference),physical(d)):
                raise ValueError('paired components differ')
            comparisons += 1
            if name != 'warmup':values.append(total(d,'total'))
        actual=summary['primary'][variant]
        if not close(statistics.median(values),actual['median_solver_s']):
            raise ValueError('false paired median')
        if not close(min(values),actual['minimum_s']) or not close(max(values),actual['maximum_s']):
            raise ValueError('false paired range')
    pilots=0
    cores=0
    for n in [8000,32768,110592,262144,512000]:
        target=root/f'capacity/{n:06}'
        admission=json.loads((target/'admission.json').read_bytes())
        expected=88*n+32*(1<<(n-1).bit_length())+96+8*(n+1)+744*n
        ceiling=min(6*1024**3,admission['gpu_total']*3//5,max(0,admission['gpu_free']-2*1024**3))
        if admission['initial_lattice_estimate_bytes'] != expected or admission['ceiling_bytes'] != ceiling:
            raise ValueError('false initial allocation estimate')
        if not admission['admitted']:
            if (target/'pilot').exists():raise ValueError('unsafe pilot executed')
            continue
        p,cpu=read(target/'cpu-pilot');completed(p,cpu,4)
        p,gpu=read(target/'pilot');completed(p,gpu,4)
        if not same(physical(cpu),physical(gpu)):raise ValueError('capacity pilot components differ')
        pilots+=1
        long=json.loads((target/'long-run-admission.json').read_bytes())
        estimate=total(gpu,'total')*120
        if not close(estimate,long['projected_480_step_s']) or long['admitted'] != (estimate<=90):
            raise ValueError('false long-run admission')
        if (target/'core').exists():
            if not long['admitted']:raise ValueError('impractical trajectory executed')
            p,d=read(target/'core');completed(p,d,480,warnings=True)
            total(d,'total')
            if (target/'historical-bitset-core').exists():
                _, historical=read(target/'historical-bitset-core')
                if not same(physical(historical),physical(d)):
                    raise ValueError('historical capacity endpoint/diagnostics differ')
            for particle in d['final_snapshot']['particles']:
                for quantity in ['position_m','velocity_m_s']:
                    if any(not math.isfinite(v) for v in particle[quantity].values()):
                        raise ValueError('non-finite accepted endpoint')
                xyz={k:struct.unpack('!f',struct.pack('!f',v))[0] for k,v in particle['position_m'].items()}
                for plane in d['input']['planes']:
                    offset=struct.unpack('!f',struct.pack('!f',plane['offset_m']))[0]
                    if sum(xyz[k]*plane['normal'][k] for k in ['x','y','z']) < offset:
                        raise ValueError('escaped accepted endpoint')
            cores+=1
    return {'passed':True,'exact_observation_rich_comparisons':comparisons,
            'exact_independent_capacity_pilots':pilots,'complete_finite_plane_compliant_capacity_endpoints':cores,
            'quality_scope':'CFL warnings and absent density qualification remain diagnostic limitations'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    parser.add_argument('summary',type=Path)
    args=parser.parse_args()
    print(json.dumps(audit(args.directory,args.summary),indent=2))
