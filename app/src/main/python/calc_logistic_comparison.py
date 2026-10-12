"""Nested unpenalized logistic fits and paired held-out prediction comparisons."""
import math
import random
from bisect import bisect_left, bisect_right
import mpmath as mp
from calc_shared import MathError, require
from calc_advanced_common import table, integer, number
from calc_statistics import _normal_sf, _chisq_sf


def _solve(matrix, right):
    n = len(right); lower = [[0.0]*n for _ in range(n)]
    scale = max(matrix[i][i] for i in range(n))
    for i in range(n):
        for j in range(i+1):
            value = matrix[i][j]-math.fsum(lower[i][k]*lower[j][k] for k in range(j))
            if i == j:
                require(value > max(1e-13,scale*1e-12), 'Logistic comparison requires identifiable, nonseparated MLE fits')
                lower[i][j] = math.sqrt(value)
            else: lower[i][j] = value/lower[j][j]
    forward = []
    for i in range(n): forward.append((right[i]-math.fsum(lower[i][j]*forward[j] for j in range(i)))/lower[i][i])
    result = [0.0]*n
    for i in range(n-1,-1,-1): result[i]=(forward[i]-math.fsum(lower[j][i]*result[j] for j in range(i+1,n)))/lower[i][i]
    return result


def _sigmoid(z):
    v = math.exp(-abs(z)); return 1/(1+v) if z >= 0 else v/(1+v)


def _softplus(z): return max(0,z)+math.log1p(math.exp(-abs(z)))


def fit_mle(rows, count):
    n = len(rows); p = count+1; target = [row[-1] for row in rows]
    require(n > p and all(y in (0,1) for y in target) and 0 < sum(target) < n, 'Logistic fits require both 0/1 classes and more rows than coefficients')
    transforms = []
    for j in range(count):
        peak = max(abs(row[j]) for row in rows) or 1
        center = math.fsum(row[j]/peak/n for row in rows)
        sd = math.sqrt(math.fsum((row[j]/peak-center)**2/n for row in rows))
        require(sd > 0, 'Logistic comparison requires identifiable, nonseparated MLE fits')
        transforms.append((peak,center,sd))
    design = [[1.0]+[(row[j]/peak-center)/sd for j,(peak,center,sd) in enumerate(transforms)] for row in rows]
    prevalence = sum(target)/n; beta = [math.log(prevalence/(1-prevalence))]+[0.0]*count
    def evaluate(b, derivatives=False):
        scores = [math.fsum(x*v for x,v in zip(row,b)) for row in design]
        require(all(math.isfinite(z) for z in scores), 'Logistic prediction is outside the numeric range')
        loss = math.fsum(_softplus(-z if y else z) for z,y in zip(scores,target))
        if not derivatives: return loss
        gradient = [0.0]*p; information = [[0.0]*p for _ in range(p)]
        for row,z,y in zip(design,scores,target):
            prob = _sigmoid(z); v=math.exp(-abs(z)); weight=v/(1+v)**2
            for i in range(p):
                gradient[i] += row[i]*(y-prob)
                for j in range(i+1): information[i][j] += weight*row[i]*row[j]
        for i in range(p):
            for j in range(i): information[j][i]=information[i][j]
        return loss,gradient,information
    for iteration in range(150):
        loss,gradient,information=evaluate(beta,True); step=_solve(information,gradient)
        if max(map(abs,step)) < 1e-8 and max(map(abs,gradient)) < 1e-7: break
        rate=1.0
        while rate >= 2**-35:
            candidate=[b+rate*d for b,d in zip(beta,step)]
            if evaluate(candidate) <= loss+1e-12: beta=candidate;break
            rate *= .5
        else: raise MathError('Logistic MLE did not converge; check separation and scaling')
        require(max(map(abs,beta)) < 50, 'Logistic comparison requires finite MLEs; separation detected')
    else: raise MathError('Logistic MLE did not converge in 150 iterations')
    return {'beta':beta,'transforms':transforms,'ll':-evaluate(beta),'p':p,'n':n,'iterations':iteration+1}


def predict(model, rows):
    beta=model['beta'];transforms=model['transforms']
    scores=[beta[0]+math.fsum(beta[j+1]*(row[j]/peak-center)/sd for j,(peak,center,sd) in enumerate(transforms)) for row in rows]
    require(all(math.isfinite(z) for z in scores), 'Logistic prediction is outside the numeric range')
    return scores


