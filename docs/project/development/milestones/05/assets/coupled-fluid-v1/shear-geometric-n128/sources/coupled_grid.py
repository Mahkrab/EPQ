# /// script
# dependencies = ["numpy==2.5.4", "scipy==1.18.1"]
# ///
"""Isolated two-dimensional MAC geometry and compatible variable-density pressure.

Density belongs to material transport. Averaging cell masses defines the staggered
mass used by momentum and by the pressure adjoint; it is not a density floor. The
gas/liquid interface is internal to this fixed rectangular two-fluid domain.
"""
from dataclasses import dataclass
import numpy as np
from scipy.sparse import coo_matrix,diags
from scipy.sparse.linalg import spsolve
from scipy.fft import fft2,ifft2,fft,ifft,dct,idct


@dataclass
class Grid:
    nx:int
    ny:int
    lx:float=.2
    ly:float=.1
    periodic_y:bool=False
    rho_liquid:float=1000.
    rho_gas:float=1.2

    def __post_init__(self):
        if min(self.nx,self.ny)<4 or min(self.lx,self.ly,self.rho_liquid,self.rho_gas)<=0:
            raise ValueError('positive dimensions/densities and at least4 cells required')
        self.hx=self.lx/self.nx;self.hy=self.ly/self.ny;self.volume=self.hx*self.hy
        self.x=(np.arange(self.nx)+.5)*self.hx;self.y=(np.arange(self.ny)+.5)*self.hy
        indices=np.arange(self.nx*self.ny).reshape(self.ny,self.nx);owner=indices.ravel();right=np.roll(indices,-1,axis=1).ravel()
        up=np.roll(indices,-1,axis=0).ravel();keep=np.ones(self.nx*self.ny,bool)
        if not self.periodic_y:keep.reshape(self.ny,self.nx)[-1]=False
        self.vkeep=keep;owners=np.r_[owner,owner[keep]];neighbours=np.r_[right,up[keep]];nf=len(owners);faces=np.arange(nf)
        self.C=coo_matrix((np.r_[-np.ones(nf),np.ones(nf)],(np.r_[owners,neighbours],np.r_[faces,faces])),shape=(len(owner),nf)).tocsr()
        self.area=np.r_[np.full(len(owner),self.hy),np.full(keep.sum(),self.hx)]
        self.distance=np.r_[np.full(len(owner),self.hx),np.full(keep.sum(),self.hy)]

    def pack(self,u,v):return np.r_[u.ravel(),v.ravel()[self.vkeep]]

    def unpack(self,q):
        n=self.nx*self.ny;u=q[:n].reshape(self.ny,self.nx).copy();v=np.zeros(n);v[self.vkeep]=q[n:]
        return u,v.reshape(self.ny,self.nx)

    def density(self,alpha):return self.rho_gas+(self.rho_liquid-self.rho_gas)*alpha

    def face_density(self,alpha):
        rho=self.density(alpha);rx=.5*(rho+np.roll(rho,-1,axis=1));ry=.5*(rho+np.roll(rho,-1,axis=0))
        if not self.periodic_y:ry[-1]=rho[-1]
        return rx,ry

    def divergence(self,u,v):return (-self.C@(self.area*self.pack(u,v))/self.volume).reshape(self.ny,self.nx)

    def project(self,alpha,u,v,dt,method='auto'):
        if dt<=0:raise ValueError('positive timestep required')
        rx,ry=self.face_density(alpha);rho=self.pack(rx,ry);mass=rho*self.volume;before=self.pack(u,v)
        rhs=self.C@(self.area*before/dt);rhs-=rhs.mean()
        coefficient=self.area/(rho*self.distance)
        matrix=self.C@diags(coefficient)@self.C.T
        if method=='auto':method='rectangular-direct' if np.ptp(rho)<1e-12 else 'sparse-direct'
        if method=='rectangular-direct':
            if np.ptp(rho)>1e-12:raise ValueError('constant density required for rectangular direct solve')
            source=(rhs/self.volume).reshape(self.ny,self.nx)
            kx=np.arange(self.nx);ky=np.arange(self.ny)
            eigen=4*np.sin(np.pi*kx/self.nx)**2/self.hx**2
            eigen=eigen[None,:]+4*np.sin(np.pi*ky/(self.ny if self.periodic_y else 2*self.ny))[:,None]**2/self.hy**2
            spectrum=fft2(source) if self.periodic_y else dct(fft(source,axis=1),type=2,axis=0,norm='ortho')
            eigen[0,0]=1.;spectrum*=rho[0]/eigen;spectrum[0,0]=0
            p=(ifft2(spectrum) if self.periodic_y else ifft(idct(spectrum,type=2,axis=0,norm='ortho'),axis=1)).real.ravel()
        elif method=='sparse-direct':
            p=np.zeros(len(rhs));p[1:]=spsolve(matrix[1:,1:].tocsc(),rhs[1:]);p-=p.mean()
        else:raise ValueError('unknown pressure method')
        gradient=(self.C.T@p)/(rho*self.distance);after=before-dt*gradient
        outu,outv=self.unpack(after);norm=np.linalg.norm(rhs)
        residual=float(np.linalg.norm(matrix@p-rhs)/max(norm,1e-30)) if norm>1e-20 else float(np.linalg.norm(matrix@p-rhs))
        delta=after-before
        record={'method':method,'relative_residual':residual,'divergence_dt_max':float(np.max(abs(self.divergence(outu,outv)))*dt),
            'projection_energy_change':float(.5*np.dot(mass*(after+before),delta)),
            'pressure_impulse_x':float(np.sum(mass[:self.nx*self.ny]*delta[:self.nx*self.ny])),
            'pressure_impulse_y':float(np.sum(mass[self.nx*self.ny:]*delta[self.nx*self.ny:])),
            'correction_velocity_max':float(np.max(abs(delta)))}
        return outu,outv,p.reshape(self.ny,self.nx),record

    def diagnostics(self,alpha,u,v,g=0.):
        rx,ry=self.face_density(alpha);mass=self.pack(rx,ry)*self.volume;q=self.pack(u,v);n=self.nx*self.ny
        rho=self.density(alpha)
        return {'liquid_volume':float(alpha.sum()*self.volume),'mass':float(rho.sum()*self.volume),
            'momentum_x':float(np.dot(mass[:n],q[:n])),'momentum_y':float(np.dot(mass[n:],q[n:])),
            'kinetic':float(.5*np.dot(mass*q,q)),'potential':float(g*self.volume*np.sum(rho*self.y[:,None])),
            'alpha_min':float(alpha.min()),'alpha_max':float(alpha.max()),'divergence_max':float(np.max(abs(self.divergence(u,v)))),
            'velocity_max':float(max(np.max(abs(u)),np.max(abs(v))))}
