"""Development-only NumPy/SciPy references; no application estimator imported."""
import json
from pathlib import Path
import numpy as np
from scipy import stats, optimize, integrate, special
from scipy.linalg import helmert
from statsmodels.stats.multitest import multipletests

ROOT=Path(__file__).resolve().parents[1]
cases=[]


def add(name,args,expected,tolerance=2e-9):
    cases.append(dict(function=name,arguments=args,expected=expected,tolerance=tolerance))


rng=np.random.default_rng(20261015)
for a,b,n in [(4,1,22),(2,1,12),(3,3,24),(2,2,16)]:
    x=rng.normal(size=(n,a*b))*np.linspace(.7,2,a*b)+np.linspace(0,1,a*b)
    x+=rng.normal(size=(n,1))
    transforms={'':helmert(a)} if b==1 else {
        'A ':np.kron(helmert(a),np.ones((1,b))/np.sqrt(b)),
        'B ':np.kron(np.ones((1,a))/np.sqrt(a),helmert(b)),
        'AB ':np.kron(helmert(a),helmert(b))}
    expected=[]
    for prefix,c in transforms.items():
        y=x@c.T; d=len(c); covariance=np.atleast_2d(np.cov(y,rowvar=False)); eigen=np.linalg.eigvalsh(covariance)
        f=n*np.sum(y.mean(axis=0)**2)/np.trace(covariance)
        gg=np.sum(eigen)**2/(d*np.sum(eigen**2)); hf=min(1.,(n*d*gg-2)/(d*(n-1-d*gg))) if d>1 else 1.
        expected.extend([([prefix+'F'],float(f)),([prefix+'GG epsilon'],float(gg)),([prefix+'HF epsilon'],float(hf))])
        for kind,eps in [('GG',gg),('HF',hf)]:
            expected.extend([([prefix+kind+' df1'],float(d*eps)),([prefix+kind+' df2'],float((n-1)*d*eps)),
                             ([prefix+kind+' p'],float(stats.f.sf(f,d*eps,(n-1)*d*eps)))])
        if d>1:
            logw=np.log(eigen).sum()-d*np.log(eigen.mean()); chi2=-(n-1-(2*d*d+d+2)/(6*d))*logw; df=d*(d+1)/2-1
            expected.extend([([prefix+'Mauchly W'],float(np.exp(logw))),([prefix+'Mauchly chi2'],float(chi2)),
                             ([prefix+'Mauchly df'],df),([prefix+'Mauchly p'],float(stats.chi2.sf(chi2,df)))])
    add('repeatedanova',[x.tolist(),b],expected)

for sizes,control in [([5,7,6],0),([6,4,5,7],2),([2,80,120],0),([3,5],1)]:
    groups=[np.round(rng.normal(i*.45,1.2,n),1) for i,n in enumerate(sizes)]
    k=len(groups); n=sum(sizes); df=n-k; means=[g.mean() for g in groups]
    pooled=sum(np.sum((g-g.mean())**2) for g in groups)/df
    for method in ('scheffe','dunnett','conover'):
        pairs=[(i,control) for i in range(k) if i!=control] if method=='dunnett' else [(i,j) for i in range(k) for j in range(i+1,k)]
        args=[[g.tolist() for g in groups]]; expected=[]
        if method=='dunnett':
            args.append(control+1); others=[i for i in range(k) if i!=control]
            correlation=np.empty((k-1,k-1))
            for i,left in enumerate(others):
                for j,right in enumerate(others):
                    correlation[i,j]=1. if i==j else (1/sizes[control])/np.sqrt((1/sizes[left]+1/sizes[control])*(1/sizes[right]+1/sizes[control]))
            def survival(q):
                return 1-stats.multivariate_t.cdf(np.full(k-1,q),shape=correlation,df=df,
                    lower_limit=np.full(k-1,-q),maxpts=2000000,random_state=np.random.default_rng(73))
            critical=optimize.brentq(lambda q:survival(q)-.05,1.,10.,xtol=1e-7)
        elif method=='scheffe': critical=np.sqrt((k-1)*stats.f.isf(.05,k-1,df))
        else:
            ranks=stats.rankdata(np.concatenate(groups)); split=np.split(ranks,np.cumsum(sizes)[:-1]); rankmeans=[v.mean() for v in split]
            s2=np.var(ranks,ddof=1); h=stats.kruskal(*groups).statistic; residual=s2*(n-1-h)/df
            raw=[]
        for at,(i,j) in enumerate(pairs):
            base=['Comparisons',at]
            if method=='conover':
                se=np.sqrt(residual*(1/sizes[i]+1/sizes[j])); t=(rankmeans[i]-rankmeans[j])/se; p=2*stats.t.sf(abs(t),df);raw.append(p)
                expected.extend([(base+['SE'],float(se)),(base+['t'],float(t)),(base+['Raw p value'],float(p))])
            else:
                delta=means[i]-means[j];se=np.sqrt(pooled*(1/sizes[i]+1/sizes[j]));t=delta/se
                p=survival(abs(t)) if method=='dunnett' else stats.f.sf(t*t/(k-1),k-1,df)
                expected.extend([(base+['t'],float(t)),(base+['Adjusted p value'],float(p)),
                                 (base+['Lower 95% CI'],float(delta-critical*se)),(base+['Upper 95% CI'],float(delta+critical*se))])
        if method=='conover':
            expected.extend([(['Comparisons',i,'Adjusted p value'],float(p)) for i,p in enumerate(multipletests(raw,method='holm')[1])])
        add(method,args,expected,2e-5 if method=='dunnett' else 2e-9)

