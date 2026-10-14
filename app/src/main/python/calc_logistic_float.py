"""Portable binary64 IRLS for large, well-conditioned logistic MLE fits."""
import math
import mpmath as mp
import sympy as s
from calc_shared import MathError, require


def inverse_information(matrix):
    """Cholesky inversion of a small positive definite information matrix."""
    p=len(matrix); lower=[[0.]*p for _ in range(p)]
    scale=max(matrix[i][i] for i in range(p))
    for i in range(p):
        for j in range(i+1):
            value=matrix[i][j]-math.fsum(lower[i][k]*lower[j][k] for k in range(j))
            if i==j:
                require(value>scale*1e-12, "Ill-conditioned logistic information")
                lower[i][j]=math.sqrt(value)
            else: lower[i][j]=value/lower[j][j]
    inverse=[[0.]*p for _ in range(p)]
    for column in range(p):
        forward=[0.]*p; backward=[0.]*p
        for i in range(p):
            forward[i]=((1. if i==column else 0.)-math.fsum(lower[i][j]*forward[j] for j in range(i)))/lower[i][i]
        for i in reversed(range(p)):
            backward[i]=(forward[i]-math.fsum(lower[j][i]*backward[j] for j in range(i+1,p)))/lower[i][i]
        for i in range(p): inverse[i][column]=backward[i]
    return inverse


def information(design, weights):
    p=len(design[0]); columns=list(zip(*design))
    matrix=[[0.]*p for _ in range(p)]
    for j in range(p):
        for k in range(j+1):
            value=math.fsum(w*x*y for w,x,y in zip(weights,columns[j],columns[k]))
            matrix[j][k]=matrix[k][j]=value
    return matrix


def fit(engine, rows):
    from calc_statistics import _normal_sf, _normal_cdf, _quantile, _chisq_sf, _mp_result
    from calc_inference import _binary_roc
    n=len(rows); p=len(rows[0]); values=[[float(v) for v in row] for row in rows]
    target=[row[-1] for row in values]
    centers=[math.fsum(row[j] for row in values)/n for j in range(p-1)]
    scales=[math.sqrt(math.fsum((row[j]-centers[j])**2 for row in values)/n) for j in range(p-1)]
    require(all(scale>0 and math.isfinite(scale) for scale in scales), "Ill-conditioned logistic predictors")
    # Fall back when conversion to binary64 cannot retain the predictor spread.
    require(all(scale>abs(center)*1e-12 for scale,center in zip(scales,centers)), "Predictor precision requires high-precision fitting")
    design=[[1.]+[(row[j]-centers[j])/scales[j] for j in range(p-1)] for row in values]
    predictor_inverse=inverse_information(information(design,[1.]*n))
    dot=lambda a,b: math.fsum(x*y for x,y in zip(a,b))
    softplus=lambda z:max(z,0.)+math.log1p(math.exp(-abs(z)))
    def evaluate(beta):
        logits=[dot(row,beta) for row in design]
        exps=[math.exp(-abs(z)) for z in logits]
        probs=[1/(1+e) if z>=0 else e/(1+e) for z,e in zip(logits,exps)]
        loss=math.fsum(softplus(-z) if y else softplus(z) for z,y in zip(logits,target))
        return logits,probs,exps,loss
    beta=[math.log(sum(target)/(n-sum(target)))]+[0.]*(p-1)
    converged=False
    for iteration in range(100):
        logits,probs,exps,loss=evaluate(beta)
        # The existing exact certificate decides whether Firth is appropriate.
        require(not all((2*y-1)*z>0 for y,z in zip(target,logits)), "Possible complete separation")
        weights=[e/(1+e)**2 for e in exps]
        covariance=inverse_information(information(design,weights))
        score=[math.fsum(row[j]*(y-prob) for row,y,prob in zip(design,target,probs)) for j in range(p)]
        step=[dot(row,score) for row in covariance]
        if max(map(abs,step))<1e-9:
            converged=True; break
        rate=1.
        while rate>1e-10:
            candidate=[b+rate*d for b,d in zip(beta,step)]
            if evaluate(candidate)[3]<=loss+1e-12*max(1.,loss): break
            rate/=2
        require(rate>1e-10,"Logistic IRLS failed to converge")
        beta=candidate
    require(converged,"Logistic IRLS failed to converge")
    logits,probs,exps,loss=evaluate(beta)
    weights=[e/(1+e)**2 for e in exps]
    covariance=inverse_information(information(design,weights))
    with mp.workdps(engine.precision+20):
        transform=mp.eye(p)
        for j in range(1,p): transform[0,j]=-centers[j-1]/scales[j-1]; transform[j,j]=1/scales[j-1]
        coefficients=transform*mp.matrix(beta)
        original_covariance=transform*mp.matrix(covariance)*transform.T
        critical=_quantile(_normal_cdf,s.Rational(975,1000),engine,0,4)
        mean=sum(target)/n; null_loss=-n*(mean*math.log(mean)+(1-mean)*math.log1p(-mean))
        lr=max(0.,2*(null_loss-loss)); auc,roc=_binary_roc(target,logits)
        report={"n":n,"df":n-p,"confidence":.95,"fitScale":"binomial","approximate":True,"warnings":[],
                "numericBackend":"float64","fitDigits":15,"iterations":iteration+1,"method":"mle","intervalMethod":"wald",
                "pseudoRSquared":str(1-loss/null_loss),"deviance":str(2*loss),"aic":str(2*loss+2*p),
                "likelihoodRatio":str(lr),"likelihoodP":mp.nstr(_chisq_sf(lr,p-1),engine.precision),
                "auc":str(auc),"roc":[[str(x),str(y)] for x,y in roc],"coefficients":[],"residuals":[],
                "influenceMethod":"glm","influenceParameters":p}
        out=lambda v:mp.nstr(v,engine.precision)
        for j,value in enumerate(coefficients):
            se=mp.sqrt(original_covariance[j,j]); low=value-critical*se; high=value+critical*se
            report["coefficients"].append({"name":"b"+str(j),"estimate":out(value),"se":out(se),"low":out(low),"high":out(high),
                "p":out(2*_normal_sf(abs(value/se))),"oddsRatio":out(mp.exp(value)),"oddsLow":out(mp.exp(low)),"oddsHigh":out(mp.exp(high)),
                "vif":None if j==0 else str(max(1.,n*predictor_inverse[j][j]))})
        for i,(row,y,z,prob,w) in enumerate(zip(design,target,logits,probs,weights)):
            h=min(1.,max(0.,w*dot(row,[dot(v,row) for v in covariance])))
            pearson=math.exp(-z/2) if y else -math.exp(z/2)
            dev=math.sqrt(2*softplus(-z)) if y else -math.sqrt(2*softplus(z))
            cook=pearson**2*h/(p*(1-h)**2) if h<1 else None
            report["residuals"].append({"row":i+1,"observed":str(y),"fitted":str(prob),"residual":str(y-prob),
                "standardized":str(pearson),"deviance":str(dev),"leverage":str(h),"cook":None if cook is None else str(cook)})
        engine.regression_report=report
        engine.regression_parameters=[[c["name"],c["estimate"]] for c in report["coefficients"]]
        engine.note="Logistic MLE fitted with float64 IRLS; probability tails and coefficient intervals use mpmath. Fit accuracy is about 15 digits."
        variables=[engine.symbol("x" if p==2 else "x"+str(j)) for j in range(1,p)]
        expression=_mp_result(coefficients[0],engine)+sum(_mp_result(coefficients[j],engine)*variables[j-1] for j in range(1,p))
        return 1/(1+s.exp(-expression))
