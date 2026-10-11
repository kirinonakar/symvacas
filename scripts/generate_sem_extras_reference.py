"""Independent NumPy/SciPy likelihood/score/percentile references; not runtime code."""
import csv
import json
import random
from pathlib import Path
import numpy as np
from scipy.optimize import minimize

ROOT=Path(__file__).resolve().parents[1]


def continuous_fit(rows,assignment,paths=(),residual=()):
    x=np.asarray(rows); scale=x.std(axis=0,ddof=1); z=(x-x.mean(axis=0))/scale
    sample=z.T@z/len(z); p=len(scale); k=max(assignment); markers=[assignment.index(i+1) for i in range(k)]
    specs=[('load',i,f-1) for i,f in enumerate(assignment) if i!=markers[f-1]]+ [('error',i,i) for i in range(p)]+[('variance',i,i) for i in range(k)]+[('path',target-1,source-1) for source,target in paths]+[('residual',i-1,j-1) for i,j in residual]
    initial=[.8 if kind=='load' else np.log(.5) if kind in ('error','variance') else 0. for kind,i,j in specs]
    def model(values):
        load=np.zeros((p,k)); b=np.zeros((k,k)); theta=np.zeros((p,p)); psi=np.zeros((k,k))
        for j,i in enumerate(markers): load[i,j]=1
        for value,(kind,i,j) in zip(values,specs):
            if kind=='load': load[i,j]=value
            elif kind=='error': theta[i,i]=np.exp(value)
            elif kind=='variance': psi[i,i]=np.exp(value)
            elif kind=='path': b[i,j]=value
            else: theta[i,j]=theta[j,i]=value
        if np.linalg.eigvalsh(theta).min()<=0: raise ValueError('Nonpositive errors')
        propagation=np.linalg.inv(np.eye(k)-b); total=propagation@psi@propagation.T
        return load@total@load.T+theta,b,total
    def objective(values):
        try:
            sigma,b,total=model(values)
            return (np.linalg.slogdet(sigma)[1]+np.trace(np.linalg.solve(sigma,sample))-np.linalg.slogdet(sample)[1]-p)/2
        except (ValueError,np.linalg.LinAlgError): return 1e8
    result=minimize(objective,initial,method='BFGS',options={'gtol':2e-8,'maxiter':2000})
    assert np.linalg.norm(result.jac,np.inf)<2e-6,result.message
    return result.x,model,specs,scale,sample,2*len(x)*result.fun


def score_reference(rows):
    values,model,specs,scale,sample,chi=continuous_fit(rows,[1]*4)
    sigma,_,_=model(values); inverse=np.linalg.inv(sigma); n=len(rows)
    derivatives=[]
    for j in range(len(values)):
        left=values.copy();right=values.copy();left[j]-=1e-5;right[j]+=1e-5
        derivatives.append((model(right)[0]-model(left)[0])/2e-5)
    info=np.array([[n*np.trace(inverse@a@inverse@b)/2 for b in derivatives] for a in derivatives])
    candidate=np.zeros((4,4));candidate[1,2]=candidate[2,1]=1
    cross=np.array([n*np.trace(inverse@a@inverse@candidate)/2 for a in derivatives])
    efficient=n*np.trace(inverse@candidate@inverse@candidate)/2-cross@np.linalg.solve(info,cross)
    score=n*np.trace((inverse-inverse@sample@inverse)@candidate)/2
    free,free_model,free_specs,free_scale,_,free_chi=continuous_fit(rows,[1]*4,residual=[(2,3)])
    position=free_specs.index(('residual',1,2))
    return {'chiSquare':chi,'MI':score**2/efficient,'EPC':-score/efficient*scale[1]*scale[2],
            'freedChiSquare':free_chi,'covariance':free[position]*free_scale[1]*free_scale[2]}


def effect_reference(rows):
    values,model,specs,scale,sample,chi=continuous_fit(rows,[1,1,1,2,2,2,3,3,3],[(1,2),(2,3),(1,3)])
    _,b,total=model(values); rawscale=scale[6]/scale[0]; standard=np.sqrt(total[0,0]/total[2,2])
    direct=b[2,0]; indirect=b[1,0]*b[2,1]
    return {'direct':direct*rawscale,'indirect':indirect*rawscale,'total':(direct+indirect)*rawscale,
            'standardizedIndirect':indirect*standard}


def main():
    with (ROOT/'tests/fixtures/efa_study_habits_sample.csv').open(encoding='utf-8-sig',newline='') as file: data=list(csv.reader(file))
    x=np.array(data[1:],dtype=float); corr=np.corrcoef(x,rowvar=False); p=corr.shape[0]; k=2
    def objective(psi):
        whitened=corr/np.sqrt(psi[:,None]*psi[None,:]); eigen=np.linalg.eigvalsh(whitened)[:-k]
        return np.sum(eigen-np.log(eigen)-1)
    fit=minimize(objective,1/np.diag(np.linalg.inv(corr)),bounds=[(1e-8,1)]*p,method='L-BFGS-B',options={'ftol':1e-14,'gtol':1e-8})
    eigen,vectors=np.linalg.eigh(corr/np.sqrt(fit.x[:,None]*fit.x[None,:])); load=np.sqrt(fit.x[:,None])*vectors[:,-k:]*np.sqrt(eigen[-k:]-1)
    rng=np.random.default_rng(42019); latent=rng.normal(size=220); covariance=np.eye(4)*.7; covariance[1,2]=covariance[2,1]=.36
    cfa=np.round(latent[:,None]*[1,.85,1.1,.95]+rng.multivariate_normal(np.zeros(4),covariance,size=220),5).tolist()
    x=rng.normal(size=180); m=.65*x+rng.normal(size=180); y=.2*x+.7*m+rng.normal(size=180)
    mediation=np.round(np.column_stack([f*loading+rng.normal(scale=.6,size=180) for f in (x,m,y) for loading in (1,.9,1.1)]),5).tolist()
    samples=25;seed=31;randomizer=random.Random(seed);draws=[]
    for _ in range(samples):
        sampled=[mediation[randomizer.randrange(len(mediation))] for row in mediation]
        draws.append(effect_reference(sampled))
    bootstrap={key:list(np.quantile([draw[key] for draw in draws],[.025,.975])) for key in ('direct','indirect','total','standardizedIndirect')}
    fixture={'source':'Independent SciPy normal likelihood optimization; NumPy expected-information Schur complement; seeded full model row refits and linearly interpolated percentiles.',
             'efaML':{'commonCovariance':(load@load.T).tolist(),'uniquenesses':fit.x.tolist(),'chiSquare':(len(data)-2-(2*p+5)/6-2*k/3)*fit.fun},
             'cfa':{'rows':cfa,'expected':score_reference(cfa)},'sem':{'rows':mediation,'expected':effect_reference(mediation),'samples':samples,'seed':seed,'bootstrap':bootstrap}}
    (ROOT/'tests/fixtures/sem_extras_reference.json').write_text(json.dumps(fixture,indent=2),encoding='utf8')


if __name__=='__main__': main()
