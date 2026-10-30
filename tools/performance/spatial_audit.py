# /// script
# dependencies = ["numpy==2.5.4", "scipy==1.18.1"]
# ///
"""Independent physical audits use KD trees and continuum slab quadrature.

The solver uses a flat cell grid. This reader instead evaluates point and field
density with SciPy's tree, and reconstructs volume independently of centroids.
Kernel-surface volume is compared with the identically reconstructed analytic
slab so convolution and sampling biases are explicit rather than fitted away.
"""
from __future__ import annotations

import argparse
from functools import lru_cache
import gzip
import hashlib
import json
from pathlib import Path
import struct

import numpy as np
from scipy.spatial import cKDTree


def kernel(distance, h):
    q=np.asarray(distance)/h
    return 21/(2*np.pi*h**3)*np.maximum(0.,1-q)**4*(1+4*q)


def density(tree, queries, h, mass):
    pairs=tree.sparse_distance_matrix(cKDTree(queries),h,output_type="coo_matrix")
    return np.bincount(pairs.col,weights=mass*kernel(pairs.data,h),minlength=len(queries))


@lru_cache(maxsize=8192)
def fraction(sx, lo_y, hi_y, sz, order=24):
    """Integrate the unit-support C2 kernel over a clipped rectangular volume."""
    nodes,weights=np.polynomial.legendre.leggauss(order)
    def axis(lo,hi):
        return lo+(nodes+1)*(hi-lo)/2,weights*(hi-lo)/2
    x,wx=axis(-1,min(1,sx));y,wy=axis(max(-1,lo_y),min(1,hi_y));z,wz=axis(-1,min(1,sz))
    if lo_y>=hi_y or lo_y>=1 or hi_y<=-1:
        return 0.
    radius=np.sqrt(x[:,None,None]**2+y[None,:,None]**2+z[None,None,:]**2)
    values=21/(2*np.pi)*np.maximum(0.,1-radius)**4*(1+4*radius)
    return float(np.sum(values*wx[:,None,None]*wy[None,:,None]*wz[None,None,:]))


def continuum(points, upper, h, depth):
    result=[];support=[]
    full=fraction(1.,-1.,1.,1.)
    for x,y,z in points:
        sx=round(min(1.,x/h,(upper[0]-x)/h),10)
        sz=round(min(1.,z/h,(upper[2]-z)/h),10)
        lo=round(max(-1.,(y-upper[1])/h),10);hi=round(min(1.,y/h),10)
        beta=fraction(sx,lo,hi,sz)/full
        fluid_lo=round(max(-1.,(y-depth)/h),10)
        gamma=fraction(sx,fluid_lo,hi,sz)/full if fluid_lo<hi else 0.
        support.append(beta);result.append(gamma)
    return np.asarray(result),np.asarray(support)


def vertical_measure(values, y, threshold):
    """Piecewise-linear threshold crossings give height and occupied thickness."""
    a,b=values[:,:-1],values[:,1:]
    above_a,above_b=a>=threshold,b>=threshold
    distance=np.diff(y)[None,:]
    cross=np.divide(threshold-a,b-a,out=np.zeros_like(a),where=b!=a)
    amount=np.where(above_a & above_b,1.,np.where(above_a, cross,np.where(above_b,1-cross,0.)))
    thickness=np.sum(np.clip(amount,0,1)*distance,axis=1)
    top=np.max(np.where(above_a | above_b,y[:-1][None,:]+np.where(above_b,1.,cross)*distance,0.),axis=1)
    return thickness,top


def volume(tree, meta, maximum_y, grid_factor=.5):
    upper=np.asarray(meta["upper"]);dx,h=meta["dx"],meta["h"]
    depth=meta["count"]*meta["mass"]/1000/(upper[0]*upper[2])
    nx=int(np.ceil(upper[0]/(dx*grid_factor)));nz=int(np.ceil(upper[2]/(dx*grid_factor)))
    x=(np.arange(nx)+.5)*upper[0]/nx;z=(np.arange(nz)+.5)*upper[2]/nz
    y=np.linspace(0,min(upper[1],max(maximum_y,depth)+h),int(np.ceil((max(maximum_y,depth)+h)/(dx*grid_factor/2)))+1)
    xx,zz=np.meshgrid(x,z,indexing="ij")
    horizontal=np.column_stack((xx.ravel(),zz.ravel()))
    queries=np.column_stack((np.repeat(horizontal[:,0],len(y)),np.tile(y,len(horizontal)),np.repeat(horizontal[:,1],len(y))))
    raw=density(tree,queries,h,meta["mass"])/1000
    expected,beta=continuum(queries,upper,h,depth)
    observed=(raw/beta).reshape((-1,len(y)));reference=(expected/beta).reshape(observed.shape)
    area=upper[0]*upper[2]/len(horizontal);physical=meta["count"]*meta["mass"]/1000
    result={"grid_factor":grid_factor,"probes":len(queries),"physical_reference_m3":physical}
    for threshold in (.45,.5,.55):
        length,top=vertical_measure(observed,y,threshold)
        ref_length,ref_top=vertical_measure(reference,y,threshold)
        observed_volume=float(np.sum(length)*area);reference_volume=float(np.sum(ref_length)*area)
        result[str(threshold)]={"observed_reconstruction_m3":observed_volume,
            "analytic_slab_reconstruction_m3":reference_volume,
            "equivalent_volume_m3":physical+observed_volume-reference_volume,
            "relative_volume_error":(observed_volume-reference_volume)/physical,
            "equivalent_mean_height_m":depth+float(np.mean(top-ref_top)),
            "occupied_column_fraction":float(np.mean(top>0))}
    return result


