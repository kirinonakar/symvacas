"""JZS t tests and one-way mixture-g ANOVA, portable to Python/WASM.

BF uses deterministic quadrature on log(g); IID conditional posterior draws
provide effect summaries, with reproducible Monte Carlo error reporting.
"""
import bisect
import math
import random
from calc_shared import require
from calc_advanced_common import vector, number, integer, option, mean
from calc_advanced_research import level_option


def quantile(values,p):
    index=(len(values)-1)*p;lo=int(index);weight=index-lo
    return values[lo]*(1-weight)+values[min(lo+1,len(values)-1)]*weight


def mixture(s0,sse,nu,q,neff,r,steps=1600):
    require(s0>0 and sse>0,'Bayesian tests require positive within-sample residual variance')
    lower=2*math.log(r)-9;upper=max(2*math.log(r)+50,math.log(s0/sse)-math.log(neff)+24)
    step=(upper-lower)/steps;grid=[];logs=[]
    for i in range(steps+1):
        u=lower+i*step;g=math.exp(u);shrink=neff*g/(1+neff*g)
        residual=sse+(s0-sse)/(1+neff*g)
        logweight=math.log(r)-.5*math.log(2*math.pi)-.5*u-r*r/(2*g)-q/2*math.log1p(neff*g)-nu/2*math.log(residual/s0)
        logs.append(logweight+math.log(.5 if i in (0,steps) else 1.));grid.append((g,shrink,residual))
    pivot=max(logs);weights=[math.exp(v-pivot) for v in logs];mass=sum(weights)
    logbf=pivot+math.log(mass*step)
    return logbf,grid,[w/mass for w in weights]


def t_components(first,second,design,null):
    if design=='paired':
        require(len(first)==len(second),'Paired Bayesian t test requires complete matched rows')
        data=[x-y-null for x,y in zip(first,second)]
    elif design=='onesample': data=[x-null for x in first]
    else:
        n1,n2=len(first),len(second);m1,m2=mean(first),mean(second);difference=m1-m2-null;neff=n1*n2/(n1+n2)
        sse=sum((v-m1)**2 for v in first)+sum((v-m2)**2 for v in second)
        return difference,neff,sse+neff*difference*difference,sse,n1+n2-1
    difference=mean(data);n=len(data);sse=sum((v-difference)**2 for v in data)
    return difference,float(n),sse+n*difference*difference,sse,n


def safe_exp(value):return math.exp(value) if value<709 else math.inf


