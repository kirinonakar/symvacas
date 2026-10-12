"""Portable nested model comparisons; prediction resampling lives in a separate module."""
import math
from types import SimpleNamespace
import mpmath as mp
from calc_shared import MathError, require
from calc_advanced_common import table, integer, number
from calc_statistics import _f_sf, _chisq_sf

FAMILIES = {'linear','logistic','poisson','nb','cox','lmm','glmm','gee','cfa','sem','mlclassification','mlregression'}
FIT_ONLY = {'lmm','glmm','gee','cfa','sem'}
OPTION_KEYS={'threshold','ties','randoma','randomb','responsefamily','points','correlation','correction','algorithm','alpha','ratio','trees','depth','forestseed','factors','estimator','basepaths','addedpaths','basecross','addedcross','baseresidual','addedresidual','excludedrows','excludedvalidation'}


def literal_options(engine,node):
    """Option keys and enumeration values are metadata, not user variables."""
    packed=engine.request.get('statisticsDatasets',{})
    if node.get('kind')=='list':pairs=[pair.get('args',[]) if pair.get('kind')=='list' else [] for pair in node.get('args',[])]
    elif node.get('kind')=='symbol' and node.get('value') in packed:pairs=packed[node['value']]
    else:return engine.build(node)
    result=[];enums={'ties','responsefamily','correlation','correction','algorithm','estimator'}
    for pair in pairs:
        require(isinstance(pair,list) and len(pair)==2,'Model comparison options must be key/value pairs')
        key,value=pair;require(isinstance(key,dict) and key.get('kind')=='symbol','Use named model comparison options')
        name=key['value']
        if isinstance(value,str):value=engine.number(value)
        elif name in enums and value.get('kind')=='symbol':value=value['value']
        else:value=engine.build(value)
        result.append([name,value])
    return result


def options(value):
    require(isinstance(value,(list,tuple)), 'Model comparison options must be key/value pairs')
    out={}
    for pair in value:
        require(isinstance(pair,(list,tuple)) and len(pair)==2, 'Model comparison options must be key/value pairs')
        key=str(pair[0]);require(key in OPTION_KEYS,'Unknown model comparison option');require(key not in out,'Duplicate model comparison option');out[key]=pair[1]
    return out


def coefficients(result):
    return [float(row['estimate']) for row in result['coefficients']]


def reduced(rows,count,family):
    if family=='cox':return [row[:2]+row[2:2+count] for row in rows]
    if family in ('lmm','glmm','gee'):return [row[:1]+row[1:1+count]+row[-1:] for row in rows]
    return [row[:count]+row[-1:] for row in rows]


def predictor_count(rows,family):return len(rows[0])-(2 if family in ('cox','lmm','glmm','gee') else 1)


