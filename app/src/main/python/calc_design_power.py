"""Fixed-design z/proportion/variance-ratio power and integer sample sizes."""
import math
from statistics import NormalDist
from calc_shared import require
from calc_advanced_common import number, integer, option
from calc_statistics import _normal_sf, _f_sf
from calc_advanced_research import critical


def design_power(design,effect,n,alpha,tail,baseline):
    require(design in ('z','proportion','proportion2','variance'),'Choose z, proportion, proportion2 or variance')
    require(tail in ('two','greater','less'),'Choose two, greater or less')
    if design=='variance':
        require(effect>0,'Alternative variance ratio must be positive')
        df=n-1
        upper=critical(alpha/2 if tail=='two' else alpha,df,df)
        lower=1/upper
        if tail=='two':return float(1-_f_sf(lower/effect,df,df)+_f_sf(upper/effect,df,df))
        return float(_f_sf(upper/effect,df,df)) if tail=='greater' else float(1-_f_sf(lower/effect,df,df))
    z=NormalDist().inv_cdf(1-alpha/(2 if tail=='two' else 1))
    if design=='z':
        shift=effect*math.sqrt(n);ratio=1.
    else:
        require(0<baseline<1 and 0<effect<1,'Proportions must lie strictly between 0 and 1')
        if design=='proportion':
            shift=(effect-baseline)*math.sqrt(n/(baseline*(1-baseline)));ratio=math.sqrt(effect*(1-effect)/(baseline*(1-baseline)))
        else:
            pooled=(effect+baseline)/2
            shift=(effect-baseline)*math.sqrt(n/(2*pooled*(1-pooled)));ratio=math.sqrt((effect*(1-effect)+baseline*(1-baseline))/(2*pooled*(1-pooled)))
    power=0.
    if tail in ('two','greater'):power+=float(_normal_sf((z-shift)/ratio))
    if tail in ('two','less'):power+=float(_normal_sf((z+shift)/ratio))
    return min(1.,max(0.,power))


def calculate(engine,name,a):
    design=option(a,0,'z');effect=number(a[1]);alpha=number(a[3]) if len(a)>3 else .05;tail=option(a,4,'two');baseline=number(a[5]) if len(a)>5 else .5
    require(0<alpha<1,'Alpha must be between 0 and 1')
    note='Fixed sample size, independent observations, no continuity correction. z: effect=(alternative−null mean)/known population SD, n observations. Proportion: effect=p1, baseline=p0, null-based z cutoff with alternative-based variance. Proportion2: effect=pA, baseline=pB, equal n per independent arm, pooled-null z cutoff. Proportion powers use the normal approximation; small expected counts need exact methods. Variance: effect=variance A/variance B, equal n per independent normal arm, exact central-F alternative scaling. No sequential design or repeated-look correction.'
    if name=='designpower':n=integer(a[2],2,1000000,capacity=True)
    else:
        target=number(a[2]);require(alpha<target<1,'Target power must exceed alpha and be below 1')
        null=1. if design=='variance' else baseline if design in ('proportion','proportion2') else 0.
        require(effect!=null,'Alternative must differ from the null')
        require(tail=='two' or tail=='greater' and effect>null or tail=='less' and effect<null,'Alternative is opposite to the chosen one-sided test')
        lo,hi=1,2
        while design_power(design,effect,hi,alpha,tail,baseline)<target:
            lo=hi;hi*=2;require(hi<=1000000,'Required sample size exceeds 1,000,000 per arm')
        while hi-lo>1:
            mid=(lo+hi)//2
            if design_power(design,effect,mid,alpha,tail,baseline)>=target:hi=mid
            else:lo=mid
        n=hi
    power=design_power(design,effect,n,alpha,tail,baseline)
    curve_sizes=sorted(set(max(2,round(n*factor)) for factor in (.25,.5,.75,1.,1.25,1.5,2.)))
    engine.statistics_plots=[{'kind':'research-scatter','title':'Fixed-design power','points':[[size,design_power(design,effect,size,alpha,tail,baseline)] for size in curve_sizes],
                              'trend':[[size,design_power(design,effect,size,alpha,tail,baseline)] for size in curve_sizes],'xlabel':'n per arm' if design in ('proportion2','variance') else 'n','ylabel':'Power'}]
    return {'Design':design,'Effect / alternative':effect,'Baseline proportion':baseline if design in ('proportion','proportion2') else None,
            'n per arm' if design in ('proportion2','variance') else 'n':n,'Total n':n*(2 if design in ('proportion2','variance') else 1),'power':power,'alpha':alpha,'Alternative':tail,
            **({'Target power':target,'Power at n−1':design_power(design,effect,n-1,alpha,tail,baseline) if n>2 else None} if name=='designsize' else {}),'Assumptions':note}