def calculate(engine,name,a):
    anova=name=='bayesanova'
    if anova:
        require(isinstance(a[0],(list,tuple)) and len(a[0])>=2,'Enter at least two independent groups')
        groups=[vector(g,2) for g in a[0]];r=number(a[1]) if len(a)>1 else .5;level=level_option(a,2)
        draws=integer(a[3],2000,100000,capacity=True) if len(a)>3 else 10000;seed=integer(a[4],0,2147483647) if len(a)>4 else 0
        sequential=option(a,5,'1');q=len(groups)-1;n=sum(map(len,groups));nu=n-1;neff=n
        center=sum(sum(g) for g in groups)/n;groupmeans=[mean(g) for g in groups];means=[m-center for m in groupmeans];sizes=list(map(len,groups))
        sse=sum(sum((v-m)**2 for v in g) for g,m in zip(groups,groupmeans));s0=sse+sum(size*m*m for size,m in zip(sizes,means))
        difference=None
    else:
        first=vector(a[0],2);second=vector(a[1],2) if a[1] else [];design=option(a,2,'independent')
        require(design in ('onesample','paired','independent'),'Choose onesample, paired or independent')
        require(design=='onesample' or len(second)>=2,'Enter both samples')
        null=number(a[3]) if len(a)>3 else 0.;r=number(a[4]) if len(a)>4 else math.sqrt(.5);level=level_option(a,5)
        draws=integer(a[6],2000,100000,capacity=True) if len(a)>6 else 10000;seed=integer(a[7],0,2147483647) if len(a)>7 else 0
        sequential=option(a,8,'1');q=1
        difference,neff,s0,sse,nu=t_components(first,second,design,null)
    require(.001<=r<=1000,'Prior scale must be between .001 and 1000')
    require(sequential in ('0','1'),'Sequential graph option must be 0 or 1')
    require(math.isfinite(s0) and s0>0 and sse>0,'Bayesian tests require positive finite within-sample residual variance')
    scale=math.sqrt(s0);s0n=1.;ssen=sse/s0
    logbf,grid,weights=mixture(s0n,ssen,nu,q,neff,r)
    cumulative=[];total=0.
    for w in weights:total+=w;cumulative.append(total)
    rng=random.Random(seed);effects=[]
    for _ in range(draws):
        at=min(len(grid)-1,bisect.bisect_left(cumulative,rng.random()));g,shrink,residual=grid[at]
        sigma=math.sqrt(residual/(2*rng.gammavariate(nu/2,1.)))
        if anova:
            z=[rng.gauss(0,1) for _ in sizes];weighted=sum(math.sqrt(size)*v for size,v in zip(sizes,z))/n
            ss=sum((math.sqrt(size)*shrink*m/scale+sigma*math.sqrt(shrink)*(v-math.sqrt(size)*weighted))**2 for size,m,v in zip(sizes,means,z))
            effects.append(ss/(ss+n*sigma*sigma))
        else:effects.append(rng.gauss(shrink*difference/scale/sigma,math.sqrt(g/(1+neff*g))))
    average=mean(effects);mcse=math.sqrt(sum((v-average)**2 for v in effects)/(draws-1)/draws);effects.sort();tail=(1-level)/2
    sequence=[]
    if sequential=='1':
        length=max(map(len,groups)) if anova else max(len(first),len(second)) if design=='independent' else len(first)
        prefixes=sorted(set([2,length]+[max(2,round(length*i/40)) for i in range(1,41)]))
        for end in prefixes:
            if anova:
                subset=[g[:end] for g in groups];nn=sum(map(len,subset));mm=sum(map(sum,subset))/nn
                gm=[mean(g) for g in subset];ee=sum(sum((v-m)**2 for v in g) for g,m in zip(subset,gm));ss=ee+sum(len(g)*(m-mm)**2 for g,m in zip(subset,gm));nn-=1;effective=nn+1
            else:
                _,effective,ss,ee,nn=t_components(first[:end],second[:end],design,null)
            if ee<=0 or ss<=0:continue
            bf=mixture(1.,ee/ss,nn,q,effective,r,steps=800)[0]
            sequence.append({'n':nn+1 if anova or design=='independent' else nn,'BF10':safe_exp(bf),'log10 BF10':bf/math.log(10)})
    engine.statistics_plots=[]
    if sequence:
        engine.statistics_plots=[{'kind':'research-scatter','title':'Sequential Bayes factor','points':[[p['n'],p['log10 BF10']] for p in sequence],
                                  'trend':[[p['n'],p['log10 BF10']] for p in sequence],'horizontal':[0],'xlabel':'Observations','ylabel':'log10 BF10',
                                  'caption':'Prefixes retain the entered within-group observation order, adding up to one observation per group per step. This path is descriptive; it is not a prospective stopping rule.'}]
    effect_label='Posterior η² (design-weighted group signal)' if anova else 'Posterior standardized effect δ (A − B − null) / σ'
    engine.statistics_full_tables={'Sequential evidence':sequence} if sequence else {}
    return {'Test':'One-way mixture-g ANOVA' if anova else 'JZS '+design+' t test','BF10':safe_exp(logbf),'BF01':safe_exp(-logbf),'log BF10':logbf,
            'Prior scale r':r,'Prior':'g ~ InvGamma(1/2,r²/2); centered group contrasts | σ,g ~ Normal(0, n g σ² (XcᵀXc)⁻¹)' if anova else 'δ ~ Cauchy(0,r); σ² nuisance prior proportional to 1/σ²; common variance for independent groups',
            effect_label:{'posterior mean':average,'credible interval':[quantile(effects,tail),quantile(effects,1-tail)],'MCSE of mean':mcse},
            'credible level':level,'Posterior IID draws':draws,'Seed':seed,'Sequential evidence':sequence[:100],
            'Assumptions':'Independent normal observations; paired t operates on within-subject A−B differences, independent t assumes common variance. Two-sided point-null comparison, BF01=1/BF10. Posterior effects condition on H1; intervals are simulated equal-tailed intervals, not frequentist confidence intervals. BF quadrature integrates a proper effect prior and uses the same nuisance convention under both models. ANOVA compares one common mean against all group means with a design-dependent mixture-g prior; this is not a factorial/repeated-measures ANOVA or a claim of matching JASP default ANOVA priors. Sequential evidence preserves input order and is not a prespecified group-sequential study design.'}
