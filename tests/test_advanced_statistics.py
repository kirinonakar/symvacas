"""Public-dispatch statistics checks, with independent SciPy/statsmodels fixtures."""
import ast
import json
import math
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app/src/main/python'))
from calc_engine import dispatch
from calc_evaluator import Engine
from calc_advanced_statistics import FUNCTIONS, advanced
from calc_shared import MathError
import sympy as s

def tree(source):
    def visit(node):
        if isinstance(node,ast.Call): return {'kind':'call','value':node.func.id,'args':[visit(a) for a in node.args]}
        if isinstance(node,ast.List): return {'kind':'list','args':[visit(a) for a in node.elts]}
        if isinstance(node,ast.Name): return {'kind':'symbol','value':node.id}
        if isinstance(node,ast.Constant): return {'kind':'number','value':str(node.value)}
        if isinstance(node,ast.UnaryOp): return {'kind':'unary','value':'-' if isinstance(node.op,ast.USub) else '+','args':[visit(node.operand)]}
        raise ValueError(ast.dump(node))
    return visit(ast.parse(source,mode='eval').body)

def evaluate(source):
    result=json.loads(dispatch(json.dumps({'tree':tree(source),'precision':20,'budget':30})))
    if not result['ok']: raise AssertionError(source+': '+result['error'])
    return result

def run(name,*args):
    return advanced(Engine({}),name,[s.sympify(v) for v in args])

class AdvancedStatisticsTests(unittest.TestCase):

    def test_statistics_tables_preserve_exact_answers_and_parallel_row_relationships(self):
        result=evaluate('stats([1,2,4])')
        summary=result['statisticsReport']['sections'][0]
        mean=next(row[1] for row in summary['rows'] if row[0]=='mean')
        self.assertEqual(mean['exact'],'7/3')
        self.assertEqual(mean['tree']['kind'],'fraction')
        self.assertIn('mean: 7/3',result['exact'])
        interval=evaluate('tinterval(95,[1,2,4,5])')['statisticsReport']
        self.assertEqual(next(section for section in interval['sections'] if section['title']=='confidence interval')['columns'],['Lower','Upper'])
        adjusted=evaluate('padjust([0.01,0.03,0.2],holm)')['statisticsReport']
        rows=next(section for section in adjusted['sections'] if section['title']=='P-value adjustment')['rows']
        self.assertEqual(len(rows),3)
        self.assertAlmostEqual(float(rows[1][1]['exact']),.03)
        self.assertAlmostEqual(float(rows[1][2]['exact']),.06)
        comparisons=evaluate('tukey([1,2,3],[4,5,7],[3,6,8])')['statisticsReport']['sections'][0]
        self.assertEqual(comparisons['columns'],['Comparison','Mean difference','Adjusted p value'])
        self.assertEqual([row[0] for row in comparisons['rows']],['x-y','x-z','y-z'])

    def test_advanced_analyses_reject_invalid_arity_and_data(self):
        with self.subTest(scenario='registered_analyses_reject_missing_and_excess_arguments'):
            definitions=json.loads((ROOT/'app/src/main/assets/advanced_statistics.json').read_text(encoding='utf-8'))
            self.assertEqual(FUNCTIONS,{item['id'] for item in definitions if item['id'] not in ('shapiro','normaltest','tukey','gameshowell','tinterval','zinterval')})
            for name in FUNCTIONS:
                for args in ([],[s.Integer(0)]*21):
                    with self.subTest(function=name,count=len(args)):
                        with self.assertRaisesRegex(MathError,name+' argument count mismatch'):
                            advanced(Engine({}),name,args)
        with self.subTest(scenario='invalid_inputs_fail_without_plausible_results'):
            sources=['padjust([0.1,1.1])','cohend([1,1],[2,2])','mcnemar([[1,-2],[3,4]])','kaplanmeier([[1,2],[2,1]])','logrank([[1,0],[2,0]],[[1,0],[2,0]])',
                     'poissonreg([[1,-1],[2,2],[3,4]])','impute([[NA,1],[NA,2]])','pca([[1,2],[1,3]])','cohend([1,2],[3,4,5],paired)',
                     'crossvalidate([[0,1],[1,3],[2,5]],3)','gee([[1,0,1],[1,1,2],[2,0,3],[2,1,4]])','cox([[1,1,1],[2,1,1],[3,1,1],[4,1,1]])',
                     'multinomial([[-2,0],[-1,0],[1,1],[2,1]])','cox([[1,1,3],[2,1,2],[3,1,1],[4,0,0]])',
                     'poissonreg([[0,0],[0,0],[1,2],[1,3],[1,1]])','impute([[1,NA],[2,NA]],regression)',
                     'crossvalidate([[0,1],[1,3],[2,5]],3,0,random,ridge,0)']
            for source in sources:
                with self.subTest(source=source):
                    result=json.loads(dispatch(json.dumps({'tree':tree(source),'budget':30})))
                    self.assertFalse(result['ok'],source)

    def test_survival_reports_preserve_ties_groups_and_censoring(self):
        with self.subTest(scenario='survival_suite_preserves_ties_ci_and_two_group_logrank'):
            rows=[[1,1,1],[1,0,1],[2,1,1],[3,0,1],[1,0,2],[2,1,2],[3,1,2],[4,0,2]]
            report=evaluate('survivalanalysis('+str(rows)+',0)')['survival']
            curve=report['groups'][0]['curve']
            self.assertEqual(curve[0][:5],[1,4,1,1,.75])
            reference=run('kaplanmeier',[r[:2] for r in rows if r[2]==1])['survival table']
            for actual,expected in zip(curve,reference):
                for x,y in zip(actual,expected):self.assertAlmostEqual(x,float(y),places=12)
            lr=run('logrank',[r[:2] for r in rows if r[2]==1],[r[:2] for r in rows if r[2]==2])
            for key in ['chi2','df','p']:self.assertAlmostEqual(report['logrank'][key],float(lr[key]),places=12)
        with self.subTest(scenario='survival_multigroup_is_invariant_to_label_and_row_order'):
            rows=[[1,1,1],[2,0,1],[2,1,2],[4,1,2],[3,1,3],[5,0,3]]
            first=evaluate('survivalanalysis('+str(rows)+')')['survival']
            second=evaluate('survivalanalysis('+str([[t,e,4-g] for t,e,g in reversed(rows)])+')')['survival']
            self.assertEqual(first['logrank']['df'],2)
            self.assertGreater(first['logrank']['chi2'],0)
            self.assertAlmostEqual(first['logrank']['chi2'],second['logrank']['chi2'],places=12)
            self.assertAlmostEqual(first['logrank']['p'],second['logrank']['p'],places=12)
        with self.subTest(scenario='survival_censor_only_and_single_subject_groups_keep_curves'):
            report=evaluate('survivalanalysis([[1,0,1],[2,0,2]],1)')['survival']
            self.assertIn('error',report['logrank'])
            self.assertIn('error',report['cox'])
            for group in report['groups']:
                self.assertIsNone(group['median'])
                self.assertEqual(group['curve'][0][1],1)
                self.assertEqual(group['curve'][0][4:],[1,1,1])
            report=evaluate('survivalanalysis([[0,1,1],[2,0,2]])')['survival']
            self.assertEqual(report['groups'][0]['curve'][0],[0,1,1,0,0,0,0])
            self.assertEqual(report['groups'][0]['median'],0)


    def test_independent_reference_fixtures(self):
        fixtures=ROOT/'tests/fixtures/advanced_statistics_reference.json'
        if not fixtures.exists(): self.fail('Reference fixtures must be checked in')
        for case in json.loads(fixtures.read_text(encoding='utf-8')):
            with self.subTest(case=case['name']):
                value=run(case['function'],*case['arguments'])
                for path,expected in case['expected']:
                    actual=value
                    for key in path: actual=actual[key]
                    self.assertAlmostEqual(float(actual),expected,delta=case.get('tolerance',1e-6)*max(1,abs(expected)))


