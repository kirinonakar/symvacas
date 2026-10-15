"""Independent numerical references and end-to-end research analysis reports."""
import json
import math
import unittest
from test_advanced_statistics import ROOT, run
from calc_shared import MathError

META=[[.2,.1],[.45,.15],[-.1,.12],[.6,.2],[.3,.11]]
MEASURE=[[9,2,5,8],[6,1,3,2],[8,4,6,8],[7,1,2,6],[10,5,6,9],[6,2,4,7]]


class ResearchStatisticsTests(unittest.TestCase):
    def test_continuous_summary_effects_units_direction_and_invalid_sd_or_sizes(self):
        rows=[[12,3,50,10,2.5,48],[15,4,60,12,3.5,55],[9,2,40,8,2.2,42]]
        for measure in ('md','smd'):
            first=run('metaanalysis',rows,'pm',.95,'z',1,measure)
            reversed_=run('metaanalysis',[row[3:]+row[:3] for row in rows],'pm',.95,'z',1,measure)
            self.assertAlmostEqual(float(first['estimate']),-float(reversed_['estimate']),places=12)
            scaled=run('metaanalysis',[[m1*10,s1*10,n1,m2*10,s2*10,n2] for m1,s1,n1,m2,s2,n2 in rows],'pm',.95,'z',1,measure)
            self.assertAlmostEqual(float(scaled['estimate'])/(10 if measure=='md' else 1),float(first['estimate']),places=10)
            self.assertAlmostEqual(float(first['Studies'][0]['Mean difference']),2)
            self.assertAlmostEqual(float(first['Studies'][0]['SE (MD)']),math.sqrt(9/50+6.25/48))
        for bad in ([12,-3,50,10,2,48],[12,3,1,10,2,48],[12,3,50.5,10,2,48],[12,0,50,10,0,48]):
            with self.assertRaises(MathError):run('metaanalysis',[bad,rows[1]],'pm',.95,'z',1,'smd')
    def test_binary_counts_zero_correction_exclusions_and_group_direction(self):
        counts=[[12,100,20,100],[8,80,15,90],[25,150,40,160]]
        for measure in ('oddsratio','riskratio'):
            result=run('metaanalysis',counts,'pm',.95,'z',1,measure,.5)
            reversed_=run('metaanalysis',[row[2:]+row[:2] for row in counts],'pm',.95,'z',1,measure,.5)
            self.assertAlmostEqual(float(result['Pooled ratio'])*float(reversed_['Pooled ratio']),1,places=10)
            self.assertAlmostEqual(float(result['Studies'][0]['OR']),12*80/(88*20),places=10)
            self.assertAlmostEqual(float(result['Studies'][0]['RR']),.6,places=10)
            self.assertAlmostEqual(float(result['Studies'][0]['SE log(OR)']),math.sqrt(1/12+1/88+1/20+1/80),places=10)
        counts=[[0,20,0,20],[0,20,5,20],[3,30,6,30]]
        result=run('metaanalysis',counts,'fixed',.95,'z',1,'oddsratio',.5)
        self.assertEqual(int(result['Excluded study count']),1);self.assertEqual(int(result['Studies'][0]['Study']),2)
        self.assertEqual(result['Studies'][0]['Continuity corrected'],'yes')
        self.assertAlmostEqual(float(result['Studies'][0]['OR']),.5*15.5/(20.5*5.5))
        with self.assertRaises(MathError):run('metaanalysis',counts,'fixed',.95,'z',1,'oddsratio',0)
        for data in ([[21,20,5,20],[3,30,6,30]],[[1.5,20,5,20],[3,30,6,30]]):
            with self.assertRaises(MathError):run('metaanalysis',data,'fixed',.95,'z',1,'riskratio',.5)


    def test_independent_references(self):
        fixture=json.loads((ROOT/'tests/fixtures/research_statistics_reference.json').read_text(encoding='utf8'))
        for case in fixture['cases']:
            with self.subTest(function=case['function'],options=case['arguments'][1:]):
                result=run(case['function'],*case['arguments'])
                for path,expected in case['expected']:
                    actual=result
                    for key in path: actual=actual[key]
                    self.assertAlmostEqual(float(actual),expected,delta=case['tolerance']*max(1,abs(expected)),msg=str(path))


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
