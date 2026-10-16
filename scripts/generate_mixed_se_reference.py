"""Development-only MixedLM estimates and dense GLS fixed-effect SE oracle.

Uses statsmodels for variance estimation and NumPy for (X' V^-1 X)^-1.
The latter is the model-based covariance used by lme4's Gaussian LMMs;
statsmodels' observed-Hessian bse can differ on unbalanced designs.
"""
import json
from pathlib import Path
import numpy as np
import scipy
from scipy.stats import norm
import statsmodels
import statsmodels.api as sm

ROOT=Path(__file__).resolve().parents[1]
existing=json.loads((ROOT/'tests/fixtures/advanced_statistics_reference.json').read_text())
datasets={}
for slope,label in [(0,'intercept'),(1,'slope')]:
    name='Mixed random '+('intercept' if slope==0 else 'slope')+' reml'
    datasets[label]=(next(case['arguments'][0] for case in existing if case['name']==name),slope)
rng=np.random.default_rng(947)
rows=[]
for subject in range(24):
    intercept=rng.normal(0,.8)
    for point in range(3+subject%5):
        first=rng.normal(.3*subject,1)
        second=rng.normal(0,1)
        rows.append([subject,first,second,1+.6*first-.3*second+intercept+rng.normal(0,.4)])
datasets['unbalanced']=(rows,0)
cases=[]
for label,(rows,slope) in datasets.items():
    array=np.asarray(rows); x=sm.add_constant(array[:,1:-1]); y=array[:,-1]; groups=array[:,0]
    for method in ('reml','ml'):
        z=x[:,:2] if slope else np.ones((len(y),1))
        fit=sm.MixedLM(y,x,groups=groups,exog_re=z).fit(reml=method=='reml',method='bfgs',disp=False,gtol=1e-10,maxiter=2000)
        assert fit.converged
        covariance=fit.scale*np.eye(len(y))
        for group in set(groups):
            indices=np.flatnonzero(groups==group)
            covariance[np.ix_(indices,indices)]+=z[indices]@fit.cov_re@z[indices].T
        se=np.sqrt(np.diag(np.linalg.inv(x.T@np.linalg.solve(covariance,x))))
        beta=fit.fe_params
        cases.append({'name':label+' '+method,'rows':rows,'slope':slope,'method':method,
                      'estimates':beta.tolist(),'SE':se.tolist(),'residual variance':float(fit.scale),
                      'p':(2*norm.sf(np.abs(beta/se))).tolist(),
                      'CI95':np.column_stack((beta-norm.ppf(.975)*se,beta+norm.ppf(.975)*se)).tolist()})
destination=ROOT/'tests/fixtures/mixed_se_reference.json'
destination.write_text(json.dumps({'source':f'statsmodels {statsmodels.__version__}; NumPy {np.__version__}; SciPy {scipy.__version__}; dense GLS covariance',
                                 'cases':cases},indent=2)+'\n',encoding='utf-8')
print(destination)
