"""Numerical references and public report contract for omnibus normality."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'app/src/main/python'))
sys.path.insert(0, str(ROOT/'tests'))
from test_advanced_statistics import evaluate, tree
from calc_engine import dispatch
from calc_statistics import _dagostino_pearson
from calc_shared import MathError
import sympy as s


class NormaltestTests(unittest.TestCase):
    def test_independent_references_and_report(self):
        cases = json.loads((ROOT/'tests/fixtures/normaltest_reference.json').read_text())['cases']
        for case in cases:
            with self.subTest(case=case['label']):
                result = evaluate('normaltest('+str(case['values'])+')')
                report = result['statisticsReport']
                self.assertEqual(report['analysis'], 'normaltest')
                self.assertEqual(report['title'], 'D’Agostino–Pearson')
                summary = next(v for v in report['sections'] if v['title']=='Summary')
                cells = {row[0]: float(row[1]['decimal']) for row in summary['rows']}
                for key, ref in [('K²','K2'), ('p value','p'), ('skewness z','skew_z'), ('kurtosis z','kurt_z')]:
                    self.assertAlmostEqual(cells[key], case[ref], delta=2e-10*max(1, abs(case[ref])))
                self.assertEqual(cells['df'], 2)
                self.assertEqual(cells['n'], len(case['values']))
                self.assertEqual([p['kind'] for p in report['plots']], ['qq','distribution'])
                self.assertEqual([v['label'] for v in report['highlights']], ['K²','p value','n'])
                self.assertEqual(bool(report.get('warnings')), len(case['values'])<=20)
                self.assertIn('K²:', result['exact'])

    def test_invalid_data_and_arity(self):
        for values in [[], list(range(7)), [1]*8, ['1']*8, [s.I]*8,
                       [0]*7+[s.nan], [0]*7+[s.oo], [0]*7+[s.Symbol('x')]]:
            with self.subTest(values=str(values)):
                with self.assertRaises(MathError): _dagostino_pearson(values)
        for source in ['normaltest()', 'normaltest(1)', 'normaltest([1,2,3,4,5,6,7,8],left)',
                       'normaltest([1,2,3,4,5,6,7,8],[1,2])']:
            result = json.loads(dispatch(json.dumps({'tree':tree(source)})))
            self.assertFalse(result['ok'], source)


if __name__ == '__main__': unittest.main()
