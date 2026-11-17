"""Independent numerical references and inference/paired-validation contracts."""
import json
import math
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app/src/main/python'))
from calc_model_comparison import calculate,fit_comparison
from calc_model_comparison_validation import holm
from calc_evaluator import Engine

class ModelComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference=json.loads((ROOT/'tests/fixtures/model_comparison_reference.json').read_text(encoding='utf-8'))['cases']
        cls.schema=next(v for v in json.loads((ROOT/'app/src/main/assets/advanced_statistics.json').read_text(encoding='utf-8')) if v['id']=='modelcompare')
    def run_model(self,rows,family='linear',count=1,mode='apparent',argument=5,samples=0,options=None,scan=0):
        return calculate(SimpleNamespace(note=''),'modelcompare',[rows,count,family,mode,argument,.95,samples,4,options or [],scan])
    def example(self,family):return [[float(v) for v in row] for row in self.schema['exampleRowsByFamily'][family]]
    def test_independent_partial_f_count_cox_and_ml_mixed_references(self):
        for item in self.reference:
            with self.subTest(family=item['family']):
                result=self.run_model(item['rows'],item['family'],mode='fit' if item['family']=='lmm' else 'apparent')
                for key,expected in item['expected'].items():self.assertAlmostEqual(result[key],expected,delta=2e-5*max(1,abs(expected)))
    def test_candidates_keep_baseline_common_rows_and_holm_all_attempts(self):
        rows=[row[:2]+[math.sin(i),row[-1]] for i,row in enumerate(self.example('linear'))]
        result=self.run_model(rows,count=1,scan=1);records=result['Candidate comparisons'];self.assertEqual(len(records),2)
        for record,value in zip(records,holm([r['p'] for r in records])):self.assertEqual(record['Holm p'],value)
        self.assertTrue(all(r['Holm p']>=r['p'] for r in records))
    def test_boundary_random_structure_and_gee_do_not_receive_ordinary_lrt(self):
        a={'n':30,'p':2,'AIC':10.,'BIC':11.,'log likelihood':-2.,'singular fit':0};b=dict(a,p=3,AIC=9.,BIC=12.,**{'log likelihood':-1.})
        for family,first,second,same in [('lmm',a,b,False),('glmm',a,dict(b,**{'singular fit':1}),True),('nb',dict(a,**{'dispersion boundary':1}),b,True),('gee',a,b,True),('mlregression',a,b,True)]:
            test,reason=fit_comparison(first,second,family,1,2,same);self.assertNotIn('LRT χ²',test);self.assertNotIn('p',test);self.assertTrue(reason)
    def test_measurement_same_indicators_nested_ml_and_wlsmv_guard(self):
        rows=self.example('cfa');opts=[['factors',[1,1,1,2,2,2]],['addedresidual',[[2,5]]]]
        ml=self.run_model(rows,'cfa',count=0,mode='fit',options=opts)
        self.assertGreater(ml['Difference df'],0);self.assertIn('ΔCFI (B − A)',ml)
        fake={'n':len(rows),'χ²':10.,'df':8,'CFI':.95,'RMSEA':.04}
        with patch('calc_advanced_sem.fit',side_effect=[fake,dict(fake,**{'χ²':8.,'df':7})]):
            ordinal=self.run_model(rows,'cfa',count=0,mode='fit',options=opts+[['estimator','wlsmv']])
        self.assertNotIn('p',ordinal);self.assertNotIn('Difference χ²',ordinal)
        self.assertNotIn('Δχ² (B − A)',ordinal)

    def test_saved_variables_cannot_replace_family_or_option_metadata(self):
        from test_advanced_statistics import tree
        source='modelcompare('+str(self.example('logistic'))+',1,logistic,apparent,0,0.95,0,0,[[threshold,0.7]],0)'
        engine=Engine({'variables':{'logistic':tree('99'),'apparent':tree('99'),'threshold':tree('99')}})
        result=engine.build(tree(source))
        self.assertEqual(result['Analysis family'],'logistic');self.assertEqual(result['Validation method'],'apparent')
        self.assertTrue(result['Paired differences'])

if __name__=='__main__':unittest.main()
