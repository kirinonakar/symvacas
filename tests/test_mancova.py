"""MANCOVA reference accuracy, invalid designs and public report integration."""
import json
import unittest
from test_advanced_statistics import ROOT, run
from calc_shared import MathError


class MancovaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads((ROOT/'tests/fixtures/mancova_reference.json').read_text())['cases']

    def test_independent_statsmodels_references(self):
        for case in self.cases:
            result = run('mancova', *case['arguments'])
            for path, expected in case['expected']:
                actual = result
                for key in path: actual = actual[key]
                self.assertAlmostEqual(float(actual), expected, delta=case['tolerance']*max(1, abs(expected)), msg=f'{case["name"]}: {path}')

    def test_covariate_and_response_scale_invariance(self):
        rows, c, level, _ = self.cases[1]['arguments']
        baseline = run('mancova', rows, c, level, 0)
        shifted = [[r[0], r[1]*100+1e5, r[2]*.01-900, r[3]*1e4, r[4]*.001, r[5]*-2] for r in rows]
        result = run('mancova', shifted, c, level, 0)
        for first, second in zip(baseline['Multivariate tests'], result['Multivariate tests']):
            for key in ('Statistic','F','p'):
                self.assertAlmostEqual(float(first[key]), float(second[key]), delta=2e-7*max(1, abs(float(first[key]))))

    def test_invalid_designs_raise_math_error(self):
        rows, c, _, _ = self.cases[0]['arguments']
        invalid = [([r[:-1] for r in rows], 1), (rows, 0), (rows, 2),
                   ([[1]+r[1:] for r in rows], c),
                   ([[r[0], 1]+r[2:] for r in rows], c),
                   ([[r[0], r[0]]+r[2:] for r in rows], c),
                   ([[r[0], r[1], r[2], 2*r[2]] for r in rows], c),
                   (rows[:4], c), (rows, c, 1), (rows, c, .95, 2)]
        for args in invalid:
            with self.subTest(args=args):
                with self.assertRaises(MathError): run('mancova', *args)


if __name__ == '__main__':
    unittest.main()
