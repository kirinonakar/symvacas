"""Inverse-variance meta-regression with a common residual heterogeneity."""
import math
import mpmath as mp
from calc_shared import require
from calc_advanced_common import table, number, option, mean
from calc_advanced_linear import least_squares
from calc_advanced_research import critical, level_option
from calc_advanced_research import binary_studies, continuous_studies
from calc_statistics import _normal_sf, _t_sf, _f_sf, _chisq_sf


def fit_model(design,y,v,method):
    k=len(y);p=len(design[0]);df=k-p
    require(df>0,'Meta-regression requires more studies than coefficients')
    def fit(tau):
        weights=[1/(vi+tau) for vi in v]
        beta,cov,q,fitted=least_squares(design,y,weights)
        return beta,cov,q,fitted,weights
    fixed=fit(0);tau=0.
    if method=='dl':
        w=fixed[4]; x=mp.matrix(design)
        squared=x.T*mp.diag([wi*wi for wi in w])*x
        correction=sum(w)-float(sum((fixed[1]*squared)[i,i] for i in range(p)))
        require(correction>0,'Meta-regression weights are numerically unidentified')
        tau=max(0.,(fixed[2]-df)/correction)
    elif method=='pm' and fixed[2]>df:
        lo,hi=0.,max(v)
        while fit(hi)[2]>df: hi*=2
        for _ in range(65):
            mid=(lo+hi)/2
            if fit(mid)[2]>df:lo=mid
            else:hi=mid
        tau=(lo+hi)/2
    return (*fit(tau),tau,df)