class BayesianStatisticsTests(unittest.TestCase):
    def test_bayesian_distributions_match_references_and_prior_moment_constraints(self):
        with self.subTest(scenario='independent_distribution_references'):
            fixtures = json.loads((ROOT/'tests/fixtures/bayesian_statistics_reference.json').read_text())
            for case in fixtures:
                with self.subTest(function=case['function'], arguments=case['arguments']):
                    result = run(case['function'], *case['arguments'])
                    for key, expected in case['expected'].items():
                        pairs = zip(result[key], expected) if isinstance(expected, list) else [(result[key], expected)]
                        for actual, reference in pairs:
                            self.assertTrue(math.isclose(float(actual), reference, rel_tol=case['tolerance'], abs_tol=1e-12), (key, actual, reference))
        with self.subTest(scenario='mean_prior_update_prediction_and_undefined_moments'):
            result = run('bayesmean', [1,3], 2, 2, 1, 1, .95, 2)
            for key, value in [('posterior mean',2), ('posterior kappa',4), ('posterior alpha',2), ('posterior beta',2), ('mean posterior t scale',.5), ('P(mean > threshold)',.5)]:
                self.assertEqual(float(result[key]), value)
            self.assertGreater(float(result['predictive interval'][1]-result['predictive interval'][0]), float(result['credible interval'][1]-result['credible interval'][0]))
            heavy = run('bayesmean', [1], 0, 1, .1, 1)
            self.assertEqual(heavy['posterior SD'], 'unavailable')
            self.assertEqual(heavy['posterior variance mean'], 'unavailable')
            constant = run('bayesmean', [3,3,3])
            self.assertLess(float(constant['credible interval'][0]), float(constant['posterior mean']))
            shifted = run('bayesmean', [101,103], 102, 2, 1, 1, .95, 102)
            self.assertAlmostEqual(float(shifted['credible interval'][0]-result['credible interval'][0]), 100)


if __name__ == "__main__": unittest.main()
