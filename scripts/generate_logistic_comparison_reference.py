"""Independent statsmodels MLE/SciPy tests and brute-force paired AUC placements."""
import json
from pathlib import Path
import numpy as np
import statsmodels.api as sm
from scipy.special import expit
from scipy.stats import binomtest, chi2, norm

ROOT=Path(__file__).resolve().parents[1]
rng=np.random.default_rng(62145)
def sample(n):
    x=rng.normal(size=(n,2))
    y=rng.binomial(1,expit(-.25+.6*x[:,0]+.9*x[:,1]))
    return np.column_stack((x,y))
train=sample(96);validation=sample(72);target=validation[:,-1]
fits=[sm.Logit(train[:,-1],sm.add_constant(train[:,:k])).fit(disp=False) for k in (1,2)]
scores=[sm.add_constant(validation[:,:k])@fit.params for k,fit in zip((1,2),fits)]
def placement(score):
    positive=score[target==1];negative=score[target==0]
    kernels=(positive[:,None]>negative[None,:]).astype(float)+.5*(positive[:,None]==negative[None,:])
    return kernels.mean(),kernels.mean(axis=1),kernels.mean(axis=0)
pa,pb=map(placement,scores)
variance=np.var(pb[1]-pa[1],ddof=1)/len(pa[1])+np.var(pb[2]-pa[2],ddof=1)/len(pa[2])
delta=pb[0]-pa[0];ci=delta+norm.ppf(.975)*np.sqrt(variance)*np.array([-1,1])
correct=[(z>=0)==target for z in scores];gain=np.sum(~correct[0]&correct[1]);loss=np.sum(correct[0]&~correct[1])
performance=[]
for score,place in zip(scores,(pa,pb)):
    prob=expit(score);cal=sm.Logit(target,sm.add_constant(score)).fit(disp=False)
    performance.append([place[0],np.mean((score>=0)==target),np.mean(np.logaddexp(0,score)-target*score),np.mean((prob-target)**2),*cal.params])
lr=2*(fits[1].llf-fits[0].llf)
data={'source':'statsmodels Logit unpenalized MLE; SciPy chi2/binomtest; brute-force paired DeLong placements',
      'train':train.tolist(),'validation':validation.tolist(),
      'training':[[f.llf,f.aic,f.bic] for f in fits],'performance':performance,
      'lrt':[lr,float(chi2.sf(lr,1))],
      'delong':[delta,float(variance),ci.tolist(),float(2*norm.sf(abs(delta)/np.sqrt(variance)))],
      'mcnemar':[int(gain),int(loss),float(binomtest(int(gain),int(gain+loss)).pvalue)]}
(ROOT/'tests/fixtures/logistic_comparison_reference.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf8')
