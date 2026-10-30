# /// script
# dependencies = ["numpy==2.5.4", "scipy==1.18.1"]
# ///
"""Compatible face-flux projection on a fixed rectangular fluid domain.

Cell volume, face area and dual distance define both divergence and its exact
mass adjoint. A fractional last layer locates the planar free surface physically;
it is not rounded to a particle or grid-cell centre. This is an isolated pressure
operator, not a particle advection or production fluid solver.
"""
from dataclasses import dataclass
import numpy as np
from scipy.sparse import coo_matrix,diags
from scipy.sparse.linalg import cg,LinearOperator


@dataclass
class Faces:
    C: object
    volume: np.ndarray
    area: np.ndarray
    distance: np.ndarray
    axis: np.ndarray
    position: np.ndarray
    cells: np.ndarray
    boundary: np.ndarray
    shape: tuple
    lengths: tuple
    rho: float=1000.
    kind: str='free'

    @property
    def mass(self):return self.rho*self.area*self.distance

    @property
    def D(self):return -diags(1/self.volume)@self.C@diags(self.area)

    @property
    def G(self):return diags(1/(self.rho*self.distance))@self.C.T

    @property
    def L(self):return self.C@diags(self.area/(self.rho*self.distance))@self.C.T

    def gradient(self,p,external=0.):
        return self.G@p+self.boundary*external/(self.rho*self.distance)

    def project(self,u,dt,external=0.,tolerance=1e-11,maxiter=5000):
        if dt<=0:raise ValueError('positive timestep required')
        matrix=self.L.tocsr();boundary_gradient=self.boundary*external/(self.rho*self.distance)
        rhs=self.C@(self.area*(u/dt-boundary_gradient));null=not np.any(self.boundary)
        if null:
            rhs-=rhs.mean();gauge=float(matrix.diagonal().mean())
            operator=LinearOperator(matrix.shape,matvec=lambda x:matrix@x+gauge*x.mean())
        else:operator=matrix
        diagonal=matrix.diagonal()
        if np.any(diagonal<=0):raise ValueError('empty pressure cell')
        preconditioner=LinearOperator(matrix.shape,matvec=lambda x:x/diagonal)
        history=[]
        norm=max(np.linalg.norm(rhs),1e-30)
        def observe(p):history.append(float(np.linalg.norm(rhs-operator@p)/norm))
        p,info=cg(operator,rhs,rtol=tolerance,atol=1e-14,M=preconditioner,maxiter=maxiter,callback=observe)
        if info:raise ValueError(f'pressure solve failed: {info}')
        if null:p-=p.mean()
        after=u-dt*self.gradient(p,external)
        return after,p,np.asarray(history)


def mac(shape,lengths=(.2,.05,.2),kind='free',fraction=1.):
    nx,ny,nz=shape
    if min(shape)<2 or kind not in ['free','closed','periodic'] or not 0<fraction<=1:raise ValueError('invalid MAC geometry')
    if kind=='periodic' and fraction!=1:raise ValueError('fractional periodic layer unsupported')
    lx,height,lz=lengths;hx=lx/nx;hz=lz/nz;dy=np.full(ny,height/(ny-1+fraction));dy[-1]*=fraction
    cy=np.cumsum(dy)-dy/2;index=np.arange(nx*ny*nz).reshape(nx,ny,nz)
    xx,yy,zz=np.meshgrid((np.arange(nx)+.5)*hx,cy,(np.arange(nz)+.5)*hz,indexing='ij')
    cells=np.column_stack((xx.ravel(),yy.ravel(),zz.ravel()));vol=np.broadcast_to((hx*hz*dy)[None,:,None],shape).ravel().copy()
    owners=[];neighbours=[];areas=[];distances=[];axes=[];positions=[];boundaries=[]
    for axis in range(3):
        owner=index.ravel();neighbour=np.roll(index,-1,axis=axis).ravel();pos=cells.copy();boundary=np.zeros(len(owner),bool)
        if axis==0:
            pos[:,0]=(pos[:,0]+hx/2)%lx;area=vol/hx;distance=np.full(len(owner),hx)
        elif axis==2:
            pos[:,2]=(pos[:,2]+hz/2)%lz;area=vol/hz;distance=np.full(len(owner),hz)
        else:
            yi=np.indices(shape)[1].ravel();pos[:,1]=np.cumsum(dy)[yi]
            area=np.full(len(owner),hx*hz);distance=(dy[yi]+dy[(yi+1)%ny])/2
            if kind!='periodic':
                top=yi==ny-1;neighbour[top]=-1;distance[top]=dy[-1]/2;boundary[top]=kind=='free'
                keep=~top if kind=='closed' else np.ones(len(owner),bool)
                owner,neighbour,pos,area,distance,boundary=[a[keep] for a in [owner,neighbour,pos,area,distance,boundary]]
            else:pos[:,1]%=height
        owners.append(owner);neighbours.append(neighbour);areas.append(area);distances.append(distance);axes.append(np.full(len(owner),axis));positions.append(pos);boundaries.append(boundary)
    owner=np.concatenate(owners);neighbour=np.concatenate(neighbours);face=np.arange(len(owner));inside=neighbour>=0
    C=coo_matrix((np.r_[-np.ones(len(owner)),np.ones(inside.sum())],(np.r_[owner,neighbour[inside]],np.r_[face,face[inside]])),shape=(len(cells),len(owner))).tocsr()
    return Faces(C,vol,np.concatenate(areas),np.concatenate(distances),np.concatenate(axes),np.concatenate(positions),cells,np.concatenate(boundaries),shape,lengths,kind=kind)


