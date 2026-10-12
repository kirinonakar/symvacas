"""Residual parameters, efficient score diagnostics and latent path effects."""
import math
import random
import mpmath as mp
from calc_shared import require, MathError
from calc_advanced_common import integer
from calc_statistics import _chisq_sf


def options(name,args,p):
    at=(3 if name=='sem' else 2)+5
    pairs=[]
    for pair in args[at] if len(args)>at else []:
        require(isinstance(pair,(list,tuple)) and len(pair)==2,'Use [indicator,indicator] residual covariance pairs')
        i,j=[integer(v,1,p)-1 for v in pair]
        require(i!=j,'Residual covariance needs two different indicators')
        pairs.append(tuple(sorted((i,j))))
    require(len(set(pairs))==len(pairs),'Residual covariance pairs must be distinct')
    mi=integer(args[at+1],0,1) if len(args)>at+1 else 0
    samples=integer(args[at+2],0,10000,capacity=True) if len(args)>at+2 else 0
    require(samples==0 or samples>=20,'Use at least 20 SEM bootstrap samples')
    seed=integer(args[at+3],0,2147483647) if len(args)>at+3 else 0
    return pairs,mi,samples,seed


def connected(paths,k):
    reach={(source,target) for source,target in paths}
    for middle in range(k):
        reach|={(source,target) for source in range(k) for target in range(k)
                if (source,middle) in reach and (middle,target) in reach}
    return reach


def candidates(p,k,assignments,markers,cross,paths,residual):
    reach=connected(paths,k)
    for i in range(p):
        for j in range(k):
            if j!=assignments[i]-1 and (i,j) not in cross: yield 'loading',i,j
    for i in range(p):
        for j in range(i):
            if tuple(sorted((i,j))) not in residual: yield 'residual',i,j
    for source in range(k):
        for target in range(k):
            if source!=target and (source,target) not in paths and (target,source) not in reach:
                yield 'path',target,source


def mi_row(kind,i,j,mi,epc,scales,markers,label=None):
    if kind=='loading':
        row={'Kind':'Cross-loading','term':'feature:'+str(i+1),'Factor':j+1}; unit=scales[i]/scales[markers[j]]
    elif kind=='residual':
        row={'Kind':'Residual covariance','First indicator':'feature:'+str(j+1),'Second indicator':'feature:'+str(i+1)}; unit=scales[i]*scales[j]
    else:
        row={'Kind':'Structural path','term':str(j+1)+' → '+str(i+1)}; unit=scales[markers[i]]/scales[markers[j]]
    row.update({'MI':mi,'Expected parameter change':epc*unit,'p':float(_chisq_sf(mi,1))})
    if label is not None: row['Group']='group:'+format(label,'.15g')
    return row


def normal_mi(parameters,prepared,model,labels,p,k,assignments,markers,cross,paths,residual,scales):
    from calc_advanced_sem_extended import observed_loss
    q=len(parameters); info=mp.zeros(q); gradient=mp.zeros(q,1); blocks=[]
    for g in prepared:
        sigma,mu,deriv=model(parameters,g,True)
        _,gm,gc=observed_loss(mu,sigma,g['patterns'])
        for index,d,dm in deriv:
            gradient[index]+=float((gm.T*dm)[0]+(sum(gc[i,j]*d[j,i] for i in range(p) for j in range(p)) if d is not None else 0))
        for at,count,center,second in g['patterns']:
            inv=mp.matrix([[sigma[i,j] for j in at] for i in at])**-1
            columns=mp.zeros(len(at)**2,q); means=mp.zeros(len(at),q)
            for index,d,dm in deriv:
                part=inv*mp.matrix([[d[i,j] for j in at] for i in at]) if d is not None else mp.zeros(len(at))
                for i in range(len(at)):
                    means[i,index]+=dm[at[i]]
                    for j in range(len(at)): columns[i*len(at)+j,index]+=part[i,j]
            transposed=mp.matrix([[columns[j*len(at)+i,h] for h in range(q)] for i in range(len(at)) for j in range(len(at))])
            info+=count*(columns.T*transposed/2+means.T*inv*means)
            blocks.append((g,at,count,inv,columns,means))
    inverse=info**-1; rows=[]
    for label,g in zip(labels,prepared):
        for kind,i,j in candidates(p,k,assignments,markers,cross,paths,residual):
            trial=dict(g,local=g['local']+[(kind,i,j,q)])
            sigma,mu,deriv=model(parameters+[0.],trial,True); _,d,dm=deriv[-1]
            _,gm,gc=observed_loss(mu,sigma,g['patterns'])
            score=float((gm.T*dm)[0]+sum(gc[a,b]*d[b,a] for a in range(p) for b in range(p)))
            crossinfo=mp.zeros(q,1); diagonal=0.
            for block,at,count,inv,columns,means in blocks:
                if block is not g: continue
                part=inv*mp.matrix([[d[a,b] for b in at] for a in at]); mean=mp.matrix([dm[a] for a in at])
                vector=mp.matrix([part[b,a] for a in range(len(at)) for b in range(len(at))])
                crossinfo+=count*(columns.T*vector/2+means.T*inv*mean)
                diagonal+=count*(float(sum(part[a,b]*part[b,a] for a in range(len(at)) for b in range(len(at))))/2+float((mean.T*inv*mean)[0]))
            efficient=diagonal-float((crossinfo.T*inverse*crossinfo)[0])
            if efficient<=1e-8*max(1.,diagonal): continue
            score-=float((crossinfo.T*inverse*gradient)[0])
            rows.append(mi_row(kind,i,j,score**2/efficient,-score/efficient,scales,markers,label if len(labels)>1 else None))
    return sorted(rows,key=lambda row:row['MI'],reverse=True)


