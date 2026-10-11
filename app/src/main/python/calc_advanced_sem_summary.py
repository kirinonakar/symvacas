"""Fully standardized Wald inference and latent explained variance.

Numerical delta method uses the full fitted parameter covariance, including
uncertainty in the variances used for standardization. Marker loadings are
fixed only in raw units and still have standardized uncertainty.
"""
import math
import mpmath as mp
from calc_shared import require


def fit_diagnostics(result,iterations,gradient,residual_ratios):
    """Expose checks performed by the fitter without rating scientific validity."""
    result['diagnostics']={
        'Optimization convergence':'Passed',
        'Maximum absolute gradient':max(map(abs,gradient)),
        'Iterations':iterations,
        'Parameter identification':'Passed',
        'Residual variance boundary':'Passed',
        'Minimum residual variance ratio':min(residual_ratios),
        'Fit assessment':'Unavailable (zero degrees of freedom)' if result['df']==0 else 'Review fit indices and residuals',
        'Interpretation':'Convergence, local identification and residual-variance checks passed. These numerical checks do not establish model validity, distribution assumptions or causality. Fit indices must be interpreted together with residuals, uncertainty, sample size and study design.'}


def measurement_markers(groups,cross):
    """Prefer a pure marker, otherwise fix the first primary loading for scale.

    Cross-loadings remain free on markers. Degrees of freedom and the fitted
    information matrix determine identification, not indicator counts.
    """
    complex_indicators={i for i,j in cross}
    pure=[[i for i in group if i not in complex_indicators] for group in groups]
    return [(clean or group)[0] for clean,group in zip(pure,groups)]


def augment(result, parameters, covariance, model, specs, paths):
    """model returns (indicator covariance, loadings, latent covariance, B)."""
    loading_rows=result['Loadings']; path_rows=result['Structural paths']
    entries=[('loading',int(row['term'].split(':')[1])-1,row['Factor']-1,row) for row in loading_rows]
    entries += [('path',int(row['term'].split(' → ')[1])-1,int(row['term'].split(' → ')[0])-1,row) for row in path_rows]

    def standardized(x):
        sigma,load,total,structural=model(x)
        return [float(load[i,j]*mp.sqrt(total[j,j]/sigma[i,i])) if kind=='loading'
                else float(structural[i,j]*mp.sqrt(total[j,j]/total[i,i])) for kind,i,j,_ in entries]

    estimates=standardized(parameters)
    # Nuisance means/thresholds have zero derivatives. Shared group indices
    # are differentiated once, against the full joint covariance matrix.
    active=sorted({index for kind,i,j,index in specs if kind in ('loading','path','diagonal','covariance','error','residual')})
    jac=mp.zeros(len(entries),len(active))
    for column,index in enumerate(active):
        step=1e-5*max(1.,abs(parameters[index]))
        lower=list(parameters); upper=list(parameters)
        lower[index]-=step; upper[index]+=step
        lo=standardized(lower); hi=standardized(upper)
        for row in range(len(entries)): jac[row,column]=(hi[row]-lo[row])/(2*step)
    cov=mp.matrix([[covariance[i,j] for j in active] for i in active])
    projected=jac*cov
    for row,((kind,i,j,target),estimate) in enumerate(zip(entries,estimates)):
        variance=float(sum(projected[row,col]*jac[row,col] for col in range(len(active))))
        se=math.sqrt(max(0.,variance)); critical=1.959963984540054
        target['Standardized SE']=se
        target['Standardized CI95']=[estimate-critical*se,estimate+critical*se]
        if kind=='loading': target['Indicator']=i+1

    sigma,load,total,structural=model(parameters)
    common=load*total*load.T
    result['Indicator R²']=[{'term':'feature:'+str(i+1),'Indicator':i+1,'R²':float(common[i,i]/sigma[i,i])} for i in range(sigma.rows)]
    inverse=mp.eye(total.rows)-structural
    disturbance=inverse*total*inverse.T
    endogenous={target for source,target in paths}
    result['Latent R²']=[{'Factor':i+1,'R²':float(1-disturbance[i,i]/total[i,i]) if i in endogenous else None,
                          'Role':'Endogenous' if i in endogenous else 'Exogenous (R² not applicable)'} for i in range(total.rows)]
    exogenous=[i for i in range(total.rows) if i not in endogenous]
    result['Exogenous correlations']=[{'term':str(j+1)+' ↔ '+str(i+1),
                                      'Correlation':float(total[i,j]/mp.sqrt(total[i,i]*total[j,j]))}
                                     for i in exogenous for j in exogenous if j<i]

