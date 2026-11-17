"""Social-science numeric references, invalid models and report integration."""
import json
import unittest
from test_advanced_statistics import ROOT, run
from calc_shared import MathError

class SocialStatisticsTests(unittest.TestCase):
    def test_independent_references(self):
        fixture=json.loads((ROOT/'tests/fixtures/social_statistics_reference.json').read_text(encoding='utf8'))
        for case in fixture['cases']:
            with self.subTest(function=case['function'],options=case['arguments'][1:]):
                result=run(case['function'],*case['arguments'])
                for path,expected in case['expected']:
                    actual=result
                    for key in path: actual=actual[key]
                    self.assertAlmostEqual(float(actual),float(expected),delta=case['tolerance']*max(1,abs(expected)),msg=str(path))


    def test_invalid_models_do_not_return_finite_inference(self):
        cases=[('cronbach',[[[1,1],[1,1],[1,1]]]),
               ('efa',[[[1,2],[2,4],[3,6]],1]),
               ('cfa',[[[1,2,3],[2,3,4],[3,4,5],[4,5,6],[5,6,7]],[1,1,2]]),
               ('sem',[[[1,2,3,4,5,6]]*8,[1,1,1,2,2,2],[[1,2],[2,1]]]),
               ('manova',[[[1,1,2],[1,2,4],[2,3,6],[2,4,8]]]),
               ('mediation',[[[1,2,3]]*8,100]),
               ('moderation',[[[1,2,3]]*8]),
               ('phi',[[[1,2,3],[3,4,5]]]),
               ('dunn',[[[1,1],[1,1]]]),
               ('discriminantanalysis',[[[1,1],[2,1],[3,2],[4,2]],'qda','unknown']),
               ('quantreg',[[[1,2],[2,3],[3,4],[4,6]],1]),
               ('tobit',[[[1,0],[2,0],[3,0],[4,0]]]),
               ('tobit',[[[1,1],[2,2],[3,3],[4,4]],2,1]),
               ('zeroinflated',[[[1,1],[2,2],[3,3],[4,4]]]),
               ('hcluster',[[[1,2],[2,3],[3,4]],4])]
        for name,args in cases:
            with self.subTest(function=name):
                with self.assertRaises(MathError): run(name,*args)


if __name__=='__main__': unittest.main()
