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
                if ',categorical)' in item['command'] or item.get('categorical'):self.assertEqual(metrics,['n','Category count'])
                else:self.assertIn('mean',metrics)
                self.assertTrue(report['notes'])

    def test_numeric_summary_threshold_counts_distinct_values_and_keeps_numeric_results(self):
        result=evaluate('stats([0,1,1])')
        self.assertNotIn('Category frequencies',result['exact'])
        self.assertFalse(any(row[0]=='mean' for section in result['statisticsReport']['sections'] for row in section['rows']))
        self.assertTrue(any(section['title']=='Category frequencies' for section in result['statisticsReport']['sections']))
        for count in (9,10,11):
            result=evaluate('stats(['+','.join(map(str,range(count)))+'])')
            tables=[section for section in result['statisticsReport']['sections'] if section['title']=='Category frequencies']
            self.assertEqual(bool(tables),count<10)
            self.assertTrue(any(row[0]=='mean' for section in result['statisticsReport']['sections'] for row in section['rows']))
        result=evaluate('stats(['+','.join(['0','1']*20)+'])')
        self.assertTrue(any(section['title']=='Category frequencies' for section in result['statisticsReport']['sections']))

    def test_overall_summarizes_all_columns_with_sample_sd_and_binary_categories(self):
        cases=json.loads((Path(__file__).parent/'fixtures/statistics_summary.json').read_text(encoding='utf8'))['overallCases']
        for item in cases:
            with self.subTest(source=item['source']):
                result=json.loads(dispatch(json.dumps({'tree':tree(item['command']),'statisticsTermLabels':item['labels'],'precision':20})))
                self.assertTrue(result['ok'],result.get('error'))
                report=result['statisticsReport']
                self.assertEqual(report['title'],'Overall')
                self.assertEqual([section['title'] for section in report['sections']],
                                 (['Numeric data'] if item['numeric'] else [])+(['Categorical data'] if item['categorical'] else []))
                for section in report['sections']:
                    self.assertTrue(section['literalColumns'])
                    if section['title']=='Numeric data':
                        self.assertEqual(section['columns'],['Column','mean','sd','min','max','valid.n'])
                        self.assertEqual(len(section['rows']),len(item['numeric']))
                        for actual,expected in zip(section['rows'],item['numeric']):
                            self.assertEqual(actual[0],expected[0])
                            for value,target in zip(actual[1:],expected[1:]):
                                if target is None:self.assertEqual(value,'undefined')
                                else:self.assertAlmostEqual(float(value['decimal']),target)
                    else:
                        self.assertEqual(section['columns'],['Column','Category','numb (%)'])
                        for actual,expected in zip(section['rows'],item['categorical']):
                            self.assertEqual(actual[0],expected[0]);self.assertEqual(actual[2],expected[2])
                            if isinstance(actual[1],dict):self.assertEqual(float(actual[1]['decimal']),float(expected[1]))
                            else:self.assertEqual(actual[1],expected[1])
                        self.assertEqual(len(section['rows']),len(item['categorical']))

    def test_binary_summary_handles_constant_columns_and_equivalent_numeric_values(self):
        for source in ('stats([0,0])','stats([1,1])','stats([0.0,1.0,1])','stats([0,-0,1])'):
            result=evaluate(source)
            self.assertNotIn('mean:',result['exact'])
            self.assertTrue(any(section['title']=='Category frequencies' for section in result['statisticsReport']['sections']))

    def test_overall_large_category_table_retains_copy_rows_and_rejects_invalid_contracts(self):
        result=evaluate('stats([['+','.join(map(str,range(150)))+']],overall,[1])')
        section=result['statisticsReport']['sections'][0]
        self.assertEqual(section['totalRows'],150);self.assertEqual(len(section['rows']),100)
        self.assertEqual(len(section['copyRows']),150)
        for source in ('stats([[]],overall,[0])','stats([[2,3]],overall,[])','stats([[2,3]],overall,[2])','stats([2,3],overall,[0,0])'):
            self.assertFalse(json.loads(dispatch(json.dumps({'tree':tree(source)})))['ok'])

    def test_overall_packed_columns_support_full_dataset_height_and_copy(self):
        columns=[['2']*5000,['0','1']*2500,list(map(str,range(5000)))]
        request={'tree':{'kind':'call','value':'stats','args':[{'kind':'symbol','value':'Data'},
                 {'kind':'symbol','value':'overall'},{'kind':'list','args':[{'kind':'number','value':str(flag)} for flag in (0,0,1)]}]},
                 'statisticsDatasets':{'Data':columns}}
        result=json.loads(dispatch(json.dumps(request)))
        self.assertTrue(result['ok'],result.get('error'))
        numeric,categorical=result['statisticsReport']['sections']
        self.assertEqual(int(numeric['rows'][0][-1]['decimal']),5000)
        self.assertEqual(categorical['totalRows'],5002)
        self.assertEqual(len(categorical['copyRows']),5002)
        self.assertEqual(categorical['rows'][0][-1],'2500 (50.00%)')
        request['statisticsDatasets']['Data'][0].append('2')
        result=json.loads(dispatch(json.dumps(request)))
        self.assertFalse(result['ok']);self.assertIn('Statistics dataset limit',result['error'])

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