def placements(target, scores):
    positive=[z for y,z in zip(target,scores) if y==1];negative=[z for y,z in zip(target,scores) if y==0]
    require(positive and negative,'AUC comparison requires both 0 and 1')
    a=sorted(positive);b=sorted(negative);m=len(a);n=len(b)
    v10=[(bisect_left(b,z)+bisect_right(b,z))/(2*n) for z in positive]
    v01=[1-(bisect_left(a,z)+bisect_right(a,z))/(2*m) for z in negative]
    return math.fsum(v10)/m,v10,v01


def roc(target,scores):
    positives=sum(target);negatives=len(target)-positives;tp=fp=0;points=[[0.0,0.0]]
    order=sorted(range(len(scores)),key=lambda i:scores[i],reverse=True);i=0
    while i<len(order):
        end=i+1
        while end<len(order) and scores[order[end]]==scores[order[i]]:end+=1
        for at in order[i:end]:
            if target[at]:tp+=1
            else:fp+=1
        points.append([fp/negatives,tp/positives]);i=end
    return points


def delong(target,a,b,level=.95):
    aa,x,y=placements(target,a);bb,u,v=placements(target,b)
    def variance(values):
        center=math.fsum(values)/len(values)
        return math.fsum((z-center)**2 for z in values)/(len(values)-1)
    delta=bb-aa;result={'estimate':delta,'p':None,'interval':None,'intervalA':None,'intervalB':None,'variance':None}
    if min(len(x),len(y))<2:return result
    var_a=variance(x)/len(x)+variance(y)/len(y);var_b=variance(u)/len(u)+variance(v)/len(v)
    var_d=variance([j-i for i,j in zip(x,u)])/len(x)+variance([j-i for i,j in zip(y,v)])/len(y)
    critical=float(mp.sqrt(2)*mp.erfinv(level));result['variance']=var_d
    for key,estimate,var in [('intervalA',aa,var_a),('intervalB',bb,var_b)]:
        if var>0:result[key]=[max(0,estimate-critical*math.sqrt(var)),min(1,estimate+critical*math.sqrt(var))]
    if var_d>0:
        result.update(p=2*_normal_sf(abs(delta)/math.sqrt(var_d)),interval=[max(-1,delta-critical*math.sqrt(var_d)),min(1,delta+critical*math.sqrt(var_d))])
    elif delta==0:result.update(p=mp.mpf(1),interval=[0.0,0.0])
    return result


def metrics(target,scores,threshold):
    probabilities=[_sigmoid(z) for z in scores];cut=math.log(threshold/(1-threshold))
    correct=[int((z>=cut)==bool(y)) for y,z in zip(target,scores)]
    return {'AUC':placements(target,scores)[0],'Accuracy':sum(correct)/len(target),
            'Log loss':math.fsum(_softplus(-z if y else z) for y,z in zip(target,scores))/len(target),
            'Brier score':math.fsum((p-y)**2 for y,p in zip(target,probabilities))/len(target)},correct


def calibration(target,scores):
    bins=[[] for _ in range(10)]
    for y,z in zip(target,scores):
        p=_sigmoid(z);bins[min(9,int(p*10))].append((p,y))
    curve=[[math.fsum(p for p,y in cell)/len(cell),sum(y for p,y in cell)/len(cell),len(cell)] for cell in bins if cell]
    intercept=slope=None
    try:
        fitted=fit_mle([[z,y] for z,y in zip(scores,target)],1);peak,center,sd=fitted['transforms'][0]
        slope=fitted['beta'][1]/sd/peak;intercept=fitted['beta'][0]-fitted['beta'][1]*center/sd
    except MathError:pass
    return {'Calibration intercept':intercept,'Calibration slope':slope},curve


def folds_for(rows,folds,seed,identities=None):
    identities=list(range(len(rows))) if identities is None else identities
    classes=[sorted(set(identity for identity,row in zip(identities,rows) if row[-1]==y)) for y in (0,1)]
    require(min(map(len,classes))>=folds,'Each class needs at least as many distinct observations as folds')
    rng=random.Random(seed);mapping={}
    for group in classes:
        rng.shuffle(group)
        for i,identity in enumerate(group):mapping[identity]=i%folds
    return [mapping[identity] for identity in identities]


def cross_predictions(rows,count,folds,seed,identities=None):
    assigned=folds_for(rows,folds,seed,identities);a=[None]*len(rows);b=[None]*len(rows)
    for fold in range(folds):
        training=[row for row,at in zip(rows,assigned) if at!=fold];indices=[i for i,at in enumerate(assigned) if at==fold]
        test=[rows[i] for i in indices];ma=fit_mle(training,count);mb=fit_mle(training,len(rows[0])-1)
        for i,pa,pb in zip(indices,predict(ma,test),predict(mb,test)):a[i]=pa;b[i]=pb
    return a,b