def ordinal_mi(estimates,prepared,model,labels,p,k,assignment,markers,cross,paths,residual,jac,w,gamma,sample,implied,n):
    bread=jac.T*w*jac; inverse=bread**-1; rows=[]; q=len(estimates)
    for label,g in zip(labels,prepared):
        for kind,i,j in candidates(p,k,assignment,markers,cross,paths,residual):
            trial=dict(g,local=g['local']+[(kind,i,j,q)])
            values,deriv=model(estimates+[0.],trial,True)
            d=mp.zeros(jac.rows,1)
            for a in range(len(values)): d[g['at']+a]=deriv[a,q]
            # Associate matrix-vector products first. Building the full moment
            # projection repeatedly is needlessly expensive in portable WASM.
            r=d-jac*(inverse*(jac.T*(w*d)))
            curvature=n*float((r.T*w*r)[0]); variance=n*float((r.T*w*gamma*w*r)[0])
            if curvature<=1e-8 or variance<=1e-8: continue
            score=n*float((r.T*w*(implied-sample))[0])
            rows.append(mi_row(kind,i,j,score**2/variance,-score/curvature,[1.]*p,markers,label if len(labels)>1 else None))
    return sorted(rows,key=lambda row:row['MI'],reverse=True)


def effects(parameters,covariance,model,specs,paths,scales):
    if not paths: return []
    sigma,load,total,b=model(parameters); k=b.rows
    pairs=sorted(connected(paths,k)); descriptions=[(source,target,kind) for source,target in pairs for kind in ('Direct effect','Indirect effect','Total effect')]
    def values(x):
        _,_,latent,b=model(x); propagation=(mp.eye(k)-b)**-1-mp.eye(k)
        output=[]
        for source,target,kind in descriptions:
            value=b[target,source] if kind=='Direct effect' else propagation[target,source]-b[target,source] if kind=='Indirect effect' else propagation[target,source]
            output.extend([float(value)*scales[target]/scales[source],float(value*mp.sqrt(latent[source,source]/latent[target,target]))])
        return output
    estimates=values(parameters); active=sorted({index for kind,i,j,index in specs if kind not in ('mean','latentmean','threshold')})
    jac=mp.zeros(len(estimates),len(active))
    if covariance is not None:
        for column,index in enumerate(active):
            step=1e-5*max(1.,abs(parameters[index])); lo=list(parameters); hi=list(parameters); lo[index]-=step; hi[index]+=step
            lower=values(lo); upper=values(hi)
            for row in range(len(estimates)): jac[row,column]=(upper[row]-lower[row])/(2*step)
        projected=jac*mp.matrix([[covariance[i,j] for j in active] for i in active])*jac.T
    rows=[]
    for index,(source,target,kind) in enumerate(descriptions):
        row={'term':str(source+1)+' → '+str(target+1),'Effect':kind,'Estimate':estimates[2*index],'Standardized estimate':estimates[2*index+1]}
        if covariance is not None:
            for offset,prefix in ((0,''),(1,'Standardized ')):
                se=math.sqrt(max(0,float(projected[2*index+offset,2*index+offset]))); estimate=estimates[2*index+offset]
                row[prefix+'SE']=se; row[prefix+'CI95']=[estimate-1.959963984540054*se,estimate+1.959963984540054*se]
        rows.append(row)
    return rows


