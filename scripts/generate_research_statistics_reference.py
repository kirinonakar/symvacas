"""Regenerate independent research references (SciPy/statsmodels/Pingouin).

Optional packages are used only here, never by the portable runtime or tests.
For isolated installs pass --reference-libs build/research-reference.
"""
import argparse
import json
from pathlib import Path
import sys

parser=argparse.ArgumentParser()
parser.add_argument('--reference-libs')
args=parser.parse_args()
if args.reference_libs: sys.path.insert(0,str(Path(args.reference_libs).resolve()))
import numpy as np
import pandas as pd
import scipy
from scipy import stats
import statsmodels
from statsmodels.stats.meta_analysis import combine_effects
from statsmodels.stats.weightstats import ttost_ind,ttost_paired
import pingouin as pg

ROOT=Path(__file__).resolve().parents[1]
cases=[]
def add(name,arguments,expected,tolerance=1e-9):
    cases.append(dict(function=name,arguments=arguments,expected=[[list(path),float(value)] for path,value in expected],tolerance=tolerance))

meta=[[.2,.1],[.45,.15],[-.1,.12],[.6,.2],[.3,.11]]
y,se=np.asarray(meta).T
for method,external in [('fixed','iterated'),('dl','chi2'),('pm','iterated')]:
    reference=combine_effects(y,se**2,method_re=external,atol=1e-12,maxiter=1000)
    fixed=method=='fixed'; estimate=reference.mean_effect_fe if fixed else reference.mean_effect_re
    variance=reference.var_eff_w_fe if fixed else reference.var_eff_w_re
    expected=[(('estimate',),estimate),(('SE',),np.sqrt(variance)),(('Q',),reference.q),
              (('I² (%)',),max(0,reference.i2)*100),(('τ²',),0 if fixed else reference.tau2),
              (('confidence interval',0),estimate-stats.norm.ppf(.975)*np.sqrt(variance)),
              (('confidence interval',1),estimate+stats.norm.ppf(.975)*np.sqrt(variance))]
    add('metaanalysis',[meta,method,.95,'z',1],expected)
    if not fixed:
        modified_se=np.sqrt(max(reference.var_eff_w_re,reference.var_hksj_re))
        radius=stats.t.ppf(.975,len(y)-1)*modified_se
        add('metaanalysis',[meta,method,.95,'hksj',1],[(('SE',),modified_se),(('confidence interval',0),estimate-radius),(('confidence interval',1),estimate+radius)])
# Egger is an independent statsmodels OLS, including intercept uncertainty.
import statsmodels.api as sm
egger=sm.OLS(y/se,sm.add_constant(1/se)).fit()
add('metaanalysis',[meta,'pm',.95,'hksj',1],[(('Egger test','Intercept'),egger.params[0]),(('Egger test','SE'),egger.bse[0]),(('Egger test','p'),egger.pvalues[0])])

icc=[[9,2,5,8],[6,1,3,2],[8,4,6,8],[7,1,2,6],[10,5,6,9],[6,2,4,7]]
data=pd.DataFrame([(i,j,value) for i,row in enumerate(icc) for j,value in enumerate(row)],columns=['subject','rater','score'])
# Disable output rounding so the reference retains numerical CI precision.
pg.options['round.column.CI95%']=None
reference=pg.intraclass_corr(data=data,targets='subject',raters='rater',ratings='score')
for model,base in [('oneway','ICC1'),('random','ICC2'),('mixed','ICC3')]:
    for unit,suffix in [('single',''),('average','k')]:
        row=reference[reference.Type==base+suffix].iloc[0]
        add('icc',[icc,model,unit,.95],[(('ICC',),row.ICC),(('F',),row.F),(('p',),row.pval)])
        add('icc',[icc,model,unit,.95],[(('confidence interval',0),row['CI95%'][0]),(('confidence interval',1),row['CI95%'][1])])

a=np.array([9.8,10.1,10.2,9.9,10,10.1,9.9,10.2]); b=np.array([10,10.2,10.1,9.8,10.1,10,9.9,10.1])
for method,var in [('welch','unequal'),('student','pooled')]:
    p,lower,upper=ttost_ind(a,b,-.5,.5,usevar=var)
    add('tost2',[a.tolist(),b.tolist(),-.5,.5,method,.05],[(('TOST p',),p),(('Lower t',),lower[0]),(('Lower p',),lower[1]),(('Upper t',),upper[0]),(('Upper p',),upper[1]),(('df',),lower[2])])
p,lower,upper=ttost_paired(a,b,-.5,.5)
add('tostpaired',[a.tolist(),b.tolist(),-.5,.5,.05],[(('TOST p',),p),(('Lower t',),lower[0]),(('Lower p',),lower[1]),(('Upper t',),upper[0]),(('Upper p',),upper[1])])
lower=stats.ttest_1samp(a,9.5,alternative='greater'); upper=stats.ttest_1samp(a,10.5,alternative='less')
ci=stats.t.interval(.90,len(a)-1,loc=np.mean(a)-10,scale=stats.sem(a))
add('tost',[a.tolist(),-.5,.5,10,.05],[(('Lower t',),lower.statistic),(('Lower p',),lower.pvalue),(('Upper t',),upper.statistic),(('Upper p',),upper.pvalue),(('confidence interval',0),ci[0]),(('confidence interval',1),ci[1])])

measure=np.array([[10,10.5],[12,11.8],[8,8.6],[15,14.7],[11,11.3],[9,9.1]])
for mode in ('difference','log'):
    differences=np.diff(np.log(measure) if mode=='log' else measure,axis=1).ravel()*-1
    center=np.mean(differences); sd=np.std(differences,ddof=1); ci=stats.t.interval(.95,len(measure)-1,loc=center,scale=stats.sem(differences))
    add('blandaltman',[measure.tolist(),.95,mode],[(('Bias',),center),(('SD of differences',),sd),(('Lower agreement limit',),center-stats.norm.ppf(.975)*sd),(('Upper agreement limit',),center+stats.norm.ppf(.975)*sd),(('Bias CI',0),ci[0]),(('Bias CI',1),ci[1])])

output=dict(sources=['statsmodels.stats.meta_analysis.combine_effects','statsmodels.OLS','statsmodels.stats.weightstats.ttost_ind/ttost_paired','pingouin.intraclass_corr','scipy.stats'],
            versions=dict(scipy=scipy.__version__,statsmodels=statsmodels.__version__,pingouin=pg.__version__),cases=cases)
(ROOT/'tests/fixtures/research_statistics_reference.json').write_text(json.dumps(output,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
print(f'Wrote {len(cases)} independent reference cases')
