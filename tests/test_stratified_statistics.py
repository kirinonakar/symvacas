import json
import unittest
from test_advanced_statistics import ROOT, run, evaluate
from calc_shared import MathError

ROWS = [[12,18,8,22],[20,15,10,25],[8,12,6,14]]


class StratifiedStatisticsTests(unittest.TestCase):
    def test_independent_statsmodels_references(self):
        fixture = json.loads((ROOT/'tests/fixtures/stratified_statistics_reference.json').read_text(encoding='utf-8'))
        for case in fixture['cases']:
            with self.subTest(function=case['function'],mode=case['arguments'][1],rows=case['arguments'][0]):
                result = run(case['function'],*case['arguments'])
                for key, expected in case['expected'].items():
                    if isinstance(expected,list):
                        for actual,value in zip(result[key],expected): self.assertAlmostEqual(float(actual),value,places=10)
                    else: self.assertAlmostEqual(float(result[key]),expected,places=10)

    def test_reordering_direction_and_confidence_level(self):
        for name in ('mantelhaenszel','breslowday'):
            original = run(name,ROWS)
            reverse = run(name,[[c,d,a,b] for a,b,c,d in ROWS[::-1]])
            self.assertAlmostEqual(float(original['χ²']),float(reverse['χ²']),places=12)
            self.assertAlmostEqual(float(original['Pooled odds ratio']*reverse['Pooled odds ratio']),1,places=12)
            wider = run(name,ROWS,'uncorrected',.99)['confidence interval']
            self.assertLess(wider[0],original['confidence interval'][0])
            self.assertGreater(wider[1],original['confidence interval'][1])

    def test_unit_odds_and_sparse_boundary_cells(self):
        rows = [[10,20,10,20],[15,15,15,15]]
        for mode in ('uncorrected','tarone'):
            result = run('breslowday',rows,mode)
            self.assertEqual(float(result['Pooled odds ratio']),1)
            self.assertAlmostEqual(float(result['χ²']),0,places=12)
            self.assertEqual(float(result['p value']),1)
        for rows,odds in [([[0,10,5,5]],0),([[10,0,0,10]],float('inf'))]:
            result = run('mantelhaenszel',rows)
            self.assertEqual(float(result['Pooled odds ratio']),odds)
            self.assertEqual(result['confidence interval'],'unavailable')
            with self.assertRaises(MathError): run('breslowday',rows*2)
        self.assertGreater(float(run('breslowday',[[0,10,5,5],[5,5,4,6]])['χ²']),0)

    def test_continuity_correction_does_not_inflate_tiny_deviation(self):
        rows = [[2,3,4,5]]  # |a−E(a)| = 1/7 < .5: do not apply correction.
        self.assertEqual(run('mantelhaenszel',rows)['χ²'],run('mantelhaenszel',rows,'corrected')['χ²'])

    def test_uninformative_strata_are_listed_and_do_not_change_the_test(self):
        rows=[[1,0,0,1],[1,1,0,0],[0,0,2,0]]
        result=run('mantelhaenszel',rows)
        self.assertEqual(result['Input observations'],6)
        self.assertEqual(result['n'],2)
        self.assertEqual(result['Excluded strata count'],2)
        self.assertEqual([row['Stratum'] for row in result['Excluded strata']],[2,3])
        self.assertEqual(result['χ²'],run('mantelhaenszel',rows[:1])['χ²'])
        with self.assertRaisesRegex(MathError,'at least two informative strata'):run('breslowday',rows)
        valid=run('breslowday',ROWS+rows[1:])
        self.assertEqual(valid['χ²'],run('breslowday',ROWS)['χ²'])

    def test_invalid_counts_margins_options_and_strata(self):
        for name in ('mantelhaenszel','breslowday'):
            for rows in ([],[[1,2,3]],[[1,2,3,4,5]],[[1,-1,2,3]],[[1,.5,2,3]],[[0,0,2,3]],[[0,1,0,2]],[[0,0,0,0]]):
                with self.subTest(name=name,rows=rows),self.assertRaises(MathError): run(name,rows)
            for args in ((ROWS,'invalid'),(ROWS,'uncorrected',1),(ROWS,'uncorrected',0)):
                with self.assertRaises(MathError): run(name,*args)
        with self.assertRaises(MathError): run('breslowday',ROWS[:1])

    def test_public_expression_reports_and_copy(self):
        for name,title in [('mantelhaenszel','Mantel–Haenszel test'),('breslowday','Breslow–Day test')]:
            result = evaluate(f'{name}({ROWS})')
            self.assertEqual(result['statisticsReport']['title'],title)
            self.assertEqual([v['label'] for v in result['statisticsReport']['highlights']],['χ²','df','p value','Pooled odds ratio'])
            self.assertIn('Pooled odds ratio',result['exact'])


if __name__ == '__main__': unittest.main()
