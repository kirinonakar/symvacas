"""Trimmed-mean inference, Winsorized association and Huber M regression."""
import math
import statistics
import mpmath as mp
from calc_shared import require, MathError
from calc_advanced_common import vector, table, number, mean, variance, dot, inverse, inference
from calc_advanced_linear import least_squares
from calc_advanced_research import critical, level_option
from calc_statistics import _t_sf, _f_sf


def trim_summary(data, trim):
    values=sorted(vector(data,2)); n=len(values); g=int(n*trim); h=n-2*g
    require(h>=2,'At least two observations must remain after trimming')
    winsor=[values[g]]*g+values[g:n-g]+[values[n-g-1]]*g
    v=variance(winsor); d=(n-1)*v/(h*(h-1))
    require(d>0,'Winsorized variance must be positive')
    return mean(values[g:n-g]),d,h,winsor


def calculate(engine,name,a):
    if name=='robustreg': return robust_regression(engine,a)
    trim=number(a[2] if name in ('yuen','winsorcor') and len(a)>2 else a[1] if name=='trimmedanova' and len(a)>1 else .2)
    require(0<=trim<.5,'Trimming proportion per tail must be in [0, .5)')
    level=level_option(a,3 if name in ('yuen','winsorcor') else 2)
    assumptions='Independent observations; trim floor(n × proportion) values from each tail. Yuen/Welch trimmed-mean inference uses Winsorized variances and approximate degrees of freedom. The estimand is a trimmed population mean, not the ordinary mean.'
    if name=='winsorcor':
        x=vector(a[0],4); y=vector(a[1],4); require(len(x)==len(y),'Correlation requires complete paired rows')
        wx=trim_summary(x,trim)[3]; wy=trim_summary(y,trim)[3]; n=len(x); g=int(n*trim)
        mx,my=mean(wx),mean(wy)
        ssx=sum((v-mx)**2 for v in wx); ssy=sum((v-my)**2 for v in wy)
        # Restore original pair order; independently sorting the two margins would destroy association.
        lo_x,hi_x=wx[0],wx[-1];lo_y,hi_y=wy[0],wy[-1]
        wx=[min(hi_x,max(lo_x,v)) for v in x];wy=[min(hi_y,max(lo_y,v)) for v in y]
        r=max(-1.,min(1.,sum((v-mx)*(w-my) for v,w in zip(wx,wy))/math.sqrt(ssx*ssy)))
        df=n-2*g-2; require(df>0,'More paired rows are required after Winsorization')
        t=r*math.sqrt((n-2)/(1-r*r)) if abs(r)<1 else math.copysign(math.inf,r)
        engine.statistics_plots=[{'kind':'research-scatter','title':'Winsorized pairs','points':list(map(list,zip(wx,wy))),'xlabel':'Winsorized A','ylabel':'Winsorized B'}]
        return {'n':n,'Winsorized correlation':r,'Trim per tail':trim,'t':t,'df':df,'p':float(2*_t_sf(abs(t),df)),
                'Assumptions':'Independent complete paired rows. Each marginal tail is Winsorized separately while preserving pairs. Approximate t test uses n−2 floor(n trim)−2 df (WRS2 convention); not a Pearson normal-theory CI. No interval is supplied.'}
    if name=='yuen':
        first=trim_summary(a[0],trim); second=trim_summary(a[1],trim); m1,d1,h1,_=first; m2,d2,h2,_=second
        se=math.sqrt(d1+d2);df=(d1+d2)**2/(d1*d1/(h1-1)+d2*d2/(h2-1));delta=m1-m2;t=delta/se; radius=critical((1-level)/2,df)*se
        engine.statistics_plots=[{'kind':'intervals','title':'Trimmed mean difference','rows':[['A − B',delta,delta-radius,delta+radius]],'reference':0}]
        return {'Trimmed mean A':m1,'Trimmed mean B':m2,'Retained A':h1,'Retained B':h2,'Trim per tail':trim,
                'estimate':delta,'SE':se,'t':t,'df':df,'p':float(2*_t_sf(abs(t),df)),'confidence level':level,'confidence interval':[delta-radius,delta+radius],'Assumptions':assumptions}
    require(name=='trimmedanova','Unknown robust analysis')
    require(isinstance(a[0],(list,tuple)) and len(a[0])>=2,'Enter at least two independent groups')
    groups=[trim_summary(v,trim) for v in a[0]];k=len(groups); weights=[1/g[1] for g in groups];total=sum(weights)
    center=sum(w*g[0] for w,g in zip(weights,groups))/total
    b=sum((1-w/total)**2/(g[2]-1) for w,g in zip(weights,groups))
    statistic=sum(w*(g[0]-center)**2 for w,g in zip(weights,groups))/(k-1)/(1+2*(k-2)*b/(k*k-1));df2=(k*k-1)/(3*b)
    cutoff=[critical((1-level)/2,g[2]-1)*math.sqrt(g[1]) for g in groups]
    engine.statistics_plots=[{'kind':'intervals','title':'Trimmed means','rows':[[str(i+1),g[0],g[0]-c,g[0]+c] for i,(g,c) in enumerate(zip(groups,cutoff))]}]
    return {'F':statistic,'df1':k-1,'df2':df2,'p':float(_f_sf(statistic,k-1,df2)),'Trim per tail':trim,
            'Groups':[{'Group':i+1,'Trimmed mean':g[0],'Retained n':g[2],'SE':math.sqrt(g[1])} for i,g in enumerate(groups)],'Assumptions':assumptions+' Plotted intervals are individual, not simultaneous; no post-hoc adjustment.'}


