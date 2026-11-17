"""Independent numerical references and end-to-end research analysis reports."""
import json
import unittest
from test_advanced_statistics import ROOT, run
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