def percentile(values,p):
    values=sorted(values);at=(len(values)-1)*p;lo=int(at);fraction=at-lo
    return values[lo]*(1-fraction)+values[min(lo+1,len(values)-1)]*fraction


def bootstrap(rows,target,a,b,count,mode,folds,threshold,level,resamples,seed):
    rng=random.Random(seed);indices=[[i for i,y in enumerate(target) if y==label] for label in (0,1)]
    draws={key:[] for key in ('AUC','Accuracy','Log loss','Brier score')};aucs=[[],[]];success=attempts=0
    while success<resamples and attempts<resamples*10:
        attempts+=1;sample=[rng.choice(group) for group in indices for _ in group]
        labels=[target[i] for i in sample]
        try:
            if mode=='crossvalidation':
                sampled=[rows[i] for i in sample];pa,pb=cross_predictions(sampled,count,folds,seed,sample)
            else:pa=[a[i] for i in sample];pb=[b[i] for i in sample]
            sa,_=metrics(labels,pa,threshold);sb,_=metrics(labels,pb,threshold)
        except MathError:continue
        for key in draws:draws[key].append(sb[key]-sa[key])
        aucs[0].append(sa['AUC']);aucs[1].append(sb['AUC']);success+=1
    require(success==resamples,'Too many invalid bootstrap refits; reduce folds or improve sample size and identifiability')
    alpha=(1-level)/2
    intervals={key:[percentile(values,alpha),percentile(values,1-alpha)] for key,values in draws.items()}
    return intervals,[[percentile(values,alpha),percentile(values,1-alpha)] for values in aucs],attempts-success