def robust_regression(engine,a):
    rows=table(a[0],4,2);n=len(rows);p=len(rows[0]); y=[r[-1] for r in rows]
    c=number(a[1]) if len(a)>1 else 1.345;require(c>0,'Huber tuning constant must be positive')
    centers=[mean(col) for col in zip(*rows)]; scales=[math.sqrt(variance(col)) for col in zip(*rows)]
    require(all(v>0 for v in scales),'Selected regression columns must vary')
    design=[[1.]+[(r[j]-centers[j])/scales[j] for j in range(p-1)] for r in rows]
    target=[(v-centers[-1])/scales[-1] for v in y]; beta=least_squares(design,target)[0]
    for iteration in range(200):
        residual=[v-dot(row,beta) for row,v in zip(design,target)]
        scale=statistics.median(abs(v-statistics.median(residual)) for v in residual)/.6744897501960817
        require(scale>1e-12,'Residual MAD is zero; robust regression inference is unavailable')
        u=[v/scale for v in residual];weights=[min(1.,c/abs(v)) if v else 1. for v in u]
        updated=least_squares(design,target,weights)[0]
        if max(abs(v-w) for v,w in zip(beta,updated))<1e-8:
            beta=updated;break
        beta=updated
    else: raise MathError('Huber M regression did not converge')
    residual=[v-dot(row,beta) for row,v in zip(design,target)];u=[v/scale for v in residual]
    psi=[max(-c,min(c,v)) for v in u];derivative=[1. if abs(v)<c else 0. for v in u]
    bread=mp.matrix([[sum(d*row[i]*row[j] for row,d in zip(design,derivative)) for j in range(p)] for i in range(p)])
    meat=mp.matrix([[sum(v*v*row[i]*row[j] for row,v in zip(design,psi)) for j in range(p)] for i in range(p)])
    inv=inverse(bread);cov=inv*meat*inv*(scale*scale*n/(n-p))
    transform=mp.zeros(p);transform[0,0]=scales[-1]
    for j in range(1,p): transform[j,j]=scales[-1]/scales[j-1];transform[0,j]=-centers[j-1]*transform[j,j]
    original=list(map(float,transform*mp.matrix(beta)));original[0]+=centers[-1];cov=transform*cov*transform.T
    coefficients=inference(original,cov,['Intercept']+['feature:'+str(j) for j in range(1,p)])
    fitted=[dot([1.]+r[:-1],original) for r in rows]
    engine.statistics_plots=[{'kind':'research-scatter','title':'Huber regression residuals','points':[[f,v-f] for f,v in zip(fitted,y)],'horizontal':[0],'xlabel':'Fitted','ylabel':'Residual'}]
    return {'n':n,'Estimator':'Huber M (IRLS, iterated residual MAD)','Tuning constant':c,'Iterations':iteration+1,'Residual scale':scale*scales[-1],
            'coefficients':coefficients,'Assumptions':'Independent rows, numeric predictors and response; intercept included. Huber M reduces response-outlier influence but does not protect against high-leverage predictors. This is not a high-breakdown MM estimator. HC1 score-sandwich asymptotic Wald inference treats the estimated MAD scale as fixed; small-sample and scale-estimation uncertainty are not fully covered.'}
