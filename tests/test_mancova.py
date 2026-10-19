"""MANCOVA reference accuracy, invalid designs and public report integration."""
import json
import unittest
from test_advanced_statistics import ROOT, run, tree
from calc_engine import dispatch
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

    def test_slope_check_can_be_skipped_or_unavailable(self):
        rows = [[1,0,1,4],[1,1,3,2],[2,0,3,5],[2,1,2,7],[2,2,6,3]]
        result = run('mancova', rows)
        self.assertEqual(result['Slope homogeneity']['status'], 'unavailable')
        self.assertNotIn('Slope homogeneity', run('mancova', rows, 1, .95, 0))

    def test_public_dispatch_reports_labels_intervals_and_reusable_answers(self):
        rows, c, level, _ = self.cases[0]['arguments']
        request = {'tree':tree(f'mancova({rows},{c},{level},1)'), 'precision':12,
                   'statisticsTermLabels':{'Group':'Treatment','group:1':'Control','group:2':'Low','group:3':'High','x1':'Age','response:1':'Score','response:2':'Speed'}}
        response = json.loads(dispatch(json.dumps(request)))
        self.assertTrue(response['ok'], response.get('error'))
        report = response['statisticsReport']
        self.assertEqual(report['title'], 'MANCOVA')
        sections = {section['title']:section for section in report['sections']}
        self.assertIn('Multivariate tests', sections)
        self.assertIn('Univariate follow-up tests', sections)
        self.assertIn('Adjusted means', sections)
        self.assertIn('Treatment', str(sections['Multivariate tests']))
        self.assertIn('Control', str(sections['Adjusted means']))
        self.assertIn('Score', str(sections['Adjusted means']))
        self.assertTrue(any(plot['kind']=='intervals' for plot in report['plots']))
        self.assertTrue(report['assumptions'])
        self.assertIn('Multivariate tests', response['exact'])


if __name__ == '__main__':
    unittest.main()
