"""Independent numerical references and contracts for the six research extensions."""
import json
import unittest
from test_advanced_statistics import ROOT, run
from calc_shared import MathError

IDS=set('omega bayesttest bayesanova metaregression metasubgroup designpower designsize yuen trimmedanova winsorcor robustreg parametricsurvival'.split())


class PriorityStatisticsTests(unittest.TestCase):
    def test_independent_numerical_references(self):
        fixture=json.loads((ROOT/'tests/fixtures/priority_statistics_reference.json').read_text(encoding='utf8'))
        for case in fixture['cases']:
            with self.subTest(function=case['function'],options=case['arguments'][1:]):
                result=run(case['function'],*case['arguments'])
                for path,expected in case['expected']:
                    actual=result
                    for key in path:actual=actual[key]
                    self.assertAlmostEqual(float(actual),expected,delta=case['tolerance']*max(1,abs(expected)),msg=str(path))


    def test_survival_predictions_units_censoring_and_entry_validation(self):
        data=[[1,1],[2,0],[3,1],[4,1],[6,0],[7,1]]
        first=run('parametricsurvival',data,'exponential',.95,-1,5)
        # Intercept-only exponential ML rate = events / total exposure.
        expected=sum(row[0] for row in data)/sum(row[1] for row in data)
        self.assertAlmostEqual(float(first['Predicted survival times'][0]['Predicted mean time']),expected,places=8)
        scaled=run('parametricsurvival',[[t*10,e] for t,e in data],'exponential',.95,-1,50)
        self.assertAlmostEqual(float(first['Predicted survival times'][0]['Survival at prediction time']),float(scaled['Predicted survival times'][0]['Survival at prediction time']),places=9)
        for invalid in ([[0,1],[2,1],[3,1],[4,1]],[[1,0],[2,0],[3,0],[4,0]],[[1,1,1],[2,1,2],[3,1,3],[4,1,4]]):
            with self.assertRaises(MathError):run('parametricsurvival',invalid,'weibull',.95,2 if len(invalid[0])==3 else -1)


if __name__=='__main__':unittest.main()
