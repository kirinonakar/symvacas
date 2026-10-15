"""Presentation-only tables for Statistics; reusable answers stay untouched."""
import sympy as s
import math
from calc_display import approximate, display_rounded, display_tree, readable

BASIC = set('mean median variance stdev mode skewness kurtosis sumdata quartiles stats covariance correlation ttest ttest2 ttestpaired ztest ztest2 chi2test chi2independence fisherexact anova tukey shapiro wilcoxon mannwhitney kruskal tinterval zinterval'.split())
BASIC.update(('welchanova','gameshowell'))
TITLES = dict(zip('stats mean median variance stdev sumdata quartiles covariance correlation ttest ttest2 ttestpaired ztest ztest2 chi2test chi2independence fisherexact anova tukey shapiro wilcoxon mannwhitney kruskal tinterval zinterval padjust effectsize levene bartlett mcnemar kaplanmeier logrank cox repeatedanova poissonreg nbreg mixedmodel gee glmm multinomial ordinal bootstrap power samplesize impute crossvalidate pca kmeans'.split(),
    ['Descriptive statistics','Mean','Median','Variance','Standard deviation','Sum','Quartiles','Covariance','Correlation','One-sample t test','Welch t test','Paired t test','One-sample z test','Two-sample z test','χ² test','χ² independence test','Fisher exact test','ANOVA','Tukey HSD','Shapiro–Wilk','Wilcoxon','Mann–Whitney','Kruskal–Wallis','t interval','z interval','P-value adjustment','Effect size','Levene test','Bartlett test','McNemar test','Kaplan–Meier','Log-rank test','Cox regression','Repeated-measures ANOVA','Poisson regression','Negative binomial regression','Mixed model','GEE','GLMM','Multinomial regression','Ordinal regression','Bootstrap','Power','Sample size','Imputation','Cross-validation','PCA','K-means']))


TITLES.update({'mode':'Mode', 'skewness':'Skewness', 'kurtosis':'Excess kurtosis'})
TITLES['logisticcompare']='Nested logistic model comparison'
TITLES['modelcompare']='Model Comparison'
TITLES.update({'scheffe':'Scheffé post-hoc test','dunnett':'Dunnett control comparisons','conover':'Conover–Iman post-hoc test'})
TITLES.update({'propztest':'One-sample proportion z test', 'propztest2':'Two-sample proportion z test',
               'ancova':'ANCOVA', 'glm':'Generalized linear model (GLM)',
               'welchanova':'Welch ANOVA','gameshowell':'Games–Howell','linearmodel':'Factorial linear model / ANOVA', 'twowayanova':'Two-way ANOVA', 'friedman':'Friedman test',
               'cohend':'Effect size', 'eta2':'Effect size', 'bootstrapci':'Bootstrap confidence interval',
               'testpower':'Power', 'kstest':'Kolmogorov–Smirnov test',
               'bayesproportion':'Bayesian proportion', 'bayesmean':'Bayesian mean', 'bayesrate':'Bayesian rate',
               'bayescompare':'Bayesian Two-Sample Comparison','bayesbootstrap':'Bayesian Bootstrap'})
TITLES.update({'cronbach':'Cronbach α reliability','efa':'Exploratory factor analysis (EFA)',
               'cfa':'Confirmatory factor analysis (CFA)','sem':'Structural equation model (SEM)',
               'manova':'MANOVA','mediation':'Mediation analysis','moderation':'Moderation analysis',
               'cramerv':'Cramér’s V','phi':'Phi coefficient','cohenkappa':'Cohen’s κ agreement',
               'dunn':'Dunn post-hoc test','discriminantanalysis':'Discriminant analysis (LDA/QDA)',
               'quantreg':'Quantile regression','zeroinflated':'Zero-inflated regression (ZIP/ZINB)',
               'tobit':'Tobit censored regression','hcluster':'Hierarchical clustering'})
TITLES.update({'arima': 'ARIMA / time-series forecast', 'sarima': 'SARIMA / time-series forecast'})
TITLES.update({'metaanalysis':'Meta-analysis','icc':'Intraclass correlation (ICC)', 'blandaltman':'Bland–Altman agreement',
               'tost':'One-sample equivalence (TOST)','tost2':'Independent equivalence (TOST)','tostpaired':'Paired equivalence (TOST)'})
TITLES['cramerv']='Phi / Cramér’s V'
TITLES.update({'pearson':'Pearson correlation','spearman':'Spearman rank correlation','kendall':'Kendall tau-b correlation'})
TITLES.update({'omega':'McDonald’s ω (single factor)','bayesttest':'Bayesian t test (JZS)',
               'bayesanova':'Bayesian one-way ANOVA','metaregression':'Meta-regression','metasubgroup':'Meta-analysis subgroups',
               'designpower':'Power: z / proportion / variance','designsize':'Sample size: z / proportion / variance',
               'yuen':'Yuen trimmed-mean test','trimmedanova':'Trimmed-mean ANOVA','winsorcor':'Winsorized correlation',
               'robustreg':'Huber robust regression (M)','parametricsurvival':'Parametric survival (AFT)'})


