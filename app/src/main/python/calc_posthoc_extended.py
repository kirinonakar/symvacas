"""Scheffé all-contrast and Dunnett control-comparison inference, without SciPy."""
import math
from functools import lru_cache
from calc_shared import require
from calc_advanced_common import integer, vector
from calc_statistics import _f_sf, _t_sf, _studentized_range_grid


@lru_cache(maxsize=64)
def dunnett_grid(sizes, control):
    """Condition on the shared normal control mean and independent residual chi²."""
    _, variance, normalization=_studentized_range_grid(float(sum(sizes)-len(sizes)))
    steps=max(120,2*math.ceil(12*math.sqrt(max(sizes)/sizes[control])))
    step=16/steps
    normal=[]
    for i in range(steps+1):
        z=-8+i*step
        weight=(1 if i in (0,steps) else 4 if i%2 else 2)*step/3
        normal.append((z,weight*math.exp(-z*z/2)/math.sqrt(2*math.pi)))
    ratios=[math.sqrt(sizes[i]/sizes[control]) for i in range(len(sizes)) if i!=control]
    return normal,variance,normalization,ratios


def dunnett_sf(t, sizes, control):
    if t<=0: return 1.
    df=sum(sizes)-len(sizes)
    if len(sizes)==2: return float(2*_t_sf(t,df))
    normal,variance,normalization,ratios=dunnett_grid(sizes,control)
    # Very small tail probabilities concentrate at residual scales O(1/t).
    # Resolve u=t*scale instead of sampling past that entire region on a fixed
    # scale grid. Keep the full-distribution normalization (not the truncated mass).
    upper=math.sqrt(df)+14
    if t>8 and upper/t<variance[-1][0]/2:
        power=4. if df<4 else 1.; step=upper**(1/power)/512
        log_scale=math.log(2)+df/2*math.log(df/2)-math.lgamma(df/2)
        variance=[]
        for i in range(1,513):
            position=i*step; u=position**power; scale=u/t
            weight=(1 if i==512 else 4 if i%2 else 2)*step/3
            log_density=log_scale+(df-1)*(math.log(u)-math.log(t))-df*scale*scale/2-math.log(t)
            variance.append((scale,weight*math.exp(log_density+math.log(power)+(power-1)*math.log(position))))
    total=0.; root2=math.sqrt(2)
    for scale,weight in variance:
        widths=[t*scale*math.sqrt(1+r*r) for r in ratios]
        conditional=0.
        for z,w in normal:
            log_inside=0.
            for ratio,width in zip(ratios,widths):
                # P(any rejection | control z, residual scale); erfc retains tails.
                outside=min(1.,.5*(math.erfc((width-z*ratio)/root2)+math.erfc((width+z*ratio)/root2)))
                if outside>=1: log_inside=-math.inf; break
                log_inside+=math.log1p(-outside)
            conditional+=w*(-math.expm1(log_inside))
        total+=weight*conditional
    raw=float(2*_t_sf(t,df))
    return min(1.,(len(sizes)-1)*raw,max(raw,total/normalization))


@lru_cache(maxsize=64)
def dunnett_critical(sizes,control):
    low,high=0.,4.
    while dunnett_sf(high,sizes,control)>.05: high*=2
    for _ in range(27):
        middle=(low+high)/2
        if dunnett_sf(middle,sizes,control)>.05: low=middle
        else: high=middle
    return (low+high)/2


def calculate(engine,name,a):
    groups=[vector(g) for g in a[0]]
    require(len(groups)>=2 and all(len(g)>=2 for g in groups),'Post-hoc comparisons require at least two groups and two observations per group')
    means=[math.fsum(g)/len(g) for g in groups]
    moments=[(m,math.fsum((v-m)**2 for v in g)/(len(g)-1),len(g)) for g,m in zip(groups,means)]
    sizes=tuple(len(g) for g in groups); k=len(groups); df=sum(sizes)-k
    pooled=math.fsum((n-1)*v for _,v,n in moments)/df
    require(pooled>0,'Post-hoc comparisons require positive pooled within-group variance')
    control=integer(a[1],1,k)-1 if name=='dunnett' and len(a)>1 else 0
    if name=='dunnett':
        critical=dunnett_critical(sizes,control)
        pairs=[(i,control) for i in range(k) if i!=control]
    else:
        low,high=0.,4.
        while float(_f_sf(high,k-1,df))>.05: high*=2
        for _ in range(48):
            middle=(low+high)/2
            if float(_f_sf(middle,k-1,df))>.05: low=middle
            else: high=middle
        critical=math.sqrt((k-1)*(low+high)/2)
        pairs=[(i,j) for i in range(k) for j in range(i+1,k)]
    labels=engine.request.get('statisticsTermLabels',{})
    def label(i): return labels.get('sample:'+str(i+1),'Sample '+str(i+1))
    rows=[]
    for i,j in pairs:
        difference=moments[i][0]-moments[j][0]; se=math.sqrt(pooled*(1/sizes[i]+1/sizes[j])); t=difference/se
        p=dunnett_sf(abs(t),sizes,control) if name=='dunnett' else float(_f_sf(t*t/(k-1),k-1,df))
        rows.append({'Comparison':label(i)+' − '+label(j),'Mean difference':difference,'SE':se,'df':df,'t':t,
                     'Adjusted p value':p,'Lower 95% CI':difference-critical*se,'Upper 95% CI':difference+critical*se})
    engine.note='Independent normal groups, equal variances; pooled one-way ANOVA residual variance. '+(
        'Dunnett two-sided single-step control comparisons: deterministic conditional normal/chi-square quadrature of the joint multivariate t distribution.' if name=='dunnett' else
        'Scheffé simultaneous inference protects all linear contrasts, including these pairwise differences.')
    return {'Method':'Dunnett' if name=='dunnett' else 'Scheffé','Control':label(control) if name=='dunnett' else 'Not applicable',
            'Comparisons':rows,'Assumptions':engine.note}