def fit(rows,family,opts,random_effect=None):
    """Fit two models with identical likelihood conventions and response rows."""
    n=len(rows); count=predictor_count(rows,family);p=count+1; result={};pred=None
    scratch=SimpleNamespace(note='',comparison_intercept_only=True)
    if family=='linear':
        from calc_advanced_linear import least_squares
        design=[[1.]+r[:-1] for r in rows];target=[r[-1] for r in rows]
        beta,_,sse,fitted=least_squares(design,target)
        total=math.fsum((v-math.fsum(target)/n)**2 for v in target)
        boundary=sse<=64*n*max(math.ulp(v)**2 for v in target)
        ll=None if boundary else -n/2*(math.log(2*math.pi)+1+math.log(sse/n))
        result={'log likelihood':ll,'AIC':None if boundary else 2*(p+1)-2*ll,'BIC':None if boundary else math.log(n)*(p+1)-2*ll,'SSE':sse,'R²':1-sse/total if total else None,'residual variance boundary':int(boundary)}
        pred=lambda data:[math.fsum(b*x for b,x in zip(beta,[1.]+r[:-1])) for r in data]
    elif family=='logistic':
        from calc_logistic_comparison import fit_mle,predict
        model=fit_mle(rows,count);ll=model['ll'];result={'log likelihood':ll,'AIC':2*p-2*ll,'BIC':math.log(n)*p-2*ll}
        pred=lambda data:predict(model,data)
    elif family in ('poisson','nb'):
        from calc_advanced_regression import model
        if family=='nb':
            try:result=model(rows,'nbreg')
            except MathError:
                boundary=model(rows,'poissonreg');beta=coefficients(boundary)
                mu=[math.exp(math.fsum(b*x for b,x in zip(beta,[1.]+r[:-1]))) for r in rows]
                require(math.fsum((r[-1]-m)**2-r[-1] for r,m in zip(rows,mu))<=0,'NB2 comparison did not converge to an identifiable interior or Poisson-boundary estimate')
                result=dict(boundary,**{'dispersion alpha (NB2)':0.,'dispersion boundary':1,'NB2 estimation':'ML (Poisson boundary)'})
        else:result=model(rows,'poissonreg')
        beta=coefficients(result)
        pred=lambda data:[math.exp(math.fsum(b*x for b,x in zip(beta,[1.]+r[:-1]))) for r in data]
        mu=pred(rows);alpha=result.get('dispersion alpha (NB2)',0.)
        if alpha:
            size=1/alpha
            deviance=2*math.fsum((y*math.log(y/m) if y else 0)-(y+size)*math.log((y+size)/(m+size)) for r,m in zip(rows,mu) for y in [r[-1]])
        else:deviance=2*math.fsum((y*math.log(y/m) if y else 0)-(y-m) for r,m in zip(rows,mu) for y in [r[-1]])
        result['Deviance']=max(0.,deviance);result['BIC']=math.log(n)*(p+int(family=='nb' and not result.get('dispersion boundary')))-2*result['log likelihood']
    elif family=='cox':
        from calc_advanced_survival import calculate
        ties=str(opts.get('ties','efron'))
        if count:
            result=calculate(scratch,'cox',[rows,ties,-1,0]);beta=coefficients(result);ll=result['partial log likelihood']
            pred=lambda data:[math.fsum(b*x for b,x in zip(beta,r[2:])) for r in data]
        else:
            require(ties in ('efron','breslow'),'Cox ties: breslow or efron')
            require(all(r[0]>=0 and r[1] in (0,1) for r in rows) and sum(r[1] for r in rows)>0,'Cox requires nonnegative times and binary event indicators')
            ll=0.
            for t in sorted({r[0] for r in rows if r[1]}):
                d=sum(r[0]==t and r[1]==1 for r in rows);risk=sum(r[0]>=t for r in rows)
                ll-=d*math.log(risk) if ties=='breslow' else math.fsum(math.log(risk-j) for j in range(d))
            pred=lambda data:[0.]*len(data)
        p=count;result.update({'log likelihood':ll,'AIC':2*p-2*ll,'BIC':math.log(max(1,sum(r[1] for r in rows)))*p-2*ll})
    elif family in ('lmm','glmm','gee'):
        effect=0 if random_effect is None else random_effect
        if family=='lmm':
            from calc_advanced_longitudinal import calculate
            result=calculate(scratch,'mixedmodel',[rows,effect,'ml'])
        elif family=='glmm':
            from calc_advanced_glmm import calculate
            result=calculate(scratch,'glmm',[rows,str(opts.get('responsefamily','binomial')),integer(opts.get('points',15),1,31,capacity=True),[],'offset','refit',effect])
        else:
            from calc_advanced_longitudinal import calculate
            result=calculate(scratch,'gee',[rows,str(opts.get('responsefamily','gaussian')),str(opts.get('correlation','independence')),[],str(opts.get('correction','robust'))])
            result['AIC']=result['BIC']=result['log likelihood']=None
    elif family in ('mlclassification','mlregression'):
        from calc_advanced_learning import machine_fit
        kind=str(opts.get('algorithm','ridge'));alpha=number(opts.get('alpha',.1));ratio=number(opts.get('ratio',.5))
        require(alpha>0 and 0<=ratio<=1,'ML comparison requires positive penalty and an L1 ratio between 0 and 1')
        require(kind in ('ridge','lasso','elasticnet','forest'),'Choose ridge, lasso, elasticnet or forest')
        if not count:
            mean=math.fsum(r[-1] for r in rows)/n
            pred=lambda data:[mean]*len(data)
        elif kind=='forest':
            import sympy as s
            from calc_machine_learning import fit_random_forest
            # Retain the normal forest fitting path and its runtime safeguards.
            scratch.precision=30
            fit_random_forest(scratch,[[s.Float(v,16) for v in row] for row in rows],[s.Integer(integer(opts.get('trees',50),1,200,capacity=True)),s.Integer(integer(opts.get('depth',6),1,20,capacity=True)),s.Integer(integer(opts.get('forestseed',0),0,2147483647))],task='classification' if family=='mlclassification' else 'regression')
            predict=scratch.regression_predict;pred=lambda data:[predict(r[:-1]) for r in data]
        else:
            if family=='mlclassification':
                require(kind=='ridge','Classification uses ridge logistic or forest')
                predict=machine_fit(rows,'logistic',alpha,0.)
            else:predict=machine_fit(rows,kind,alpha,1. if kind=='lasso' else ratio if kind=='elasticnet' else 0.)
            pred=lambda data:[predict(r[:-1]) for r in data]
        result={'log likelihood':None,'AIC':None,'BIC':None}
        p=None
    else:raise MathError('Unknown model comparison family')
    return dict(result,n=n,p=p,predict=pred,notes=scratch.note)


