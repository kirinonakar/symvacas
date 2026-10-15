"""Independent SciPy/statsmodels references; never imported by the app runtime."""
import json
import math
from pathlib import Path
import numpy as np
from scipy import integrate, optimize, stats
import statsmodels.api as sm
from statsmodels.stats.oneway import anova_oneway
from statsmodels.tools.numdiff import approx_hess
from statistics_extensions_schema import OMEGA, META, GROUPS, SURVIVAL

ROOT=Path(__file__).resolve().parents[1]
cases=[]

def add(name,args,expected,tolerance=2e-7):
    cases.append(dict(function=name,arguments=args,expected=[[path,value] for path,value in expected],tolerance=tolerance))


# Direct congeneric covariance likelihood, separately parameterized from the
# engine's profiled uniqueness/eigendecomposition optimization.
data=np.asarray(OMEGA);cov=np.cov(data,rowvar=False);corr=np.corrcoef(data,rowvar=False);p=corr.shape[0]
def omega_objective(params):
    load=params[:p];psi=np.exp(params[p:]);sigma=np.outer(load,load)+np.diag(psi)
    return np.linalg.slogdet(sigma)[1]+np.trace(np.linalg.solve(sigma,corr))
fit=optimize.minimize(omega_objective,np.r_[np.repeat(.7,p),np.repeat(math.log(.5),p)],method='BFGS',options={'gtol':1e-8})
load=fit.x[:p];psi=np.exp(fit.x[p:])
for mode,scale in [('raw',np.sqrt(np.diag(cov))),('standardized',np.ones(p))]:
    signal=np.sum(load*scale)**2;omega=signal/(signal+np.sum(psi*scale**2))
    add('omega',[OMEGA,mode],[(['McDonald ω'],float(omega))],2e-6)

for design in ('onesample','paired','independent'):
    first=np.array([10.,11,9,10,12]);second=np.array([13.,14,12,15,13]);r=math.sqrt(.5)
    if design=='independent':
        t=float(stats.ttest_ind(first,second,equal_var=True).statistic);df=len(first)+len(second)-2;neff=len(first)*len(second)/(len(first)+len(second))
    else:
        values=first if design=='onesample' else first-second;t=float(stats.ttest_1samp(values,0).statistic);df=len(values)-1;neff=len(values)
    # Rouder/Morey t-statistic integral, not the engine's SSE/log-g grid.
    def integrand(g):
        return math.exp(-.5*math.log1p(neff*g)+(df+1)/2*(math.log1p(t*t/df)-math.log1p(t*t/(df*(1+neff*g))))+stats.invgamma.logpdf(g,.5,scale=r*r/2))
    bf=integrate.quad(integrand,0,np.inf,epsabs=1e-10,epsrel=1e-10)[0]
    add('bayesttest',[first.tolist(),[] if design=='onesample' else second.tolist(),design,0,r,.95,20000,17,1],[(['BF10'],bf),(['BF01'],1/bf)])

groups=[np.asarray(g) for g in GROUPS];n=sum(map(len,groups));grand=np.mean(np.concatenate(groups));s0=sum(np.sum((g-grand)**2) for g in groups);sse=sum(np.sum((g-g.mean())**2) for g in groups);r=.5
bf=integrate.quad(lambda g:math.exp(-(len(groups)-1)/2*math.log1p(n*g)-(n-1)/2*math.log((sse+(s0-sse)/(1+n*g))/s0)+stats.invgamma.logpdf(g,.5,scale=r*r/2)),0,np.inf,epsabs=1e-10)[0]
add('bayesanova',[GROUPS,r,.95,20000,17,1],[(['BF10'],bf),(['BF01'],1/bf)])

for mode in ('regression','subgroup'):
    rows=np.asarray(META);y=rows[:,0];v=rows[:,1]**2;x=sm.add_constant(rows[:,2] if mode=='regression' else rows[:,3]-1);df=len(y)-x.shape[1]
    def wls(tau):
        fit=sm.WLS(y,x,weights=1/(v+tau)).fit();q=float(np.sum((y-fit.fittedvalues)**2/(v+tau)))
        return fit,q
    for method in ('fixed','dl','pm'):
        fit,q=wls(0);w=1/v
        tau=max(0.,(q-df)/(sum(w)-np.trace(fit.normalized_cov_params@(x.T@(w[:,None]**2*x))))) if method=='dl' else optimize.brentq(lambda t:wls(t)[1]-df,0,10) if method=='pm' and q>df else 0.
        fit,q=wls(tau);cov=fit.normalized_cov_params*(max(1.,q/df) if method!='fixed' else 1)
        expected=[(['τ²'],float(tau)),(['Residual Q'],q),(['coefficients',0,'estimate'],float(fit.params[0])),(['coefficients',1,'estimate'],float(fit.params[1])),(['coefficients',1,'SE'],math.sqrt(cov[1,1]))]
        args=[rows[:,:3].tolist() if mode=='regression' else rows[:,[0,1,3]].tolist(),method,.95,'z' if method=='fixed' else 'hksj']
        add('metaregression' if mode=='regression' else 'metasubgroup',args,expected,3e-7)

