"""Independent numerical references and end-to-end research analysis reports."""
import json
import math
import unittest
from test_advanced_statistics import ROOT, run, evaluate, tree
from calc_engine import dispatch
from calc_shared import MathError

META=[[.2,.1],[.45,.15],[-.1,.12],[.6,.2],[.3,.11]]
MEASURE=[[9,2,5,8],[6,1,3,2],[8,4,6,8],[7,1,2,6],[10,5,6,9],[6,2,4,7]]


class ResearchStatisticsTests(unittest.TestCase):
    def test_independent_references(self):
        fixture=json.loads((ROOT/'tests/fixtures/research_statistics_reference.json').read_text(encoding='utf8'))
        for case in fixture['cases']:
            with self.subTest(function=case['function'],options=case['arguments'][1:]):
                result=run(case['function'],*case['arguments'])
                for path,expected in case['expected']:
                    actual=result
                    for key in path: actual=actual[key]
                    self.assertAlmostEqual(float(actual),expected,delta=case['tolerance']*max(1,abs(expected)),msg=str(path))

    def test_all_research_examples_are_public_functions_and_structured_reports(self):
        ids={'metaanalysis','icc','blandaltman','tost','tost2','tostpaired'}
        definitions=json.loads((ROOT/'app/src/main/assets/advanced_statistics.json').read_text(encoding='utf8'))
        for item in definitions:
            if item['id'] not in ids: continue
            with self.subTest(analysis=item['id']):
                report=evaluate(item['example'])['statisticsReport']
                self.assertEqual(report['analysis'],item['id']);self.assertTrue(report['sections']);self.assertTrue(report['plots']);self.assertTrue(report['assumptions'])
                if item['id'].startswith('tost'):
                    self.assertEqual(report['plots'][0]['thresholds'],[-.5,.5])

    def test_meta_homogeneity_units_hksj_and_degenerate_egger(self):
        homogeneous=run('metaanalysis',[[.3,.1],[.3,.2],[.3,.3]],'pm')
        self.assertEqual(float(homogeneous['τ²']),0);self.assertEqual(float(homogeneous['I² (%)']),0)
        ordinary=run('metaanalysis',META,'dl',.95,'z')
        adjusted=run('metaanalysis',META,'dl',.95,'hksj')
        self.assertGreater(float(adjusted['confidence interval'][1]-adjusted['confidence interval'][0]),float(ordinary['confidence interval'][1]-ordinary['confidence interval'][0]))
        for factor in (1e-6,1e6):
            scaled=run('metaanalysis',[[y*factor,se*factor] for y,se in META],'dl')
            self.assertAlmostEqual(float(scaled['estimate'])/factor,float(ordinary['estimate']),places=10)
            self.assertAlmostEqual(float(scaled['τ²'])/factor**2,float(ordinary['τ²']),places=10)
            self.assertAlmostEqual(float(scaled['Q']),float(ordinary['Q']),places=10)
        same_se=run('metaanalysis',[[.1,.2],[.3,.2],[.4,.2]])
        self.assertIn('Unavailable',same_se['Egger test']['Status'])
        small=run('metaanalysis',META[:2]);self.assertEqual(small['Prediction interval'],'unavailable')
        self.assertAlmostEqual(sum(float(row['Weight (%)']) for row in ordinary['Studies']),100,places=10)

    def test_icc_rater_shift_consistency_negative_and_boundary_cases(self):
        shifted=[[value+(30 if j==1 else 0) for j,value in enumerate(row)] for row in MEASURE]
        consistency=run('icc',MEASURE,'mixed');new=run('icc',shifted,'mixed')
        self.assertAlmostEqual(float(new['ICC']),float(consistency['ICC']),places=10)
        self.assertLess(float(run('icc',shifted,'random')['ICC']),float(run('icc',MEASURE,'random')['ICC']))
        self.assertLess(float(run('icc',[[1,4],[2,2],[4,1]],'oneway')['ICC']),0)
        perfect=run('icc',[[1,1],[2,2],[3,3]])
        self.assertEqual(float(perfect['ICC']),1);self.assertEqual(perfect['confidence interval'],'unavailable')
        wider=run('icc',MEASURE,'random','single',.99)['confidence interval'];regular=run('icc',MEASURE)['confidence interval']
        self.assertLess(float(wider[0]),float(regular[0]));self.assertGreater(float(wider[1]),float(regular[1]))

    def test_bland_altman_direction_units_all_points_and_log_ratios(self):
        data=[[10,10.5],[12,11.8],[8,8.6],[15,14.7]]
        normal=run('blandaltman',data);reverse=run('blandaltman',[row[::-1] for row in data])
        self.assertAlmostEqual(float(normal['Bias']),-float(reverse['Bias']))
        self.assertAlmostEqual(float(normal['Lower agreement limit']),-float(reverse['Upper agreement limit']))
        constant_ratio=run('blandaltman',[[2,1],[4,2],[8,4]],.95,'log')
        self.assertAlmostEqual(float(constant_ratio['Geometric mean ratio A/B']),2)
        self.assertAlmostEqual(float(constant_ratio['Ratio agreement limits'][0]),2)

    def test_tost_is_not_a_nonsignificant_difference_and_uses_90_percent_ci(self):
        wide=run('tost',[-3,-1,0,1,3],-.1,.1)
        self.assertEqual(float(wide['Difference from zero p']),1);self.assertEqual(wide['Equivalent'],'not established')
        narrow=run('tost',[-.03,-.01,0,.01,.03],-.1,.1)
        self.assertEqual(narrow['Equivalent'],'yes');self.assertAlmostEqual(float(narrow['confidence level']),.9)
        bounds=narrow['confidence interval'];self.assertGreater(float(bounds[0]),-.1);self.assertLess(float(bounds[1]),.1)
        translated=run('tost',[9.97,9.99,10,10.01,10.03],-.1,.1,10)
        self.assertAlmostEqual(float(translated['TOST p']),float(narrow['TOST p']),places=10)
        self.assertEqual(run('tost',[.1,.2,.3],-.1,.1)['Equivalent'],'not established')

    def test_large_meta_report_and_study_names_preserve_numeric_answer(self):
        data=[[.1+i*.001,.2+(i%3)*.01] for i in range(120)]
        request={'tree':tree('metaanalysis('+str(data)+',pm)'),'precision':20,'budget':30,
                 'statisticsTermLabels':{'study:1':'Study A'}}
        result=json.loads(dispatch(json.dumps(request)));self.assertTrue(result['ok'],result.get('error'))
        forest,funnel=result['statisticsReport']['plots']
        self.assertEqual(forest['rows'][0][0],'Study A');self.assertEqual(len(forest['rows']),121);self.assertEqual(len(funnel['points']),120)
        studies=next(section for section in result['statisticsReport']['sections'] if section['title']=='Studies')
        self.assertEqual(studies['rows'][0][0],'Study A');self.assertEqual(len(studies['copyRows']),120)

    def test_invalid_inputs_fail_instead_of_returning_misleading_inference(self):
        cases=[('metaanalysis',[[[.1,0],[.2,.1]]]),('metaanalysis',[[[.1,-.1],[.2,.1]]]),
               ('metaanalysis',[META,'fixed',.95,'hksj']),('metaanalysis',[META,'pm',1]),
               ('icc',[[[1,1],[1,1]]]),('icc',[MEASURE,'invalid']),
               ('blandaltman',[[[0,1],[2,2],[3,3]],.95,'log']),
               ('tost',[[1,2,3],1,-1]),('tost',[[1,1,1],-1,1]),('tost',[[1,2,3],-1,1,0,.5]),
               ('tostpaired',[[1,2,3],[1,2],-1,1]),('tost2',[[1,1],[1,1],-1,1])]
        for name,args in cases:
            with self.subTest(function=name,args=args),self.assertRaises(MathError):run(name,*args)


if __name__=='__main__': unittest.main()
