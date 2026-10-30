# /// script
# dependencies = ["numpy==2.5.4", "scipy==1.18.1"]
# ///
"""Screen two lightweight meshless shortcuts before building a fluid solver.

Unweighted Voronoi parcels are deliberately distinguished from the full weighted
Power Particles algorithm. Their areas partition space, but need not follow
material parcels under an isochoric map. The WLS prototype separately tests why
linear consistency plus an adjoint does not guarantee constant-pressure forces.
"""
import numpy as np
from scipy.spatial import Voronoi,cKDTree
from scipy.sparse import coo_matrix


def points(n,jitter=.1):
    x=(np.arange(n)+.5)/n
    p=np.stack(np.meshgrid(x,x,indexing='ij'),axis=-1).reshape(-1,2)
    index=np.arange(len(p))[:,None]
    p+=jitter/n*np.sin(index*np.array([1.234,2.345])+np.array([.12,.56]))
    return p%1


def partition(p,basis=None):
    basis=np.eye(2) if basis is None else np.asarray(basis)
    shifts=np.stack(np.meshgrid([-1,0,1],[-1,0,1],indexing='ij'),axis=-1).reshape(-1,2)
    tiled=np.concatenate([(p+s)@basis.T for s in shifts]);diagram=Voronoi(tiled)
    centre=int(np.flatnonzero(np.all(shifts==0,axis=1))[0]);start=centre*len(p);areas=[];centroids=[]
    for i in range(start,start+len(p)):
        region=diagram.regions[diagram.point_region[i]]
        if -1 in region or len(region)<3:raise ValueError('unbounded periodic central cell')
        vertices=diagram.vertices[region];vnext=np.roll(vertices,-1,axis=0);cross=vertices[:,0]*vnext[:,1]-vertices[:,1]*vnext[:,0];area=cross.sum()/2
        centroid=np.sum((vertices+vnext)*cross[:,None],axis=0)/(6*area)
        areas.append(abs(area));centroids.append(centroid)
    return np.asarray(areas),np.asarray(centroids)


def volume_screen(n,jitter):
    p=points(n,jitter);initial,centres=partition(p)
    gamma=.1;F=np.array([[1,gamma],[0,1.]])
    affine,_=partition(p,F)
    moved=p.copy();moved[:,0]+=.1*np.sin(2*np.pi*p[:,1])/(2*np.pi);moved%=1
    sinusoidal,_=partition(moved)
    # Material volumes must stay unchanged under either detF=1 map. Recomputed
    # geometric control cells are not automatically the same material parcels.
    return {'n':n,'jitter_fraction':jitter,'sum_area_error':float(abs(initial.sum()-1)),
        'affine_material_volume_rms_error':float(np.sqrt(np.mean(((affine-initial)/initial)**2))),
        'sinusoidal_material_volume_rms_error':float(np.sqrt(np.mean(((sinusoidal-initial)/initial)**2)))}, {
        'points':p,'initial_area':initial,'affine_area':affine,'sinusoidal_area':sinusoidal,'centroids':centres}


def wls_screen(n,jitter):
    p=points(n,jitter);N=len(p);tree=cKDTree(p,boxsize=1);radius=2.5/n;rows=[];cols=[];values=[]
    for i,neighbours in enumerate(tree.query_ball_point(p,radius)):
        neighbours=np.array([j for j in neighbours if j!=i]);r=p[neighbours]-p[i];r-=np.rint(r)
        w=(1-np.linalg.norm(r,axis=1)/radius)**3;moment=(r*w[:,None]).T@r;b=np.linalg.solve(moment,(r*w[:,None]).T).T
        for k in range(2):
            rows.extend([i]*len(neighbours));cols.extend((2*neighbours+k).tolist());values.extend(b[:,k].tolist())
            rows.append(i);cols.append(2*i+k);values.append(float(-b[:,k].sum()))
    D=coo_matrix((values,(rows,cols)),shape=(N,2*N)).tocsr();volume=np.full(N,1/N)
    G=-(D.T@np.ones(N))/1. # rho1 and equal physical volumes cancel.
    translation=np.tile([.4,-.2],N);load=np.sin(np.arange(N)*.123);impulse=(D.T@load).reshape(N,2).sum(axis=0)
    return {'n':n,'jitter_fraction':jitter,'constant_pressure_force_rms':float(np.linalg.norm(G)/np.sqrt(N)),
        'rigid_translation_divergence_max':float(np.max(np.abs(D@translation))),
        'total_pressure_force':impulse.tolist()}, {'points':p,'constant_pressure_force':G.reshape(N,2),'D_data':D.data,'D_indices':D.indices,'D_indptr':D.indptr,'volume':volume}
