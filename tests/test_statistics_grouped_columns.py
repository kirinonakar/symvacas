import json
from pathlib import Path
import unittest
from test_advanced_statistics import tree, evaluate
from calc_engine import dispatch


class GroupedColumnTests(unittest.TestCase):
    def test_grouped_tests_match_scipy_and_preserve_category_count_and_percent_differences(self):
        cases=json.loads((Path(__file__).parent/'fixtures/statistics_grouped_columns.json').read_text(encoding='utf8'))['cases']
        for item in cases:
            with self.subTest(name=item['name']):
                result=json.loads(dispatch(json.dumps({'tree':tree(item['command']),'statisticsTermLabels':item['labels'],'precision':20})))
                self.assertTrue(result['ok'],result.get('error'))
                report=result['statisticsReport'];summary=report['sections'][0]
                self.assertEqual(len(summary['rows']),len(item['expected']))
                for index,(row,expected) in enumerate(zip(summary['rows'],item['expected'])):
                    values=dict(zip(summary['columns'],row))
                    self.assertAlmostEqual(float(values['p-value']['decimal']),expected['p-value'],places=12)
                    self.assertEqual(int(values['n']['decimal']),expected['n'])
                    self.assertEqual(values['Significant'],'yes' if expected['p-value']<.05 else 'no')
                    if item.get('categorical'):
                        self.assertEqual(values['Column'],expected['column']);self.assertEqual(values['Category'],expected['category'])
                        for at,count in enumerate(expected['counts']):self.assertEqual(values[f"numb ({item['labels'][f'sample:{at+1}']}) (%)"],count)
                        self.assertEqual(values['diff (%)'],expected['diffs'][0])
                        self.assertTrue(all(column not in summary['columns'] for column in ['mean','mean1','mean2','sd','min','max','normality','equal var']))
                    else:
                        for at,mean in enumerate(expected['means']):self.assertAlmostEqual(float(values[f"mean ({item['labels'][f'sample:{at+1}']})"]['decimal']),mean,places=12)
                        for at,diff in enumerate(expected['diffs']):self.assertAlmostEqual(float(values['diff' if len(expected['diffs'])==1 else f'diff (1-{at+2})']['decimal']),diff,places=12)
                if item['settings']['op']=='chi2independence':
                    self.assertTrue(any('Fisher exact' in warning['text'] for warning in report['warnings']))
                    self.assertTrue(any(section['title']=='Expected-count diagnostics' for section in report['sections']))
                if item['settings']['op'] in ('anova','welchanova') or item['settings']['op']=='kruskal' and len(item['expected'][0]['means'])>2:
                    self.assertTrue(any('post-hoc' in section['title'] for section in report['sections']))


    def test_binary_zero_only_column_shows_the_event_count_without_fabricating_a_p_value(self):
        result=evaluate('fisherexact([[0,0,1,1]],[[0,0,0,0]],batch)')
        summary=result['statisticsReport']['sections'][0]
        self.assertNotIn('Category',summary['columns'])
        row=summary['rows'][0]
        self.assertEqual(row[1:4],['0 (0.00%)','0 (0.00%)','0 (0.00%)'])
        self.assertEqual(row[4],'undefined');self.assertEqual(row[-1],'unavailable')

    def test_each_batched_contingency_table_keeps_margins_row_and_column_percentages(self):
        item=next(item for item in json.loads((Path(__file__).parent/'fixtures/statistics_grouped_columns.json').read_text(encoding='utf8'))['cases'] if item['settings']['op']=='chi2independence')
        result=json.loads(dispatch(json.dumps({'tree':tree(item['command']),'statisticsTermLabels':item['labels']})))
        self.assertTrue(result['ok'],result.get('error'))
        sections={section['title']:section for section in result['statisticsReport']['sections']}
        row=sections['color (z) · Row percentages (%)'];column=sections['color (z) · Column percentages (%)']
        self.assertEqual(row['columns'],['Group','red','blue','Total'])
        self.assertEqual(row['totalRow'],2);self.assertEqual(column['totalRow'],2)
        self.assertAlmostEqual(float(row['rows'][0][1]['decimal']),200/3)
        self.assertAlmostEqual(float(row['rows'][1][1]['decimal']),50)
        self.assertAlmostEqual(float(column['rows'][0][1]['decimal']),50)
        self.assertAlmostEqual(float(column['rows'][0][2]['decimal']),100/3)
        self.assertEqual(float(row['rows'][0][-1]['decimal']),100)
        self.assertEqual(float(column['rows'][-1][1]['decimal']),100)
        grouped=[section for section in sections.values() if section.get('contingencyGroup')]
        self.assertEqual(len(grouped),8)
        self.assertTrue(all(not section['contingencyExpanded'] for section in grouped))
        single=evaluate('chi2independence([0,0,1,1],[0,1,0,1])')['statisticsReport']
        self.assertTrue(all(section['contingencyExpanded'] for section in single['sections'] if section.get('contingencyGroup')))
        batch_single=evaluate('chi2independence([[0,0,1,1]],[[0,1,0,1]],batch,1)')['statisticsReport']
        self.assertTrue(all(section['contingencyExpanded'] for section in batch_single['sections'] if section.get('contingencyGroup')))


if __name__=='__main__':unittest.main()
