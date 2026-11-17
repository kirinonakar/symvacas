import json
from pathlib import Path
import unittest
from test_advanced_statistics import tree
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


    def test_overall_packed_columns_support_full_dataset_height_and_copy(self):
        columns=[['2']*5000,['0','1']*2500,list(map(str,range(5000)))]
        request={'tree':{'kind':'call','value':'stats','args':[{'kind':'symbol','value':'Data'},
                 {'kind':'symbol','value':'overall'},{'kind':'list','args':[{'kind':'number','value':str(flag)} for flag in (0,0,1)]}]},
                 'statisticsDatasets':{'Data':columns}}
        result=json.loads(dispatch(json.dumps(request)))
        self.assertTrue(result['ok'],result.get('error'))
        numeric,categorical=result['statisticsReport']['sections']
        self.assertEqual(int(numeric['rows'][0][-2]['decimal']),5000)
        self.assertEqual(int(numeric['rows'][0][-1]['decimal']),10000)
        self.assertEqual(categorical['totalRows'],5002)
        self.assertEqual(len(categorical['copyRows']),5002)
        self.assertEqual(categorical['rows'][0][-1],'2500 (50.00%)')
        request['statisticsDatasets']['Data'][0].append('2')
        result=json.loads(dispatch(json.dumps(request)))
        self.assertFalse(result['ok']);self.assertIn('Statistics dataset limit',result['error'])


if __name__=='__main__':unittest.main()
