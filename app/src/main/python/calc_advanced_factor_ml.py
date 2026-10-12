"""Profile normal ML over positive uniquenesses, with portable eigensolvers."""
import math
import mpmath as mp
from calc_shared import require
from calc_advanced_optimize import minimize


def extract(corr, count):
    p=corr.rows
    df=((p-count)**2-p-count)//2
    require(df>=0,'ML factor extraction needs nonnegative model degrees of freedom')
    inv=corr**-1
    initial=[min(.95,max(.01,1/float(inv[i,i]))) for i in range(p)]
    def profile(x):
        psi=[1/(1+math.exp(-v)) if v>=0 else math.exp(v)/(1+math.exp(v)) for v in x]
        require(min(psi)>1e-10,'ML uniqueness reached a Heywood boundary')
        root=mp.diag([mp.sqrt(v) for v in psi])
        eigen,vectors=mp.eigsy(root**-1*corr*root**-1)
        selected=list(range(p-1,p-count-1,-1))
        load=root*mp.matrix([[vectors[i,j]*mp.sqrt(max(0,eigen[j]-1)) for j in selected] for i in range(p)])
        sigma=load*load.T+mp.diag(psi)
        return psi,load,sigma
    logdet=float(mp.log(mp.det(corr)))
    def objective(x):
        psi,load,sigma=profile(x); inverse=sigma**-1
        value=(float(mp.log(mp.det(sigma)))+float(sum((inverse*corr)[i,i] for i in range(p)))-logdet-p)/2
        score=inverse-inverse*corr*inverse
        return value,[float(score[i,i])*psi[i]*(1-psi[i])/2 for i in range(p)]
    parameters,loss,iterations=minimize([math.log(v/(1-v)) for v in initial],objective,tolerance=1e-8,maximum=1000)
    psi,load,sigma=profile(parameters)
    require(min(psi)>1e-6,'Heywood / boundary uniqueness; reduce factors or revise items')
    # Order unrotated axes by common variance, so variance percentages remain
    # squared-loading shares rather than eigenvalues of a whitened matrix.
    eigen,vectors=mp.eigsy(load.T*load)
    require(min(eigen)>1e-8,'ML factor variance is on a boundary; reduce the factor count')
    order=list(range(count-1,-1,-1)); load=load*mp.matrix([[vectors[i,j] for j in order] for i in range(count)])
    return load,[float(eigen[j]) for j in order],max(0.,2*loss),df,iterations
