"""Stable coordinates for Gaussian mixed-model fitting and likelihood profiles."""
import math
import mpmath as mp
from calc_shared import require


def coordinates(x, y, fixed=None):
    """Fit near unit scale, retaining the exact affine map to reported units.

    Raw cross-products lose the residual variation when predictors or outcomes
    have a large offset. Fixed raw coefficients become linear constraints in
    these coordinates, including the intercept in ML likelihood profiles.
    """
    columns=list(zip(*x)); n=len(y); p=len(columns)
    centers=[column[0]+math.fsum(v-column[0] for v in column)/n for column in columns[1:]]
    scales=[math.sqrt(math.fsum((v-center)**2 for v in column)/(n-1)) for column,center in zip(columns[1:],centers)]
    require(all(v>0 for v in scales),'Predictors are collinear')
    design=[[1.0]+[(v-center)/scale for v,center,scale in zip(row[1:],centers,scales)] for row in x]
    center=y[0]+math.fsum(v-y[0] for v in y)/n
    scale=math.sqrt(math.fsum((v-center)**2 for v in y)/(n-1))
    require(scale>0,'Mixed model requires residual variation')
    response=[(v-center)/scale for v in y]
    with mp.workdps(50):
        transform=mp.eye(p)
        for j in range(1,p):
            transform[0,j]=-mp.mpf(centers[j-1])/scales[j-1]
            transform[j,j]=1/mp.mpf(scales[j-1])
    constraint=None
    if fixed is not None:
        index,value=fixed
        constraint=([transform[index,j] for j in range(p)],(mp.mpf(value)-(center if index==0 else 0))/scale)
    return design,response,transform,center,scale,scales,constraint


def restore_fit(fields, setup, method, slopes=None):
    """Restore coefficients, information, variance ratios and likelihood units."""
    _,_,transform,center,scale,scales,_=setup
    objective,beta,information,rss,random=fields
    # Preserve the information matrix even for a large shift of the origin.
    # Its inverse is also evaluated at this precision (see covariance below).
    with mp.workdps(50):
        back=transform**-1
        beta=scale*transform*beta; beta[0]+=center
        information=back.T*information*back
        if slopes is not None:
            indices=[0]+list(slopes)
            random_transform=mp.matrix([[transform[i,j] for j in indices] for i in indices])
            random=random_transform*random*random_transform.T
    degrees=len(setup[1])-(len(beta) if method=='reml' else 0)
    correction=2*degrees*math.log(scale)
    if method=='reml': correction+=2*math.fsum(math.log(s) for s in scales)
    return objective+correction,beta,information,rss*scale*scale,random


def covariance(information, sigma):
    """Invert restored GLS information without losing precision to its origin."""
    with mp.workdps(50): return information**-1*sigma


def random_coordinates(x,y,slopes,beta,theta):
    """Evaluate BLUPs and singularity in the same stable fitting coordinates."""
    design,response,transform,center,scale,_,_=coordinates(x,y)
    indices=[0]+list(slopes)
    with mp.workdps(50):
        random_transform=mp.matrix([[transform[i,j] for j in indices] for i in indices])
        back=random_transform**-1
        theta=back*theta*back.T
        shifted=mp.matrix(beta); shifted[0]-=center
        fitted=(transform**-1)*shifted/scale
        residual=[response[i]-sum(row[j]*fitted[j] for j in range(len(row))) for i,row in enumerate(design)]
    z=[[row[j] for j in indices] for row in design]
    return z,residual,theta,scale*random_transform
