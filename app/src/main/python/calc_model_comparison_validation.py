"""Shared paired prediction metrics, folds and bootstrap for model comparison."""
import math
import random
from calc_shared import MathError,require
from calc_advanced_common import integer,number
from calc_logistic_comparison import metrics,percentile


def holm(values):
    order=sorted(range(len(values)),key=values.__getitem__);out=[0.]*len(values);previous=0.
    for rank,i in enumerate(order):previous=max(previous,min(1.,values[i]*(len(values)-rank)));out[i]=previous
    return out


def concordance(rows,scores):
    """Harrell concordance in O(n log n); equal-time events are not comparable."""
    ordered=sorted(set(scores));rank={v:i+1 for i,v in enumerate(ordered)};tree=[0]*(len(ordered)+1)
    def add(at):
        while at<len(tree):tree[at]+=1;at+=at&-at
    def total(at):
        result=0
        while at:result+=tree[at];at-=at&-at
        return result
    groups={}
    for i,row in enumerate(rows):groups.setdefault(row[0],[]).append(i)
    numerator=denominator=0.;later=0
    for time in sorted(groups,reverse=True):
        censored=[i for i in groups[time] if not rows[i][1]];events=[i for i in groups[time] if rows[i][1]]
        for i in censored:add(rank[scores[i]]);later+=1
        for i in events:
            at=rank[scores[i]];lower=total(at-1);equal=total(at)-lower
            numerator+=lower+.5*equal;denominator+=later
        for i in events:add(rank[scores[i]]);later+=1
    return numerator/denominator if denominator else None


def paired_metrics(rows,a,b,family,threshold=.5):
    target=[r[-1] for r in rows]
    def measure(scores):
        require(all(math.isfinite(v) for v in scores),'Nonfinite validation predictions')
        if family in ('logistic','mlclassification'):
            require(set(target)<={0,1} and 0<sum(target)<len(target),'Classification validation requires both 0 and 1')
            if family=='mlclassification':scores=[math.log(max(1e-15,min(1-1e-15,v))/(1-max(1e-15,min(1-1e-15,v)))) for v in scores]
            result=metrics(target,scores,threshold)[0]
            return {key:result[key] for key in (('AUC','Accuracy','Log loss') if family=='mlclassification' else ('AUC','Accuracy','Log loss','Brier score'))}
        if family=='cox':return {'C-index':concordance(rows,scores)}
        n=len(target);sse=math.fsum((v-y)**2 for v,y in zip(scores,target));center=math.fsum(target)/n;sst=math.fsum((y-center)**2 for y in target)
        return {'RMSE':math.sqrt(sse/n),'MAE':math.fsum(abs(v-y) for v,y in zip(scores,target))/n,'R²':1-sse/sst if sst else None}
    return measure(a),measure(b)


def assignments(rows,k,seed,family,identities=None):
    identities=list(range(len(rows))) if identities is None else identities;unique={i:r for i,r in zip(identities,rows)}
    binary=family in ('logistic','mlclassification','cox');classes={}
    for i,row in unique.items():classes.setdefault(row[1] if family=='cox' else row[-1] if binary else 0,[]).append(i)
    rng=random.Random(seed);mapping={}
    for label in sorted(classes):
        group=sorted(classes[label])
        require(len(group)>=k,'Each validation stratum needs at least as many distinct observations as folds')
        rng.shuffle(group)
        for j,i in enumerate(group):mapping[i]=j%k
    return [mapping[i] for i in identities]


def evaluate(rows,count,family,mode,argument,opts,seed,fit,identities=None):
    from calc_model_comparison import reduced,FIT_ONLY
    if family in FIT_ONLY:return rows,[],[],[]
    if mode=='crossvalidation':
        k=integer(argument,2,len(rows));folds=assignments(rows,k,seed,family,identities);a=[None]*len(rows);b=a.copy()
        for fold in range(k):
            train=[r for r,at in zip(rows,folds) if at!=fold];indices=[i for i,at in enumerate(folds) if at==fold];test=[rows[i] for i in indices]
            ma=fit(reduced(train,count,family),family,opts);mb=fit(train,family,opts)
            for i,pa,pb in zip(indices,ma['predict'](reduced(test,count,family)),mb['predict'](test)):a[i]=pa;b[i]=pb
        return rows,rows,a,b
    if mode=='holdout':
        fraction=number(argument);require(0<fraction<1,'Holdout fraction must be between 0 and 1')
        classes={};binary=family in ('logistic','mlclassification','cox')
        for i,row in enumerate(rows):classes.setdefault(row[1] if family=='cox' else row[-1] if binary else 0,[]).append(i)
        rng=random.Random(seed);selected=set()
        for label in sorted(classes):
            group=classes[label]
            require(len(group)>=4,'Each holdout stratum needs at least four observations');rng.shuffle(group)
            size=max(2,min(len(group)-2,int(len(group)*fraction+.5)));selected.update(group[:size])
        train=[r for i,r in enumerate(rows) if i not in selected];test=[r for i,r in enumerate(rows) if i in selected]
    else:
        require(mode in ('external','apparent'),'Prediction comparisons require external, holdout, crossvalidation or apparent validation')
        train=rows;test=argument if mode=='external' else rows
    a=fit(reduced(train,count,family),family,opts);b=fit(train,family,opts)
    return train,test,a['predict'](reduced(test,count,family)),b['predict'](test)


def bootstrap(rows,validation,a,b,count,family,mode,argument,opts,level,samples,seed,fit):
    rng=random.Random(seed);groups={};binary=family in ('logistic','mlclassification','cox')
    for i,row in enumerate(validation):groups.setdefault(row[1] if family=='cox' else row[-1] if binary else 0,[]).append(i)
    draws={};success=attempts=0;threshold=number(opts.get('threshold',.5))
    while success<samples and attempts<samples*10:
        attempts+=1;indices=[rng.choice(groups[label]) for label in sorted(groups) for _ in groups[label]];sample=[validation[i] for i in indices]
        try:
            if mode=='crossvalidation':_,sample,pa,pb=evaluate(sample,count,family,mode,argument,opts,seed,fit,indices)
            else:pa=[a[i] for i in indices];pb=[b[i] for i in indices]
            ma,mb=paired_metrics(sample,pa,pb,family,threshold)
        except (MathError,OverflowError,ZeroDivisionError):continue
        valid={key:mb[key]-ma[key] for key in ma if ma[key] is not None and mb[key] is not None}
        # Undefined C-index or R² draws are counted instead of inventing values.
        if not valid:continue
        for key,value in valid.items():draws.setdefault(key,[]).append(value)
        success+=1
    require(success==samples,'Too many invalid paired bootstrap refits; improve identifiability or reduce folds')
    alpha=(1-level)/2
    return {key:[percentile(values,alpha),percentile(values,1-alpha)] for key,values in draws.items() if len(values)>=max(20,int(.9*samples))},attempts-success