def fit_comparison(a,b,family,count,full,structures_equal=True):
    delta=full-count;out={};reason=''
    for metric in ('AIC','BIC','R²','Deviance'):
        if a.get(metric) is not None and b.get(metric) is not None:out['Δ'+metric+' (B − A)']=b[metric]-a[metric]
    if family=='linear':
        if a.get('residual variance boundary') or b.get('residual variance boundary'):
            return out,'Residual variance is at numerical zero; Gaussian likelihood criteria and partial F inference are unavailable. Prediction differences remain descriptive.'
        df=b['n']-b['p'];require(df>0 and b['SSE']>0,'Residual degrees of freedom and variance must be positive')
        improvement=a['SSE']-b['SSE'];require(improvement>=-1e-8*max(1.,a['SSE']),'Expanded linear fit has larger residual error')
        f=max(0.,improvement)/delta/(b['SSE']/df);out.update({'F':f,'df1':delta,'df2':df,'p':float(_f_sf(f,delta,df))})
    elif family in ('logistic','poisson','nb','cox','lmm','glmm'):
        reliable=structures_equal and all(model.get('optimizer converged',1) and not model.get('singular fit',0) and not model.get('dispersion boundary',0) for model in (a,b))
        if family=='glmm' and any(model.get('quadrature check')=='refit failed' or any(row.get('CI95') is None for row in model.get('coefficients',[])) for model in (a,b)):reliable=False
        if reliable:
            improvement=b['log likelihood']-a['log likelihood']
            if improvement>=-1e-7*max(1.,abs(a['log likelihood'])):
                lr=max(0.,2*improvement);out.update({'LRT χ²':lr,'LRT df':delta,'p':float(_chisq_sf(lr,delta))})
            else:reason='Expanded fit has lower likelihood; likelihood-ratio inference omitted.'
        else:reason='Random-effect structures differ, a variance/dispersion is on the boundary, or fit diagnostics failed; ordinary chi-square LRT omitted. Compare ML AIC/BIC descriptively.'
    elif family=='gee':reason='GEE uses estimating equations, not a full likelihood; LRT, AIC and BIC are omitted. Robust coefficient inference is retained in each fitted model.'
    else:reason='Penalized and forest models are compared by paired validation predictions; ordinary likelihood-ratio tests and AIC/BIC are omitted.'
    return out,reason


