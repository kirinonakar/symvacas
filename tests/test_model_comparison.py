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
from calc_model_comparison_validation import concordance,assignments,holm
from calc_shared import MathError
from calc_evaluator import Engine
from calc_statistics_report import statistics_report

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
    def test_shared_cv_bootstrap_is_reproducible_and_has_paired_intervals(self):
        rows=self.example('linear');a=self.run_model(rows,mode='crossvalidation',argument=3,samples=100);b=self.run_model(rows,mode='crossvalidation',argument=3,samples=100)
        self.assertEqual(a,b)
        reference=self.run_model(rows)
        self.assertEqual(a['ΔR² (B − A)'],reference['ΔR² (B − A)'])
        self.assertIn('ΔValidation R² (B − A)',a)
        self.assertTrue(all(row[2] is not None and row[3]>=row[2] and row[4] is None for row in a['Paired differences']))
        assigned=assignments([rows[0],rows[0],*rows[1:]],3,7,'linear',[0,0,*range(1,len(rows))]);self.assertEqual(assigned[0],assigned[1])
    def test_survival_concordance_matches_explicit_comparable_pairs_and_ties(self):
        rows=[[1,1],[1,0],[2,1],[2,1],[3,0]];scores=[3,3,2,2,1]
        numerator=denominator=0
        for i,left in enumerate(rows):
            for j,right in enumerate(rows):
                if left[1] and (left[0]<right[0] or left[0]==right[0] and not right[1]):
                    numerator+=int(scores[i]>scores[j])+.5*int(scores[i]==scores[j]);denominator+=1
        self.assertEqual(concordance(rows,scores),numerator/denominator)
        self.assertIsNone(concordance([[1,0],[2,0]],[1,2]))
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
    def test_ml_ridge_and_forest_emit_prediction_differences_without_fit_tests(self):
        for family in ('mlclassification','mlregression'):
            for algorithm in ('ridge','forest'):
                result=self.run_model(self.example(family),family,mode='holdout',argument=.3,options=[['algorithm',algorithm],['trees',10],['depth',3]])
                metrics=[row[0] for row in result['Paired differences']]
                self.assertEqual(metrics,['AUC','Accuracy','Log loss'] if family=='mlclassification' else ['RMSE','MAE','R²'])
                self.assertNotIn('p',result)
                if family=='mlregression':self.assertTrue(all(row[4] is None for row in result['Paired differences']))
                else:self.assertIsNotNone(result['Paired differences'][1][4])

    def test_logistic_preserves_paired_external_inference_and_calibration(self):
        reference=json.loads((ROOT/'tests/fixtures/logistic_comparison_reference.json').read_text(encoding='utf-8'))
        result=self.run_model(reference['train'],'logistic',mode='external',argument=reference['validation'])
        auc=result['Paired differences'][0]
        self.assertAlmostEqual(float(auc[4]),reference['delong'][3],places=10)
        self.assertEqual([row[5] for row in result['Paired differences']],['Paired DeLong','Exact McNemar + paired bootstrap CI','Paired bootstrap CI','Paired bootstrap CI'])
        self.assertEqual([result['Improved classifications'],result['Worsened classifications']],reference['mcnemar'][:2])
        self.assertEqual(len(result['Calibration curves']),2)
        cv=self.run_model(self.example('logistic'),'logistic',mode='crossvalidation',argument=3)
        self.assertTrue(all(row[4] is None for row in cv['Paired differences']))
        self.assertIn('DeLong',cv['Paired differences'][0][5]);self.assertIn('McNemar',cv['Paired differences'][1][5])
        self.assertEqual(result['Improved classifications']-result['Worsened classifications'],round(result['Paired differences'][1][1]*result['Validation performance'][0]['n']))
        report=statistics_report('modelcompare',result,10)
        paired=next(section for section in report['sections'] if section['title']=='Paired performance differences (B − A)')
        self.assertEqual([row[5] for row in paired['rows']],['Paired DeLong','Exact McNemar + paired bootstrap CI','Paired bootstrap CI','Paired bootstrap CI'])


    def test_invalid_roles_or_numeric_options_fail(self):
        rows=self.example('linear')
        with self.assertRaises(MathError):self.run_model(rows,count=2)
        with self.assertRaises(MathError):self.run_model(rows,mode='holdout',argument=1)
        with self.assertRaises(MathError):self.run_model(rows,samples=1)
        with self.assertRaises(MathError):self.run_model(rows,options=[['unknown',1]])

    def test_exact_linear_prediction_does_not_invent_f_inference_from_roundoff(self):
        rows=[[i,math.sin(i),1+2*i+3*math.sin(i)] for i in range(20)]
        result=self.run_model(rows)
        self.assertNotIn('F',result);self.assertNotIn('p',result)
        self.assertIsNone(result['Model fit'][1][3]);self.assertIn('numerical zero',result['Comparison inference'])

    def test_saved_variables_cannot_replace_family_or_option_metadata(self):
        from test_advanced_statistics import tree
        source='modelcompare('+str(self.example('logistic'))+',1,logistic,apparent,0,0.95,0,0,[[threshold,0.7]],0)'
        engine=Engine({'variables':{'logistic':tree('99'),'apparent':tree('99'),'threshold':tree('99')}})
        result=engine.build(tree(source))
        self.assertEqual(result['Analysis family'],'logistic');self.assertEqual(result['Validation method'],'apparent')
        self.assertTrue(result['Paired differences'])

if __name__=='__main__':unittest.main()