def calculate(engine,name,args):
    rows=table(args[0],minimum=4,columns=2);width=len(rows[0]);count=integer(args[1],0,width-2)
    mode=str(args[2]) if len(args)>2 else 'crossvalidation';require(mode in ('external','holdout','crossvalidation'),'Choose external, holdout or crossvalidation')
    threshold=number(args[4]) if len(args)>4 else .5;level=number(args[5]) if len(args)>5 else .95
    require(0<threshold<1 and 0<level<1,'Threshold and confidence level must be between 0 and 1')
    resamples=integer(args[6],0,20000,capacity=True) if len(args)>6 else 200;seed=integer(args[7],0,2147483647) if len(args)>7 else 0
    require(resamples==0 or resamples>=100,'Use zero or at least 100 bootstrap resamples')
    require(all(row[-1] in (0,1) for row in rows),'Logistic response must be binary 0/1')
    folds=0;train=rows
    if mode=='external':
        require(len(args)>3,'Provide a validation table')
        evaluation=table(args[3],minimum=4,columns=width);require(all(len(row)==width for row in evaluation),'Validation columns must match the training model')
    elif mode=='holdout':
        fraction=number(args[3]) if len(args)>3 else .25;require(0<fraction<1,'Holdout fraction must be between 0 and 1')
        rng=random.Random(seed);test_indices=set()
        for label in (0,1):
            group=[i for i,row in enumerate(rows) if row[-1]==label];require(len(group)>=4,'Holdout validation needs at least four observations in each class')
            rng.shuffle(group);size=max(2,min(len(group)-2,int(len(group)*fraction+.5)));test_indices.update(group[:size])
        train=[row for i,row in enumerate(rows) if i not in test_indices];evaluation=[row for i,row in enumerate(rows) if i in test_indices]
    else:
        folds=integer(args[3],2,len(rows)) if len(args)>3 else 5;evaluation=rows;require(resamples>=100,'Cross-validation confidence intervals require at least 100 bootstrap refits')
    require(all(row[-1] in (0,1) for row in evaluation),'Logistic response must be binary 0/1')
    require(0<sum(row[-1] for row in evaluation)<len(evaluation),'Validation requires both 0 and 1')
    excluded_train=excluded_validation=0
    if len(args)>8:
        require(isinstance(args[8],(list,tuple)) and len(args[8])==2,'Provide original training and validation row counts')
        excluded_train=integer(args[8][0],len(rows),2147483647)-len(rows)
        validation_count=integer(args[8][1],len(evaluation) if mode=='external' else 0,2147483647)
        if mode=='external':excluded_validation=validation_count-len(evaluation)
    ma=fit_mle(train,count);mb=fit_mle(train,width-1)
    difference=mb['ll']-ma['ll'];require(difference>=-1e-7,'Expanded MLE has lower likelihood; fit did not converge')
    lr=max(0,2*difference);df=mb['p']-ma['p']
    if mode=='crossvalidation':a,b=cross_predictions(rows,count,folds,seed)
    else:a=predict(ma,evaluation);b=predict(mb,evaluation)
    target=[row[-1] for row in evaluation];sa,ca=metrics(target,a,threshold);sb,cb=metrics(target,b,threshold)
    calibration_a,curve_a=calibration(target,a);calibration_b,curve_b=calibration(target,b)
    sa.update(calibration_a);sb.update(calibration_b)
    compared=delong(target,a,b,level) if mode!='crossvalidation' else {'interval':None,'p':None,'intervalA':None,'intervalB':None}
    gain=sum(not x and y for x,y in zip(ca,cb));loss=sum(x and not y for x,y in zip(ca,cb));discordant=gain+loss
    mcnemar=mp.mpf(1) if not discordant else min(mp.mpf(1),2*mp.betainc(discordant-min(gain,loss),min(gain,loss)+1,0,mp.mpf('.5'),regularized=True))
    intervals={};failures=0;auc_intervals=[compared['intervalA'],compared['intervalB']]
    if resamples:
        intervals,boot_aucs,failures=bootstrap(evaluation,target,a,b,count,mode,folds,threshold,level,resamples,seed)
        if mode=='crossvalidation':auc_intervals=boot_aucs
    if mode!='crossvalidation':intervals['AUC']=compared['interval']
    differences=[]
    for metric in ('AUC','Accuracy','Log loss','Brier score'):
        interval=intervals.get(metric);p=compared['p'] if metric=='AUC' else mcnemar if metric=='Accuracy' and mode!='crossvalidation' else None
        method=('Refitted CV bootstrap CI' if mode=='crossvalidation' else 'Paired DeLong' if metric=='AUC' else 'Exact McNemar + paired bootstrap CI' if metric=='Accuracy' else 'Paired bootstrap CI')
        differences.append([metric,sb[metric]-sa[metric],*(interval or [None,None]),p,method])
    assumptions=['Unpenalized maximum-likelihood logistic models; Model A is nested in Model B. Both fits use the same complete training rows. Finite identifiable fits and independent observations are required. LRT evaluates training fit, not future prediction improvement.',
                 'All performance differences are Model B − Model A. Higher AUC/accuracy and lower log loss/Brier score indicate improvement. Classification uses probability ≥ the specified threshold; choose it before examining validation outcomes.',
                 'Bootstrap samples are paired and class-stratified, conditional on observed class proportions. Invalid refits are retried and counted. Neither model selection nor data-driven threshold tuning is included.']
    if mode=='crossvalidation':assumptions.append('Pooled out-of-fold predictions share training observations. Ordinary paired DeLong and McNemar p values are not IID-valid here and are not reported. Percentile confidence intervals refit both models in every bootstrap sample and repeat the same stratified fold procedure; duplicated original observations stay in the same fold to prevent leakage. These internal-validation intervals are approximate.')
    else:assumptions.append('Validation observations must be independent of training and of each other. DeLong and exact McNemar evaluate paired validation predictions conditional on the fitted models. Held-out bootstrap intervals do not include uncertainty from fitting the training models. Degenerate DeLong variance or fewer than two observations per class can leave intervals/p values unavailable.')
    assumptions.append('Calibration curves use ten probability bins. Calibration intercept and slope come from joint logistic recalibration on validation logits (ideal 0 and 1); finite estimates can be unavailable with constant scores or separation.')
    training=[]
    for label,model in [('Model A',ma),('Model B',mb)]:training.append([label,model['n'],model['p'],model['ll'],2*model['p']-2*model['ll'],math.log(model['n'])*model['p']-2*model['ll']])
    return {'LRT χ²':lr,'LRT df':df,'LRT p':_chisq_sf(lr,df),'ΔAIC (B − A)':training[1][4]-training[0][4],'ΔBIC (B − A)':training[1][5]-training[0][5],
            'Excluded training rows':excluded_train,'Excluded validation rows':excluded_validation,
            'Training models':training,'Validation models':[[label,len(target),*(values[key] for key in ('AUC','Accuracy','Log loss','Brier score','Calibration intercept','Calibration slope'))] for label,values in [('Model A',sa),('Model B',sb)]],
            'Paired differences':differences,'Validation method':mode,'Seed':seed,**({'Folds':folds} if mode=='crossvalidation' else {'Requested holdout fraction':fraction,'Actual holdout fraction':len(evaluation)/len(rows)} if mode=='holdout' else {}),'Threshold':threshold,'Confidence level':level,'Bootstrap resamples':resamples,'Invalid bootstrap refits':failures,'Improved classifications':gain,'Worsened classifications':loss,
            'ROC curves':[roc(target,a),roc(target,b)],'AUC intervals':auc_intervals,'Calibration curves':[curve_a,curve_b],'Assumptions':assumptions}
