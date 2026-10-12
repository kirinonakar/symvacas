"""Independent SciPy/statsmodels references; these packages are not runtime dependencies."""
import json
import math
from pathlib import Path
import numpy as np
import scipy
from scipy.stats import f,chi2
import statsmodels
import statsmodels.api as sm
from statsmodels.duration.hazard_regression import PHReg

rng=np.random.default_rng(812)
n=120;x=rng.normal(size=(n,2));mean=1+.3*x[:,0]+.6*x[:,1]
linear=mean+rng.normal(size=n)
poisson=rng.poisson(np.exp(.5+.2*x[:,0]+.35*x[:,1]))
nb=rng.negative_binomial(1.2,1.2/(1.2+np.exp(.7+.2*x[:,0]+.3*x[:,1])))
event=rng.exponential(np.exp(-.3*x[:,0]-.4*x[:,1]));censor=rng.exponential(2,size=n);time=np.minimum(event,censor);status=(event<=censor).astype(int)
out={'source':{'scipy':scipy.__version__,'statsmodels':statsmodels.__version__},'cases':[]}
for family,target in [('linear',linear),('poisson',poisson),('nb',nb)]:
    fits=[]
    for width in (1,2):
        design=sm.add_constant(x[:,:width])
        model=sm.OLS(target,design) if family=='linear' else sm.Poisson(target,design) if family=='poisson' else sm.NegativeBinomial(target,design)
        fits.append(model.fit() if family=='linear' else model.fit(disp=False,maxiter=500))
    a,b=fits;expected={'ΔAIC (B − A)':float(b.aic-a.aic),'ΔBIC (B − A)':float(b.bic-a.bic)}
    if family=='linear':
        statistic=((a.ssr-b.ssr)/(b.ssr/(n-3)));expected.update(F=float(statistic),p=float(f.sf(statistic,1,n-3)),**{'ΔR² (B − A)':float(b.rsquared-a.rsquared)})
    else:
        statistic=2*(b.llf-a.llf);expected.update({'LRT χ²':float(statistic),'p':float(chi2.sf(statistic,1))})
    out['cases'].append({'family':family,'rows':np.column_stack((x,target)).tolist(),'expected':expected})
fits=[PHReg(time,x[:,:width],status=status,ties='efron').fit(disp=False) for width in (1,2)]
a,b=fits;statistic=2*(b.llf-a.llf)
out['cases'].append({'family':'cox','rows':np.column_stack((time,status,x)).tolist(),'expected':{'LRT χ²':float(statistic),'p':float(chi2.sf(statistic,1)),'ΔAIC (B − A)':float(2-2*(b.llf-a.llf))}})
groups=np.repeat(np.arange(16),6);x=rng.normal(size=(len(groups),2));response=1+.3*x[:,0]+.5*x[:,1]+rng.normal(size=16)[groups]+rng.normal(size=len(groups))*.7
fits=[sm.MixedLM(response,sm.add_constant(x[:,:width]),groups).fit(reml=False,method='bfgs',disp=False) for width in (1,2)]
assert all(model.converged for model in fits)
a,b=fits;statistic=2*(b.llf-a.llf)
out['cases'].append({'family':'lmm','rows':np.column_stack((groups+1,x,response)).tolist(),'expected':{'LRT χ²':float(statistic),'p':float(chi2.sf(statistic,1)),'ΔAIC (B − A)':float(b.aic-a.aic),'ΔBIC (B − A)':float(b.bic-a.bic)}})
path=Path(__file__).resolve().parents[1]/'tests/fixtures/model_comparison_reference.json'
path.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('Generated independent references for linear, Poisson, NB2, Cox and ML LMM comparisons.')
