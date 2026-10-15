import json
from pathlib import Path
import unittest
from test_advanced_statistics import tree, evaluate
from calc_engine import dispatch


class ColumnTTestTests(unittest.TestCase):
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
