"""Independent numerical references and public-dispatch comparison suites."""
import json
from pathlib import Path
import unittest
import sympy as s
from test_advanced_statistics import run, evaluate, tree
from calc_engine import dispatch
from calc_shared import MathError

ROOT=Path(__file__).resolve().parents[1]


class ComparisonTests(unittest.TestCase):
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


if __name__=='__main__':unittest.main()
