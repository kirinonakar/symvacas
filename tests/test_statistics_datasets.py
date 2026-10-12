"""Statistics UI-sized literal tables through the public evaluation boundary."""
import json
import pathlib
import sys
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'app/src/main/python'))
from calc_engine import dispatch, Engine
from calc_shared import MathError
import sympy as s

def number(value): return {'kind':'number','value':str(value)}
def listing(values): return {'kind':'list','args':values}
def table(rows): return listing([listing([number(cell) for cell in row]) for row in rows])
def call(name,*args): return {'kind':'call','value':name,'args':list(args)}
def symbol(name): return {'kind':'symbol','value':name}
def evaluate(tree,**options): return json.loads(dispatch(json.dumps({'tree':tree,'precision':15,**options})))

class StatisticsDatasetTests(unittest.TestCase):

    def test_numeric_lists_keep_exact_values_and_variable_references(self):
        values=listing([number('0.1'),{'kind':'unary','value':'-','args':[number('0.3')]},number('2e-1')])
        direct=evaluate(call('mean',values))
        stored=evaluate(call('mean',symbol('D1')),variables={'D1':values})
        self.assertEqual('0',direct['exact'])
        self.assertEqual(direct['resultAst'],stored['resultAst'])
        engine=Engine({})
        engine.prepare_statistics_dataset(values)
        self.assertEqual(s.Rational(-3,10),engine.build(values)[1])
        packed=evaluate(call('mean',symbol('Data')),statisticsDatasets={'Data':['0.1','-0.3','2e-1']})
        self.assertTrue(packed['ok'],packed)
        self.assertEqual(direct['resultAst'],packed['resultAst'])
        invalid=evaluate(call('mean',symbol('Data')),statisticsDatasets={'Data':['1','sin(x)']})
        self.assertFalse(invalid['ok'])

    def test_dataset_bounds_and_formula_complexity_are_separate(self):
        for rows in [[[1]]*5001,[[1]*102]]:
            result=evaluate(call('mixedmodel',table(rows)))
            self.assertFalse(result['ok'])
            self.assertIn('Statistics dataset limit',result['error'])
        # Expressions inside cells must not bypass the normal node budget.
        formula={'kind':'binary','value':'+','args':[number(1),number(2)]}
        result=evaluate(call('mean',listing([formula]*4500)))
        self.assertFalse(result['ok'])
        self.assertIn('Expression complexity limit',result['error'])
        # A normal matrix/list also keeps the expression limit.
        with self.assertRaisesRegex(MathError,'Expression complexity limit'):
            Engine({}).build(listing([number(1)]*12001))
        too_large=evaluate(call('mean',listing([number('1e100001')])))
        self.assertFalse(too_large['ok'])
        self.assertIn('Decimal exponent limit',too_large['error'])

    def test_packed_formula_cells_keep_exact_values_missing_semantics_and_complexity(self):
        formula={'kind':'binary','value':'/','args':[number(1),number(2)]}
        rows=[['1','2'] for _ in range(5000)];rows[2][1]=symbol('NA');rows[3][1]=formula
        engine=Engine({'statisticsDatasets':{'Data':rows}})
        computed=engine.build(call('impute',symbol('Data'),symbol('mean')))
        self.assertEqual(float(computed['data'][3][1]),.5)
        self.assertAlmostEqual(float(computed['data'][2][1]),(4998*2+.5)/4999,places=12)
        self.assertEqual(len(computed['data']),5000)
        result=evaluate(call('impute',symbol('Data'),symbol('mean')),statisticsDatasets={'Data':rows[:300]})
        self.assertTrue(result['ok'],result.get('error'))
        self.assertIn('0.5',result['exact'])
        bare=evaluate(symbol('Data'),statisticsDatasets={'Data':['0.1',formula]})
        self.assertTrue(bare['ok'],bare)
        self.assertEqual(bare['exact'],'[1/10, 1/2]')
        cycle=evaluate(call('mean',symbol('Data')),statisticsDatasets={'Data':[symbol('Data')]})
        self.assertFalse(cycle['ok']);self.assertIn('Cyclic statistics dataset',cycle['error'])
        complex=evaluate(call('mean',symbol('Data')),statisticsDatasets={'Data':[formula]*5000})
        self.assertFalse(complex['ok']);self.assertIn('Expression complexity limit',complex['error'])

if __name__=='__main__': unittest.main()
