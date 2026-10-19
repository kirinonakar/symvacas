"""Compact, frequency-aware polar meshes for certified radial sine surfaces."""
from functools import lru_cache
import math
import sympy as s
from calc_graph_common import graph_function, _finite_real


def angular_surface(expression,x,y,sliders,xmin,xmax,ymin,ymax,count):
    """Resolve atan2's angular detail on rings clustered around its singularity.

    Do not fan triangles into the origin: an angle-dependent height can have
    different directional limits there. The innermost ring is subpixel wide.
    Keep the atan2 branch cut as two independent mesh boundaries.
    """
    angle=s.atan2(y,x)
    if not expression.has(angle) or not (xmin<=0<=xmax and ymin<=0<=ymax):return None
    frequency=1.0
    for term in expression.atoms(s.sin,s.cos):
        coefficient=term.args[0].expand().coeff(angle)
        if coefficient.has(x,y):continue
        try:value=_finite_real(graph_function(coefficient,(),sliders)())
        except (ValueError,TypeError,ZeroDivisionError,OverflowError):value=None
        if value is not None:frequency=max(frequency,abs(value))
    angles=max(64,min(256,max(count*2,math.ceil(frequency*20))))
    angles=4*math.ceil(angles/4)
    radial_count=max(32,count)
    radius=math.hypot(max(abs(xmin),abs(xmax)),max(abs(ymin),abs(ymax)))/math.cos(math.pi/angles)
    if not math.isfinite(radius) or radius<=0:return None
    radii=[radius*max(1e-6,(i/radial_count)**2) for i in range(radial_count+1)]
    snap=lambda value:math.copysign(0.0,value) if abs(value)<1e-14 else value
    circle=[(snap(math.cos(-math.pi+2*math.pi*i/angles)),snap(math.sin(-math.pi+2*math.pi*i/angles))) for i in range(angles+1)]
    fn=graph_function(expression,(x,y),sliders)
    mesh=[];heights=[]
    for r in radii:
        row=[]
        for cx,cy in circle:
            xx,yy=r*cx,r*cy
            try:zz=_finite_real(fn(xx,yy))
            except (ValueError,TypeError,ZeroDivisionError,OverflowError):zz=None
            row.append([xx,yy,zz] if zz is not None else None)
            if zz is not None and xmin<=xx<=xmax and ymin<=yy<=ymax:heights.append(zz)
        mesh.append(row)
    if not heights:return None
    return {'surface':mesh,'angularSurface':True,'zMin':min(heights),'zMax':max(heights),'surfaceSamples':count}


@lru_cache(maxsize=64)
def radial_sine_coefficient(expression,x,y):
    numerator,denominator=s.fraction(expression)
    if denominator!=x*x+y*y or numerator.func!=s.sin:return None
    coefficient=s.cancel(numerator.args[0]/denominator)
    return coefficient if not coefficient.has(x,y) else None


def _sinc_profile(phase):
    if phase<1e-4:
        return 1-phase*phase/6+phase**4/120,-phase/3+phase**3/30
    value=math.sin(phase)/phase
    return value,(math.cos(phase)-value)/phase


@lru_cache(maxsize=32)
def _radial_phases(count):
    # Resolve visible curvature, with larger intervals where 1/phase damps it.
    # Once the entire remaining oscillation is subpixel, a final outer ring is
    # sufficient. Normals there also suppress unresolvable lighting shimmer.
    pixels=200*count/96
    tolerance=.65
    cutoff=pixels/(1.2173*tolerance)
    phases=[];phase=0.0
    while phase<cutoff:
        value,slope=_sinc_profile(phase)
        curvature=min(1/3,1/phase+2/phase**2+2/phase**3) if phase else 1/3
        step=min(math.pi,math.sqrt(8*tolerance*1.2173/(pixels*curvature)))
        phases.append((phase,value,slope,step))
        phase+=step
    return tuple(phases),cutoff


def radial_sine_surface(expression,x,y,sliders,xmin,xmax,ymin,ymax,count):
    coefficient=radial_sine_coefficient(expression,x,y)
    if coefficient is None:return None
    a=_finite_real(graph_function(coefficient,(),sliders)())
    if a is None:return None
    amplitude=abs(a)
    nearest=lambda lo,hi:0 if lo<=0<=hi else min(abs(lo),abs(hi))
    rmin=math.hypot(nearest(xmin,xmax),nearest(ymin,ymax))
    # The cached pixel-error bound uses the central peak's height scale. A
    # cropped view without that peak must use the general sampler instead.
    if rmin>0:return None
    rmax=math.hypot(max(abs(xmin),abs(xmax)),max(abs(ymin),abs(ymax)))
    # Circumscribe the viewport, so polygon chords cannot cut off its corners.
    outer_count=max(12,min(96,count))
    rmax/=math.cos(math.pi/outer_count)
    if not math.isfinite(amplitude*rmax*rmax):return None
    profile,cutoff=_radial_phases(count)
    rings=[]
    pixel_scale=200/max(xmax-xmin,ymax-ymin)
    height_pixels=200*count/96
    def append(radius,phase,value,slope,step):
        angles=max(24,min(96,math.ceil(max(
            2*math.pi*math.sqrt(max(0,radius*pixel_scale)/5.2),
            math.pi*math.sqrt(2*min(phase,cutoff)/step),
            math.pi*math.sqrt(height_pixels*abs(phase*slope)/(1.2173*.65))))))
        # Quantize topology to avoid one-vertex changes on every slider frame.
        angles=min(96,4*math.ceil(angles/4))
        fade=max(0,min(1,2*(cutoff-phase)/cutoff))
        fade=fade*fade*(3-2*fade)
        rings.append([radius,a*value,2*a*amplitude*radius*slope*fade,1 if radius==0 else angles])
    lo,hi=amplitude*rmin*rmin,amplitude*rmax*rmax
    value,slope=_sinc_profile(lo)
    append(rmin,lo,value,slope if lo<cutoff else 0,math.pi/2)
    if amplitude:
        for phase,value,slope,step in profile:
            if lo<phase<hi:append(math.sqrt(phase/amplitude),phase,value,slope,step)
    value,slope=_sinc_profile(hi)
    append(rmax,hi,value,slope if hi<cutoff else 0,math.pi/2)
    rings[-1][3]=outer_count
    values=[ring[1] for ring in rings]
    return {'surface':[],'surfaceRings':rings,'zMin':min(values),'zMax':max(values),
            'surfaceSamples':count}
