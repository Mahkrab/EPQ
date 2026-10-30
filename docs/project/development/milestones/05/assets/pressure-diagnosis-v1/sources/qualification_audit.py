# /// script
# dependencies = ["numpy==2.5.4", "scipy==1.18.1"]
# ///
"""Independently audit physical fields and reconcile complete stage-energy work.

The particle reader and KD kernel calculations are shared with the preceding
spatial study. Calibration constants are independently summed from physical
particle volume, never read back from the native solver's reported constant.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from tools.performance.spatial_audit import density,frames,kernel,continuum,volume


def calibration_constants(mass,h,mode):
    ell=(mass/1000)**(1/3);extent=int(np.ceil(h/ell))
    axis=np.arange(-extent,extent+1)*ell
    xyz=np.stack(np.meshgrid(axis,axis,axis,indexing='ij'),axis=-1).reshape((-1,3))
    lattice=float(np.sum(kernel(np.linalg.norm(xyz,axis=1),h)))
    return ((mass*lattice-1000) if mode=='self' else 0.,mass*lattice/1000 if mode=='ratio' else 1.)


def coherent_kinetic(p,v,spacing):
    bins=np.floor(p/spacing).astype(int)
    _,indices,counts=np.unique(bins,axis=0,return_inverse=True,return_counts=True)
    means=np.column_stack([np.bincount(indices,weights=v[:,k])/counts for k in range(3)])
    return float(np.sum(np.sum(means*means,axis=1)*counts)/(2*len(p)))


def physical_audit(directory, volume_samples=True):
    request=json.loads((directory/"request.json").read_text());boundary=request["parameters"]["boundary"]
    collection=json.loads((directory/"collection.json").read_text())
    path=directory/"states.bin.gz"
    with path.open("rb") as file:
        if hashlib.file_digest(file,"sha256").hexdigest()!=collection["gzip_sha256"]:raise ValueError("gzip hash differs")
    with gzip.open(path,"rb") as file:
        if hashlib.file_digest(file,"sha256").hexdigest()!=collection["raw_sha256"]:raise ValueError("raw hash differs")
    results=[];wall_tree=None
    parameters=request["parameters"]
    for meta,wall,step,p,v in frames(path):
        if wall_tree is None:wall_tree=cKDTree(wall)
        tree=cKDTree(p);h,dx,mass=meta["h"],meta["dx"],meta["mass"]
        rho=density(tree,p,h,mass)
        if boundary:rho+=density(wall_tree,p,h,1000*dx**3 if parameters["wall_volume"] else mass)
        bias,ratio=calibration_constants(mass,h,parameters["calibration"])
        raw_errors=rho/1000-1;errors=(rho-bias)/ratio/1000-1;upper=np.asarray(meta["upper"])
        depth=len(p)*mass/(1000*upper[0]*upper[2]);centre=p.mean(axis=0)
        nn=tree.query(p,k=2,workers=1)[0][:,1]
        xs=(np.arange(24)+.271828)*upper[0]/24;zs=(np.arange(16)+.618034)*upper[2]/16
        xx,zz=np.meshgrid(xs,zs,indexing="ij")
        probes=np.column_stack((xx.ravel(),np.full(xx.size,depth/2),zz.ravel()))
        expected,beta=continuum(probes,upper,h,depth)
        measured=density(tree,probes,h,mass)/1000
        field_error=(measured-expected)/np.maximum(expected,.2)
        column_results={}
        for factor in (1,2):
            nx=int(round(upper[0]/(factor*dx)));nz=int(round(upper[2]/(factor*dx)))
            ix=np.clip((p[:,0]/upper[0]*nx).astype(int),0,nx-1);iz=np.clip((p[:,2]/upper[2]*nz).astype(int),0,nz-1)
            heights=np.zeros(nx*nz);np.maximum.at(heights,ix*nz+iz,p[:,1]+dx/2)
            column_results[str(factor)]={"volume_m3":float(heights.mean()*upper[0]*upper[2]),"wet_fraction":float(np.mean(heights>0))}
        t=step*meta["dt"]
        record={"step":step,"time_s":t,"count":len(p),"dx":dx,"h":h,"mass_kg":len(p)*mass,
                "expected_depth_m":depth,"nominal_layers":depth/dx,"centre":centre.tolist(),
                "centroid_relative_error":float((centre[1]-depth/2)/(depth/2)),
                "height_p95_plus_half_dx_m":float(np.quantile(p[:,1],.95,method="lower")+dx/2),
                "height_relative_error":float((np.quantile(p[:,1],.95,method="lower")+dx/2-depth)/depth),
                "p95_compression":float(np.quantile(np.maximum(errors,0),.95,method="lower")),
                "raw_site_p95_compression":float(np.quantile(np.maximum(raw_errors,0),.95,method="lower")),
                "model_bias_kg_m3":bias,"model_ratio":ratio,
                "max_compression":float(np.max(errors)),"minimum_separation_fraction_dx":float(nn.min()/dx),
                "boundary_violation_m":float(max(0.,np.max(-p),np.max(p-upper))),
                "potential_J_kg":float(parameters["gravity"]*centre[1]),
                "mean_velocity":v.mean(axis=0).tolist(),"axis_kinetic_J_kg":(.5*np.mean(v*v,axis=0)).tolist(),
                "coherent_bin_kinetic_J_kg":coherent_kinetic(p,v,.1),
                "kinetic_J_kg":float(np.sum(v*v)/(2*len(v))),
                "mechanical_J_kg":float(np.sum(v*v)/(2*len(v))+parameters["gravity"]*centre[1]),
                "interparticle_slab_density_p95_absolute_error":float(np.quantile(np.abs(field_error),.95,method="lower")),
                "interparticle_slab_density_mean_signed_error":float(field_error.mean()),
                "geometric_columns":column_results}
        if volume_samples and t>=5-1e-9 and abs(t*2-round(t*2))<1e-7:
            record["field_volume"]=volume(tree,meta,float(p[:,1].max()))
        results.append(record)
    if not results or results[-1]["step"]!=meta["steps"]:raise ValueError("incomplete accepted stream")
    with (directory/"audit.jsonl").open("x") as file:
        for record in results:file.write(json.dumps(record,allow_nan=False)+"\n")
    settled=[r for r in results if 5-1e-9<=r["time_s"]<=6+1e-9]
    summary={"observations":len(results),"final":results[-1],"max_p95_compression":max(r["p95_compression"] for r in results),
             "max_positive_density_error":max(r["max_compression"] for r in results),
             "minimum_separation_fraction_dx":min(r["minimum_separation_fraction_dx"] for r in results),
             "max_energy_gain_J_kg":max(r["mechanical_J_kg"]-results[0]["mechanical_J_kg"] for r in results),
             "settled_mean_centroid_m":float(np.mean([r["centre"][1] for r in settled])) if settled else None,
             "settled_max_kinetic_J_kg":max((r["kinetic_J_kg"] for r in settled),default=None),
             "settled_max_centroid_error":max((abs(r["centroid_relative_error"]) for r in settled),default=None),
             "settled_max_interparticle_error":max((r["interparticle_slab_density_p95_absolute_error"] for r in settled),default=None)}
    (directory/"physical-summary.json").write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n")
    print(directory.name,"centroid",summary["final"]["centroid_relative_error"],"rho",summary["max_p95_compression"],flush=True)
    return summary


def energy_audit(directory):
    request=json.loads((directory/'request.json').read_text());parameters=request['parameters'];dt=parameters['dt'];g=parameters['gravity']
    collection=json.loads((directory/'collection.json').read_text())
    compressed=(directory/'ledger.jsonl.gz').read_bytes();raw=gzip.decompress(compressed)
    if hashlib.sha256(compressed).hexdigest()!=collection['ledger']['gzip_sha256'] or hashlib.sha256(raw).hexdigest()!=collection['ledger']['raw_sha256']:
        raise ValueError('energy ledger checksum differs')
    rows=[json.loads(line) for line in raw.splitlines()]
    if len(rows)!=collection['solver_metrics']['completed_steps']:raise ValueError('ledger step missing')
    maximum={'closure':0.,'gravity':0.,'checkpoint_K':0.,'checkpoint_U':0.,'checkpoint_momentum':0.,'momentum_budget':0.,'density_internal_impulse':0.,'contact_impulse':0.,'viscous_impulse':0.,'viscous_angular':0.,'viscous_increase':0.,'reconstruction':0.}
    indexed={r['step']:r for r in rows}
    for meta,wall,step,p,v in frames(directory/'states.bin.gz'):
        if step==0:continue
        r=indexed[step]['accepted'];maximum['checkpoint_K']=max(maximum['checkpoint_K'],abs(float(np.mean(np.sum(v*v,axis=1))/2)-r['K']))
        maximum['checkpoint_U']=max(maximum['checkpoint_U'],abs(float(g*p[:,1].mean())-r['U']))
        maximum['checkpoint_momentum']=max(maximum['checkpoint_momentum'],float(np.max(np.abs(v.mean(axis=0)-r['mean_v']))))
    phases=['density','contact','plane','viscosity'];windows={}
    for i,r in enumerate(rows):
        if r['step']!=i+1:raise ValueError('unordered ledger steps')
        E=lambda name:r[name]['K']+r[name]['U']
        initial=E('initial');prediction=E('prediction');accepted=E('accepted')
        work=sum(r[k]['dK']+r[k]['dU'] for k in phases)
        maximum['closure']=max(maximum['closure'],abs(accepted-prediction-work))
        maximum['gravity']=max(maximum['gravity'],abs(prediction-initial+.5*g*g*dt*dt))
        if i:
            previous=rows[i-1]['accepted']
            if max(abs(r['initial'][k]-previous[k]) for k in ['K','U'])>1e-10:raise ValueError('energy ledger continuity differs')
        maximum['density_internal_impulse']=max(maximum['density_internal_impulse'],float(np.max(np.abs(np.array(r['density']['impulse_per_kg'])-r['density_wall_impulse_per_kg']))))
        momentum=np.array(r['accepted']['mean_v'])-r['initial']['mean_v']-np.array([0.,-g*dt,0.])-r['density_wall_impulse_per_kg']-np.array(r['plane']['impulse_per_kg'])
        maximum['momentum_budget']=max(maximum['momentum_budget'],float(np.max(np.abs(momentum))))
        for name,key in [('contact','contact_impulse'),('viscosity','viscous_impulse')]:maximum[key]=max(maximum[key],float(np.max(np.abs(r[name]['impulse_per_kg']))))
        maximum['viscous_angular']=max(maximum['viscous_angular'],float(np.max(np.abs(r['viscosity']['angular_impulse_per_kg']))))
        maximum['viscous_increase']=max(maximum['viscous_increase'],r['viscosity']['dK'])
        maximum['reconstruction']=max(maximum['reconstruction'],r['reconstruction_error_m_s'])
    for label,lo,hi in [('all',0,float('inf')),('settled',5,6),('tail',max(0,parameters['duration']-1),parameters['duration'])]:
        selected=[r for r in rows if lo+1e-9<r['time']<=hi+1e-9]
        if not selected:continue
        delta=[r['accepted']['K']+r['accepted']['U']-r['initial']['K']-r['initial']['U'] for r in selected]
        first=selected[0]['initial'];last=selected[-1]['accepted']
        states=[first]+[r['accepted'] for r in selected]
        windows[label]={'steps':len(selected),'state_samples':len(states),
            'start_time_s':selected[0]['time']-dt,'end_time_s':selected[-1]['time'],
            'initial':first,'final':last,'net_energy_change':last['K']+last['U']-first['K']-first['U'],
            'sum_positive_accepted_energy_steps':sum(max(0,d) for d in delta),'maximum_positive_accepted_step':max(delta),
            'maximum_K':max(r['K'] for r in states),'mean_K':float(np.mean([r['K'] for r in states])),
            'minimum_U':min(r['U'] for r in states),'maximum_U':max(r['U'] for r in states),
            'active_density_constraints':sum(r['active_density_constraints'] for r in selected),
            'max_viscous_row_dt':max(r['max_viscous_row_dt'] for r in selected),
            'phase_work':{name:{'dK':sum(r[name]['dK'] for r in selected),'dU':sum(r[name]['dU'] for r in selected),
                'positive_dE':sum(r[name]['positive_dE'] for r in selected),'negative_dE':sum(r[name]['negative_dE'] for r in selected),
                'max_displacement':max(r[name]['max_displacement'] for r in selected),'active_particle_stages':sum(r[name]['active_particle_stages'] for r in selected)} for name in phases}}
    result={'maximum_identity_residuals':maximum,'windows':windows,'every_step_max_energy_above_initial':max(r['accepted']['K']+r['accepted']['U']-rows[0]['initial']['K']-rows[0]['initial']['U'] for r in rows)}
    (directory/'energy-summary.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('directory',type=Path);parser.add_argument('--energy-only',action='store_true');args=parser.parse_args()
    if not args.energy_only:physical_audit(args.directory)
    result=energy_audit(args.directory)
    print(args.directory.name,result['maximum_identity_residuals'])


if __name__=='__main__':main()