def frames(path):
    opener=gzip.open if path.suffix==".gz" else open
    with opener(path,"rb") as file:
        header=file.read(16)
        if len(header)!=16:raise ValueError("truncated header")
        magic,n,w,steps=struct.unpack("<4I",header)
        if magic!=0x50424634 or n>100000 or w>1000000:raise ValueError("invalid spatial header")
        raw=file.read(88)
        if len(raw)!=88:raise ValueError("truncated constants")
        dt,h,rest,mass,lx,ly,lz,k,dx,inset,contact=struct.unpack("<11d",raw)
        if not (k==2 and 0<dx<h and mass>0):raise ValueError("invalid spatial constants")
        wall=np.frombuffer(file.read(w*24),dtype="<f8")
        if wall.size!=w*3:raise ValueError("truncated walls")
        wall=wall.reshape((-1,3)).copy()
        meta=dict(count=n,steps=steps,dt=dt,h=h,rest=rest,mass=mass,upper=[lx,ly,lz],dx=dx,inset=inset,contact=contact)
        while True:
            head=file.read(4)
            if not head:break
            if len(head)!=4:raise ValueError("truncated step")
            arrays=np.frombuffer(file.read(n*48),dtype="<f8")
            if arrays.size!=n*6:raise ValueError("truncated frame")
            p=arrays[:n*3].reshape((-1,3));v=arrays[n*3:].reshape((-1,3))
            if not np.isfinite(arrays).all():raise ValueError("nonfinite observation")
            yield meta,wall,struct.unpack("<I",head)[0],p.copy(),v.copy()


def audit(directory, volume_samples=True):
    request=json.loads((directory/"request.json").read_text());boundary=request["parameters"]["boundary"]
    collection=json.loads((directory/"collection.json").read_text())
    path=directory/"states.bin.gz"
    with path.open("rb") as file:
        if hashlib.file_digest(file,"sha256").hexdigest()!=collection["gzip_sha256"]:raise ValueError("gzip hash differs")
    with gzip.open(path,"rb") as file:
        if hashlib.file_digest(file,"sha256").hexdigest()!=collection["raw_sha256"]:raise ValueError("raw hash differs")
    results=[];wall_tree=None
    for meta,wall,step,p,v in frames(path):
        if wall_tree is None:wall_tree=cKDTree(wall)
        tree=cKDTree(p);h,dx,mass=meta["h"],meta["dx"],meta["mass"]
        rho=density(tree,p,h,mass)
        if boundary:rho+=density(wall_tree,p,h,mass)
        errors=rho/1000-1;upper=np.asarray(meta["upper"])
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
                "max_compression":float(np.max(errors)),"minimum_separation_fraction_dx":float(nn.min()/dx),
                "boundary_violation_m":float(max(0.,np.max(-p),np.max(p-upper))),
                "kinetic_J_kg":float(np.sum(v*v)/(2*len(v))),
                "mechanical_J_kg":float(np.sum(v*v)/(2*len(v))+9.81*centre[1]),
                "interparticle_slab_density_p95_absolute_error":float(np.quantile(np.abs(field_error),.95,method="lower")),
                "interparticle_slab_density_mean_signed_error":float(field_error.mean()),
                "geometric_columns":column_results}
        if volume_samples and t>=5-1e-9 and abs(t*2-round(t*2))<1e-7:
            record["field_volume"]=volume(tree,meta,float(p[:,1].max()))
        results.append(record)
    if not results or results[-1]["step"]!=meta["steps"]:raise ValueError("incomplete accepted stream")
    with (directory/"audit.jsonl").open("x") as file:
        for record in results:file.write(json.dumps(record,allow_nan=False)+"\n")
    settled=[r for r in results if r["time_s"]>=5-1e-9]
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


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory",type=Path);parser.add_argument("--no-volume",action="store_true")
    args=parser.parse_args();audit(args.directory,not args.no_volume)
