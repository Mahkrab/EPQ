# /// script
# dependencies = ["numpy==2.5.4", "scipy==1.18.1"]
# ///
"""Reduce horizontally uniform particle pressure constraints to layer matrices.

The reduction sums derivatives of individual particles, including reflected
targets. Its row norm remains the full three-dimensional native Jacobi norm;
the norm of the reduced row would be a different preconditioner. No fluid is
advanced and no replacement pressure method is implemented here.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np


@dataclass
class LayerOperator:
    positions: np.ndarray
    constraint: np.ndarray
    jacobian: np.ndarray
    full_row_norm2: np.ndarray
    edges: list
    dx: float
    h: float


def kernel_and_gradient(r,h,volume):
    radius=np.linalg.norm(r,axis=1);q=radius/h;t=np.maximum(0.,1-q)
    coefficient=21/(2*np.pi*h**3)
    w=volume*coefficient*t**4*(1+4*q)
    # r is neighbour minus owner: this is dC/d(owner position).
    g=(20*volume*coefficient/h**2*t**3)[:,None]*r
    return w,g


def site_bias(dx,support):
    axis=np.arange(-int(np.ceil(support)),int(np.ceil(support))+1)*dx
    r=np.stack(np.meshgrid(axis,axis,axis,indexing='ij'),axis=-1).reshape(-1,3)
    return float(kernel_and_gradient(r,support*dx,dx**3)[0].sum()-1)


def assemble(layers,support=2,gamma=.3,closure='free',phase=0.,height=.05,
             profile='mixed',frozen_edges=None,layer_positions=None):
    if layers<2 or support<1 or closure not in ['free','closed','periodic','fixed']:
        raise ValueError('invalid layer geometry')
    dx=height/layers;h=support*dx
    if closure=='periodic' and 2*h>=height:raise ValueError('periodic support must be less than half the depth')
    y=(np.arange(layers)+.5)*dx
    k=(2*np.pi if profile=='periodic' else np.pi/2)/height
    shift=gamma*np.sin(k*y)/k+phase*dx
    positions=np.column_stack((shift,y,np.zeros(layers)))
    if layer_positions is not None:
        positions=np.asarray(layer_positions).copy();shift=positions[:,0];y=positions[:,1]
    J=np.zeros((layers,3*layers));C=np.zeros(layers);diag=np.zeros(layers);graphs=[]
    offsets=np.arange(-int(np.ceil(support))-1,int(np.ceil(support))+2)
    ox,oz=np.meshgrid(offsets,offsets,indexing='ij');ox=ox.ravel();oz=oz.ravel()
    bias=site_bias(dx,support)
    for i in range(layers):
        derivatives={};density=0.;graph=[]
        kinds=['real']
        if closure in ['free','closed']:kinds+=['bottom']
        if closure=='closed':kinds+=['top']
        if closure=='periodic':kinds+=['below','above']
        if closure=='fixed':kinds+=['fixed']
        for kind in kinds:
            js=range(layers) if kind!='fixed' else range(int(np.ceil(support))+1)
            for j in js:
                yy=y[j] if kind!='fixed' else -(j+.5)*dx
                sx=shift[j] if kind!='fixed' else 0.
                if kind=='bottom':yy=-yy
                if kind=='top':yy=2*height-yy
                if kind=='below':yy-=height
                if kind=='above':yy+=height
                if abs(yy-y[i])>=h:continue
                centre=-int(np.rint((sx-shift[i])/dx));xx=ox+centre
                r=np.column_stack((xx*dx+sx-shift[i],np.full(len(xx),yy-y[i]),oz*dx))
                radius=np.linalg.norm(r,axis=1);valid=radius<h
                weights,gradients=kernel_and_gradient(r,h,dx**3)
                for index in np.flatnonzero(valid):
                    key=(kind,j,int(xx[index]),int(oz[index]))
                    if frozen_edges is not None and key not in frozen_edges[i]:continue
                    graph.append(key)
                    density+=weights[index]
                    value=gradients[index]
                    if kind=='real' and j==i and xx[index]==0 and oz[index]==0:continue
                    own=(i,0,0);derivatives[own]=derivatives.get(own,np.zeros(3))+value
                    if kind=='fixed':continue
                    target=(j,int(xx[index]),int(oz[index]));transformed=value.copy()
                    if kind in ['bottom','top']:transformed[1]*=-1
                    derivatives[target]=derivatives.get(target,np.zeros(3))-transformed
        for (j,_,_),g in derivatives.items():J[i,3*j:3*j+3]+=g
        diag[i]=sum(float(g@g) for g in derivatives.values())
        C[i]=density-bias-1
        graphs.append(set(graph))
    return LayerOperator(positions,C,J,diag,graphs,dx,h)


def manufactured(op,gamma,closure,profile='mixed',gravity=9.81):
    n=len(op.constraint);H=.05;y=op.positions[:,1]
    k=(2*np.pi if profile=='periodic' else np.pi/2)/H
    velocity=np.zeros((n,3));velocity[:,0]=np.sin(k*y)
    pressure=np.ones(n)*gravity*H if closure=='periodic' else gravity*(H-y)
    action=-(op.jacobian.T@pressure).reshape(n,3)
    divergence=op.jacobian@velocity.ravel()
    # This exact least-squares projection uses the SAME discrete constraint.
    # It removes iterative/epsilon explanations without changing the formulation.
    gram=op.jacobian@op.jacobian.T
    _,singular,right=np.linalg.svd(op.jacobian,full_matrices=False)
    active=singular>1e-12*singular[0]
    correction=-(right[active].T@(right[active]@velocity.ravel())).reshape(n,3)
    projected=velocity+correction
    projection_residual=float(np.linalg.norm(op.jacobian@projected.ravel())/max(np.linalg.norm(divergence),np.linalg.norm(op.jacobian)*np.linalg.norm(velocity)*1e-12))
    eigen=np.linalg.eigvalsh(gram)
    tangent_force=action[:,0]
    bulk=(y>=2*op.h)&(y<=H-2*op.h)
    centred=(np.eye(n)-np.ones((n,n))/n)@op.jacobian
    _,centred_s,centred_v=np.linalg.svd(centred,full_matrices=False)
    active_c=centred_s>1e-12*centred_s[0]
    centred_correction=centred_v[active_c].T@(centred_v[active_c]@velocity.ravel())
    return {'layers':n,'support':op.h/op.dx,'dx':op.dx,'h':op.h,'gamma':gamma,'closure':closure,
        'divergence_error_H_over_U':float(np.linalg.norm(divergence)/np.sqrt(n)*H),
        'pressure_tangent_rms_over_g':float(np.linalg.norm(tangent_force)/np.sqrt(n)/gravity),
        'pressure_tangent_bulk_rms_over_g':float(np.sqrt(np.mean(tangent_force[bulk]**2))/gravity) if bulk.any() else None,
        'bulk_particles_per_column':int(bulk.sum()),
        'pressure_mode_acceleration_over_U_per_s':float(np.dot(velocity[:,0],tangent_force)/np.dot(velocity[:,0],velocity[:,0])),
        'exact_projection_mode_loss':float(-np.sum(correction*velocity)/np.sum(velocity*velocity)),
        'zero_mean_row_diagnostic_mode_loss':float(velocity.ravel()@centred_correction/np.sum(velocity*velocity)),
        'constant_pressure_force_H_scaled':float(np.linalg.norm(op.jacobian.T@np.ones(n))/np.sqrt(n)*H),
        'exact_projection_velocity_L2':float(np.linalg.norm(correction)/np.linalg.norm(velocity)),
        'exact_projection_residual_relative':projection_residual,
        'constraint_p95_positive':float(np.quantile(np.maximum(op.constraint,0),.95)),
        'minimum_eigenvalue':float(eigen[0]),'maximum_eigenvalue':float(eigen[-1]),
        'maximum_layer_gradient_norm':float(np.linalg.norm(op.jacobian,axis=1).max())}, {
            'positions':op.positions,'C':op.constraint,'J':op.jacobian,'full_row_norm2':op.full_row_norm2,
            'velocity':velocity,'pressure_over_rho':pressure,'pressure_action':action,
            'J_velocity':divergence,'gram_eigenvalues':eigen,'singular_values':singular,
            'zero_mean_row_projected_velocity':velocity-centred_correction.reshape(n,3),
            'projected_velocity':projected}
