"""Independent numerical references and public-dispatch comparison suites."""
import json
from pathlib import Path
import unittest
import sympy as s
from test_advanced_statistics import run, evaluate, tree
from calc_engine import dispatch
from calc_shared import MathError
from calc_advanced_linear import least_squares, partial_f_test

ROOT=Path(__file__).resolve().parents[1]


class ComparisonTests(unittest.TestCase):
    def test_shapiro_diagnostics_across_every_calling_family(self):
        a=[2,3,4,2,5];b=[4,4,7,3,6];c=[5,7,8,6,7]
        cases=[('shapiro('+str(a)+')',0),('ttest(0,'+str(a)+')',1),
               ('ttest2(0,'+str(a)+','+str(b)+')',2),('ttestpaired(0,'+str(a)+','+str(b)+')',1),
               ('ztest(0,1,'+str(a)+')',1),('ztest2(0,1,1,'+str(a)+','+str(b)+')',2),
               ('tinterval(95,'+str(a)+')',1),('zinterval(95,1,'+str(a)+')',1)]
        for method in ('anova','welchanova','tukey','gameshowell','bartlett'):
            cases.append((method+'('+','.join(str(v) for v in (a,b,c))+')',3))
        for method in ('scheffe','dunnett'):cases.append((method+'('+str([a,b,c])+')',3))
        for method in ('ttest2','ttestpaired'):cases.append((method+'(0,'+str([a])+','+str([b])+',batch)',1 if method=='ttestpaired' else 2))
        for method in ('anova','welchanova','wilcoxon'):cases.append((method+'('+str([a])+','+str([b])+',batch)',1 if method=='wilcoxon' else 2))
        ancova=[[group,i,2+group+1.3*i+noise] for group in (1,2) for i,noise in enumerate([.2,-.4,.7,-.2,.3])]
        factorial=[[g,h,2*g+3*h+noise] for g in (1,2) for h in (1,2) for noise in [.2,-.4,.7,-.2,.3]]
        linear=[[i,2+1.3*i+noise] for i,noise in enumerate([.2,-.4,.7,-.2,.3])]
        cases.extend([('ancova('+str(ancova)+')',2),('twowayanova('+str(factorial)+')',4),('linearmodel('+str(linear)+')',1)])
        for source,count in cases:
            with self.subTest(source=source):
                report=evaluate(source)['statisticsReport']; checks=[]
                for section in report['sections']:
                    if 'Check' not in section['columns']:continue
                    at=section['columns'].index('Check'); p=next((section['columns'].index(key) for key in ('p value','p-value') if key in section['columns']),None)
                    checks.extend(row[p] for row in section['rows'] if row[at]=='Shapiro–Wilk')
                self.assertEqual(len(checks),count)
                self.assertTrue(all(isinstance(value,dict) and 0<=float(value['decimal'])<=1 for value in checks),report.get('details'))
        from calc_evaluator import Engine
        from calc_statistics import fit_regression
        ref=json.loads((ROOT/'tests/fixtures/sphericity_posthoc_reference.json').read_text(encoding='utf8'))['regression_normality']
        engine=Engine({'precision':30});fit_regression(engine,s.sympify(ref['rows']),'linear')
        self.assertAlmostEqual(float(engine.regression_report['shapiroP']),ref['p'],delta=2e-7)

    def test_shapiro_shared_estimator_accepts_derived_numbers_and_preserves_domain_checks(self):
        from calc_statistics import _shapiro_wilk
        ref=json.loads((ROOT/'tests/fixtures/sphericity_posthoc_reference.json').read_text(encoding='utf8'))
        for case in ref['shapiro_cases']:
            values=case.get('values',list(range(case.get('range_count',0))))
            variants=[values,list(map(float,values)),list(map(s.sympify,values))] if len(values)<5000 else [values]
            for data in variants:
                with self.subTest(n=len(data),kind=type(data[0]).__name__):
                    w,p,n=_shapiro_wilk(data)
                    self.assertEqual(n,len(data));self.assertAlmostEqual(w,case['W'],delta=2e-8)
                    self.assertAlmostEqual(p,case['p'],delta=max(1e-100,case['p']*2e-6))
        for scale in (1e-300,1e308):
            first=_shapiro_wilk([-1.,-.5,0.,.5,1.]); second=_shapiro_wilk([v*scale for v in [-1.,-.5,0.,.5,1.]])
            self.assertAlmostEqual(first[0],second[0],places=12);self.assertAlmostEqual(first[1],second[1],places=12)
        for data in ([1.,2.],[1.]*5,[1.,2.,float('inf')],[1.,2.,float('nan')],list(range(5001)),[s.I,1,2],['1','2','3']):
            with self.subTest(invalid_type=type(data[0]).__name__,n=len(data)):
                with self.assertRaises(MathError):_shapiro_wilk(data)

    def test_repeated_report_n5_normality_condition_means_and_paired_intervals(self):
        ref=json.loads((ROOT/'tests/fixtures/sphericity_posthoc_reference.json').read_text(encoding='utf8'))['repeated_report']
        request={'tree':tree('repeatedanova('+str(ref['rows'])+')'),'precision':20,
                 'statisticsTermLabels':{'feature:1':'x','feature:2':'y','feature:3':'z'}}
        result=json.loads(dispatch(json.dumps(request)));self.assertTrue(result['ok'],result.get('error'))
        report=result['statisticsReport']; sections={section['title']:section for section in report['sections']}
        def number(section,row,column): return float(section['rows'][row][section['columns'].index(column)]['decimal'])
        summary=sections['Condition summaries']
        self.assertEqual([row[0] for row in summary['rows']],['x','y','z'])
        for i,expected in enumerate(ref['conditions']):
            self.assertEqual(number(summary,i,'n'),5)
            self.assertAlmostEqual(number(summary,i,'Mean'),expected['mean'],places=12)
            self.assertAlmostEqual(number(summary,i,'SD'),expected['sd'],places=12)
        self.assertEqual(len(sections['Contrast summaries']['rows']),2)
        checks=sections['Assumption checks']
        from calc_statistics import _shapiro_wilk
        for i,expected in enumerate(ref['contrasts']):
            self.assertEqual(number(checks,i,'n'),5)
            self.assertAlmostEqual(number(checks,i,'Statistic'),expected['W'],delta=2e-8)
            self.assertAlmostEqual(number(checks,i,'p value'),expected['p'],delta=2e-7)
            native=[sum(map(float,row[:i+1]))-(i+1)*float(row[i+1]) for row in ref['rows']]
            self.assertAlmostEqual(_shapiro_wilk(native)[1],expected['p'],delta=2e-7)
        pairs=sections['Paired t post-hoc (Holm)']
        self.assertEqual([row[0] for row in pairs['rows']],['x − y','x − z','y − z'])
        for i,expected in enumerate(ref['pairs']):
            for column,key in [('Mean difference','difference'),('SE','SE'),('n','n'),('df','df'),('Statistic','t'),
                               ('Lower 95% CI','lower'),('Upper 95% CI','upper'),('Raw p value','raw_p'),('Adjusted p value','holm_p')]:
                self.assertAlmostEqual(number(pairs,i,column),expected[key],delta=2e-10)
        intervals=next(plot for plot in report['plots'] if plot['kind']=='intervals')
        self.assertEqual(intervals['reference'],0);self.assertIn('unadjusted',intervals['title'])
        self.assertTrue(any('Holm adjusts p values only' in note for note in report['notes']))
        for values in ([1.,1.,1.,1.,1.],[1.,2.],[1.,2.,float('nan')]):
            with self.assertRaises(MathError):_shapiro_wilk(values)

    def test_sphericity_and_extended_posthoc_independent_references(self):
        fixture=json.loads((ROOT/'tests/fixtures/sphericity_posthoc_reference.json').read_text(encoding='utf8'))
        for case in fixture['cases']:
            with self.subTest(function=case['function'],sizes=[len(g) for g in case['arguments'][0]]):
                result=run(case['function'],*case['arguments'])
                for path,expected in case['expected']:
                    actual=result
                    for key in path: actual=actual[key]
                    self.assertAlmostEqual(float(actual),expected,delta=case['tolerance']*max(1,abs(expected)),msg=str(path))
        from calc_posthoc_extended import dunnett_sf
        for case in fixture['dunnett_tails']:
            actual=dunnett_sf(case['statistic'],tuple(case['sizes']),0)
            self.assertAlmostEqual(actual,case['probability'],delta=case['probability']*2e-6)

    def test_sphericity_two_levels_and_singular_covariance_do_not_claim_a_test(self):
        two=run('repeatedanova',[[1,3],[2,3],[4,7],[5,6]])
        self.assertEqual(two['Mauchly p'],'unavailable')
        self.assertEqual(float(two['HF epsilon']),1.)
        self.assertEqual(float(two['GG p']),float(two['p']))
        # Three contrasts but only two independent subject vectors: retain GG,
        # withhold Mauchly instead of silently dropping zero eigenvalues.
        singular=run('repeatedanova',[[1,2,4,7],[2,4,5,9],[3,5,8,11]])
        self.assertEqual(singular['Mauchly W'],'unavailable');self.assertEqual(singular['Mauchly p'],'unavailable')
        self.assertGreater(float(singular['GG epsilon']),0.)
        for method,args in [('conover',[[[1,1],[2,2],[3,3]]]),('dunnett',[[[1,2],[3,4]],3]),
                            ('scheffe',[[[1,1],[3,3]]]),('dunnett',[[[1],[2,3]]])]:
            with self.subTest(method=method,args=args):
                with self.assertRaises(MathError):run(method,*args)

    def test_new_posthoc_reports_keep_control_labels_assumptions_and_omnibus(self):
        for method in ('scheffe','dunnett','conover'):
            with self.subTest(method=method):
                source=method+'([[1,2,3,5],[4,6,7],[8,9,12,14]]'+(',2' if method=='dunnett' else '')+')'
                report=evaluate(source)['statisticsReport']
                self.assertTrue(report['assumptions'])
                self.assertTrue(any(section['title']==('Overall Kruskal–Wallis' if method=='conover' else 'Overall ANOVA') for section in report['sections']))
                self.assertTrue(report['plots'])
                comparisons=next(section for section in report['sections'] if section['title']=='Comparisons')
                if method=='dunnett':
                    self.assertEqual(len(comparisons['rows']),2)
                    self.assertEqual([row[0] for row in comparisons['rows']],['Sample 1 − Sample 2','Sample 3 − Sample 2'])

    def test_rank_and_repeated_posthoc_families_use_matched_samples_and_holm(self):
        ref=json.loads((ROOT/'tests/fixtures/statistics_group_reference.json').read_text())
        for method,title in [('friedman','Wilcoxon post-hoc (Holm)'),('repeatedanova','Paired t post-hoc (Holm)'),('kruskal','Comparisons')]:
            source=method+'('+(str(ref['repeated']) if method!='kruskal' else ','.join(str(sample) for sample in ref['samples']))+')'
            report=evaluate(source)['statisticsReport']
            section=next(section for section in report['sections'] if section['title']==title)
            if method=='kruskal': self.assertTrue(any(section['title']=='Dunn post-hoc (Holm)' for section in report['sections']))
            for i,row in enumerate(section['rows']):
                for key,reference in [('Raw p value','raw'),('Adjusted p value','holm')]:
                    self.assertAlmostEqual(float(row[section['columns'].index(key)]['decimal']),ref['posthoc'][method][reference][i],places=12)
            if method=='repeatedanova':
                qq=next(plot for plot in report['plots'] if plot['kind']=='qq')
                self.assertEqual(len(qq['series']),len(ref['repeated'][0])-1)
                self.assertEqual(qq['series'][0]['n'],len(ref['repeated']))

    def test_imputation_application_data_does_not_use_display_rounding(self):
        request={'tree':tree('impute([[1,NA],[2,4],[NA,6],[5,8]],mean)'),'precision':3}
        result=json.loads(dispatch(json.dumps(request)))
        self.assertTrue(result['ok'],result.get('error'))
        self.assertEqual(result['imputation']['data'][2][0],'2.6666666666666665')
        self.assertEqual(result['imputation']['imputedCells'],2)

    def test_student_welch_games_howell_and_tie_corrected_friedman(self):
        ref=json.loads((ROOT/'tests/fixtures/statistics_group_reference.json').read_text())
        groups=ref['samples']
        source=','.join(str(sample) for sample in groups)
        welch=evaluate('welchanova('+source+')')['statisticsReport']
        sections={section['title']:section for section in welch['sections']}
        values={row[0]:float(row[1]['decimal']) for row in sections['Summary']['rows'] if isinstance(row[1],dict)}
        for key,actual in [('F',values['F']),('df2',values['df denominator']),('p',values['p value'])]:
            self.assertAlmostEqual(actual,ref['welch'][key],places=12)
        self.assertIn('Games–Howell post-hoc',sections)
        pairs=sections['Games–Howell post-hoc'];cols=pairs['columns']
        for row,expected in zip(pairs['rows'],ref['pairs']):
            def value(column):return float(row[cols.index(column)]['decimal'])
            self.assertAlmostEqual(value('Adjusted p value'),expected['p'],delta=2e-6)
            self.assertAlmostEqual(value('Lower 95% CI'),expected['ci'][0],delta=2e-4)
            self.assertAlmostEqual(value('Upper 95% CI'),expected['ci'][1],delta=2e-4)
        classic=evaluate('anova('+source+')')['statisticsReport']
        self.assertTrue(any(section['title']=='Tukey–Kramer post-hoc' for section in classic['sections']))
        student=evaluate('ttest2(0,'+str(groups[0])+','+str(groups[1])+',student)')
        summary=student['statisticsReport']['sections'][0]
        numeric={row[0]:float(row[1]['decimal']) for row in summary['rows']}
        self.assertAlmostEqual(numeric['t'],ref['student']['t'],places=12)
        self.assertAlmostEqual(numeric['p value'],ref['student']['p'],places=12)
        self.assertEqual(student['statisticsReport']['title'],'Student t test')
        friedman=run('friedman',ref['repeated'])
        self.assertAlmostEqual(float(friedman['chi2']),ref['friedman']['chi2'],places=12)
        self.assertAlmostEqual(float(friedman['p']),ref['friedman']['p'],places=12)

    def test_three_factor_type_ii_iii_against_statsmodels(self):
        fixture=json.loads((ROOT/'tests/fixtures/statistics_factorial_reference.json').read_text())
        for case in fixture['cases']:
            model=run('linearmodel',fixture['rows'],[1,2,3],3,case['type'],s.Symbol('sum'))
            for term in model['ANOVA']:
                reference=case['expected'][term['Term']]
                self.assertAlmostEqual(float(term['SS']),reference['sum_sq'],delta=1e-9)
                self.assertEqual(int(term['df']),int(reference['df']))
                if term['Term']!='Residual':
                    self.assertAlmostEqual(float(term['F']),reference['F'],delta=1e-8)
                    self.assertAlmostEqual(float(term['p']),reference['PR(>F)'],delta=1e-12)


    def test_partial_f_blocks_and_unidentifiable_models(self):
        x=[[1.,i,float(i%2)] for i in range(10)]
        y=[2+3*row[1]+row[2]+.2*(row[1]%3) for row in x]
        fit=least_squares(x,y); test=partial_f_test(x,y,[1,2],fit)
        self.assertEqual(test['df'],2)
        self.assertAlmostEqual(test['SS'],sum((v-sum(y)/len(y))**2 for v in y)-fit[2],places=10)
        with self.assertRaises(MathError):run('twowayanova',[[1,1,2],[1,1,3],[1,2,4],[2,2,5],[2,2,6]],1)
        with self.assertRaises(MathError):run('linearmodel',[[1,1,2],[1,1,4],[1,2,5],[1,2,6],[2,1,4],[2,1,5],[2,2,8],[2,2,10]],[1,2],2,3,s.Symbol('treatment'))


if __name__=='__main__':unittest.main()
