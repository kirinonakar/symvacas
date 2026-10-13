import json
from pathlib import Path
import unittest
from unittest.mock import patch
from test_advanced_statistics import tree, evaluate
from calc_engine import dispatch


class StatisticsSummaryTests(unittest.TestCase):
    def test_shared_summary_plans_report_counts_and_nonmissing_percentages(self):
        cases=json.loads((Path(__file__).parent/'fixtures/statistics_summary.json').read_text(encoding='utf8'))['cases']
        for item in cases:
            with self.subTest(source=item['source'],column=item['column']):
                result=json.loads(dispatch(json.dumps({'tree':tree(item['command']),'statisticsTermLabels':item['labels'],'precision':20})))
                self.assertTrue(result['ok'],result.get('error'))
                report=result['statisticsReport']
                section=next(section for section in report['sections'] if section['title']=='Category frequencies')
                rows=section['rows'][:-1]
                labels=[row[0] if isinstance(row[0],str) else row[0]['decimal'] for row in rows]
                for actual,expected in zip(labels,item['categories']):
                    if ',categorical)' in item['command']:self.assertEqual(actual,expected)
                    else:self.assertAlmostEqual(float(actual),float(expected))
                self.assertEqual(len(rows),len(item['categories']))
                self.assertEqual([int(row[1]['decimal']) for row in rows],item['counts'])
                for row,percent in zip(rows,item['percentages']):self.assertAlmostEqual(float(row[2]['decimal']),percent)
                self.assertEqual(int(section['rows'][-1][1]['decimal']),sum(item['counts']))
                self.assertEqual(float(section['rows'][-1][2]['decimal']),100)
                self.assertEqual(section['totalRow'],len(rows))
                summary=next(section for section in report['sections'] if section['title']=='Summary')
                metrics=[row[0] for row in summary['rows']]
                if ',categorical)' in item['command']:self.assertEqual(metrics,['n','Category count'])
                else:self.assertIn('mean',metrics)
                self.assertTrue(report['notes'])

    def test_numeric_summary_threshold_counts_distinct_values_and_keeps_numeric_results(self):
        result=evaluate('stats([0,1,1])')
        self.assertNotIn('Category frequencies',result['exact'])
        self.assertTrue(any(row[0]=='mean' for section in result['statisticsReport']['sections'] for row in section['rows']))
        for count in (9,10,11):
            result=evaluate('stats(['+','.join(map(str,range(count)))+'])')
            tables=[section for section in result['statisticsReport']['sections'] if section['title']=='Category frequencies']
            self.assertEqual(bool(tables),count<10)
            self.assertTrue(any(row[0]=='mean' for section in result['statisticsReport']['sections'] for row in section['rows']))
        result=evaluate('stats(['+','.join(['0','1']*20)+'])')
        self.assertTrue(any(section['title']=='Category frequencies' for section in result['statisticsReport']['sections']))

    def test_large_explicit_category_tables_copy_all_rows(self):
        result=evaluate('stats(['+','.join(map(str,range(150)))+'],categorical)')
        section=next(section for section in result['statisticsReport']['sections'] if section['title']=='Category frequencies')
        self.assertEqual(section['totalRows'],151)
        self.assertEqual(len(section['rows']),100)
        self.assertEqual(len(section['copyRows']),151)

    def test_numeric_columns_with_ten_distinct_values_skip_category_frequency_computation(self):
        with patch('calc_evaluator.summary_frequencies',side_effect=AssertionError('Category frequencies should not be calculated')) as frequency:
            result=evaluate('stats(['+','.join(map(str,range(10)))+'])')
            frequency.assert_not_called()
        self.assertFalse(any(section['title']=='Category frequencies' for section in result['statisticsReport']['sections']))

    def test_category_summary_rejects_empty_data_and_unknown_options(self):
        for source in ('stats([],categorical)','stats([0,1],other)'):
            result=json.loads(dispatch(json.dumps({'tree':tree(source)})))
            self.assertFalse(result['ok'])


if __name__=='__main__':unittest.main()
