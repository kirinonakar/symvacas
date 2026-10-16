"""Reference and unit/origin invariance regressions for Gaussian LMM inference."""
import json
import math
from pathlib import Path
import sys
import unittest
import sympy as s

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app/src/main/python'))
from calc_advanced_statistics import advanced
from calc_evaluator import Engine


def calculate(rows,slope=0,method='reml',ci='wald'):
    return advanced(Engine({}),'mixedmodel',[s.sympify(value) for value in (rows,slope,method,ci)])


class MixedSETests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=json.loads((ROOT/'tests/fixtures/mixed_se_reference.json').read_text())['cases']

    def test_fixed_effect_se_and_inference_match_dense_gls_references(self):
        for case in self.cases:
            with self.subTest(case=case['name']):
                result=calculate(case['rows'],case['slope'],case['method'])
                self.assertEqual(int(result['optimizer converged']),1)
                for index,row in enumerate(result['coefficients']):
                    for key,expected in [('estimate',case['estimates'][index]),('SE',case['SE'][index]),('p',case['p'][index])]:
                        self.assertAlmostEqual(float(row[key]),expected,delta=3e-6*max(abs(expected),1e-6))
                    for actual,expected in zip(row['CI95'],case['CI95'][index]):
                        self.assertAlmostEqual(float(actual),expected,delta=3e-6*max(abs(expected),1e-6))

    def test_large_origins_and_unit_changes_preserve_slopes_se_and_blups(self):
        for name in ('intercept reml','slope reml','unbalanced reml'):
            case=next(case for case in self.cases if case['name']==name)
            reference=calculate(case['rows'],case['slope'])
            # The small-outcome case previously failed the absolute RSS guard;
            # large offsets changed SE through catastrophic cancellation.
            for dx,dy,sx,sy in [(1e6,0,1,1),(0,1e6,1,1),(0,0,1e6,1),(0,0,1e-6,1e-6)]:
                with self.subTest(case=name,dx=dx,dy=dy,sx=sx,sy=sy):
                    rows=[[row[0],(row[1]+dx)*sx,*row[2:-1],(row[-1]+dy)*sy] for row in case['rows']]
                    result=calculate(rows,case['slope'])
                    self.assertEqual(result['singular fit'],reference['singular fit'])
                    for index in range(1,len(result['coefficients'])):
                        actual=result['coefficients'][index]; expected=reference['coefficients'][index]
                        factor=sy/(sx if index==1 else 1)
                        for key in ('estimate','SE'):
                            self.assertAlmostEqual(float(actual[key])/factor,float(expected[key]),delta=2e-7)
                        self.assertAlmostEqual(float(actual['p']),float(expected['p']),delta=2e-7)
                        for a,b in zip(actual['CI95'],expected['CI95']): self.assertAlmostEqual(float(a)/factor,float(b),delta=3e-7)
                    self.assertAlmostEqual(float(result['residual variance'])/sy**2,float(reference['residual variance']),delta=2e-7)
                    for actual,expected in zip(result['subject random effects (BLUP)'],reference['subject random effects (BLUP)']):
                        if case['slope']:
                            self.assertAlmostEqual(float(actual['x1'])*sx/sy,float(expected['x1']),delta=2e-7)
                            restored_intercept=float(actual['Intercept'])/sy+dx*float(actual['x1'])*sx/sy
                        else: restored_intercept=float(actual['Intercept'])/sy
                        self.assertAlmostEqual(restored_intercept,float(expected['Intercept']),delta=5e-7)
                    # REML's density changes by its response/design Jacobian.
                    p=len(reference['coefficients']); expected_shift=-(len(rows)-p)*math.log(sy)-math.log(sx)
                    self.assertAlmostEqual(float(result['restricted log likelihood']-reference['restricted log likelihood']),expected_shift,delta=2e-5)

    def test_profile_constraints_remain_in_original_coefficient_units(self):
        case=next(case for case in self.cases if case['name']=='intercept reml')
        reference=calculate(case['rows'],ci='profile')
        shifted=calculate([[g,(x+1e6)*1e3,y+1e6] for g,x,y in case['rows']],ci='profile')
        for a,b in zip(shifted['coefficients'][1]['CI95'],reference['coefficients'][1]['CI95']):
            self.assertAlmostEqual(float(a)*1e3,float(b),delta=2e-6)
        for result in (reference,shifted):
            self.assertTrue(all(row['p']=='unavailable' for row in result['coefficients']))
            self.assertTrue(all(len(row['CI95'])==2 for row in result['coefficients']))


if __name__=='__main__': unittest.main()
