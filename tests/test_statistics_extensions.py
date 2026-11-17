"""Independent numerical references and contracts for expanded model designs."""
import json
import unittest
from test_advanced_statistics import ROOT, run, evaluate
from calc_shared import MathError


class StatisticsExtensionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=json.loads((ROOT/'tests/fixtures/statistics_extension_reference.json').read_text())['cases']

    def test_independent_references(self):
        for case in self.cases:
            with self.subTest(function=case['function'],options=case['arguments'][1:4]):
                result=run(case['function'],*case['arguments'])
                for path,expected in case['expected']:
                    actual=result
                    for key in path: actual=actual[key]
                    self.assertAlmostEqual(float(actual),float(expected),delta=case['tolerance']*max(1,abs(expected)),msg=str(path))

    def test_fiml_na_dispatch_empty_rows_and_complete_equivalence(self):
        case=next(c for c in self.cases if c['function']=='cfa' and c['arguments'][-1]=='fiml')
        rows,assignment=case['arguments'][:2]
        expression='cfa('+str(rows).replace("'NA'",'NA')+','+str(assignment)+',[],fiml)'
        result=evaluate(expression)
        self.assertIn('FIML',result['exact']); self.assertTrue(result['statisticsReport']['sections'])
        fit=run('cfa',rows,assignment,[],'fiml')
        empty=run('cfa',rows+[['NA']*6],assignment,[],'fiml')
        self.assertEqual(empty['Dropped empty rows'],1)
        self.assertAlmostEqual(float(fit['χ²']),float(empty['χ²']),places=7)
        complete=self.cases[0]['arguments'][0]
        cov=run('cfa',complete,assignment)
        fiml=run('cfa',complete,assignment,[],'fiml')
        self.assertAlmostEqual(float(cov['χ²']),float(fiml['χ²']),places=5)
        self.assertEqual(cov['df'],fiml['df'])

    def test_invalid_model_designs_and_missing_coverage(self):
        rows=self.cases[0]['arguments'][0]; assignment=[1,1,1,2,2,2]
        cases=[('efa',[rows,2,'unknown']),('efa',[rows,2,'none','wrong']),('efa',[rows,'parallel','none','pa',5]),
               ('cfa',[rows,assignment,[[1,2],[2,2],[3,2]]]),('cfa',[rows,assignment,[[2,2],[2,2]]]),
               ('cfa',[rows,assignment,[],'fiml',[1]*len(rows),'unknown']),
               ('cfa',[[r[:3]+['NA']*3 if i%2 else ['NA']*3+r[3:] for i,r in enumerate(rows)],assignment,[],'fiml']),
               ('manova',[rows,'repeated',4]),('manova',[[[1,1,2,3]]*10,'factorial',2,2])]
        for function,args in cases:
            with self.subTest(function=function,args=args[1:]):
                with self.assertRaises(MathError): run(function,*args)


if __name__=='__main__': unittest.main()