def calculate(engine,name,a):
    rows=table(a[0],3,3);method=option(a,1,'pm');level=level_option(a,2);mode=option(a,3,'hksj')
    measure=option(a,4,'generic');measure={'oddsratio':'or','riskratio':'rr'}.get(measure,measure)
    require(measure in ('generic','or','rr','md','smd'),'Choose generic, oddsratio, riskratio, md or smd effects')
    prefix=4 if measure in ('or','rr') else 6 if measure in ('md','smd') else 2
    require(len(rows[0])>prefix,'Select study summary columns and at least one moderator/group column')
    excluded=[];indices=list(range(1,len(rows)+1))
    if measure!='generic':
        raw=[r[:prefix] for r in rows];mod=[r[prefix:] for r in rows]
        if measure in ('or','rr'):
            effects,_,excluded,indices=binary_studies(raw,measure,number(a[5]) if len(a)>5 else .5)
        else:effects,_=continuous_studies(raw,measure)
        rows=[effect+mod[index-1] for effect,index in zip(effects,indices)]
    k=len(rows)
    require(method in ('fixed','dl','pm'),'Choose fixed, dl or pm meta-analysis')
    require(mode in ('z','hksj') and (method!='fixed' or mode=='z'),'Fixed effects use z; random effects use z or hksj')
    y=[r[0] for r in rows];se=[r[1] for r in rows]
    require(all(s>0 for s in se),'Study standard errors must be positive (not SD or variance)')
    origin=mean(y);scale=max(max(se),max(abs(v-origin) for v in y));target=[(v-origin)/scale for v in y];v=[(s/scale)**2 for s in se]
    require(all(vi>0 and math.isfinite(vi) for vi in v),'Standard-error ratios exceed the numeric range')
    labels=engine.request.get('statisticsTermLabels',{}); subgroup=name=='metasubgroup'
    if subgroup:
        require(len(rows[0])==3,'Subgroup rows: effect, SE, numeric group ID')
        groups=list(dict.fromkeys(r[2] for r in rows)); require(len(groups)>=2,'Choose at least two subgroups')
        require(all(sum(r[2]==g for r in rows)>=2 for g in groups),'Each subgroup requires at least two studies')
        def group_label(g):return labels.get('group:'+str(int(g)),str(g)) if g.is_integer() and g>0 else str(g)
        design=[[1.]+[float(r[2]==g) for g in groups[1:]] for r in rows]
        names=['Intercept']+[group_label(g)+' − '+group_label(groups[0]) for g in groups[1:]]
    else:
        raw=[r[2:] for r in rows];centers=[mean(c) for c in zip(*raw)];spreads=[max(abs(v-c) for v in col) for col,c in zip(zip(*raw),centers)]
        require(all(s>0 for s in spreads),'Moderators must vary')
        design=[[1.]+[(value-c)/s for value,c,s in zip(r,centers,spreads)] for r in raw]
        names=['Intercept']+['feature:'+str(j+1) for j in range(len(centers))]
    p=len(design[0]);beta,cov,q,fitted,weights,tau,df=fit_model(design,target,v,method)
    inflation=max(1.,q/df) if mode=='hksj' else 1.
    test_cov=cov*inflation
    signal=mp.matrix(beta[1:]);block=test_cov[1:,1:];wald=float((signal.T*block**-1*signal)[0])
    qm={'F':wald/(p-1),'df1':p-1,'df2':df,'p':float(_f_sf(wald/(p-1),p-1,df))} if mode=='hksj' else {'χ²':wald,'df':p-1,'p':float(_chisq_sf(wald,p-1))}
    transform=mp.eye(p)*scale
    if not subgroup:
        for j,(c,s) in enumerate(zip(centers,spreads),1):transform[j,j]=scale/s;transform[0,j]=-scale*c/s
    actual=list(map(float,transform*mp.matrix(beta)));actual[0]+=origin;actual_cov=transform*test_cov*transform.T
    cutoff=critical((1-level)/2,df if mode=='hksj' else None)
    coefficients=[]
    for i,b in enumerate(actual):
        sd=math.sqrt(float(actual_cov[i,i]));t=b/sd
        coefficients.append({'term':names[i],'estimate':b,'SE':sd,'Statistic':t,'p':float(2*(_t_sf(abs(t),df) if mode=='hksj' else _normal_sf(abs(t)))),
                             'Lower CI':b-cutoff*sd,'Upper CI':b+cutoff*sd})
    baseline=fit_model([[1.] for _ in rows],target,v,method)[5]
    studies=[{'Study':indices[i],'Estimate':y[i],'SE':se[i],'Fitted':origin+scale*fitted[i],'Residual':scale*(target[i]-fitted[i]),'Weight (%)':100*weights[i]/sum(weights)} for i in range(k)]
    result={'Studies (k)':k,'Method':method,'Inference':mode,'Residual df':df,'τ²':tau*scale*scale,'Residual Q':q,
            'Residual Q p':float(_chisq_sf(q,df)),'Moderator test':qm,'Heterogeneity R²':max(0.,1-tau/baseline) if baseline>0 else None,
            'Effect measure':measure,'Continuity correction':(number(a[5]) if len(a)>5 else .5) if measure in ('or','rr') else None,
            'Excluded study count':len(excluded),'Excluded studies':excluded[:100],
            'confidence level':level,'coefficients':coefficients,'Studies':studies[:100],
            'Assumptions':'Independent studies with known positive sampling SE; log effects and log SE for ratios. All moderators are prespecified study-level variables; ecological associations are not individual causal effects. Common residual τ² across studies/subgroups. PM solves residual Q=k−p; DL uses generalized moment trace correction. Modified HKSJ uses max(1,Q/(k−p)) and t/F inference. Moderator test compares all slopes jointly. Dependent effects require their sampling covariance and are not handled by this model. No trim-and-fill or selection-bias correction.'}
    engine.statistics_full_tables={'Studies':studies,**({'Excluded studies':excluded} if excluded else {})};engine.statistics_plots=[]
    if subgroup:
        summaries=[];forest=[];result['Reference subgroup']=group_label(groups[0])
        for index,g in enumerate(groups):
            row=mp.matrix([1.]+[float(index==j) for j in range(1,len(groups))]);estimate=origin+scale*float((row.T*mp.matrix(beta))[0]);sd=scale*math.sqrt(float((row.T*test_cov*row)[0]));radius=cutoff*sd
            label=group_label(g);summaries.append({'Group':label,'Studies':sum(r[2]==g for r in rows),'estimate':estimate,'SE':sd,'Lower CI':estimate-radius,'Upper CI':estimate+radius})
            forest.append([label,estimate,estimate-radius,estimate+radius])
        result['Subgroups']=summaries;engine.statistics_plots=[{'kind':'intervals','title':'Subgroup pooled effects (common τ²)','rows':forest,'reference':0}]
    elif p==2:
        ordered=sorted(r[2] for r in rows);trend=[[x,actual[0]+actual[1]*x] for x in (ordered[0],ordered[-1])]
        engine.statistics_plots=[{'kind':'research-scatter','title':'Meta-regression','points':[[r[2],r[0]] for r in rows],'trend':trend,'xlabel':labels.get('feature:1','Moderator'),'ylabel':'Effect estimate',
                                  'caption':'Line: fitted mean effect. Independent study estimates; point size does not encode weight.'}]
    return result
