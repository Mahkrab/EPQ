# /// script
# dependencies = ["numpy==2.5.4", "scipy==1.18.1"]
# ///
"""Independent material maps, quadrature and two-layer linear gravity-wave fields.

No tested transport or pressure routine is used to construct these references.
The rigid-lid dispersion relation follows from harmonic velocity potentials,
normal-velocity continuity and pressure continuity at the liquid/gas interface.
"""
import numpy as np
from numpy.polynomial.legendre import leggauss


def circle_fraction(grid,centres,radius,time=0.,speed=0.,shear=0.,quadrature=64):
    nodes,weights=leggauss(quadrature);x=grid.x[:,None]+grid.hx/2*nodes
    x0=(x-speed*time)%grid.lx;result=np.zeros((grid.ny,grid.nx))
    for cx,cy in centres:
        dx=(x0-cx+grid.lx/2)%grid.lx-grid.lx/2
        extent=np.sqrt(np.maximum(radius*radius-dx*dx,0.))
        centre=cy+shear*time*np.sin(2*np.pi*x0/grid.lx)
        for shift in [-grid.ly,0,grid.ly] if grid.periodic_y else [0]:
            lower=centre-extent+shift;upper=centre+extent+shift
            height=np.maximum(0,np.minimum(grid.y[:,None,None]+grid.hy/2,upper)-np.maximum(grid.y[:,None,None]-grid.hy/2,lower))
            height=np.where(abs(dx)<radius,height,0.)
            result+=np.sum(height*weights,axis=2)/(2*grid.hy)
    return np.minimum(result,1.)


def interface_fraction(grid,height,quadrature=16):
    nodes,weights=leggauss(quadrature);x=grid.x[:,None]+grid.hx/2*nodes
    surface=height(x)
    fraction=np.clip((surface[None,:,:]-(grid.y-grid.hy/2)[:,None,None])/grid.hy,0,1)
    return np.sum(fraction*weights,axis=2)/2


def wave_frequency(grid,depth):
    k=2*np.pi/grid.lx;gas=grid.ly-depth
    return np.sqrt((grid.rho_liquid-grid.rho_gas)*9.81*k/(grid.rho_liquid/np.tanh(k*depth)+grid.rho_gas/np.tanh(k*gas)))


def wave_reference(grid,depth,amplitude,time,quadrature=12):
    k=2*np.pi/grid.lx;H=grid.ly;ha=H-depth;omega=wave_frequency(grid,depth)
    nodes,weights=leggauss(quadrature);c=np.cos(omega*time);s=np.sin(omega*time)
    alpha=interface_fraction(grid,lambda x:depth+amplitude*np.cos(k*x)*c,quadrature)
    def integral(kind,xcentre,ycentre):
        xx=xcentre[None,:,None]+grid.hx/2*nodes[None,None,:]
        lo=ycentre[:,None,None]-grid.hy/2;hi=lo+grid.hy
        eta=depth+amplitude*np.cos(k*xx)*c;wl=np.broadcast_to(lo,(grid.ny,grid.nx,quadrature));wh=np.minimum(hi,np.maximum(lo,eta))
        al=wh;ah=np.broadcast_to(hi,wl.shape);rw,ra=grid.rho_liquid,grid.rho_gas
        if kind=='u':
            water=amplitude*omega/k/np.sinh(k*depth)*(np.sinh(k*wh)-np.sinh(k*wl))*np.sin(k*xx)*s
            air=-amplitude*omega/k/np.sinh(k*ha)*(np.sinh(k*(H-al))-np.sinh(k*(H-ah)))*np.sin(k*xx)*s
        elif kind=='v':
            water=-amplitude*omega/k/np.sinh(k*depth)*(np.cosh(k*wh)-np.cosh(k*wl))*np.cos(k*xx)*s
            air=amplitude*omega/k/np.sinh(k*ha)*(np.cosh(k*(H-ah))-np.cosh(k*(H-al)))*np.cos(k*xx)*s
        else:
            water=ra*9.81*ha*(wh-wl)+rw*9.81*(depth*(wh-wl)-(wh*wh-wl*wl)/2)
            water+=rw*amplitude*omega**2/k**2/np.sinh(k*depth)*(np.sinh(k*wh)-np.sinh(k*wl))*np.cos(k*xx)*c
            air=ra*9.81*(H*(ah-al)-(ah*ah-al*al)/2)
            air-=ra*amplitude*omega**2/k**2/np.sinh(k*ha)*(np.sinh(k*(H-al))-np.sinh(k*(H-ah)))*np.cos(k*xx)*c
        if kind=='p':return np.sum((water+air)*weights,axis=2)/(2*grid.hy)
        momentum=np.sum((rw*water+ra*air)*weights,axis=2)/(2*grid.hy)
        rho=np.sum((rw*(wh-wl)+ra*(ah-al))*weights,axis=2)/(2*grid.hy)
        return momentum/rho
    u=integral('u',np.arange(1,grid.nx+1)*grid.hx,grid.y)
    v=integral('v',grid.x,np.arange(1,grid.ny+1)*grid.hy)
    if not grid.periodic_y:v[-1]=0
    p=integral('p',grid.x,grid.y);p-=p.mean()
    return alpha,u,v,p


def height_mode(grid,alpha,depth):
    eta=grid.hy*alpha.sum(axis=0)-depth
    return float(2*np.mean(eta*np.cos(2*np.pi*grid.x/grid.lx))),float(2*np.mean(eta*np.sin(2*np.pi*grid.x/grid.lx)))
