"""Presentation-only companion analyses on the exact samples used by a test.

Keep the primary value/Ans unchanged. Diagnostics never choose a different test.
"""
import math
import statistics
import mpmath as mp
from types import SimpleNamespace
import sympy as s
from calc_shared import MathError, flatten
from calc_statistics import _shapiro_wilk, _tail_argument, statistical_test
from calc_statistics_report import statistics_report
from calc_advanced_inference import calculate as grouped_test
from calc_posthoc import posthoc_comparisons, holm_comparisons, dunn_comparisons
from calc_effect_interpretation import contingency_effects


def normal_views(values, label):
    try: ordered = sorted(float(v) for v in values)
    except (TypeError,ValueError,OverflowError): return None
    if not ordered or not all(math.isfinite(v) for v in ordered):
        return None
    n = len(ordered)
    # Thin only the plotted points, retaining the full sample for all statistics.
    indices = sorted({round(i*(n-1)/min(n-1,199)) for i in range(min(n,200))}) if n>1 else [0]
    normal = statistics.NormalDist()
    points = [[normal.inv_cdf((i+.5)/n), ordered[i]] for i in indices]
    def quantile(p):
        at=(n-1)*p; lo=int(at); hi=min(n-1,lo+1)
        return ordered[lo]+(ordered[hi]-ordered[lo])*(at-lo)
    slope=(quantile(.75)-quantile(.25))/(normal.inv_cdf(.75)-normal.inv_cdf(.25))
    center=quantile(.25)-slope*normal.inv_cdf(.25)
    reference=[[points[0][0],center+slope*points[0][0]], [points[-1][0],center+slope*points[-1][0]]]
    lo,hi=ordered[0],ordered[-1]
    if lo==hi: lo-=.5; hi+=.5
    bins=min(30,max(5,math.ceil(math.sqrt(n))))
    width=(hi-lo)/bins
    if not math.isfinite(width) or width<=0: return None
    counts=[0]*bins
    for value in ordered: counts[min(bins-1,max(0,int((value-lo)/width)))]+=1
    return ({'label':label,'points':points,'referenceLine':reference,'n':n},
            {'label':label,'edges':[lo+i*width for i in range(bins+1)],'counts':counts,'n':n})


def sample_summary(sample,label,heading='Sample'):
    try:
        data=[float(v) for v in sample]
        if data and all(math.isfinite(v) for v in data):
            return {heading:label,'n':len(data),'Mean':statistics.mean(data),'SD':statistics.stdev(data) if len(data)>1 else None,
                    'Median':statistics.median(data),'Minimum':min(data),'Maximum':max(data)}
    except (TypeError,ValueError,OverflowError):
        pass
    return {heading:label,'n':len(sample),'status':'Summary exceeds plotting numeric range'}