def statistics_report(name, value, precision, labels=None):
    """Each section has named columns and cells using the normal result formatter.

    Preview large tables at 100 rows; copyRows retains every formatted row for Copy.
    Never infer that unrelated vectors of equal length describe the same observations.
    """
    sections = []
    plots = []
    assumptions = []
    details = []
    table_labels = labels if isinstance(labels, dict) else {}
    def mean_heading(index): return 'mean ('+table_labels.get('sample:'+str(index),str(index))+')'
    contingency = name in ('chi2independence', 'fisherexact', 'mcnemar','cramerv','phi','cohenkappa')
    categorical = contingency and all(table_labels.get(key) for key in ('table:row', 'table:column'))

    def cell(v):
        if isinstance(v, str): return v
        if isinstance(v, bool): return str(v)
        if v is None: return 'unavailable'
        if v is s.nan: return 'undefined'
        if isinstance(v,(int,float)): v=s.sympify(v)
        shown = display_rounded(v, precision)
        dec = approximate(v, precision)
        return {'exact': readable(shown), 'decimal': readable(dec),
                'tree': display_tree(shown), 'decimalTree': display_tree(dec),
                'approximate': bool(getattr(shown, 'has', lambda *_: False)(s.Float))}

    def add(title, columns, rows):
        if rows and columns:
            formatted = [[cell(v) for v in row] for row in rows]
            section = {'title': title, 'columns': columns, 'rows': formatted[:100], 'totalRows': len(rows)}
            if len(rows) > 100: section['copyRows'] = formatted
            sections.append(section)
            return section

    def count_table(title, headers, values, row_heading=None, row_names=None):
        counts = [[s.sympify(v) for v in row] for row in values]
        row_totals = [sum(row) for row in counts]
        column_totals = [sum(column) for column in zip(*counts)]
        total = sum(row_totals)
        margins = [row+[row_total] for row,row_total in zip(counts,row_totals)]+[column_totals+[total]]
        row_labels = (row_names if row_names is not None else [table_labels.get('table:row:'+str(i+1),str(i+1)) for i in range(len(counts))])+['Total']
        columns = [row_heading if row_heading is not None else table_labels.get('table:row','Row')]+headers+['Total']
        def table(heading, rows):
            section = add(heading, columns, [[label]+row for label,row in zip(row_labels,rows)])
            section['totalRow'] = len(counts)
            section.update({'contingencyGroup':'table','contingencyTitle':'Contingency table','contingencyExpanded':True})
        table(title, margins)
        if title == 'observed':
            def percent(count, denominator):
                return 100*count/denominator if denominator != 0 else None
            table('Row percentages (%)', [[percent(count,row[-1]) for count in row] for row in margins])
            table('Column percentages (%)', [[percent(count,margins[-1][j]) for j,count in enumerate(row)] for row in margins])

    def vector(v): return isinstance(v, (list, tuple)) and all(not isinstance(x, (list, tuple, dict)) for x in v)

    def explanatory(key, item):
        # Match metadata, not text length: variable names and fitted expressions
        # are still data, and numeric inference fields stay in tables.
        key = str(key).lower().replace('_', ' ').strip()
        metadata = ('method', 'estimator', 'estimation', 'extraction', 'rotation',
                    'convention', 'inference', 'interpretation', 'description',
                    'note', 'notes', 'warning', 'warnings', 'reason')
        text = isinstance(item, str) or vector(item) and all(isinstance(x, str) for x in item)
        return text and any(key == word or key.endswith(' '+word) for word in metadata)

    def describe(title, key, item, context=()):
        for text in item if isinstance(item, (list, tuple)) else [item]:
            if text: details.append({'section':title, 'label':str(key), 'text':text, 'context':list(context)})

    def extract_details(title, remaining, context=()):
        for key in list(remaining):
            if explanatory(key, remaining[key]): describe(title, key, remaining.pop(key), context)

    def finite(v):
        try: return float(v) if math.isfinite(float(v)) else None
        except (TypeError,ValueError,OverflowError): return None

    def interval_plot(title, rows, reference=None):
        points=[]
        for label,estimate,lower,upper in rows:
            values=list(map(finite,(estimate,lower,upper)))
            if all(v is not None for v in values) and values[1]<=values[0]<=values[2]: points.append([str(label),*values])
        if points:
            plot = {'kind':'intervals','title':title,'rows':points,'reference':reference}
            if name in ('tost','tost2','tostpaired'):
                plot.update(reference=0, thresholds=[float(value['Lower equivalence bound']),float(value['Upper equivalence bound'])],
                            xlabel='Difference from reference' if name=='tost' else 'Difference (A − B)',
                            caption='Confidence interval level = 1 − 2α. Equivalence requires the whole interval to lie strictly inside the prespecified bounds.')
            if name in ('icc','cohenkappa'):
                plot.update(domain=[0,1],caption='Display range is 0–1. Arrows mark estimates outside this range; original estimates and confidence limits remain in the tables.')
            plots.append(plot)

    def visit(title, v):
        if isinstance(v, s.MatrixBase): v = v.tolist()
        if isinstance(v, dict):
            remaining = dict(v)
            effect_rows=[]
            if title=='Summary' and name in ('cramerv','phi') and 'Cramér’s V' in remaining:
                effect_rows=[[metric,remaining.pop(metric),remaining.pop(rating,'unavailable')]
                             for metric,rating in [('phi','Phi effect rating'),('Cramér’s V','V effect rating')] if metric in remaining]
            if name=='cfa': remaining.pop('Latent R²',None)
            if isinstance(remaining.get('Assumptions'), str):
                assumptions.append(remaining.pop('Assumptions'))
            elif isinstance(remaining.get('Assumptions'), list) and all(isinstance(v,str) for v in remaining['Assumptions']):
                assumptions.extend(remaining.pop('Assumptions'))
            extract_details(title, remaining)
            if isinstance(remaining.get('diagnostics'),dict):
                visit('Model diagnostics',remaining.pop('diagnostics'))
            estimate=v.get('estimate',v.get('Cohen κ',v.get('posterior mean',v.get('sample mean'))))
            interval=v.get('credible interval',v.get('confidence interval'))
            if name!='metaanalysis' and vector(interval) and len(interval)==2:
                interval_plot('Credible interval' if 'credible interval' in v else 'Confidence interval',[(TITLES.get(name,name) if title=='Summary' else title,estimate,*interval)])
            elif 'lower' in v and 'upper' in v:
                interval_plot('Confidence interval',[(TITLES.get(name,name) if title=='Summary' else title,estimate,v['lower'],v['upper'])])
            if name=='bayescompare' and 'difference credible interval' in v:
                interval_plot('Difference credible interval', [('Difference (B − A)',v['Posterior Mean Difference (B - A)'],*v['difference credible interval'])],0)
                interval_plot('Effect credible interval', [('Posterior Effect Size',v['Posterior Effect Size'],*v['effect credible interval'])],0)
            if name == 'tukey':
                pairs = [key[:-16] for key in remaining if key.endswith(' mean difference')]
                add('Pairwise comparisons', ['Comparison','Mean difference','Adjusted p value'],
                    [[pair, remaining.pop(pair+' mean difference'), remaining.pop(pair+' adjusted p value')] for pair in pairs])
            # Preserve row relationships for known parallel arrays.
            bundles = [('P-value adjustment', 'Observation', ['raw p','adjusted p','reject (1=yes)']),
                       ('Components', 'Component', ['eigenvalues','explained variance ratio','cumulative explained variance']),
                       ('Feature scaling', 'Feature', ['centers','scales']),
                       ('Fold scores', 'Fold', ['fold MSE','fold log loss'])]
            summary = [[key, item] for key, item in remaining.items() if not isinstance(item, (dict, list, tuple, s.MatrixBase))]
            add(title, ['Metric','Value'], summary)
            if effect_rows:add('Effect size',['Effect size','Value','Rating'],effect_rows)
            for key, _ in summary: remaining.pop(key)
            for heading, index, keys in bundles:
                present = [key for key in keys if key in remaining and vector(remaining[key])]
                if not present: continue
                lengths = {len(remaining[key]) for key in present}
                if len(lengths) != 1: continue
                add(heading, [index]+present, [[table_labels.get('feature:'+str(i+1),i+1) if name=='pca' and index=='Feature' else i+1]+[remaining[key][i] for key in present] for i in range(next(iter(lengths)))])
                for key in present: remaining.pop(key)
            for key, item in remaining.items(): visit(key, item)
        elif isinstance(v, (list, tuple)):
            if not v: return
            if name=='stats' and title=='Category frequencies':
                rows=[[table_labels.get('summary:category:'+str(row['Category']), row['Category']), row['Count'], row['Percentage (%)']] for row in v]
                rows.append(['Total', sum(row['Count'] for row in v), s.Integer(100)])
                section=add(title,['Category','Count','Percentage (%)'],rows)
                section['totalRow']=len(v)
                return
            if all(isinstance(row, dict) for row in v):
                intervals=[]; expanded=[]
                for row_index, raw in enumerate(v):
                    row=dict(raw)
                    if name=='metaanalysis' and title in ('Studies','Excluded studies'): row['Study']=table_labels.get('study:'+str(row['Study']),str(row['Study']))
                    if name in ('cfa','sem') and title=='Latent R²' and row.get('Role')=='Exogenous (R² not applicable)': row['R²']='Not applicable'
                    bounds=row.pop('CI95',None)
                    if isinstance(bounds,(list,tuple)) and len(bounds)==2: row['Lower 95% CI'],row['Upper 95% CI']=bounds
                    elif 'CI95' in raw: row['Lower 95% CI']=row['Upper 95% CI']=None
                    standardized_bounds=row.pop('Standardized CI95',None)
                    if isinstance(standardized_bounds,(list,tuple)) and len(standardized_bounds)==2:
                        row['Standardized lower 95% CI'],row['Standardized upper 95% CI']=standardized_bounds
                    for key,prefix in (('Bootstrap CI95','Bootstrap '),('Standardized bootstrap CI95','Standardized bootstrap ')):
                        bounds=row.pop(key,None)
                        if isinstance(bounds,(list,tuple)) and len(bounds)==2: row[prefix+'lower 95% CI'],row[prefix+'upper 95% CI']=bounds
                        elif key in raw: row[prefix+'lower 95% CI']=row[prefix+'upper 95% CI']=None
                    label=row.get('term',row.get('Term',row.get('group',row.get('Group',row.get('Comparison','')))))
                    if name in ('arima','sarima') and not label: label=row.get('Parameter','')
                    estimate=row.get('estimate',row.get('Estimate',row.get('Mean',row.get('adjusted mean',row.get('Mean difference')))))
                    low=row.get('Lower 95% CI',row.get('Lower CI'))
                    high=row.get('Upper 95% CI',row.get('Upper CI'))
                    standardized=name in ('cfa','sem') and title in ('Loadings','Structural paths')
                    if standardized:
                        estimate=row.get('Standardized loading',row.get('Standardized path'))
                        low=row.get('Standardized lower 95% CI'); high=row.get('Standardized upper 95% CI')
                    if label:
                        if title=='Effects': label=str(label)+' / '+str(row.get('Effect',''))
                        if name in ('cfa','sem') and 'Group' in row: label=str(row['Group'])+' / '+str(label)
                        if name in ('cfa','sem') and 'Factor' in row: label=str(label)+' / Factor '+str(row['Factor'])
                        intervals.append((label,estimate,low,high))
                    identifiers = ('term','Term','group','Group','Factor','Feature','Variable','Parameter','Effect','Comparison','Check','Component','Threshold')
                    context = [{'label':key, 'value':str(row[key])} for key in identifiers if key in row]
                    if not context: context = [{'label':'Observation', 'value':str(row_index+1)}]
                    extract_details(title, row, context)
                    expanded.append(row)
                if intervals:
                    plot_title={'Loadings':'Standardized factor loadings (95% CI)','Structural paths':'Standardized structural paths (95% CI)'}.get(title,title+' intervals') if name in ('cfa','sem') else title+' intervals'
                    interval_plot(plot_title,intervals,0 if (name in ('cfa','sem','gameshowell') or 'coefficients' in title.lower() or 'post-hoc' in title.lower()) else None)
                v=expanded
                keys = list(dict.fromkeys(key for row in v for key in row))
                if title=='Effects':
                    raw_keys=[key for key in keys if not key.startswith('Standardized ')]
                    add(title,raw_keys,[[row.get(key,'unavailable') for key in raw_keys] for row in v])
                    standard_keys=[key for key in keys if key in ('term','Effect','Group') or key.startswith('Standardized ')]
                    add('Standardized effects',standard_keys,[[row.get(key,'unavailable') for key in standard_keys] for row in v])
                else:
                    hidden=('First indicator position','Second indicator position') if title=='Residual covariances' else ()
                    keys=[key for key in keys if key not in hidden and not (title=='Residual covariances' and key=='term')]
                    add(title, keys, [[row.get(key, 'unavailable') for key in keys] for row in v])
            elif all(vector(row) for row in v) and len({len(row) for row in v}) == 1:
                width = len(v[0])
                headers = {'survival table':['Time','At risk','Events','Censored','Survival','Lower 95% CI','Upper 95% CI'],
                           'observed':['Category 1','Category 2'], 'expected':['Category 1','Category 2']}.get(title)
                if headers is None or len(headers) != width:
                    prefix = ('Factor ' if name=='efa' else 'PC') if title in ('loadings','scores','Structure loadings','Factor correlations') else 'Feature ' if title=='centroids' else 'Column '
                    headers = [prefix+str(i+1) for i in range(width)]
                    if title=='centroids': headers=[table_labels.get('feature:'+str(i+1),header) for i,header in enumerate(headers)]
                index = 'Feature' if title in ('loadings','Structure loadings') else 'Factor' if title=='Factor correlations' else 'Cluster' if title == 'centroids' else 'Observation'
                if contingency and title in ('observed', 'expected'):
                    if categorical:
                        headers = [str(table_labels['table:column'])+': '+str(table_labels.get('table:column:'+str(i+1), 'Category '+str(i+1))) for i in range(width)]
                    count_table(title, headers, v)
                    return
                add(title, [index]+headers, [[table_labels.get('feature:'+str(i+1),i+1) if name in ('pca','efa') and index=='Feature' else i+1]+list(row) for i,row in enumerate(v)])
            elif vector(v):
                if title in ('confidence interval','credible interval','difference credible interval','effect credible interval','Ratio confidence interval','Slope CI','Bias CI','Lower limit CI (approximate)','Upper limit CI (approximate)','quartiles (inclusive)','Quartiles'):
                    labels = ['Lower','Upper'] if len(v)==2 else ['Q1','Median','Q3']
                    if len(labels)==len(v): add(title, labels, [list(v)]); return
                add(title, ['Fold' if title in ('fold MSE','fold log loss','fold sizes') else 'Observation','Value'], [[i+1,item] for i,item in enumerate(v)])
            else:
                for i,item in enumerate(v): visit(title+' '+str(i+1), item)
        elif explanatory(title, v): describe(title, title, v)
        else: add(title, ['Metric','Value'], [[title,v]])

    if name in ('stats','mode','skewness','kurtosis','mean','median','stdev','variance','sumdata','quartiles','correlation','covariance') and table_labels.get('sample:1'):
        add('Analyzed variables',['Sample'],[[table_labels[key]] for key in sorted(table_labels) if key.startswith('sample:')])
    if categorical:
        add('Compared columns', ['First column', 'Second column'] if name == 'mcnemar' else ['Row variable', 'Column variable'], [[table_labels['table:row'], table_labels['table:column']]])
    if name=='bayesbootstrap' and isinstance(value,dict) and value.get('comparison'):
        add('Compared groups',['Group A','Group B'],[[table_labels.get('sample:A','A'),table_labels.get('sample:B','B')]])
    if name=='kmeans' and isinstance(value,dict):
        assignments=value.get('labels (1-based)',[])
        add('Cluster sizes',['Cluster','n'],[[i+1,sum(label==i+1 for label in assignments)] for i in range(len(value.get('centroids',[])))])
    if name=='crossvalidate' and isinstance(value,dict):
        metric='fold log loss' if 'fold log loss' in value else 'fold MSE'
        scores=value.get(metric,[])
        if scores: plots.append({'kind':'bars','title':'Validation score by fold','values':list(map(float,scores)),'labels':['Fold '+str(i+1) for i in range(len(scores))],'ylabel':'Log loss' if metric=='fold log loss' else 'MSE'})
    if name=='friedman' and isinstance(value,dict):
        ranks=value['mean ranks'];plots.append({'kind':'bars','title':'Mean ranks by condition','values':list(map(float,ranks)),'labels':[table_labels.get('feature:'+str(i+1),'Condition '+str(i+1)) for i in range(len(ranks))],'ylabel':'Mean rank'})
    if name=='padjust' and isinstance(value,dict):
        plots.append({'kind':'bars','title':'Raw and adjusted p values','values':list(map(float,value['adjusted p'])),'secondary':list(map(float,value['raw p'])),'labels':[str(i+1) for i in range(len(value['raw p']))],'ylabel':'p value','reference':float(value['alpha']),'maximum':1})
    if name in ('cfa','sem') and isinstance(value,dict):
        from calc_statistics_sem_diagram import diagrams
        plots.extend(diagrams(value,table_labels))
        assumptions.append('Fully standardized coefficients: 95% Wald confidence intervals by the delta method using the full parameter covariance. Fixed raw marker loadings retain standardized uncertainty. Latent R² = 1 − disturbance variance / total latent variance; R² is not applicable to exogenous factors. WLSMV loadings refer to underlying probit responses. Diagram arrows show specified effects, not proof of causality.')
        assumptions.append('Indicator R² = 1 − indicator residual variance / model-implied indicator variance. Cross-loadings include factor covariance terms. With WLSMV, R² refers to the underlying probit response.')
    if name=='modelcompare' and isinstance(value,dict):
        value=dict(value)
        if 'Model fit' in value:
            add('Compared models',['Model','Variables','Response'],[[model,table_labels.get('model:'+letter,model),table_labels.get('response','')] for model,letter in [('Model A','A'),('Model B','B')]])
            add('Model fit',['Model','n','Fixed coefficients','Log likelihood','AIC','BIC','R²','Deviance','χ²','df','CFI','RMSEA'],value.pop('Model fit'))
        if 'Validation performance' in value:
            performance=value.pop('Validation performance');columns=list(performance[0])
            add('Validation performance',columns,[[row.get(key) for key in columns] for row in performance])
        if 'Paired differences' in value:
            differences=value.pop('Paired differences')
            add('Paired performance differences (B − A)',['Metric','Difference','Lower CI','Upper CI','p value','Inference'],differences)
            for row in differences:interval_plot('Δ'+str(row[0])+' (B − A)',[['Model B − Model A',*row[1:4]]],0)
        if 'ROC curves' in value:
            curves=value.pop('ROC curves')
            intervals=value.pop('AUC intervals',[None,None])
            plots.append({'kind':'roc-comparison','title':'ROC / AUC comparison','evaluation':str(value['Validation method']),
                          'series':[{'label':row['Model'],'points':[[float(x),float(y)] for x,y in points],'auc':float(row['AUC']),'interval':[float(v) for v in interval] if isinstance(interval,(list,tuple)) and all(finite(v) is not None for v in interval) else None} for row,points,interval in zip(performance,curves,intervals)]})
        if 'Calibration curves' in value:
            calibration=value.pop('Calibration curves')
            plots.append({'kind':'calibration-comparison','title':'Calibration comparison','evaluation':str(value['Validation method']),
                          'series':[{'label':row['Model'],'points':[[float(x),float(y),int(n)] for x,y,n in points]} for row,points in zip(performance,calibration)]})
        if 'Candidate comparisons' in value:
            candidates=value.pop('Candidate comparisons');columns=list(dict.fromkeys(key for row in candidates for key in row))
            for row in candidates:row['Candidate']=table_labels.get('candidate:'+str(row['Candidate']),str(row['Candidate']))
            add('Candidate comparisons',columns,[[row.get(key) for key in columns] for row in candidates])
        if 'Failed candidate comparisons' in value:
            failed=value.pop('Failed candidate comparisons')
            add('Failed candidate comparisons',['Candidate','Reason'],[[table_labels.get('candidate:'+str(row['Candidate']),str(row['Candidate'])),row['Reason']] for row in failed])
    if name=='logisticcompare' and isinstance(value,dict):
        value=dict(value)
        add('Compared predictors',['Model','Predictors','Response'],[[model,table_labels.get('model:'+letter,model),table_labels.get('response','0/1')] for model,letter in [('Model A','A'),('Model B','B')]])
        add('Training model fit',['Model','n','Coefficient count','Log likelihood','AIC','BIC'],value.pop('Training models'))
        validation=value.pop('Validation models')
        add('Validation performance',['Model','n','AUC','Accuracy','Log loss','Brier score','Calibration intercept','Calibration slope'],validation)
        differences=value.pop('Paired differences')
        add('Paired performance differences (B − A)',['Metric','Difference','Lower CI','Upper CI','p value','Inference'],differences)
        curves=value.pop('ROC curves');intervals=value.pop('AUC intervals');calibration=value.pop('Calibration curves')
        plot_series=[{'label':row[0],'points':[[float(x),float(y)] for x,y in points],'auc':float(row[2]),'interval':[float(v) for v in interval] if isinstance(interval,(list,tuple)) and all(finite(v) is not None for v in interval) else None} for row,points,interval in zip(validation,curves,intervals)]
        plots.append({'kind':'roc-comparison','title':'ROC / AUC comparison','series':plot_series,'evaluation':str(value['Validation method'])})
        plots.append({'kind':'calibration-comparison','title':'Calibration comparison','series':[{'label':row[0],'points':[[float(x),float(y),int(n)] for x,y,n in points]} for row,points in zip(validation,calibration)],'evaluation':str(value['Validation method'])})
        delta=differences[0]
        if all(finite(v) is not None for v in delta[1:4]):interval_plot('ΔAUC (B − A)',[['Model B − Model A',*delta[1:4]]],0)
    overall = name == 'stats' and isinstance(value, dict) and 'Numeric data' in value and 'Categorical data' in value
    batch_t = name in ('ttest2', 'ttestpaired') and isinstance(value, dict) and 'Comparisons' in value
    column_batch = isinstance(value,dict) and 'Column comparisons' in value
    if column_batch:
        label = lambda index: table_labels.get('batch:column:'+str(index),str(index+1))
        group_count = int(value['Group count'])
        rows = value['Column comparisons']
        category_label = lambda index,category: table_labels.get('batch:category:'+str(index)+':'+str(category),category)
        suffix = ['p-value','n','Significant']
        if value['Categorical']:
            show_category = any(not row['Binary'] for row in rows)
            headings = ['Column']+(['Category'] if show_category else [])+['numb ('+table_labels.get('sample:'+str(at+1),str(at+1))+') (%)' for at in range(group_count)]+(['diff (%)'] if group_count==2 else ['diff (1-'+str(at+1)+') (%)' for at in range(1,group_count)])+suffix
            def count_percent(amount,percent):
                return str(amount)+' ('+(f'{float(percent):.2f}%' if finite(percent) is not None else 'unavailable')+')'
            formatted=[]
            for row in rows:
                formatted.append([label(row['Column'])]+([category_label(row['Column'],row['Category'])] if show_category else [])+
                    [count_percent(row['count'+str(at+1)],row['percent'+str(at+1)]) for at in range(group_count)]+
                    [count_percent(row['count diff'+str(at+1)],row['percent diff'+str(at+1)]) for at in range(1,group_count)]+[row[key] for key in suffix])
            section=add('Summary',headings,formatted)
            for table in value['Contingency tables']:
                headings=[str(category_label(table['Column'],category)) for category in table['Categories']]
                names=[table_labels.get('sample:'+str(at+1),str(at+1)) for at in range(len(table['Observed']))]
                for key,title in [('Observed','observed'),('Expected','expected')]:
                    start=len(sections)
                    count_table(title,headings,table[key],row_heading='Group',row_names=names)
                    for added in sections[start:]:
                        added['title']=label(table['Column'])+' · '+added['title']
                        added.update({'contingencyGroup':'column:'+str(table['Column']), 'contingencyLabel':label(table['Column']),
                                      'contingencyExpanded':len(value['Contingency tables'])==1})
            checks=value['Column checks']
            add('Expected-count diagnostics',['Column','Minimum expected','Cells below 5','Cells below 1','Cells'],
                [[label(row['Column'])]+[row[key] for key in ['Minimum expected','Cells below 5','Cells below 1','Cells']] for row in checks])
        else:
            headings=['Column']+[mean_heading(at+1) for at in range(group_count)]+(['diff'] if group_count==2 else ['diff (1-'+str(at+1)+')' for at in range(1,group_count)])+suffix+['normality','equal var']
            section=add('Summary',headings,[[label(row['Column'])]+[row['mean'+str(at+1)] for at in range(group_count)]+
                [row['diff'+str(at+1)] for at in range(1,group_count)]+[row[key] for key in suffix+['normality','equal var']] for row in rows])
            add('Detailed assumption checks',['Column','Check','Sample','p-value','Result'],
                [[label(row['Column']),row['Check'],table_labels.get('sample:'+row['Sample'],row['Sample']),row['p-value'],row['Result']] for row in value['Column checks']])
        if section:section['literalColumns']=True
        for row in value['Column details']:details.append({'section':label(row['Column']),'label':'Note','text':row['Reason']})
    elif batch_t:
        keys = ['mean1', 'mean2', 'diff', 'p-value', 'n', 'Significant', 'normality', 'equal var']
        label = lambda index: table_labels.get('batch:column:'+str(index), str(index+1))
        section = add('Summary', ['Column',mean_heading(1),mean_heading(2)]+keys[2:],
                      [[label(row['Column'])]+[row[key] for key in keys] for row in value['Comparisons']])
        section['literalColumns'] = True
        checks = value['Assumption checks']
        add('Detailed assumption checks', ['Column', 'Check', 'Sample', 'p-value', 'Result'],
            [[label(row['Column']), row['Check'], table_labels.get('sample:'+row['Sample'], row['Sample']),
              row['p-value'], row['Result']] for row in checks])
        for row in checks+value['Unavailable comparisons']:
            if row.get('Reason'): details.append({'section':label(row['Column']), 'label':row.get('Check', 'Unavailable comparison'), 'text':row['Reason']})
    elif overall:
        metrics = ['mean', 'sd', 'min', 'max', 'valid.n']
        add('Numeric data', ['Column']+metrics,
            [[table_labels.get('overall:column:'+str(row['Column']), str(row['Column']+1))]+
             [row[key] for key in metrics] for row in value['Numeric data']])
        add('Categorical data', ['Column', 'Category', 'numb (%)'],
            [[table_labels.get('overall:column:'+str(row['Column']), str(row['Column']+1)),
              table_labels.get('overall:category:'+str(row['Column'])+':'+str(row['Category']), row['Category']),
              f"{row['Count']} ({float(row['Percentage (%)']):.2f}%)"] for row in value['Categorical data']])
        for section in sections: section['literalColumns'] = True
    else:
        visit('Summary' if isinstance(value, dict) else TITLES.get(name, name), value)
    priority=['Cronbach α','Cohen κ',"Cramér’s V",'phi','Indirect effect a×b','CFI','RMSEA','KMO','p value','p','mean difference','posterior mean','Posterior Mean Difference (B - A)','Posterior Effect Size','BF10','P(μB > μA)','estimate','power','achieved power','n per group / pairs','R²','Adjusted R²','Kendall W','eta2','Cohen d','Cohen dz','RMSE','R2','inertia']
    report_title='Overall' if overall else TITLES.get(name,name)
    if batch_t:
        report_title='Paired t tests' if name == 'ttestpaired' else 'Student t tests' if value['Method'] == 'student' else 'Welch t tests'
    if name=='mcnemar' and isinstance(value,dict):
        priority=['discordant pairs','p']
        report_title={'asymptotic':'McNemar','exact':'Exact McNemar','corrected':'McNemar (continuity correction)'}.get(value.get('method'),report_title)
    if name in ('cfa','sem'): priority=['CFI','RMSEA','SRMR','p']
    if name in ('arima','sarima'): priority=['Forecast horizon','Prediction level','RMSE','Conditional AICc']
    if name=='metaanalysis': priority=['estimate','I² (%)','τ²','Q p']
    if name=='omega':priority=['McDonald ω','Cronbach α','Model p']
    if name in ('bayesttest','bayesanova'):priority=['BF10','BF01','Prior scale r']
    if name in ('metaregression','metasubgroup'):priority=['Studies (k)','τ²','Residual Q p']
    if name in ('designpower','designsize'):priority=['power','n','n per arm','Total n']
    if name=='parametricsurvival':priority=['Events','AFT scale σ','AIC','BIC']
    if name=='icc': priority=['ICC','p']
    if name=='spearman': priority=['rho','p','n']
    if name=='pearson': priority=['r','p','n']
    if name=='kendall': priority=['tau-b','p','n']
    if name=='blandaltman': priority=['Bias','Lower agreement limit','Upper agreement limit']
    if name in ('tost','tost2','tostpaired'): priority=['estimate','TOST p','Lower p','Upper p']
    if name=='logisticcompare':priority=['LRT χ²','LRT p','ΔAIC (B − A)','ΔBIC (B − A)']
    if name=='modelcompare':priority=['F','LRT χ²','Difference χ²','p','ΔR² (B − A)','ΔAUC (B − A)','ΔC-index (B − A)','ΔRMSE (B − A)','ΔAIC (B − A)']
    highlights=[{'label':('χ² p' if name in ('cfa','sem') else 'p value') if key=='p' and name in ('cfa','sem','mcnemar') else key,'value':cell(value[key])} for key in priority if isinstance(value,dict) and key in value and finite(value[key]) is not None][:4]
    report = {'analysis': name, 'title': report_title, 'sections': sections,'highlights':highlights,'plots':plots}
    if name=='pearson':
        report['notes']=['Independent paired observations; the Pearson p value assumes a bivariate normal population under the null hypothesis of zero correlation.']
    if name in ('spearman','kendall'):
        report['notes']=['Paired observations must be independent across rows. Spearman uses average ranks for ties; Kendall tau-b adjusts for tied pairs.']
        if name=='spearman' and value.get('method')=='Asymptotic t approximation':
            report['notes'].append('The p value uses a t approximation; small samples may need a permutation test.')
    if name=='stats' and isinstance(value,dict) and 'Category frequencies' in value:
        report['notes']=['Percentages use nonmissing values in the selected column.']
    if overall:
        report['notes']=['SD is the sample standard deviation. Missing cells are excluded separately for each column; percentages use valid values in that column. Columns containing only 0/1 values are categorical.']
    if batch_t:
        report['context']='diff = '+mean_heading(1)+' − '+mean_heading(2)+'.'
        report['notes']=['Significant: yes when the selected t-test p-value is below 0.05. Normality: yes when Shapiro–Wilk does not reject normality at 0.05 in both groups (paired tests check differences). Equal var: yes when Brown–Forsythe does not reject equal variances at 0.05; not applicable to paired tests. Unavailable checks are not classified as yes or no. n is the total valid count in independent groups, or the complete-pair count in paired tests. Missing values are handled separately for each column. P-values are unadjusted across columns; yes does not prove an assumption.']
    if column_batch:
        report['context']='; '.join('group'+str(at+1)+' = '+table_labels.get('sample:'+str(at+1),str(at+1)) for at in range(int(value['Group count'])))
        report['notes']=['Significant: yes at p < 0.05. Missing values are omitted separately for each column. P-values are unadjusted across columns.']
        if value['Categorical']:
            report['notes'].append('Counts and percentages use valid values within each group. Binary columns show category 1; other columns show every category. diff (%) is the count difference (percentage-point difference), group 1 minus the compared group. The p-value tests the whole column, and is repeated for its categories.')
            report['warnings']=[{'label':label(row['Column']),'text':row['Text']} for row in value['Column warnings']]
        else:
            report['notes'].append('Means describe each group. diff is group 1 minus the compared group. n is the total valid count, or the complete-pair count for paired tests. Nonparametric p-values test ranks, not differences in means. Assumption checks use 0.05; yes means not rejected, not proven.')
    if assumptions: report['assumptions'] = assumptions
    if details: report['details'] = details
    return report