def analytic_pressure(points,lengths=(.2,.05,.2),kind='free'):
    x,y,z=points.T;lx,H,lz=lengths;kx=2*np.pi/lx;kz=2*np.pi/lz;ky={'free':np.pi/(2*H),'closed':np.pi/H,'periodic':2*np.pi/H}[kind]
    p=1000*.5*H*(np.cos(kx*x)*np.cos(kz*z)*np.cos(ky*y)+.2*np.sin(2*kx*x)*np.sin(kz*z)*np.cos(ky*y))
    gradient=np.column_stack((1000*.5*H*(-kx*np.sin(kx*x)*np.cos(kz*z)*np.cos(ky*y)+.4*kx*np.cos(2*kx*x)*np.sin(kz*z)*np.cos(ky*y)),
        -1000*.5*H*ky*(np.cos(kx*x)*np.cos(kz*z)+.2*np.sin(2*kx*x)*np.sin(kz*z))*np.sin(ky*y),
        1000*.5*H*kz*(-np.cos(kx*x)*np.sin(kz*z)*np.cos(ky*y)+.2*np.sin(2*kx*x)*np.cos(kz*z)*np.cos(ky*y))))
    return p,gradient


def metrics(grid,dt=.002):
    n=len(grid.volume);nf=len(grid.area);a=grid.axis;xyz=grid.position
    seed=np.arange(n);p=np.sin(seed*.123);u=np.sin(np.arange(nf)*.321)
    work=float(p@(grid.volume*(grid.D@u))+(grid.G@p)@(grid.mass*u))
    raw_force=grid.gradient(np.ones(n)*17,17 if grid.boundary.any() else 0.)
    shear=np.where(a==0,.5*np.sin(2*np.pi*xyz[:,2]/grid.lengths[2]),0.)
    preserved,_,shear_history=grid.project(shear,dt)
    manufactured,grad=analytic_pressure(xyz,grid.lengths,grid.kind);force=grad[np.arange(nf),a]/grid.rho
    predicted=shear+dt*force
    after,pressure,history=grid.project(predicted,dt)
    expected_p,_=analytic_pressure(grid.cells,grid.lengths,grid.kind)
    if not grid.boundary.any():expected_p-=expected_p.mean()
    error=float(np.sqrt(np.sum(grid.mass*(after-shear)**2)/np.sum(grid.mass*shear**2)))
    pressure_error=float(np.sqrt(np.sum(grid.volume*(pressure-expected_p)**2)/np.sum(grid.volume*expected_p**2)))
    kinetic=lambda v:float(.5*np.dot(grid.mass*v,v))
    result={'shape':grid.shape,'volume_m3':float(grid.volume.sum()),'faces':nf,'adjoint_work_error':abs(work),
        'constant_pressure_acceleration_max':float(np.max(np.abs(raw_force))),
        'shear_divergence_max':float(np.max(np.abs(grid.D@shear))),
        'shear_preservation_relative':float(np.linalg.norm(preserved-shear)/np.linalg.norm(shear)),
        'manufactured_velocity_error':error,'manufactured_pressure_error':pressure_error,
        'pressure_iterations':len(history),'solve_relative_residual':float(history[-1]) if len(history) else 0.,
        'projection_kinetic_change_J':kinetic(after)-kinetic(predicted)}
    if grid.kind=='periodic':
        random_after,_,_=grid.project(u,dt)
        result['momentum_impulse']=[float(np.sum(grid.mass[a==k]*(random_after-u)[a==k])) for k in range(3)]
    elif grid.kind=='free':
        hydro_predict=np.where(a==1,-9.81*dt,0.)
        hydro,ph,hist=grid.project(hydro_predict,dt)
        exact=1000*9.81*(grid.lengths[1]-grid.cells[:,1]);result['hydrostatic_pressure_relative']=float(np.linalg.norm(ph-exact)/np.linalg.norm(exact));result['hydrostatic_velocity_max']=float(np.max(np.abs(hydro)))
        pp=ph.reshape(grid.shape).mean(axis=(0,2));yy=grid.cells.reshape(*grid.shape,3)[0,:,0,1]
        bed=pp[0]+(pp[0]-pp[1])/(yy[1]-yy[0])*yy[0]
        result['bed_force_relative_error']=float(abs(bed*grid.lengths[0]*grid.lengths[2]/(grid.rho*grid.volume.sum()*9.81)-1))
        result['free_surface_volume_rate_m3_s']=float(np.sum(grid.area[grid.boundary]*hydro[grid.boundary]))
    return result,{'cell_position':grid.cells,'volume':grid.volume,'face_position':grid.position,'axis':a,'area':grid.area,'dual_distance':grid.distance,
        'manufactured_pressure':pressure,'exact_pressure':expected_p,'input_velocity':predicted,'projected_velocity':after,'exact_velocity':shear,'history':history}
