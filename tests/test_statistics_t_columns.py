import json
from pathlib import Path
import unittest
import sympy as s
from test_advanced_statistics import tree
from calc_engine import dispatch
from calc_statistics import _sample_mean_variance


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


if __name__=='__main__':unittest.main()
