"""Inference guards, likelihood profiles and cluster-corrected reference checks."""
import json
import math
from pathlib import Path
import sys
import unittest
import mpmath as mp
import sympy as s

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app/src/main/python'))
from calc_advanced_statistics import advanced
from calc_advanced_common import inference,validated_covariance
from calc_evaluator import Engine
from calc_shared import MathError
from calc_statistics_report import statistics_report


def calculate(name,*args): return advanced(Engine({}),name,[s.sympify(arg) for arg in args])


class ModelDiagnosticsTests(unittest.TestCase):
    def test_covariance_rejects_invalid_matrices_and_repairs_only_roundoff(self):
        for matrix,message in [([[-.01,0],[0,1]],'negative variance'),([[1,.2],[.3,1]],'symmetric'),([[1,2],[2,1]],'semidefinite'),([[math.inf,0],[0,1]],'finite')]:
            with self.subTest(matrix=matrix),self.assertRaisesRegex(MathError,message): validated_covariance(matrix)
        corrected=validated_covariance([[-1e-14,0],[0,1]])
        self.assertEqual(corrected[0,0],0)
        rows=inference([1,2],corrected,['a','b'])
        self.assertIsNone(rows[0]['p']);self.assertIsNone(rows[0]['CI95'])
        singular=validated_covariance([[1,1+1e-12],[1+1e-12,1]])
        self.assertGreaterEqual(min(mp.eigsy(singular,eigvals_only=True)),-1e-14)
        for scale in (1e-20,1e20):
            with self.assertRaises(MathError): validated_covariance(mp.matrix([[1,2],[2,1]])*scale)
        held=inference([1,2],mp.eye(2),['a','b'],reliable=False)
        self.assertTrue(all(row['SE'] is None and row['p'] is None and row['CI95'] is None for row in held))

    def test_mixed_likelihood_profile_and_bootstrap_match_independent_references(self):
        fixture=json.loads((ROOT/'tests/fixtures/model_diagnostics_reference.json').read_text()); rows=fixture['mixed rows']
        for method in ('ml','reml'):
            result=calculate('mixedmodel',rows,0,method)
            likelihood='log likelihood' if method=='ml' else 'restricted log likelihood'
            self.assertAlmostEqual(float(result[likelihood]),fixture['mixed'][method]['log likelihood'],places=6)
            self.assertAlmostEqual(float(result['AIC']),-2*float(result[likelihood])+2*int(result['likelihood parameters']))
            self.assertAlmostEqual(float(result['BIC']),-2*float(result[likelihood])+math.log(len(rows))*int(result['likelihood parameters']))
            if method=='reml': self.assertTrue(any('identical fixed-effect' in warning for warning in result['diagnostics']['warnings']))
        for mode,settings in [('profile','profile'),('bootstrap',['bootstrap',100,7])]:
            result=calculate('mixedmodel',rows,0,'reml' if mode=='profile' else 'ml',settings)
            for row,expected in zip(result['coefficients'],fixture['mixed'][mode]):
                self.assertEqual(row['p'],'unavailable')
                for value,reference in zip(row['CI95'],expected): self.assertAlmostEqual(float(value),reference,delta=2e-5)
            report=statistics_report('mixedmodel',result,15)
            self.assertEqual(report['sections'][0]['title'],'Model diagnostics')

    def test_small_sample_gee_matches_statsmodels_bias_reduced_covariance_and_t(self):
        fixture=json.loads((ROOT/'tests/fixtures/model_diagnostics_reference.json').read_text())
        for case in fixture['gee']:
            with self.subTest(family=case['family'],corr=case['correlation']):
                result=calculate('gee',case['rows'],case['family'],case['correlation'],[],'small')
                self.assertEqual(result['covariance correction'],'Mancl-DeRouen');self.assertEqual(int(result['inference df']),len({r[0] for r in case['rows']})-2)
                for i,row in enumerate(result['coefficients']):
                    for key,expected_key in [('estimate','estimates'),('SE','SE'),('p','p')]:
                        self.assertAlmostEqual(float(row[key]),case[expected_key][i],delta=2e-5*max(1,abs(case[expected_key][i])))
                    for value,expected in zip(row['CI95'],case['CI95'][i]): self.assertAlmostEqual(float(value),expected,delta=2e-5*max(1,abs(expected)))


if __name__=='__main__': unittest.main()