def residual_rows(parameters,covariance,model,specs,scales):
    from calc_advanced_common import inference
    entries=[(i,j,index) for kind,i,j,index in specs if kind=='residual']
    if not entries: return []
    def correlations(x):
        sigma,load,total,b=model(x); theta=sigma-load*total*load.T
        return [float(theta[i,j]/mp.sqrt(theta[i,i]*theta[j,j])) for i,j,index in entries]
    estimates=correlations(parameters); active=sorted({index for kind,i,j,index in specs if kind in ('error','residual')})
    jac=mp.zeros(len(entries),len(active))
    for column,index in enumerate(active):
        step=1e-5*max(1.,abs(parameters[index])); lo=list(parameters); hi=list(parameters); lo[index]-=step; hi[index]+=step
        left=correlations(lo); right=correlations(hi)
        for row in range(len(entries)): jac[row,column]=(right[row]-left[row])/(2*step)
    projected=jac*mp.matrix([[covariance[i,j] for j in active] for i in active])*jac.T
    rows=[]
    for at,(i,j,index) in enumerate(entries):
        unit=scales[i]*scales[j]
        row=inference([parameters[index]*unit],[[covariance[index,index]*unit**2]],['feature:'+str(i+1)])[0]
        se=math.sqrt(max(0,float(projected[at,at])))
        row.update({'First indicator':'feature:'+str(i+1),'Second indicator':'feature:'+str(j+1),'Correlation':estimates[at],
                    'Standardized SE':se,'Standardized CI95':[estimates[at]-1.959963984540054*se,estimates[at]+1.959963984540054*se],
                    'First indicator position':i+1,'Second indicator position':j+1})
        rows.append(row)
    return rows


def check_normal_identification(parameters,prepared,model):
    """Rank of observed mean/covariance derivatives, without a refit Hessian.

    Bootstrap draws need admissibility and identification, not Wald SEs. The
    Jacobian rank is equivalent to nonsingularity of expected information.
    """
    rows=[];q=len(parameters)
    for g in prepared:
        sigma,mu,deriv=model(parameters,g,True)
        for observed,count,center,second in g['patterns']:
            for i in observed:
                row=[0.]*q
                for index,d,dm in deriv: row[index]+=float(dm[i])/math.sqrt(float(sigma[i,i]))
                rows.append(row)
                for j in observed:
                    if j<i: continue
                    row=[0.]*q
                    for index,d,dm in deriv:
                        if d is not None: row[index]+=float(d[i,j])/math.sqrt(float(sigma[i,i]*sigma[j,j]))
                    rows.append(row)
    jac=mp.matrix(rows);norms=[float(mp.norm(jac[:,j])) for j in range(q)]
    require(all(norms),'Bootstrap model is not identifiable')
    jac=jac*mp.diag([1/v for v in norms]);gram=jac.T*jac
    require(min(mp.eigsy(gram,eigvals_only=True))>1e-9,'Bootstrap model information is singular')


def bootstrap(engine,name,args,result,fit,samples,seed):
    from calc_advanced_social import quantile
    offset=3 if name=='sem' else 2; at=offset+5
    target=result.get('Effects',[])
    require(target,'Bootstrap indirect effects require SEM with at least one latent path')
    ids=args[offset+2] if len(args)>offset+2 and args[offset+2] else [1]*len(args[0])
    grouped={label:[row for row,ident in zip(args[0],ids) if ident==label] for label in sorted(set(ids))}
    rng=random.Random(seed); draws={ (row.get('Group'),row['term'],row['Effect']):[] for row in target }; failed=0
    for _ in range(samples):
        data=[]; groups=[]
        for label,rows in grouped.items():
            selected=[rows[rng.randrange(len(rows))] for _ in rows]; data+=selected; groups+=[label]*len(selected)
        trial=list(args); trial[0]=data
        if len(trial)>offset+2: trial[offset+2]=groups
        try:
            estimates=fit(engine,name,trial,fast=True)['Effects']
            bykey={(row.get('Group'),row['term'],row['Effect']):row for row in estimates}
            require(set(bykey)==set(draws),'Bootstrap fit changed the effect structure')
            require(all(math.isfinite(row['Estimate']) and math.isfinite(row['Standardized estimate']) for row in estimates),'Nonfinite bootstrap effect')
        except (MathError,ValueError,ZeroDivisionError,OverflowError): failed+=1; continue
        for key,values in draws.items(): values.append([bykey[key]['Estimate'],bykey[key]['Standardized estimate']])
    successful=samples-failed; valid=successful>=max(20,math.ceil(.8*samples))
    for row in target:
        values=draws[row.get('Group'),row['term'],row['Effect']]
        for index,prefix in ((0,'Bootstrap '),(1,'Standardized bootstrap ')):
            ordered=sorted(value[index] for value in values)
            row[prefix+'CI95']=[float(quantile(ordered,.025)),float(quantile(ordered,.975))] if valid else None
    result.update({'Bootstrap samples':samples,'Bootstrap successful':successful,'Bootstrap failed':failed,'Bootstrap seed':seed,
                   'Bootstrap method':'Stratified nonparametric row resampling; model refitted for every draw; percentile 95% CI'})
    if not valid: result['Bootstrap warning']='Bootstrap confidence intervals unavailable: fewer than 20 or 80% successful refits. Inspect model stability.'
