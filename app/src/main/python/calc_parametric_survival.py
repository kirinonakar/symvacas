"""Right-censored AFT likelihoods with optional delayed entry (no SciPy)."""
import math
from statistics import NormalDist
import mpmath as mp
from calc_shared import require
from calc_advanced_common import table, number, option, mean, variance, dot, integer
from calc_advanced_optimize import minimize, information
from calc_advanced_research import critical, level_option
from calc_statistics import _normal_sf


def normal_tail(z):
    if z<30:
        survival=.5*math.erfc(z/math.sqrt(2))
        return math.log(survival),math.exp(-z*z/2-.5*math.log(2*math.pi))/survival
    # Stable far-tail log survival and inverse Mills ratio.
    inv=1/(z*z);series=1-inv+3*inv**2-15*inv**3+105*inv**4-945*inv**5
    return -z*z/2-math.log(z)-.5*math.log(2*math.pi)+math.log(series),z/series


def calculate(engine,name,a):
    raw=table(a[0],4,2);family=option(a,1,'weibull');level=level_option(a,2)
    require(family in ('weibull','exponential','lognormal'),'Choose weibull, exponential or lognormal')
    entry_column=integer(a[3],-1,len(raw[0])-1) if len(a)>3 else -1
    require(entry_column==-1 or entry_column>=2,'Entry column must follow time and event (zero-based index)')
    rows=[[v for j,v in enumerate(row) if j!=entry_column] for row in raw];entries=[row[entry_column] if entry_column>=0 else 0. for row in raw]
    times=[r[0] for r in rows];events=[r[1] for r in rows];predictors=[r[2:] for r in rows];n=len(rows);p=len(rows[0])-1
    require(all(t>0 and 0<=e<t for t,e in zip(times,entries)),'Require positive time and 0 ≤ entry < time')
    require(all(e in (0,1) for e in events) and sum(events)>p,'Events must be 0/1 with more events than regression coefficients')
    require(n>p+1,'More rows are required for survival model inference')
    centers=[mean(c) for c in zip(*predictors)] if predictors[0] else [];scales=[math.sqrt(variance(c)) for c in zip(*predictors)] if centers else []
    require(all(s>0 for s in scales),'Survival predictors must vary')
    x=[[1.]+[(v-c)/s for v,c,s in zip(row,centers,scales)] for row in predictors]
    logtimes=list(map(math.log,times));estimated_scale=family!='exponential'
    horizon=number(a[4]) if len(a)>4 else mean(times);require(horizon>0,'Prediction time must be positive')
    def objective(params):
        beta=params[:p];ls=params[-1] if estimated_scale else 0.;require(abs(ls)<8,'AFT scale reached a boundary')
        sigma=math.exp(ls);value=0.;grad=[0.]*len(params)
        for row,t,lt,event,entry in zip(x,times,logtimes,events,entries):
            eta=dot(row,beta);z=(lt-eta)/sigma
            if family=='lognormal':
                if event:cost=.5*z*z+.5*math.log(2*math.pi)+ls+lt;de=-z/sigma;ds=1-z*z
                else:
                    logsf,mills=normal_tail(z);cost=-logsf;de=-mills/sigma;ds=-mills*z
                if entry>0:
                    ze=(math.log(entry)-eta)/sigma;logsf,mills=normal_tail(ze);cost+=logsf;de+=mills/sigma;ds+=mills*ze
            else:
                ez=math.exp(z);cost=ez-event*z+event*(ls+lt);de=(event-ez)/sigma;ds=(event-ez)*z+event
                if entry>0:
                    ze=(math.log(entry)-eta)/sigma;ee=math.exp(ze);cost-=ee;de+=ee/sigma;ds+=ee*ze
            value+=cost
            for j,v in enumerate(row):grad[j]+=de*v
            if estimated_scale:grad[-1]+=ds
        return value/n,[v/n for v in grad]
    start=[mean(logtimes)]+[0.]*(p-1)+([math.log(max(.2,math.sqrt(variance(logtimes))))] if estimated_scale else [])
    params,loss,iterations=minimize(start,objective,tolerance=1e-8,maximum=700);cov=information(params,objective,scale=n)
    beta=params[:p];sigma=math.exp(params[-1]) if estimated_scale else 1.;cutoff=critical((1-level)/2)
    transform=mp.eye(len(params));transform[0,0]=1
    for j,(c,s) in enumerate(zip(centers,scales),1):transform[j,j]=1/s;transform[0,j]=-c/s
    original=list(map(float,transform*mp.matrix(params)));original_cov=transform*cov*transform.T
    def finite_exp(v):return math.exp(v) if v<709 else math.inf
    coefficients=[]
    for j,b in enumerate(original[:p]):
        se=math.sqrt(float(original_cov[j,j]));radius=cutoff*se
        coefficients.append({'term':'Intercept' if j==0 else 'feature:'+str(j),'estimate':b,'SE':se,'z':b/se,'p':float(2*_normal_sf(abs(b/se))),
                             'Lower CI':b-radius,'Upper CI':b+radius,'Time ratio':finite_exp(b),'Time ratio lower':finite_exp(b-radius),'Time ratio upper':finite_exp(b+radius)})
    def quantile_eta(eta,prob):
        z=NormalDist().inv_cdf(prob) if family=='lognormal' else math.log(-math.log1p(-prob))
        return finite_exp(eta+sigma*z),z
    def survival(t,eta):
        z=(math.log(t)-eta)/sigma
        if family=='lognormal':return math.exp(normal_tail(z)[0])
        return math.exp(-math.exp(z)) if z<7 else 0.
    predictions=[]
    for i,row in enumerate(x):
        eta=dot(row,beta);median,z=quantile_eta(eta,.5);gradient=row+([sigma*z] if estimated_scale else [])
        se=math.sqrt(float((mp.matrix(gradient).T*cov*mp.matrix(gradient))[0]));logmedian=eta+sigma*z
        expectation=finite_exp(eta+sigma*sigma/2) if family=='lognormal' else finite_exp(eta+float(mp.loggamma(1+sigma)))
        predictions.append({'Subject':i+1,'Predicted median time':median,'Median lower CI':finite_exp(logmedian-cutoff*se),'Median upper CI':finite_exp(logmedian+cutoff*se),
                            'Predicted mean time':expectation,'10% event time':quantile_eta(eta,.1)[0],'90% event time':quantile_eta(eta,.9)[0],'Survival at prediction time':survival(horizon,eta)})
    horizon_max=max(max(times),min(quantile_eta(beta[0],.95)[0],max(times)*5));grid=[horizon_max*i/120 for i in range(1,121)]
    risk=n;km=1.;observed=[[0.,1.]]
    # KM overlay only without delayed entry; pooled KM and mean-predictor AFT
    # have different covariate targets, stated in the caption.
    if entry_column<0:
        for t in sorted(set(times)):
            deaths=sum(e for time,e in zip(times,events) if time==t);count=sum(time==t for time in times)
            km*=1-deaths/risk;observed.append([t,km]);risk-=count
    else:observed=[]
    engine.statistics_plots=[{'kind':'research-scatter','title':'Parametric survival at mean predictors','points':observed,'trend':[[0.,1.]]+[[t,survival(t,beta[0])] for t in grid],
                              'xlabel':'Time','ylabel':'Survival probability','caption':'Line: fitted survival at mean selected predictors. Points: pooled Kaplan–Meier without covariate adjustment (omitted for delayed entry). Quantile estimates extrapolate the chosen distribution.'}]
    engine.statistics_full_tables={'Predicted survival times':predictions}
    return {'n':n,'Events':int(sum(events)),'Distribution':family,'AFT scale σ':sigma,**({'Weibull shape':1/sigma} if family=='weibull' else {}),
            'log likelihood':-n*loss,'AIC':2*len(params)+2*n*loss,'BIC':len(params)*math.log(n)+2*n*loss,'Iterations':iterations,
            'confidence level':level,'Prediction time':horizon,'coefficients':coefficients,'Predicted survival times':predictions[:100],
            'Assumptions':'Independent subjects; positive times, event 1, right censoring 0, independent censoring conditional on predictors. Optional delayed entry conditions each likelihood contribution on survival past entry. log(T)=Xβ+σ ε with extreme-value errors (Weibull/exponential) or normal errors (lognormal); exponential fixes σ=1 and Weibull shape=1/σ. exp(β) is a time ratio, not a hazard ratio. Observed-information asymptotic Wald intervals include joint shape/scale uncertainty for predicted medians. Predicted quantiles are unconditional event times from time zero, not residual lifetime conditional on entry or current survival; 10%/90% quantiles are not confidence limits. No interval censoring or competing risks. Distributional assumptions and extrapolation need substantive justification.'}