def measurement(rows,family,opts):
    from calc_advanced_sem import fit as sem_fit
    factors=opts.get('factors',[1]*len(rows[0]));estimator=str(opts.get('estimator','ml'))
    def pairs(key):
        value=opts.get(key,[]);require(isinstance(value,(list,tuple)),'Use model parameter pairs')
        result=[tuple(integer(v,1,100) for v in pair) for pair in value if isinstance(pair,(list,tuple)) and len(pair)==2]
        require(len(result)==len(value) and len(set(result))==len(result),'Model parameter pairs must be distinct');return result
    paths=pairs('basepaths');added=pairs('addedpaths');cross=pairs('basecross');newcross=pairs('addedcross');residual=pairs('baseresidual');newresidual=pairs('addedresidual')
    require(added or newcross or newresidual,'Select added paths, cross-loadings or residual covariances')
    require(not set(paths)&set(added) and not set(cross)&set(newcross) and not set(residual)&set(newresidual),'Added model parameters must differ from existing parameters')
    require(family=='sem' or not paths+added,'CFA comparisons use cross-loadings or residual covariances')
    models=[]
    for expanded in (False,True):
        args=[rows,factors]+([paths+(added if expanded else [])] if family=='sem' else [])
        args+=[cross+(newcross if expanded else []),'complete',[],'configural',estimator,residual+(newresidual if expanded else []),0,0,0]
        result=sem_fit(SimpleNamespace(note=''),family,args);models.append(result)
    a,b=models;df=a['df']-b['df'];out={}
    for metric in ('CFI','RMSEA'):
        if a.get(metric) is not None and b.get(metric) is not None:out['Δ'+metric+' (B − A)']=b[metric]-a[metric]
    from calc_advanced_sem_summary import measurement_markers
    groups=[[i for i,v in enumerate(factors) if int(v)==factor] for factor in range(1,max(map(int,factors))+1)]
    markers_equal=measurement_markers(groups,[(i-1,j-1) for i,j in cross])==measurement_markers(groups,[(i-1,j-1) for i,j in cross+newcross])
    # Adding a directed path can replace an exogenous covariance: that is not
    # necessarily a nested covariance model, even if the path list is a superset.
    paths_equal={target for source,target in paths}=={target for source,target in paths+added}
    if estimator=='ml' and df>0 and markers_equal and paths_equal and a['χ²']>=b['χ²']-1e-6:
        chi=max(0.,a['χ²']-b['χ²']);out.update({'Difference χ²':chi,'Δχ² (B − A)':-chi,'Difference df':df,'p':float(_chisq_sf(chi,df))});reason='Normal-theory nested-model chi-square difference on identical indicators and complete rows.'
    else:reason='Chi-square difference inference omitted: adjusted WLSMV statistics, changed marker constraints, changed latent covariance structure, or no positive difference degrees of freedom. Fit-index differences are descriptive.'
    return {'Analysis family':family,'Training rows':len(rows),'Model fit':[[label,len(rows),None,None,None,None,None,None,m['χ²'],m['df'],m['CFI'],m['RMSEA']] for label,m in zip(('Model A','Model B'),models)],**out,'Comparison inference':reason,'Assumptions':['Both measurement models use identical observed indicators, factor assignments, estimator and complete rows.','WLSMV adjusted chi-square values are never subtracted to produce an ordinary chi-square p value. ΔCFI and ΔRMSEA are descriptive; they are not calibrated significance tests.']}