def companion_report(report, name, value, inputs, precision, labels=None, residuals=None):
    if isinstance(value, dict) and 'Column comparisons' in value: return report
    if name in ('ttest2', 'ttestpaired') and isinstance(value, dict) and 'Comparisons' in value:
        return report
    labels=labels or {}
    proxy=SimpleNamespace(precision=precision,note='',request={'statisticsTermLabels':labels})
    args=inputs[1] if inputs and inputs[0]==name else []
    nodes=inputs[2] if inputs and inputs[0]==name else []
    if name in ('ttest','ttest2','ttestpaired','ztest','ztest2','tinterval','zinterval','anova','welchanova','tukey','gameshowell','shapiro','wilcoxon','mannwhitney','kruskal'):
        args=_tail_argument(args,nodes)[1]
    samples=[]; notes=[]; extras=[]; diagnostics=[]; condition_summary=[]
    normality=False; variance=False
    if name in ('propztest','propztest2'):
        notes.append('Proportion z tests assume independent binary observations and use a normal approximation without continuity correction. Expected successes and failures are checked under the null hypothesis.')
        if name=='propztest2':
            notes.append('The two-sample test uses the pooled proportion under H0: pA = pB. The alternative refers to A − B; paired binary outcomes require McNemar.')
        if any(row['Status']=='Small expected counts (< 10)' for row in value['Normal approximation checks']):
            notes.append('Expected successes or failures are below 10; the normal approximation may be inaccurate. Consider an exact binomial test for one sample or Fisher exact for two independent samples.')
    if name in ('ttest','tinterval'):
        if len(args)==2 and isinstance(args[1],(list,tuple)): samples=[flatten(args[1])]
        normality=True
    elif name in ('ttest2','ttestpaired') and len(args)>=3:
        samples=[flatten(args[1]),flatten(args[2])]
        if name=='ttestpaired':
            samples=[[x-y for x,y in zip(*samples)]]
            labels={'sample:1':labels['sample:1']+' − '+labels['sample:2'] if labels.get('sample:1') and labels.get('sample:2') else 'Paired differences (A − B)'}
            notes.append('Paired analysis checks the differences, not the two raw samples. Pairing and independence between subjects must come from the study design.')
        else:
            variance=True
            if len(args)>3 and str(args[3])=='student': report['title']='Student t test'
            notes.append('Student pooled t test requires equal variances. Review the variance check and Q–Q plots; the primary method is not switched automatically.' if len(args)>3 and str(args[3])=='student' else 'Welch t test does not assume equal variances. The variance check is descriptive and does not switch the primary test.')
        normality=True
        try:
            effect=grouped_test(proxy,'cohend',[args[1],args[2],s.Symbol('paired' if name=='ttestpaired' else 'independent')])
            extras.append(('Effect size',effect))
        except (MathError,ValueError,ZeroDivisionError,OverflowError) as error:
            extras.append(('Effect size',{'status':'unavailable','reason':str(error)}))
    elif name in ('anova','welchanova','tukey','gameshowell','scheffe','dunnett','levene','bartlett','eta2'):
        samples=[flatten(group) for group in (args[0] if name in ('scheffe','dunnett') else args) if isinstance(group,(list,tuple))]
        normality=name in ('anova','welchanova','tukey','gameshowell','scheffe','dunnett','bartlett')
        variance=name in ('anova','welchanova','tukey','gameshowell','scheffe','dunnett')
        if name in ('anova','welchanova','tukey','gameshowell','scheffe','dunnett'):
            extras.append(('Effect size',grouped_test(proxy,'eta2',samples)))
            if name in ('tukey','scheffe','dunnett'): extras.append(('Overall ANOVA',statistical_test(proxy,'anova',samples,[])))
            if name=='gameshowell':extras.append(('Overall Welch ANOVA',statistical_test(proxy,'welchanova',samples,[])))
            if name in ('anova','welchanova','tukey'):
                method='gameshowell' if name=='welchanova' else 'tukey'
                try: extras.append(('Games–Howell post-hoc' if method=='gameshowell' else 'Tukey–Kramer post-hoc',posthoc_comparisons(samples,method,proxy)))
                except (MathError,ValueError,ZeroDivisionError,OverflowError) as error:extras.append(('Post-hoc comparisons',{'status':'unavailable','reason':str(error)}))
            if name in ('welchanova','gameshowell'):
                notes.append('Welch ANOVA and Games–Howell do not require equal variances. The variance check is descriptive. η² is a descriptive sums-of-squares effect size, not derived from the Welch F statistic.')
            notes.append('Post-hoc comparisons use 95% simultaneous intervals. Scheffé protects all linear contrasts; Dunnett protects the selected treatment-minus-control family; Tukey/Games–Howell use studentized-range adjusted p values. Review all comparisons together; the global test and individual pairs answer different questions.')
    elif name in ('dunn','conover') and args:
        samples=[flatten(group) for group in args[0]]
        extras.append(('Overall Kruskal–Wallis',statistical_test(proxy,'kruskal',samples,[])))
        notes.append('Rank comparisons use pooled midranks across all selected groups. A location interpretation requires similar distribution shapes. Conover–Iman is a post-hoc procedure following a significant Kruskal–Wallis test.')
    elif name in ('shapiro','normaltest') and args:
        samples=[flatten(args[0])]
        if name=='normaltest':
            notes.append('D’Agostino–Pearson combines skewness and kurtosis z scores into K². The p value uses a chi-square approximation with 2 degrees of freedom; a large p value does not prove normality. Review the Q–Q plot and study design.')
            if len(samples[0])<=20:
                report.setdefault('warnings',[]).append({'text':'For n ≤ 20, the kurtosis approximation in D’Agostino–Pearson may be inaccurate.'})
    elif name=='wilcoxon' and args:
        samples=[[x-y for x,y in zip(args[0],args[1])]] if len(args)==2 else [flatten(args[0])]
        labels={'sample:1':labels['sample:1']+' − '+labels['sample:2'] if len(args)==2 and labels.get('sample:1') and labels.get('sample:2') else labels.get('sample:1','Paired differences (A − B)')}
        notes.append('Wilcoxon signed-rank assumes symmetric differences for a location interpretation; normality is not required. Inspect the distribution and Q–Q plot for shape and outliers.')
    elif name in ('mannwhitney','kruskal','kstest'):
        samples=[flatten(group) for group in args if isinstance(group,(list,tuple))]
        if name in ('mannwhitney','kruskal'): notes.append('Rank tests compare distributions. A location or median interpretation requires comparable distribution shapes; independent observations are still required.')
        if name=='kruskal' and len(samples)>2:
            extras.append(('Dunn post-hoc (Holm)',dunn_comparisons(samples,proxy)))
            notes.append('Dunn comparisons retain the pooled ranks and tie-corrected variance of the Kruskal–Wallis sample, with two-sided normal p values and Holm adjustment over all pairs. Interpret distributions and the study design, not just medians.')
    elif name in ('repeatedanova','friedman') and args:
        conditions=[list(column) for column in zip(*args[0])]
        condition_labels={i:labels.get('feature:'+str(i+1),'Condition '+str(i+1)) for i in range(len(conditions))}
        condition_summary=[sample_summary(sample,condition_labels[i],'Condition') for i,sample in enumerate(conditions)]
        proxy.request={'statisticsTermLabels':{'sample:'+str(i+1):label for i,label in condition_labels.items()}}
        if len(conditions)>2:
            method='ttestpaired' if name=='repeatedanova' else 'wilcoxon'
            extras.append(('Paired t post-hoc (Holm)' if method=='ttestpaired' else 'Wilcoxon post-hoc (Holm)',holm_comparisons(conditions,method,proxy)))
            notes.append('Repeated-condition post-hoc comparisons preserve subject matching and adjust all pairwise p values with Holm. Paired t comparisons assume normal differences; Wilcoxon comparisons assume symmetric differences for a location interpretation. The global and pairwise tests answer different questions.')
            if name=='repeatedanova':
                notes.append('Paired t mean differences are first condition minus second condition. The 95% confidence intervals are pointwise (unadjusted); Holm adjusts p values only.')
        if name=='repeatedanova':
            samples=[[sum(float(conditions[j][row]) for j in range(i))-i*float(conditions[i][row]) for row in range(len(conditions[0]))] for i in range(1,len(conditions))]
            labels={'sample:'+str(i):'Within-subject contrast '+str(i) for i in range(1,len(conditions))}
            normality=True
            notes.append('Repeated-measures normality checks use within-subject Helmert contrasts across independent subjects. Review the contrast Q–Q plots, Mauchly sphericity test and Greenhouse–Geisser / Huynh–Feldt corrected p values. A nonsignificant Mauchly test does not establish sphericity.')
    elif name in ('ancova','twowayanova','linearmodel') and residuals:
        samples=residuals['groups']; normality=True; variance=True
        labels={'sample:'+str(i+1):label for i,label in enumerate(residuals['labels'])}
        notes.append('Two-way ANOVA diagnostics use model residuals within factor cells. Review interaction, independence and equal residual variance.' if name in ('twowayanova','linearmodel') else 'ANCOVA diagnostics use fitted-model residuals. Review the slope homogeneity test as well as linearity, independence and influential observations.')
    elif name in ('ztest','zinterval') and len(args)==3:
        samples=[flatten(args[2])]; normality=True
        notes.append('A z analysis requires a known population standard deviation. A sample SD estimate does not satisfy this requirement.')
    elif name=='ztest2' and len(args)==5:
        samples=[flatten(args[3]),flatten(args[4])]; normality=True
        notes.append('A two-sample z test requires known population standard deviations; equal variances are not required.')

    if normality and not samples:
        diagnostics.append(['Shapiro–Wilk','Raw data','unavailable','unavailable','unavailable','Enter raw observations for normality checks.'])
    qq=[]; distributions=[]; summary=[]
    for i,sample in enumerate(samples):
        label=labels.get('sample:'+str(i+1), 'Sample '+str(i+1))
        summary.append(sample_summary(sample,label))
        views=normal_views(sample,label)
        if views: qq.append(views[0]); distributions.append(views[1])
        if normality:
            try:
                w,p,n=_shapiro_wilk(sample)
                status='Evidence against normality' if p<.05 else 'Normality not rejected'
                diagnostics.append(['Shapiro–Wilk',label,w,p,n,status])
            except (MathError,ValueError,ZeroDivisionError,OverflowError) as error:
                diagnostics.append(['Shapiro–Wilk',label,'unavailable','unavailable',len(sample),str(error)])
    if variance and len(samples)>1:
        try:
            result=grouped_test(proxy,'levene',samples)
            diagnostics.append(['Brown–Forsythe','Across samples',result['F'],result['p'],sum(map(len,samples)),'Evidence against equal variances' if result['p']<.05 else 'Equal variances not rejected'])
        except (MathError,ValueError,ZeroDivisionError,OverflowError) as error:
            diagnostics.append(['Brown–Forsythe','Across samples','unavailable','unavailable',sum(map(len,samples)),str(error)])
    if diagnostics:
        notes.append('Assumption checks use α = 0.05. Review the p values with Q–Q plots, sample sizes and study design.')
    if name=='ttest' and samples and isinstance(value,dict):
        sd=float(value['sample SD'])
        if sd>0: extras.append(('Effect size',{'Cohen d (one sample)':(float(value['sample mean'])-float(args[0]))/sd}))
    if name in ('ttest','ttest2','ttestpaired') and samples and isinstance(value,dict):
        from calc_statistics import _quantile, _t_cdf
        center=value.get('mean difference',value.get('sample mean'))
        if name=='ttest2':
            nx,ny=len(args[1]),len(args[2]);vx=statistics.variance(list(map(float,args[1])));vy=statistics.variance(list(map(float,args[2])))
            se=math.sqrt(((nx-1)*vx+(ny-1)*vy)/(nx+ny-2)*(1/nx+1/ny) if len(args)>3 and str(args[3])=='student' else vx/nx+vy/ny)
        else: se=statistics.stdev(list(map(float,samples[0])))/math.sqrt(len(samples[0]))
        with mp.workdps(precision+10):
            critical=float(_quantile(lambda t:_t_cdf(t,mp.mpf(str(value['df']))),s.Rational(975,1000),proxy,0,4))
        extras.append(('Mean confidence interval (95%, two-sided)',{'estimate':center,'lower':float(center)-critical*se,'upper':float(center)+critical*se}))
    if name in ('chi2test','chi2independence') and isinstance(value,dict):
        expected=value.get('expected',args[1] if name=='chi2test' and len(args)>1 else [])
        if name=='chi2independence' and not expected and value.get('observed'):
            counts=value['observed'];total=sum(sum(row) for row in counts)
            margins=[sum(column) for column in zip(*counts)]
            expected=[[s.sympify(sum(row))*margin/total for margin in margins] for row in counts]
            report['sections'].extend(section for section in statistics_report(name,{'expected':expected},precision,labels)['sections']
                                      if section['title']!='Compared columns')
        flat=[float(v) for row in expected for v in (row if isinstance(row,(list,tuple)) else [row])]
        if flat:
            extras.append(('Expected-count diagnostics',{'minimum expected count':min(flat),'cells below 5':sum(v<5 for v in flat),'cells below 1':sum(v<1 for v in flat),'fraction below 5':sum(v<5 for v in flat)/len(flat)}))
            notes.append('Small expected counts can make the χ² approximation unreliable. For a sparse 2×2 table, consider Fisher exact. Independence must follow from the study design.')
            if name=='chi2independence' and any(v<5 for v in flat):
                report.setdefault('warnings',[]).append({'text':'Some expected counts are below 5; the chi-square approximation may be inaccurate.'})
                if len(expected)==2 and len(expected[0])==2:
                    report['warnings'].append({'text':'Consider Fisher exact for this 2×2 table.'})
    if name in ('chi2independence','fisherexact') and isinstance(value,dict) and value.get('observed'):
        effects=contingency_effects(value['observed'])
        notes.append(effects.pop('Note',''))
        extras.append(('Effect size',effects))
    summary_title='Contrast summaries' if name=='repeatedanova' else 'Sample summaries'
    for title,data in [('Condition summaries',condition_summary),(summary_title,summary),*extras]:
        if data:
            supplement=statistics_report('cramerv' if title=='Effect size' and name in ('chi2independence','fisherexact') else name,data,precision,{} if title=='Effect size' and name in ('chi2independence','fisherexact') else labels)
            for section in supplement['sections']:
                if section['title']=='Compared columns':continue
                if title=='Effect size' and name in ('chi2independence','fisherexact') and section['title']=='Summary':section['title']='Effect-size context'
                elif section['title']=='Summary' or section['title']==report['title']: section['title']=title
            report['sections'].extend(section for section in supplement['sections'] if section['title']!='Compared columns')
            if title=='Paired t post-hoc (Holm)':
                for plot in supplement.get('plots',[]):
                    if plot.get('kind')=='intervals':
                        plot.update(title='Paired mean differences (95% CI, unadjusted)',reference=0,
                                    caption='Pointwise 95% paired t intervals; Holm adjustment applies to p values only.')
            report.setdefault('plots',[]).extend(supplement.get('plots',[]))
    if diagnostics:
        # Format numeric cells through the same decimal/table contract as the primary result.
        formatted=statistics_report(name,[dict(zip(['Check','Sample','Statistic','p value','n','Interpretation'],row)) for row in diagnostics],precision)['sections']
        for section in formatted: section['title']='Assumption checks'
        report['sections'].extend(formatted)
    if qq:
        report.setdefault('plots',[]).extend([
            {'kind':'qq','title':'Normal Q–Q plot','series':qq,'diagnostic':True},
            {'kind':'distribution','title':'Sample distribution','series':distributions,'diagnostic':True}])
    report.setdefault('notes',[]).extend(notes)
    return report