report_rows=np.array([[2,4,5],[3,4,7],[4,7,8],[2,3,6],[5,6,7]])
report_contrasts=[report_rows[:,:i].sum(axis=1)-i*report_rows[:,i] for i in range(1,report_rows.shape[1])]
report_pairs=[]; report_raw=[]
for i in range(report_rows.shape[1]):
    for j in range(i+1,report_rows.shape[1]):
        difference=report_rows[:,i]-report_rows[:,j]; test=stats.ttest_rel(report_rows[:,i],report_rows[:,j]); ci=test.confidence_interval()
        report_pairs.append({'difference':float(difference.mean()),'SE':float(stats.sem(difference)),'n':len(difference),
                             'df':int(test.df),'t':float(test.statistic),'raw_p':float(test.pvalue),'lower':float(ci.low),'upper':float(ci.high)})
        report_raw.append(test.pvalue)
for row,p in zip(report_pairs,multipletests(report_raw,method='holm')[1]): row['holm_p']=float(p)
repeated_report={'rows':report_rows.tolist(),'conditions':[{'mean':float(c.mean()),'sd':float(c.std(ddof=1))} for c in report_rows.T],
                 'contrasts':[{'W':float(stats.shapiro(c).statistic),'p':float(stats.shapiro(c).pvalue)} for c in report_contrasts],
                 'pairs':report_pairs}
shapiro_cases=[]
for values in ([1,2,4],[1,2,4,7],[2,4,1,6,9],[2,4,1,6,9,3],
               [2,4,1,6,9,3,5,8,12,15,7],[2,4,1,6,9,3,5,8,12,15,7,11],list(range(30))):
    test=stats.shapiro(values)
    shapiro_cases.append({'values':values,'W':float(test.statistic),'p':float(test.pvalue)})
test=stats.shapiro(np.arange(5000,dtype=float))
shapiro_cases.append({'range_count':5000,'W':float(test.statistic),'p':float(test.pvalue)})
regression_x=np.arange(1,7,dtype=float); regression_y=np.array([2,4,5,4,5,7],dtype=float)
regression_residual=regression_y-np.polyval(np.polyfit(regression_x,regression_y,1),regression_x)
regression_normality={'rows':np.column_stack([regression_x,regression_y]).tolist(),'p':float(stats.shapiro(regression_residual).pvalue)}

tails=[]
for sizes,q in [([2,2,2],20.),([2,2,2],1000.),([4,4,4],100.),([4,4,4],1000.)]:
    df=sum(sizes)-len(sizes)
    def integrand(u):
        def conditional(z):
            outside=special.ndtr(z-u*np.sqrt(2))+special.ndtr(-z-u*np.sqrt(2))
            return (2*outside-outside**2)*stats.norm.pdf(z)
        return integrate.quad(conditional,-10,10,epsabs=1e-15)[0]*stats.chi.pdf(u/q*np.sqrt(df),df)*np.sqrt(df)/q
    probability=integrate.quad(integrand,0,np.sqrt(df)+14,epsabs=1e-100,epsrel=1e-9)[0]
    tails.append(dict(sizes=sizes,statistic=q,probability=float(probability)))

target=ROOT/'tests/fixtures/sphericity_posthoc_reference.json'
target.write_text(json.dumps({'sources':['NumPy orthonormal one-/two-factor projections and covariance eigenvalues; first-order Mauchly chi-square approximation',
    'SciPy multivariate t CDF (2 million integration points, fixed seed) and root finding for Dunnett',
    'SciPy F inverse/survival for Scheffe; SciPy pooled ranks/Kruskal H/t tails and statsmodels Holm for Conover-Iman'],
    'cases':cases,'dunnett_tails':tails,'repeated_report':repeated_report,'shapiro_cases':shapiro_cases,
    'regression_normality':regression_normality},ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf8')
print('Wrote',len(cases),'independent sphericity/post-hoc cases')
