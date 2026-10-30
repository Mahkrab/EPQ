# /// script
# dependencies = ["numpy==2.5.4", "scipy==1.18.1"]
# ///
"""Audit periodic channel observations against continuum shear and hydrostatics.

Tree-based density, phase-independent field probes and accepted-state energies
are calculated outside the native solver. The original quietness gate remains
separate from agreement with a specified viscous decay solution.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from tools.performance.spatial_audit import frames, kernel, vertical_measure
from tools.performance.qualification_audit import calibration_constants


def density_boundary(request):
    if 'density_boundary' in request:
        model=request['density_boundary']
        if model not in ['fixed','mirrored']:raise ValueError('unknown density boundary model')
        return model
    known={'traction-pbf':'fixed','traction-pbf-mirror':'mirrored','traction-pbf-axis':'mirrored','traction-pbf-modal':'mirrored'}
    name=Path(request['command'][0]).name
    if name not in known:raise ValueError('request must identify its density boundary explicitly')
    return known[name]


def periodic_density(points, queries, h, mass):
    tree=cKDTree(points,boxsize=[.2,0,.2])
    neighbours=tree.query_ball_point(queries,h)
    result=np.zeros(len(queries))
    for i,row in enumerate(neighbours):
        d=queries[i]-points[row]
        d[:,[0,2]]-=np.rint(d[:,[0,2]]/.2)*.2
        result[i]=mass*np.sum(kernel(np.linalg.norm(d,axis=1),h))
    return result


def vertical_fraction(y,lo,hi,h):
    # Both radial and vertical integrals of C2 are polynomials. Explicit
    # support endpoints avoid cancellation in negligible clipped intervals.
    def cumulative(offset):
        q=offset/h
        if q<=-1:return 0.
        if q>=1:return 1.
        t=abs(q)
        half=21*(t/14-t**3/6+t**5/2-2*t**6/3+5*t**7/14-t**8/14)
        return .5+np.sign(q)*half
    return max(0.,float(cumulative(hi-y)-cumulative(lo-y)))


def field_volume(p,meta,grid=16):
    # Irrational strides sample different subcell phases as spacing changes.
    x=(np.arange(grid)*.618033988749895+.2718281828459)%1*.2
    z=(np.arange(grid-3)*.414213562373095+.1414213562373)%1*.2
    y=np.linspace(0,.05+meta['h'],241)
    xx,zz=np.meshgrid(x,z,indexing='ij');horizontal=np.column_stack((xx.ravel(),zz.ravel()))
    queries=np.column_stack((np.repeat(horizontal[:,0],len(y)),np.tile(y,len(horizontal)),np.repeat(horizontal[:,1],len(y))))
    raw=periodic_density(p,queries,meta['h'],meta['mass']).reshape((-1,len(y)))/1000
    beta=np.array([vertical_fraction(yy,0,.1,meta['h']) for yy in y])
    analytic=np.array([vertical_fraction(yy,0,.05,meta['h']) for yy in y])/beta
    values=raw/beta
    result={}
    for threshold in [.45,.5,.55]:
        observed,top=vertical_measure(values,y,threshold)
        expected,expected_top=vertical_measure(analytic[None,:],y,threshold)
        result[str(threshold)]={'relative_volume_error':float((observed.mean()-expected[0])/.05),
            'equivalent_height_m':float(.05+top.mean()-expected_top[0]),
            'relative_height_error':float((top.mean()-expected_top[0])/.05)}
    return {'horizontal_probes':len(horizontal),'vertical_probes':len(y),'thresholds':result}


def audit(root,label,volume=True,destination=None):
    request=json.loads((root/(label+'.request.json')).read_text());params=request['parameters']
    path=root/(label+'.raw.gz')
    if not path.exists():path=root/(label+'.raw')
    boundary_model=density_boundary(request)
    records=[];initial_rms=None;initial_mode=None
    for meta,wall,step,p,v in frames(path):
        t=step*meta['dt'];h=meta['h'];mass=meta['mass'];dx=meta['dx'];mode=params['mode'];U=params['amplitude'];nu=params['nu']
        shape=np.sin(np.pi*p[:,1]/.1) if mode=='channel-mixed' else np.sin(2*np.pi*p[:,2]/.2)
        if mode=='channel-rest':shape=np.zeros(len(p))
        if initial_rms is None:
            initial_mode=U*shape.copy();initial_rms=float(np.sqrt(np.mean(initial_mode**2)))
        rate=nu*(np.pi/.1)**2
        exact=np.zeros_like(v);exact[:,0]=U*shape*np.exp(-rate*t)
        amplitude=float(np.dot(v[:,0],initial_mode)/np.dot(initial_mode,initial_mode)) if U else None
        rho=periodic_density(p,p,h,mass)
        if params['boundary']:
            if boundary_model=='mirrored':
                images=np.concatenate([p[p[:,1]<h].copy(),p[p[:,1]>.1-h].copy()])
                images[:,1]=np.where(images[:,1]<h,-images[:,1],.2-images[:,1])
                rho+=periodic_density(images,p,h,mass)
            else:rho+=periodic_density(wall,p,h,mass)
        bias,_=calibration_constants(mass,h,'self');compression=np.maximum(0,(rho-bias)/1000-1)
        tree=cKDTree(p,boxsize=[.2,0,.2]);separation=tree.query(p,k=2)[0][:,1]
        bulk=(p[:,1]>=h)&(p[:,1]<=.05-h);surface=p[:,1]>.05-h
        x=(np.arange(16)*.618033988749895+.2718281828459)%1*.2
        z=(np.arange(13)*.414213562373095+.1414213562373)%1*.2
        xx,zz=np.meshgrid(x,z,indexing='ij')
        field_error={}
        for name,yy in [('middepth',.025),('free_surface',.05)]:
            probes=np.column_stack((xx.ravel(),np.full(xx.size,yy),zz.ravel()))
            observed=periodic_density(p,probes,h,mass)/1000
            reference=vertical_fraction(yy,0,.05,h)
            field_error[name]={'p95_absolute_relative_error':float(np.quantile(np.abs(observed/reference-1),.95)),
                'mean_relative_error':float(observed.mean()/reference-1)}
        records.append({'step':step,'time_s':t,'centroid_m':float(p[:,1].mean()),
            'centroid_relative_error':float(p[:,1].mean()/.025-1),
            'height_m':float(np.quantile(p[:,1],.95,method='lower')+dx/2),
            'height_relative_error':float((np.quantile(p[:,1],.95,method='lower')+dx/2)/.05-1),
            'mass_kg':len(p)*mass,'kinetic_J_kg':float(np.sum(v*v)/(2*len(p))),
            'axis_kinetic_J_kg':(.5*np.mean(v*v,axis=0)).tolist(),
            'potential_J_kg':float(params['gravity']*p[:,1].mean()),
            'mean_v':v.mean(axis=0).tolist(),'amplitude':amplitude,
            'analytical_amplitude':float(np.exp(-rate*t)),
            'amplitude_relative_error':amplitude/np.exp(-rate*t)-1 if U else None,
            'L2_velocity_error_over_initial_rms':float(np.sqrt(np.mean(np.sum((v-exact)**2,axis=1)))/initial_rms) if U else None,
            'p95_compression':float(np.quantile(compression,.95)),
            'max_compression':float(compression.max()),
            'bulk_count':int(bulk.sum()),'surface_count':int(surface.sum()),
            'bulk_p95_compression':float(np.quantile(compression[bulk],.95)) if bulk.any() else None,
            'surface_p95_compression':float(np.quantile(compression[surface],.95)) if surface.any() else None,
            'interparticle_density':field_error,
            'minimum_separation_over_dx':float(separation.min()/dx),
            'plane_violation_m':float(max(0,meta['inset']-p[:,1].min(),p[:,1].max()-(.1-meta['inset'])))})
        if volume and (step==0 or step==meta['steps']):records[-1]['field_volume']=field_volume(p,meta)
    if not records or records[-1]['step']!=meta['steps']:raise ValueError('incomplete channel observation stream')
    ledger=root/(label+'.ledger.gz');opener=gzip.open
    if not ledger.exists():ledger=root/(label+'.ledger');opener=open
    with opener(ledger,'rt') as stream:stages=[json.loads(line) for line in stream]
    if len(stages)!=meta['steps']:raise ValueError('incomplete accepted-step ledger')
    maxima={'energy_budget':0.,'viscous_identity':0.,'reconstruction':0.,'viscous_increase':0.,'snapshot_K':0.}
    bystep={r['step']:r for r in records}
    for r in stages:
        delta=r['accepted']['K']+r['accepted']['U']-r['initial']['K']-r['initial']['U']
        prediction=r['prediction']['K']+r['prediction']['U']-r['initial']['K']-r['initial']['U']
        work=sum(r[k]['dK']+r[k]['dU'] for k in ['density','plane','contact','viscosity'])
        maxima['energy_budget']=max(maxima['energy_budget'],abs(delta-prediction-work))
        maxima['viscous_identity']=max(maxima['viscous_identity'],abs(r['viscosity']['dK']+r['physical_viscous_loss']+r['viscous_time_loss']))
        maxima['viscous_increase']=max(maxima['viscous_increase'],r['viscosity']['dK'])
        maxima['reconstruction']=max(maxima['reconstruction'],r['reconstruction_error_m_s'])
        if r['step'] in bystep:maxima['snapshot_K']=max(maxima['snapshot_K'],abs(r['accepted']['K']-bystep[r['step']]['kinetic_J_kg']))
    last=records[-1];settled=[r for r in stages if 5-1e-9<=r['time']<=6+1e-9]
    summary={'label':label,'parameters':params,'density_boundary':boundary_model,'observations':len(records),'accepted_steps':len(stages),'final':last,
        'maximum_p95_compression':max(r['p95_compression'] for r in records),
        'maximum_compression':max(r['max_compression'] for r in records),
        'maximum_abs_centroid_error':max(abs(r['centroid_relative_error']) for r in records),
        'minimum_separation_over_dx':min(r['minimum_separation_over_dx'] for r in records),
        'maximum_plane_violation':max(r['plane_violation_m'] for r in records),
        'max_L2_velocity_error':max((r['L2_velocity_error_over_initial_rms'] for r in records if U),default=None),
        'decay_rate_relative_error':float(-np.log(last['amplitude'])/(rate*last['time_s'])-1) if U and last['amplitude']>0 else None,
        'legacy_settled_max_K':max((r['accepted']['K'] for r in settled),default=None),
        'legacy_quietness_pass':max(r['accepted']['K'] for r in settled)<=.00125 if settled else None,
        'energy_maxima':maxima,'physical_viscous_loss':sum(r['physical_viscous_loss'] for r in stages),
        'time_discretisation_viscous_loss':sum(r['viscous_time_loss'] for r in stages),
        'pressure_impulse_per_kg':[sum(r['density']['impulse_per_kg'][k] for r in stages) for k in range(3)],
        'wall_viscous_impulse_per_kg':[sum(r['viscosity']['impulse_per_kg'][k] for r in stages) for k in range(3)],
        'max_condition':max(r['gradient_condition'] for r in stages),'max_cg_residual':max(r['cg_residual'] for r in stages)}
    initial=records[0]['kinetic_J_kg']+records[0]['potential_J_kg']
    summary['maximum_mechanical_energy_gain_J_kg']=max(0.,max(r['accepted']['K']+r['accepted']['U']-initial for r in stages))
    if U and mode=='channel-mixed':
        expected=2*U/np.pi*(np.exp(-rate*last['time_s'])-1)
        summary['analytical_wall_impulse_x_per_kg']=float(expected)
        summary['wall_viscous_impulse_relative_error']=float(abs(summary['wall_viscous_impulse_per_kg'][0]/expected-1))
    output=root if destination is None else destination
    output.mkdir(exist_ok=True,parents=True)
    with (output/(label+'.audit.json')).open('x') as stream:json.dump({'auditor_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'summary':summary,'records':records},stream,indent=2,allow_nan=False);stream.write('\n')
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path);parser.add_argument('label');parser.add_argument('--no-volume',action='store_true');parser.add_argument('--destination',type=Path);a=parser.parse_args()
    print(json.dumps(audit(a.root,a.label,not a.no_volume,a.destination),indent=2))


if __name__=='__main__':main()
