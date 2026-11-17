"""ANCOVA and GLM accuracy, domain validation and calculator integration."""
import json
import unittest
from test_advanced_statistics import ROOT, run

class AncovaGlmTests(unittest.TestCase):
    def test_independent_statsmodels_references(self):
        cases = json.loads((ROOT/'tests/fixtures/ancova_glm_reference.json').read_text())
        for case in cases:
            with self.subTest(case=case['name']):
                result = run(case['function'], *case['arguments'])
                for path, expected in case['expected']:
                    actual = result
                    for key in path: actual = actual[key]
                    self.assertAlmostEqual(float(actual), expected, delta=case['tolerance']*max(1, abs(expected)), msg=str(path))


    def test_glm_offsets_match_log_exposure_and_gaussian_is_ols(self):
        rows = [[0,2],[1,4],[2,3],[3,8],[4,7],[5,9]]
        gaussian = run('glm', rows)
        self.assertAlmostEqual(float(gaussian['coefficients'][1]['estimate']), 1.4, places=9)
        exposures = [1,2,3,1,2,3]
        import math
        log_offsets = [math.log(v) for v in exposures]
        first = run('glm', rows, 'poisson','log',1,exposures,'exposure')
        second = run('glm', rows, 'poisson','auto',1,log_offsets,'offset')
        self.assertAlmostEqual(float(first['deviance']),float(second['deviance']),places=10)
        self.assertEqual(first['df residual'],4)

if __name__=='__main__': unittest.main()