first,second=GROUPS[:2];result=stats.ttest_ind(first,second,equal_var=False,trim=.2);ci=result.confidence_interval()
add('yuen',[first,second,.2,.95],[(['t'],float(result.statistic)),(['df'],float(result.df)),(['p'],float(result.pvalue)),(['confidence interval',0],float(ci.low)),(['confidence interval',1],float(ci.high))])
result=anova_oneway(GROUPS,use_var='unequal',trim_frac=.2)
add('trimmedanova',[GROUPS,.2,.95],[(['F'],float(result.statistic)),(['df2'],float(result.df_denom)),(['p'],float(result.pvalue))])
x=np.array([1,2,3,4,5,6,7,8,9,30]);y=np.array([2,1,4,3,6,5,8,7,9,12]);g=2
wx=np.clip(x,np.sort(x)[g],np.sort(x)[-g-1]);wy=np.clip(y,np.sort(y)[g],np.sort(y)[-g-1]);r=float(stats.pearsonr(wx,wy).statistic);t=r*math.sqrt((len(x)-2)/(1-r*r))
add('winsorcor',[x.tolist(),y.tolist(),.2],[(['Winsorized correlation'],r),(['t'],t),(['df'],len(x)-2*g-2),(['p'],float(2*stats.t.sf(abs(t),len(x)-2*g-2)))])

data=np.array([[0,1],[1,2.5],[2,5],[3,6.5],[4,9],[5,10.5],[6,13],[7,14.5],[8,17],[9,35],[10,21],[11,22.5]])
model=sm.RLM(data[:,-1],sm.add_constant(data[:,0]),M=sm.robust.norms.HuberT(1.345))
model._estimate_scale=lambda resid,*args:float(stats.median_abs_deviation(resid,scale='normal'))
fit=model.fit(conv='coefs',tol=1e-11,maxiter=1000)
add('robustreg',[data.tolist(),1.345],[(['coefficients',i,'estimate'],float(v)) for i,v in enumerate(fit.params)],3e-6)

# Parametric likelihood through SciPy distributions. Include censored and
# delayed-entry data; reference Hessian is numerical on the complete likelihood.
for family in ('exponential','weibull','lognormal'):
    for entry in (False,True):
        rows=np.asarray(SURVIVAL);times=rows[:,0];events=rows[:,1];design=sm.add_constant(rows[:,2]);entries=np.minimum(times*.2,.5) if entry else np.zeros(len(times));estimated=family!='exponential'
        def objective(params):
            eta=design@params[:2];sigma=math.exp(params[-1]) if estimated else 1.;scale=np.exp(eta)
            dist=stats.lognorm(s=sigma,scale=scale) if family=='lognormal' else stats.weibull_min(c=1/sigma,scale=scale)
            loglike=np.where(events,dist.logpdf(times),dist.logsf(times))
            if entry:loglike-=dist.logsf(entries)
            return -float(loglike.sum())
        start=[np.log(times).mean(),0]+([0] if estimated else [])
        fit=optimize.minimize(objective,start,method='BFGS',options={'gtol':1e-8});params=fit.x;cov=np.linalg.inv(approx_hess(params,objective))
        sigma=math.exp(params[-1]) if estimated else 1.;dist=stats.lognorm(s=sigma,scale=math.exp(params[0])) if family=='lognormal' else stats.weibull_min(c=1/sigma,scale=math.exp(params[0]));median=float(dist.ppf(.5))
        arguments=rows.tolist();entry_col=-1
        if entry:arguments=[row[:2]+[float(e)]+row[2:] for row,e in zip(arguments,entries)];entry_col=2
        expected=[(['log likelihood'],-float(fit.fun)),(['AFT scale σ'],sigma),(['coefficients',0,'estimate'],float(params[0])),(['coefficients',1,'estimate'],float(params[1])),(['coefficients',1,'SE'],math.sqrt(cov[1,1])),(['Predicted survival times',0,'Predicted median time'],median)]
        add('parametricsurvival',[arguments,family,.95,entry_col,6],expected,3e-6)

for design,effect,baseline in [('z',.4,.5),('proportion',.65,.5),('proportion2',.65,.4),('variance',2.,.5)]:
    for tail in ('two','greater','less'):
        n=60;alpha=.05
        if design=='variance':
            low=stats.f.ppf(alpha/2 if tail=='two' else alpha,n-1,n-1);high=stats.f.isf(alpha/2 if tail=='two' else alpha,n-1,n-1)
            power=(stats.f.cdf(low/effect,n-1,n-1) if tail in ('two','less') else 0)+(stats.f.sf(high/effect,n-1,n-1) if tail in ('two','greater') else 0)
        else:
            if design=='z':mu=effect*math.sqrt(n);sd=1.
            elif design=='proportion':mu=(effect-baseline)*math.sqrt(n/(baseline*(1-baseline)));sd=math.sqrt(effect*(1-effect)/(baseline*(1-baseline)))
            else:
                p=(effect+baseline)/2;mu=(effect-baseline)*math.sqrt(n/(2*p*(1-p)));sd=math.sqrt((effect*(1-effect)+baseline*(1-baseline))/(2*p*(1-p)))
            z=stats.norm.isf(alpha/2 if tail=='two' else alpha);power=(stats.norm.sf(z,mu,sd) if tail in ('two','greater') else 0)+(stats.norm.cdf(-z,mu,sd) if tail in ('two','less') else 0)
        add('designpower',[design,effect,n,alpha,tail,baseline],[(['power'],float(power))])

target=ROOT/'tests/fixtures/priority_statistics_reference.json'
target.write_text(json.dumps({'reference':'SciPy distributions/optimization/quadrature; statsmodels WLS, RLM and trimmed ANOVA; WRS2 wincor t/df convention','cases':cases},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(f'Wrote {len(cases)} independent numerical cases')
