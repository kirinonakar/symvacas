import json
from pathlib import Path
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import sympy as s
from test_advanced_statistics import tree, evaluate
from calc_engine import dispatch
from calc_statistics import _sample_mean_variance
from calc_advanced_common import variance
from calc_advanced_inference import calculate


class ColumnTTestTests(unittest.TestCase):
    def test_sample_moments_preserve_exact_small_spreads_and_approximate_inputs(self):
        for offset, scale in [(s.Integer(0),s.Integer(1)), (s.Integer(10)**100,s.Rational(1,10)**100),
                              (-s.Integer(10)**100,s.Rational(1,7)), (s.sqrt(2),s.Integer(1))]:
            with self.subTest(offset=offset,scale=scale):
                mean, sample_variance, n = _sample_mean_variance([offset+k*scale for k in (0,1,4)])
                self.assertEqual(n,3)
                self.assertEqual(s.simplify(mean-offset-s.Rational(5,3)*scale),0)
                self.assertEqual(s.simplify(sample_variance-s.Rational(13,3)*scale**2),0)
        values = [s.Float('1e30',80)+s.Rational(k,1000) for k in (0,1,4)]
        _, sample_variance, _ = _sample_mean_variance(values)
        self.assertLess(abs(sample_variance-s.Rational(13,3000000)),s.Float('1e-50'))

    def test_companion_estimators_do_not_repeat_group_reductions_per_observation(self):
        class CountedSample(list):
            passes = 0
            def __iter__(self):
                self.passes += 1
                return super().__iter__()
        sample = CountedSample(range(1000))
        self.assertAlmostEqual(variance(sample),1000*1001/12)
        self.assertLessEqual(sample.passes,3)
        samples = [[s.Integer(i%17) for i in range(300)], [s.Integer(i%23) for i in range(400)]]
        import calc_advanced_inference as inference
        with patch.object(inference.statistics,'median',wraps=inference.statistics.median) as median, \
                patch.object(inference,'mean',wraps=inference.mean) as mean:
            result = calculate(SimpleNamespace(note=''),'levene',samples)
        self.assertTrue(0<=result['p']<=1)
        self.assertLessEqual(median.call_count,len(samples))
        self.assertLessEqual(mean.call_count,len(samples)+1)

    def test_grouped_columns_match_independent_scipy_references_and_actual_group_labels(self):
        cases=json.loads((Path(__file__).parent/'fixtures/statistics_t_columns.json').read_text(encoding='utf8'))['cases']
        for item in cases:
            with self.subTest(item=item['name']):
                result=json.loads(dispatch(json.dumps({'tree':tree(item['command']),'statisticsTermLabels':item['labels'],'precision':20})))
                self.assertTrue(result['ok'],result.get('error'))
                report=result['statisticsReport']; summary=report['sections'][0]
                self.assertEqual(summary['columns'],['Column',f"mean ({item['labels']['sample:1']})",f"mean ({item['labels']['sample:2']})",'diff','p-value','n','Significant','normality','equal var'])
                self.assertTrue(summary['literalColumns'])
                self.assertEqual(report['context'],f"diff = mean ({item['labels']['sample:1']}) − mean ({item['labels']['sample:2']}).")
                self.assertEqual(len(summary['rows']),len(item['expected']))
                for index,(row,expected) in enumerate(zip(summary['rows'],item['expected'])):
                    self.assertEqual(row[0],item['labels'][f'batch:column:{index}'])
                    for column,value in zip(['mean1','mean2','diff','p-value','n','Significant','normality','equal var'],row[1:]):
                        if isinstance(expected[column],str):self.assertEqual(value,expected[column])
                        else:self.assertAlmostEqual(float(value['decimal']),expected[column],places=12)
                self.assertEqual(report['plots'],[])
                self.assertTrue(any(section['title']=='Detailed assumption checks' for section in report['sections']))

    def test_small_or_constant_columns_remain_visible_without_false_yes_no_classification(self):
        result=evaluate('ttest2(0,[[2],[4,4,4],[1,2,3]],[[5],[5,5,5],[4,5,6]],batch)')
        rows=result['statisticsReport']['sections'][0]['rows']
        self.assertEqual(len(rows),3)
        self.assertEqual(rows[0][4],'undefined');self.assertEqual(rows[0][6:9],['unavailable','unavailable','unavailable'])
        self.assertEqual(rows[1][4],'undefined');self.assertEqual(rows[1][6:9],['unavailable','unavailable','unavailable'])
        self.assertNotEqual(rows[2][4],'undefined')
        self.assertTrue(result['statisticsReport']['details'])


if __name__=='__main__':unittest.main()
