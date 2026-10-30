# /// script
# dependencies = ["numpy==2.5.4", "scipy==1.18.1"]
# ///
"""Conservative phase-volume and staggered momentum fluxes for the coupled study.

The geometric split uses one frozen cell compression indicator in both directions,
so its source cancels for the pressure projection's discrete divergence. Momentum
control-volume mass fluxes are averages of the same material mass fluxes. No state
clipping or post-transport mass repair is performed.
"""
import numpy as np


def neighbour(q,shift,axis,periodic=True,kind='even'):
    out=np.roll(q,shift,axis=axis)
    if axis==0 and not periodic:
        if shift==1:out[0]=0 if kind=='vertical' else q[0]
        elif shift==-1:out[-1]=-q[-2] if kind=='vertical' else q[-1]
        else:raise ValueError('one-cell neighbour required')
    return out


def minmod(a,b,c):return np.where((a*b>0)&(a*c>0),np.sign(a)*np.minimum(np.minimum(abs(a),abs(b)),abs(c)),0.)


def slope(q,axis,periodic=True,kind='even'):
    lower=neighbour(q,1,axis,periodic,kind);upper=neighbour(q,-1,axis,periodic,kind)
    return minmod(2*(q-lower),.5*(upper-lower),2*(upper-q))


def advected(q,flux,axis,periodic=True,kind='even'):
    s=slope(q,axis,periodic,kind)
    left=q+.5*s;right=neighbour(q-.5*s,-1,axis,periodic,kind)
    return flux*np.where(flux>=0,left,right)


def rectangle_fraction(nx,ny,offset,x0,x1,y0,y1):
    """Exact area of a reconstructed half-plane intersected with a rectangle."""
    width=x1-x0;height=y1-y0;ax=abs(nx)*width;ay=abs(ny)*height
    value=offset-nx*x0-ny*y0-np.minimum(nx*width,0)-np.minimum(ny*height,0)
    small=np.minimum(ax,ay);large=np.maximum(ax,ay);denom=np.maximum(2*small*large,1e-300)
    positive=lambda a:np.maximum(a,0)**2
    fraction=(positive(value)-positive(value-ax)-positive(value-ay)+positive(value-ax-ay))/denom
    fraction=np.where(small<1e-12*np.maximum(large,1e-300),value/np.maximum(large,1e-300),fraction)
    return width*height*np.clip(fraction,0,1)


def reconstruction(alpha,periodic_y):
    # Weighted transverse differences estimate an interface normal; plane offset
    # is then inverted analytically to reproduce the actual cell volume exactly.
    above=neighbour(alpha,-1,0,periodic_y);below=neighbour(alpha,1,0,periodic_y)
    smooth_y=above+2*alpha+below
    smooth_x=np.roll(alpha,-1,axis=1)+2*alpha+np.roll(alpha,1,axis=1)
    nx=-(np.roll(smooth_y,-1,axis=1)-np.roll(smooth_y,1,axis=1))
    ny=-(neighbour(smooth_x,-1,0,periodic_y)-neighbour(smooth_x,1,0,periodic_y))
    norm=abs(nx)+abs(ny);nx=np.where(norm>1e-14,nx/np.maximum(norm,1e-300),0.);ny=np.where(norm>1e-14,ny/np.maximum(norm,1e-300),1.)
    small=np.minimum(abs(nx),abs(ny));large=np.maximum(abs(nx),abs(ny));c=np.clip(alpha,0,1)
    threshold=small/(2*large)
    off=np.where(c<threshold,np.sqrt(2*small*large*c),np.where(c>1-threshold,small+large-np.sqrt(2*small*large*(1-c)),large*c+small/2))
    off+=np.minimum(nx,0)+np.minimum(ny,0)
    return nx,ny,off


def reconstructed_y_moment(alpha,periodic_y):
    """First y moment in unit cells; subcell height matters for wave energy."""
    nx,ny,a=reconstruction(alpha,periodic_y);sx=abs(nx);sy=abs(ny)
    t=a-np.minimum(nx,0)-np.minimum(ny,0)
    def integral(value):
        return np.where(value<=0,0.,np.where(value<sy,np.maximum(value,0)**3/(6*np.maximum(sy*sy,1e-300)),value/2-sy/3))
    moment=(integral(t)-integral(t-sx))/np.maximum(sx,1e-300)
    vertical=.5*np.clip(t/np.maximum(sy,1e-300),0,1)**2
    horizontal=.5*np.clip(t/np.maximum(sx,1e-300),0,1)
    moment=np.where(sx<1e-10,vertical,np.where(sy<1e-10,horizontal,moment))
    return np.where(ny<0,np.clip(alpha,0,1)-moment,moment)