def compare_one(rows,count,family,mode,argument,level,resamples,seed,opts):
    from calc_model_comparison_validation import evaluate, paired_metrics, bootstrap
    full=predictor_count(rows,family);require(0<=count<full,'Choose at least one added predictor')
    random_a=opts.get('randoma',0);random_b=opts.get('randomb',random_a)
    train,validation,pa,pb=evaluate(rows,count,family,mode,argument,opts,seed,fit)
    a=fit(reduced(train,count,family),family,opts,random_a);b=fit(train,family,opts,random_b)
    test,reason=fit_comparison(a,b,family,count,full,random_a==random_b)
    result={'Analysis family':family,'Training rows':len(train),'Model fit':[[label,m['n'],m['p'],m.get('log likelihood'),m.get('AIC'),m.get('BIC'),m.get('R²'),m.get('Deviance'),None,None,None,None] for label,m in zip(('Model A','Model B'),(a,b))],**test,'Comparison inference':reason or ('Nested partial F test' if family=='linear' else 'Nested-model ML likelihood-ratio test'),'Validation method':mode,'Seed':seed,'Confidence level':level,'Bootstrap resamples':resamples}
    assumptions=['Model A and Model B use the same union of complete selected rows; Model B retains all baseline predictors. All numeric differences are B − A.','Candidate screening is exploratory. Multiplicity-adjusted training tests do not remove selection optimism; assess the selected model on untouched data or with a separate outer validation loop.']
    family_assumptions={
        'linear':'The partial F test assumes independent normal errors with common variance and full-rank nested designs. AIC/BIC use Gaussian ML with the residual-variance parameter.',
        'logistic':'Logistic likelihood-ratio inference assumes independent binary observations, nested unpenalized models and finite identifiable interior MLEs.',
        'poisson':'Poisson likelihood-ratio inference assumes independent counts with correctly specified log means and Poisson conditional variance.',
        'nb':'NB2 likelihood-ratio inference assumes independent counts and identifiable interior dispersion estimates in both models.',
        'cox':'Cox fit comparisons assume proportional hazards and independent noninformative censoring. Both models use the same risk sets and tie convention.',
        'glmm':'GLMM fixed-effect LRT requires the same random structure, converged marginal ML fits and interior variance parameters. Boundary or quadrature-sensitive fits receive descriptive information-criterion comparisons.',
        'lmm':'Gaussian mixed models assume independent clusters and the specified conditional Gaussian covariance structure.'}
    if family in family_assumptions:assumptions.append(family_assumptions[family])
    if family=='lmm':assumptions.append('Fixed-effect comparisons automatically fit both Gaussian mixed models by ML, with the selected random structure. REML likelihoods are not compared.')
    if family in ('lmm','glmm','gee'):
        result['Model A coefficients']=a['coefficients'];result['Model B coefficients']=b['coefficients']
        for label,m in zip(('Model A','Model B'),(a,b)):
            if m.get('diagnostics'):result[label+' diagnostics']=m['diagnostics']
    if family=='nb':assumptions.append('NB2 dispersion is jointly re-estimated in each model. ΔDeviance uses each model’s own dispersion; the nested test uses the full log likelihood.')
    if validation:
        threshold=number(opts.get('threshold',.5));require(0<threshold<1,'Classification threshold must be between 0 and 1')
        ma,mb=paired_metrics(validation,pa,pb,family,threshold)
        intervals,failures=bootstrap(rows,validation,pa,pb,count,family,mode,argument,opts,level,resamples,seed,fit) if resamples and (mode!='apparent' or family in ('logistic','mlclassification')) else ({},0)
        result['Validation performance']=[dict(Model=label,n=len(validation),**metrics) for label,metrics in zip(('Model A','Model B'),(ma,mb))]
        result['Paired differences']=[[key,mb[key]-ma[key] if ma[key] is not None and mb[key] is not None else None,*(intervals.get(key) or [None,None]),None,'Refitted paired CV bootstrap' if mode=='crossvalidation' else 'Paired validation bootstrap' if mode!='apparent' else 'Apparent training performance; descriptive'] for key in ma]
        result['Invalid bootstrap refits']=failures
        for row in result['Paired differences']:
            key='Δ'+row[0]+' (B − A)'
            if key in result:key='ΔValidation '+row[0]+' (B − A)'
            result[key]=row[1]
        if family in ('logistic','mlclassification'):
            from calc_logistic_comparison import roc,calibration,delong
            target=[r[-1] for r in validation];result['ROC curves']=[roc(target,pa),roc(target,pb)]
            if family=='logistic':
                calibration_a,curve_a=calibration(target,pa);calibration_b,curve_b=calibration(target,pb)
                for record,extra in zip(result['Validation performance'],(calibration_a,calibration_b)):record.update(extra)
                result['Calibration curves']=[curve_a,curve_b]
            cut=math.log(threshold/(1-threshold)) if family=='logistic' else threshold
            a_correct=[(score>=cut)==bool(y) for score,y in zip(pa,target)]
            b_correct=[(score>=cut)==bool(y) for score,y in zip(pb,target)]
            gain=sum(not a and b for a,b in zip(a_correct,b_correct));loss=sum(a and not b for a,b in zip(a_correct,b_correct));discordant=gain+loss
            result['Improved classifications']=gain;result['Worsened classifications']=loss
            if mode in ('external','holdout','apparent'):
                auc=delong(target,pa,pb,level)
                result['AUC intervals']=[auc['intervalA'],auc['intervalB']]
                mcnemar=mp.mpf(1) if not discordant else min(mp.mpf(1),2*mp.betainc(discordant-min(gain,loss),min(gain,loss)+1,0,mp.mpf('.5'),regularized=True))
                for row in result['Paired differences']:
                    if row[0]=='AUC':row[2:5]=[*(auc['interval'] or [None,None]),auc['p']];row[5]='Paired DeLong'
                    elif row[0]=='Accuracy':row[4]=mcnemar;row[5]='Exact McNemar + paired bootstrap CI'
                    else:row[5]='Paired bootstrap CI'
                if mode!='apparent':assumptions.append('DeLong AUC and exact McNemar inference for selected-data/holdout predictions require validation observations independent of training and of each other; these conditional tests exclude training-fit uncertainty.')
            else:
                for row in result['Paired differences']:
                    if row[0] in ('AUC','Accuracy'):
                        method='DeLong' if row[0]=='AUC' else 'McNemar'
                        row[5]=method+' p omitted (CV); refitted bootstrap CI' if mode=='crossvalidation' and resamples else method+' p omitted (CV)' if mode=='crossvalidation' else method+' p omitted (training data)'
                    elif mode=='crossvalidation':row[5]='Refitted CV bootstrap CI'
        assumptions.append('The two prediction sets use the same validation observations. CV bootstrap refits both models and repeats the shared folds; duplicate original observations remain in the same fold. Pooled CV predictions receive no ordinary IID DeLong or McNemar p values.')
        if mode=='apparent':
            assumptions.append('Training-data DeLong/McNemar p values and paired bootstrap intervals are nominal, descriptive plug-in comparisons of fitted predictions. They reuse model-fitting observations, omit fitting/selection uncertainty and do not establish independent validation improvement.' if family in ('logistic','mlclassification') else 'Training-data prediction performance is apparent fit, not independent validation; paired prediction confidence intervals are omitted.')
        if family=='cox':assumptions.append('Harrell C-index uses comparable pairs with an observed earlier event and half credit for tied risk scores. Cox AIC uses the partial likelihood and identical event rows/tie handling.')
    result['Excluded training rows']=integer(opts.get('excludedrows',0),0,2147483647)
    result['Excluded validation rows']=integer(opts.get('excludedvalidation',0),0,2147483647)
    result['Assumptions']=assumptions
    return result


