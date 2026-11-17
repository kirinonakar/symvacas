"""Independent conjugate/Laplace references and full-posterior NUTS checks."""
import json
import math
import random
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app/src/main/python'))
import symvacas_catalog as catalog
from calc_shared import MathError
from calc_nuts import sample, diagnostics, _leapfrog, _build_tree, _joint

REFERENCE = json.loads((ROOT/'tests/fixtures/bayesian_regression_reference.json').read_text())

class BayesianRegressionTests(unittest.TestCase):
    def test_conjugate_and_laplace_match_independent_references(self):
        for mode,key in [('bayeslinear','linear'),('bayeslogistic','laplace')]:
            result = catalog.regression_report(REFERENCE['rows'],mode,REFERENCE['options'])
            for actual,expected in zip(result['coefficients'],REFERENCE[key]):
                for field,value in expected.items():
                    self.assertAlmostEqual(float(actual[field]),value,places=9)
                self.assertNotIn('p',actual)
                self.assertNotIn('se',actual)
            self.assertIsNone(result['df'])
            self.assertNotIn('aic',result)
            self.assertNotIn('likelihoodP',result)
            if mode == 'bayeslinear':
                for row in result['residuals']:
                    self.assertLess(float(row['predictiveLow']),float(row['fitted']))
                    self.assertGreater(float(row['predictiveHigh']),float(row['fitted']))
            else:
                self.assertEqual(float(result['auc']),1)
                for c in result['coefficients']:
                    self.assertAlmostEqual(float(c['oddsLow']),math.exp(float(c['low'])))

    def test_nuts_matches_exact_linear_and_quadrature_logistic_posteriors(self):
        with self.subTest(scenario='nuts_matches_exact_linear_and_quadrature_logistic_posteriors'):
            for mode,key in [('bayeslinear','linear'),('bayeslogistic','logisticQuadrature')]:
                options = [2.5,.95]+([2,1] if mode == 'bayeslinear' else [])+[['nuts',2000,600,8,7,4]]
                result = catalog.regression_report(REFERENCE['rows'],mode,options)
                self.assertEqual(result['method'],'nuts')
                self.assertEqual(result['nuts']['totalSamples'],8000)
                self.assertEqual(len(result['nuts']['chainDiagnostics']),4)
                self.assertEqual(result['nuts']['divergences'],0)
                for actual,expected in zip(result['coefficients'],REFERENCE[key]):
                    self.assertLess(abs(float(actual['estimate'])-expected['estimate']),5*float(actual['mcse'])+.015)
                    self.assertLess(abs(float(actual['posteriorSD'])-expected['posteriorSD']),.08*expected['posteriorSD'])
                    self.assertLess(abs(float(actual['probabilityPositive'])-expected['probabilityPositive']),.035)
                    self.assertLess(float(actual['rHat']),1.05)
                    self.assertGreater(float(actual['ess']),100)
                    for bound in (field for field in ('low','high') if field in expected):
                        self.assertLess(abs(float(actual[bound])-expected[bound]),.2*expected['posteriorSD'])
                if mode == 'bayeslogistic':
                    # The separated posterior is asymmetric; NUTS must not merely
                    # resample the Gaussian Laplace approximation.
                    self.assertGreater(float(result['coefficients'][1]['estimate']),REFERENCE['laplace'][1]['estimate']+.3)
        with self.subTest(scenario='sampler_reproduces_seed_and_preserves_gaussian_target'):
            target = lambda q: (sum(v*v for v in q)/2,list(q))
            chains,summary = sample(target,2,1000,300,8,19,2)
            again,repeat = sample(target,2,1000,300,8,19,2)
            self.assertEqual(chains,again); self.assertEqual(summary,repeat)
            self.assertEqual([len(c) for c in chains],[1000,1000])
            for j in range(2):
                values = [row[j] for chain in chains for row in chain]
                self.assertLess(abs(sum(values)/len(values)),.1)
                self.assertAlmostEqual(sum(v*v for v in values)/len(values),1,delta=.12)
            self.assertEqual(diagnostics([[1.]*100,[1.]*100]),(None,0.0))

    def test_nuts_trajectory_limits_divergences_and_workload_failure(self):
        target = lambda q: (sum(v*v for v in q)/2,list(q))
        state = ([.3,-.7],[1.2,.4],.29,[.3,-.7])
        forward = _leapfrog(target,state,.2)
        backward = _leapfrog(target,forward,-.2)
        for actual,expected in zip(backward[0]+backward[1],state[0]+state[1]):
            self.assertAlmostEqual(actual,expected,places=14)
        tree = _build_tree(target,state,_joint(state)-1,1,4,1e200,_joint(state),random.Random(0))
        self.assertEqual(tree[3],0);self.assertFalse(tree[4]);self.assertTrue(tree[7])
        self.assertEqual(tree[6],1,'stop expanding immediately after numerical failure')
        draws,limited = sample(target,2,300,100,1,19,2)
        self.assertGreater(limited['maxTreeDepthHits'],0)
        self.assertEqual(limited['meanLeapfrogSteps'],1)
        _,adaptive = sample(target,2,300,100,8,19,2)
        self.assertGreater(adaptive['meanLeapfrogSteps'],1)
        self.assertLess(adaptive['meanLeapfrogSteps'],255)
        self.assertEqual(adaptive['maxTreeDepthHits'],0)
        self.assertTrue(all(math.isfinite(v) for chain in draws for row in chain for v in row))
        with self.assertRaisesRegex(MathError,'workload'):
            sample(target,2,100,50,8,19,2,max_evaluations=20)
        report = catalog.regression_report(REFERENCE['rows'],'bayeslinear',[2.5,.95,2,1,['nuts',100,50,1]])
        self.assertTrue(any('max tree depth' in warning for warning in report['warnings']))

if __name__ == '__main__': unittest.main()
