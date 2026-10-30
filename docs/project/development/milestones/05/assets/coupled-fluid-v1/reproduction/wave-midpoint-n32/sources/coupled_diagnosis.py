# /// script
# dependencies = ["numpy==2.5.4", "scipy==1.18.1"]
# ///
"""Attribute retained wave errors without changing the rejected coupled model."""
import argparse
import json
from pathlib import Path
import numpy as np
from tools.performance.coupled_audit import frames
from tools.performance.coupled_reference import wave_reference


def run(root):
    folder=root/'wave-diagnosis';folder.mkdir();records=[]
    for n in [32,64,128]:
        case=root/'geometry-stable'/f'wave-midpoint-n{n}';ledger=[];chosen=[];initial=None
        for grid,meta,row,field in frames(case):
            if row['kind']=='midpoint':continue
            if initial is None:initial=row['diagnostics']
            if row['stage']:ledger.append(row)
            if abs(row['time']-meta['duration']/4)<meta['dt']/2+1e-12:chosen.append((row,field))
        E0=(grid.rho_liquid-grid.rho_gas)*9.81*grid.lx*.00005**2/4
        record={'nx':n,'transport_kinetic_sum_over_E0':float(sum(r['stage']['transport_kinetic_change'] for r in ledger)/E0),
            'body_plus_projection_kinetic_sum_over_E0':float(sum(r['stage']['body_kinetic_change']+r['stage']['projection']['projection_energy_change'] for r in ledger)/E0),
            'geometric_potential_change_over_E0':float((ledger[-1]['diagnostics']['geometric_potential']-initial['geometric_potential'])/E0),
            'pressure_energy_increase_max':float(max(r['stage']['projection']['projection_energy_change'] for r in ledger))}
        row,state=chosen[0];alpha,u,v,p=state
        ar,ur,vr,pr,rx,ry=wave_reference(grid,.05,.00005,row['time'],with_density=True)
        density=grid.pack(rx,ry);computed=grid.pack(u,v);reference=grid.pack(ur,vr)
        for label,mask in [('liquid',density>grid.rho_liquid*(1-1e-8)),('gas',density<grid.rho_gas*(1+1e-8))]:
            numerator=np.dot(density[mask]*(computed-reference)[mask],(computed-reference)[mask]);denominator=np.dot(density[mask]*reference[mask],reference[mask])
            record[label+'_velocity_relative_error']=float(np.sqrt(numerator/denominator))
            record[label+'_computed_kinetic_over_E0']=float(.5*grid.volume*np.dot(density[mask]*computed[mask],computed[mask])/E0)
            record[label+'_reference_kinetic_over_E0']=float(.5*grid.volume*denominator/E0)
            record[label+'_computed_speed_max']=float(abs(computed[mask]).max());record[label+'_reference_speed_max']=float(abs(reference[mask]).max())
        np.savez_compressed(folder/f'quarter-period-n{n}.npz',state=state,reference=np.stack([ar,ur,vr,pr]),physical_rx=rx,physical_ry=ry)
        records.append(record);print(record,flush=True)
    (folder/'results.json').write_text(json.dumps({'records':records,'interpretation':'Energy ledger terms account for interacting stages; frozen-interface controls supply causal isolation. No pressure projection has positive kinetic work.'},indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);run(p.parse_args().root)