def geometric_potential(alpha,grid,gravity):
    moment=reconstructed_y_moment(alpha,grid.periodic_y)
    liquid_y=(grid.y-grid.hy/2)[:,None]*alpha+grid.hy*moment
    return float(gravity*(grid.rho_gas*grid.lx*grid.ly**2/2+(grid.rho_liquid-grid.rho_gas)*grid.volume*liquid_y.sum()))


def geometric_flux(alpha,velocity,dt,h,axis,periodic_y):
    nx,ny,offset=reconstruction(alpha,periodic_y);c=np.minimum(abs(velocity)*dt/h,1.)
    if np.max(abs(velocity)*dt/h)>.5+1e-12:raise ValueError('geometric directional CFL exceeds0.5')
    next_alpha=neighbour(alpha,-1,axis,periodic_y);nextnx=neighbour(nx,-1,axis,periodic_y);nextny=neighbour(ny,-1,axis,periodic_y);nextoff=neighbour(offset,-1,axis,periodic_y)
    if axis==1:
        positive=rectangle_fraction(nx,ny,offset,1-c,1.,0.,1.)
        negative=rectangle_fraction(nextnx,nextny,nextoff,0.,c,0.,1.)
    else:
        positive=rectangle_fraction(nx,ny,offset,0.,1.,1-c,1.)
        negative=rectangle_fraction(nextnx,nextny,nextoff,0.,1.,0.,c)
    flux=np.where(velocity>=0,positive,-negative)*h/dt
    flux=np.where((alpha>=1-1e-14)&(velocity>=0),velocity,flux)
    flux=np.where((next_alpha>=1-1e-14)&(velocity<0),velocity,flux)
    flux=np.where(((alpha<=1e-14)&(velocity>=0))|((next_alpha<=1e-14)&(velocity<0)),0,flux)
    if axis==0 and not periodic_y:flux[-1]=0
    return flux


def divergence_flux(fx,fy,grid,lower_y=None):
    previous=neighbour(fy,1,0,grid.periodic_y)
    if not grid.periodic_y:previous[0]=0 if lower_y is None else lower_y
    return (fx-np.roll(fx,1,axis=1))/grid.hx+(fy-previous)/grid.hy


def phase_transport(alpha,u,v,dt,grid,method='geometric',order=0):
    if method=='muscl':
        fx=advected(alpha,u,1);fy=advected(alpha,v,0,grid.periodic_y)
        if not grid.periodic_y:fy[-1]=0
        result=alpha-dt*divergence_flux(fx,fy,grid)
    elif method=='geometric':
        result=alpha.copy();compression=(alpha>=.5).astype(float);fluxes={}
        for axis in ([1,0] if order%2==0 else [0,1]):
            velocity=u if axis==1 else v;h=grid.hx if axis==1 else grid.hy
            flux=geometric_flux(result,velocity,dt,h,axis,grid.periodic_y)
            prevflux=neighbour(flux,1,axis,grid.periodic_y);prevvel=neighbour(velocity,1,axis,grid.periodic_y)
            if axis==0 and not grid.periodic_y:prevflux[0]=0;prevvel[0]=0
            result-=dt/h*(flux-prevflux-compression*(velocity-prevvel));fluxes[axis]=flux
        fx,fy=fluxes[1],fluxes[0]
    else:raise ValueError('unknown interface transport')
    if not np.isfinite(result).all() or result.min()<-1e-10 or result.max()>1+1e-10:raise ValueError(f'phase bounds failed: {result.min()}, {result.max()}')
    mx=grid.rho_gas*u+(grid.rho_liquid-grid.rho_gas)*fx
    my=grid.rho_gas*v+(grid.rho_liquid-grid.rho_gas)*fy
    return result,mx,my


def momentum_rate(u,v,mx,my,grid):
    uxmass=.5*(mx+np.roll(mx,-1,axis=1));uymass=.5*(my+np.roll(my,-1,axis=1))
    vxmass=.5*(mx+neighbour(mx,-1,0,grid.periodic_y));vymass=.5*(my+neighbour(my,-1,0,grid.periodic_y))
    fxu=advected(u,uxmass,1);fyu=advected(u,uymass,0,grid.periodic_y)
    fxv=advected(v,vxmass,1);fyv=advected(v,vymass,0,grid.periodic_y,'vertical')
    lower=None
    if not grid.periodic_y:
        fyu[-1]=0
        # The first free vertical velocity is one grid interval above the wall.
        # Its lower dual face is half an interval above it, not the physical wall.
        lower_mass=.5*my[0];s=slope(v,0,False,'vertical')[0]
        lower=lower_mass*np.where(lower_mass>=0,.5*v[0],v[0]-.5*s)
    du=-divergence_flux(fxu,fyu,grid);dv=-divergence_flux(fxv,fyv,grid,lower)
    if not grid.periodic_y:dv[-1]=0
    return du,dv
