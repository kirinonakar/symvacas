"""Single-factor congeneric reliability of an unweighted item sum."""
import math
import mpmath as mp
from calc_shared import require
from calc_advanced_common import table, option
from calc_advanced_survey import covariance, correlation, alpha
from calc_advanced_factor_ml import extract
from calc_statistics import _chisq_sf


def calculate(engine, name, a):
    rows=table(a[0],4,3); n=len(rows); p=len(rows[0]); mode=option(a,1,'raw')
    require(mode in ('raw','standardized'),'Choose raw or standardized reliability')
    corr,_,scales=correlation(rows)
    require(min(mp.eigsy(corr,eigvals_only=True))>1e-9,'Omega requires a positive-definite item correlation matrix')
    load,_,loss,df,iterations=extract(corr,1)
    if sum(load)<0: load=-load
    standardized=[float(load[i,0]) for i in range(p)]
    weights=scales if mode=='raw' else [1.]*p
    loading=[v*w for v,w in zip(standardized,weights)]
    error=[(1-v*v)*w*w for v,w in zip(standardized,weights)]
    require(min(error)>0,'Omega requires positive error variances; revise a Heywood fit')
    common=sum(loading)**2; omega=common/(common+sum(error))
    cov,_=covariance(rows); used=cov if mode=='raw' else corr
    residual=[float(corr[i,j])-standardized[i]*standardized[j] for i in range(p) for j in range(i)]
    correction=n-1-(2*p+5)/6-2/3
    require(correction>0,'More observations are required for omega model fit')
    diagnostics=[{'term':'feature:'+str(i+1),'Loading':loading[i],'Standardized loading':standardized[i],'Error variance':error[i]} for i in range(p)]
    engine.statistics_plots=[{'kind':'intervals','title':'Single-factor standardized loadings',
                              'rows':[[engine.request.get('statisticsTermLabels',{}).get('feature:'+str(i+1),str(i+1)),v,v,v] for i,v in enumerate(standardized)],'reference':0}]
    return {'n':n,'items':p,'McDonald ω':omega,'Cronbach α':alpha(used),'Scale':mode,
            'Estimator':'Single-factor normal ML on item correlations; raw sum rescales loadings and errors by sample SD',
            'Model χ²':correction*loss,'Model df':df,'Model p':float(_chisq_sf(correction*loss,df)) if df else None,
            'Off-diagonal RMS residual':math.sqrt(sum(v*v for v in residual)/len(residual)),
            'Iterations':iterations,'Item diagnostics':diagnostics,
            'Warning':'Opposite loading signs: check item direction before interpreting reliability' if min(standardized)<0<max(standardized) else 'Inspect model fit before interpreting reliability',
            'Assumptions':'Complete independent numeric rows, at least three varying items; reverse-code intentionally before analysis. One common factor, factor variance one and uncorrelated errors. Omega = (sum loadings)^2 / ((sum loadings)^2 + sum error variances) for the selected unweighted sum. This is single-factor omega, not hierarchical or bifactor omega. Three items give a just-identified model; fit cannot establish unidimensionality. No automatic reverse scoring or confidence interval.'}