def statistics_copy_report(name, value, details, precision):
    """Copy tables for dedicated reports without changing visible report routing."""
    if name == 'regression' and details.get('model') == 'svm':
        classification = details.get('task') == 'classification'
        data = {'Model': 'SVC' if classification else 'SVR',
                'Evaluation': 'Training data evaluation', 'n': details['n'],
                'Kernel': details['kernel'], 'Penalty C': details['C'],
                'Support vectors': details['supportVectors'], 'Iterations': details['iterations']}
        for label, key in (('Gamma', 'gamma'), ('Epsilon (SVR)', 'epsilon'),
                           ('R²', 'rSquared'), ('RMSE', 'rmse'), ('AUC', 'auc'),
                           ('Accuracy', 'accuracy'), ('Sensitivity', 'sensitivity'), ('Specificity', 'specificity')):
            if details.get(key) is not None:
                data['Training accuracy' if classification and key == 'accuracy' else label] = s.sympify(details[key])
        if details.get('coefficients'):
            data['Fitted parameters'] = [{'Parameter': row['name'], 'Estimate': s.sympify(row['estimate'])}
                                         for row in details['coefficients']]
        if classification:
            equation = details.get('decisionEquation', {})
            data['Decision function'] = 'f(x) = '+equation['expression'] if equation.get('expression') else equation.get('formula', '')
            data['Decision rule'] = 'f(x) >= 0: class 1; f(x) < 0: class 0.'
            if details['kernel'] == 'rbf' and equation:
                data['Kernel intercept b'] = equation['intercept']
                data['Predictor scales'] = [{'Variable': name, 'Scale': scale}
                                           for name, scale in zip(equation['variables'], equation['scales'])]
                data['Support vector terms'] = [
                    {'Observation': term['row'], 'aᵢ': term['coefficient'],
                     **dict(zip(('vᵢ'+str(i+1) for i in range(len(term['coordinates']))), term['coordinates']))}
                    for term in equation['supportTerms']]
            cv = details.get('crossValidation')
            if cv:
                data['Cross-validation'] = ({'Method': cv['method'], 'Folds': cv['folds'],
                                            'Random seed': cv['seed'], 'n': cv['n'],
                                            'Cross-validated accuracy': cv['accuracy']}
                                           if cv['available'] else cv['reason'])
                if cv['available']:
                    data['Cross-validation predictions'] = [
                        {'Observation': row['row'], 'Fold': row['fold'], 'Observed class': row['observed'],
                         'Predicted class': row['predicted']} for row in cv['predictions']]
            data['Decision threshold'] = details['threshold']
            data['Classification predictions'] = [
                {'Observation': row['row'], 'Observed class': int(float(row['observed'])),
                 'Predicted class': int(float(row['fitted'])), 'Decision score': s.sympify(row['decisionScore']),
                 'Support vector': 'Yes' if row.get('supportVector') else 'No'} for row in details['residuals']]
            data['Confusion matrix'] = [dict(zip(('Observed class', 'Predicted 0', 'Predicted 1'), [i]+row))
                                        for i, row in enumerate(details['confusionMatrix'])]
        else:
            data['Residual diagnostics'] = [
                {'Observation': row['row'], 'Observed': s.sympify(row['observed']),
                 'Fitted value': s.sympify(row['fitted']), 'Residual': s.sympify(row['residual'])}
                for row in details['residuals']]
        data['Warnings'] = details.get('warnings', [])
        report = statistics_report(name, data, precision)
        report['title'] = 'SVM classification' if classification else 'SVM regression'
        return report
    if name == 'regression':
        data = {('Model' if details.get('model') == 'svm' else 'Fitted expression'): value, **details}
        report = statistics_report(name, data, precision)
        report['title'] = 'Regression'
    else:
        data = {key: item for key, item in details.items() if key != 'groups'}
        for index, group in enumerate(details.get('groups', [])):
            data['Group '+str(index+1)] = {key: item for key, item in group.items() if key != 'curve'}
            data['Group '+str(index+1)]['survival table'] = group.get('curve', [])
        report = statistics_report(name, data, precision)
        report['title'] = 'Survival analysis'
    return report