def calculate(engine,name,args):
    rows=table(args[0],4,1);family=str(args[2]) if len(args)>2 else 'linear';require(family in FAMILIES,'Choose a valid model comparison family')
    opts=options(args[8]) if len(args)>8 else {};count=integer(args[1],0,len(rows[0]))
    if family in ('cfa','sem'):return measurement(rows,family,opts)
    full=predictor_count(rows,family);require(0<=count<full,'Choose at least one added predictor')
    mode=str(args[3]) if len(args)>3 else ('fit' if family in FIT_ONLY else 'crossvalidation');require(mode in ('fit','external','holdout','crossvalidation','apparent'),'Choose a valid comparison validation method')
    require(family not in FIT_ONLY or mode=='fit','Clustered comparisons use model-fit comparisons')
    argument=args[4] if len(args)>4 else 5;level=number(args[5]) if len(args)>5 else .95;require(0<level<1,'Confidence level must be between 0 and 1')
    resamples=integer(args[6],0,20000,capacity=True) if len(args)>6 else 200;seed=integer(args[7],0,2147483647) if len(args)>7 else 0
    require(resamples==0 or resamples>=100,'Use zero or at least 100 bootstrap resamples')
    scan=integer(args[9],0,1) if len(args)>9 else 0
    if mode=='external':
        argument=table(argument,4,len(rows[0]));require(all(len(r)==len(rows[0]) for r in argument),'Validation columns must match the training model')
        if rows==argument:mode='apparent'
    if not scan:return compare_one(rows,count,family,mode,argument,level,resamples,seed,opts)
    records=[];failed=[];results=[]
    for candidate in range(count,full):
        prefix=2 if family=='cox' else 1 if family in ('lmm','glmm','gee') else 0
        columns=list(range(prefix+count))+[prefix+candidate]+([] if family=='cox' else [len(rows[0])-1])
        selected=[[r[i] for i in columns] for r in rows];other=[[r[i] for i in columns] for r in argument] if mode=='external' else argument
        try:result=compare_one(selected,count,family,mode,other,level,resamples,seed,opts)
        except MathError as exc:failed.append({'Candidate':candidate-count+1,'Reason':str(exc)});continue
        record={'Candidate':candidate-count+1,'p':result.get('p')}
        record.update({key:value for key,value in result.items() if key.startswith('Δ') or key in ('F','LRT χ²')})
        for key in ('Improved classifications','Worsened classifications'):
            if key in result:record[key]=result[key]
        for metric,estimate,lower,upper,p,method in result.get('Paired differences',[]):
            record['Δ'+metric+' lower CI']=lower;record['Δ'+metric+' upper CI']=upper
        records.append(record);results.append(result)
    require(records,'No candidate comparison could be fitted')
    valid=[i for i,r in enumerate(records) if r['p'] is not None]
    # Holm uses all attempted candidates, treating failed/unavailable tests as p=1.
    from calc_model_comparison_validation import holm
    adjusted=holm([r['p'] if r['p'] is not None else 1. for r in records]+[1.]*len(failed))
    for i,r in enumerate(records):r['Holm p']=adjusted[i] if i in valid else None
    return {'Analysis family':family,'Training rows':len(rows),'Candidate comparisons':records,'Failed candidate comparisons':failed,'Comparison inference':'Each added variable is fitted separately against the same baseline; Holm correction covers all attempted candidates.','Assumptions':results[0]['Assumptions']+['All candidates use the same complete-row union. The displayed ordering does not constitute a validated variable-selection rule. Candidate prediction intervals are pointwise, not simultaneous or selection-adjusted.']}
