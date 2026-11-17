"""Reference-backed ML invariance and portable ordinal WLSMV contracts."""
import json
import unittest
from test_advanced_statistics import ROOT, run
from calc_shared import MathError


class SEMEstimationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=json.loads((ROOT/'tests/fixtures/sem_estimation_reference.json').read_text())['cases']

    def test_independent_estimates_inference_and_fit_corrections(self):
        for case in self.cases:
            self.assertLessEqual(case['tolerance'],2e-6)
            with self.subTest(function=case['function'],options=case['arguments'][1:]):
                result=run(case['function'],*case['arguments'])
                diagnostics=result['diagnostics']
                self.assertEqual(diagnostics['Optimization convergence'],'Passed')
                self.assertEqual(diagnostics['Parameter identification'],'Passed')
                self.assertLess(float(diagnostics['Maximum absolute gradient']),2e-7)
                self.assertGreater(float(diagnostics['Minimum residual variance ratio']),1e-6)
                for path,expected in case['expected']:
                    actual=result
                    for key in path: actual=actual[key]
                    self.assertAlmostEqual(float(actual),expected,delta=case['tolerance']*max(1,abs(expected)),msg=str(path))


    def test_ordinal_groups_cross_loadings_and_category_codes(self):
        case=self.cases[0]; rows=case['arguments'][0]; p=len(rows[0]); ids=[1]*len(rows)+[2]*len(rows)
        fits={mode:run('cfa',rows+rows,[1]*p,[],'complete',ids,mode,'wlsmv') for mode in ('configural','metric','scalar','strict')}
        for mode,fit in fits.items():
            self.assertEqual(fit['Invariance'],mode)
            if mode in ('scalar','strict'):
                for i in range(len(fit['Thresholds'])//2): self.assertEqual(fit['Thresholds'][i]['estimate'],fit['Thresholds'][i+len(fit['Thresholds'])//2]['estimate'])
                self.assertAlmostEqual(float(fit['Latent means'][1]['Mean']),0,delta=1e-5)
        for i in range(p): self.assertEqual(fits['strict']['Residual variances'][i]['Variance'],1.)
        self.assertEqual(fits['strict']['df']-fits['scalar']['df'],p)
        recoded=[[[-10,2,7,99][v] for v in row] for row in rows]
        same=run('cfa',recoded,*case['arguments'][1:]); original=run('cfa',*case['arguments'])
        self.assertAlmostEqual(float(same['χ²']),float(original['χ²']),places=8)
        semcase=self.cases[2]; args=semcase['arguments'][:]; args[3]=[[2,2]]
        cross=run('sem',*args)
        self.assertEqual(len(cross['Loadings']),7)


    def test_invalid_ordinal_models_fail_with_actionable_errors(self):
        rows=self.cases[0]['arguments'][0]; binary=self.cases[1]['arguments'][0]; factors=[1]*4
        for data,missing,ids,mode,estimator in [(rows,'fiml',[],'configural','wlsmv'),
                 (rows,'complete',[],'configural','bad'),
                 (binary+binary,'complete',[1]*len(binary)+[2]*len(binary),'scalar','wlsmv'),
                 (rows+[[v+1 for v in r] for r in rows],'complete',[1]*len(rows)+[2]*len(rows),'strict','wlsmv')]:
            with self.subTest(missing=missing,invariance=mode,estimator=estimator):
                with self.assertRaises(MathError): run('cfa',data,factors,[],missing,ids,mode,estimator)


if __name__=='__main__': unittest.main()
