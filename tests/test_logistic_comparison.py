"""Paired validation, refitted CV, numerical guards and public report regression tests."""
import json
import math
import random
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app/src/main/python'))
from calc_logistic_comparison import calculate, fit_mle, predict, delong, placements, folds_for, metrics
from calc_evaluator import Engine
from calc_shared import MathError
from test_advanced_statistics import evaluate

REFERENCE=json.loads((ROOT/'tests/fixtures/logistic_comparison_reference.json').read_text())
TRAIN=REFERENCE['train'];VALIDATION=REFERENCE['validation']

class LogisticComparisonTests(unittest.TestCase):
    def result(self,mode='external',argument=None,resamples=0,seed=7):
        return calculate(Engine({}),'logisticcompare',[TRAIN,1,mode,VALIDATION if argument is None else argument,.5,.95,resamples,seed])

    def test_independent_reference_fit_paired_delong_mcnemar_and_calibration(self):
        r=self.result();ref=REFERENCE
        for got,expected in zip(r['Training models'],ref['training']):
            for a,b in zip(got[3:],expected):self.assertAlmostEqual(a,b,places=8)
        for got,expected in zip(r['Validation models'],ref['performance']):
            for a,b in zip(got[2:],expected):self.assertAlmostEqual(a,b,places=8)
        self.assertAlmostEqual(r['LRT χ²'],ref['lrt'][0],places=8)
        self.assertAlmostEqual(float(r['LRT p']),ref['lrt'][1],places=10)
        self.assertEqual(r['LRT df'],1)
        auc=r['Paired differences'][0]
        for a,b in zip(auc[1:5],[ref['delong'][0],*ref['delong'][2],ref['delong'][3]]):self.assertAlmostEqual(float(a),b,places=10)
        self.assertEqual([r['Improved classifications'],r['Worsened classifications']],ref['mcnemar'][:2])
        self.assertAlmostEqual(float(r['Paired differences'][1][4]),ref['mcnemar'][2],places=12)

    def test_tied_scores_and_degenerate_variance(self):
        target=[0,0,0,1,1,1];a=[0,1,2,1,2,3];b=[0,2,3,1,2,3]
        def brute(scores):
            pos=[z for y,z in zip(target,scores) if y];neg=[z for y,z in zip(target,scores) if not y]
            pair=lambda p,n:float(p>n)+.5*(p==n)
            x=[sum(pair(p,n) for n in neg)/len(neg) for p in pos]
            y=[sum(pair(p,n) for p in pos)/len(pos) for n in neg]
            return sum(x)/len(x),x,y
        for scores in (a,b):
            actual=placements(target,scores);expected=brute(scores)
            for u,v in zip([actual[0],*actual[1],*actual[2]],[expected[0],*expected[1],*expected[2]]):self.assertAlmostEqual(u,v,places=14)
        d=delong(target,a,b);x=[v-u for u,v in zip(brute(a)[1],brute(b)[1])];y=[v-u for u,v in zip(brute(a)[2],brute(b)[2])]
        variance=lambda v:sum((z-sum(v)/len(v))**2 for z in v)/(len(v)-1)/len(v)
        self.assertAlmostEqual(d['variance'],variance(x)+variance(y),places=14)
        self.assertEqual(delong(target,a,a)['interval'],[0,0])
        self.assertEqual(delong(target,a,a)['p'],1)
        self.assertIsNone(delong([0,0,1,1],[1,1,0,0],[0,0,1,1])['p'])
        self.assertIsNone(delong([0,1],[0,1],[1,0])['interval'])

    def test_cv_refits_are_reproducible_and_duplicate_identities_never_cross_folds(self):
        r=self.result('crossvalidation',3,100);again=self.result('crossvalidation',3,100)
        self.assertEqual(r,again)
        self.assertEqual(r['Training models'][0][1],len(TRAIN))
        for metric,estimate,lo,hi,p,method in r['Paired differences']:
            self.assertLessEqual(lo,hi);self.assertTrue(math.isfinite(estimate));self.assertIsNone(p)
            self.assertEqual(method,'Refitted CV bootstrap CI')
        ids=list(range(len(TRAIN)))+[0,1,4,0]
        assignment=folds_for(TRAIN+[TRAIN[i] for i in [0,1,4,0]],3,7,ids)
        for at,identity in enumerate(ids):self.assertEqual(assignment[at],assignment[identity])

    def test_scaling_logits_threshold_and_loss_remain_stable(self):
        model=fit_mle(TRAIN,2);scores=predict(model,VALIDATION)
        scaled=[[a*1e150,b*1e-150,y] for a,b,y in TRAIN]
        other=predict(fit_mle(scaled,2),[[a*1e150,b*1e-150,y] for a,b,y in VALIDATION])
        for a,b in zip(scores,other):self.assertAlmostEqual(a,b,places=10)
        values,correct=metrics([0,1,1],[1000,-1000,0],.5)
        self.assertEqual(correct,[0,0,1]);self.assertTrue(math.isfinite(values['Log loss']))
        self.assertGreater(metrics([0,1],[-40,40],.5)[0]['Log loss'],0)

    def test_holdout_fits_only_training_split_and_bootstraps_paired_validation(self):
        r=self.result('holdout',.25,100);rng=random.Random(7);test=set()
        for label in (0,1):
            group=[i for i,row in enumerate(TRAIN) if row[-1]==label];rng.shuffle(group)
            test.update(group[:max(2,min(len(group)-2,int(len(group)*.25+.5)))])
        train=[row for i,row in enumerate(TRAIN) if i not in test];validation=[row for i,row in enumerate(TRAIN) if i in test]
        self.assertEqual(r['Training models'][0][1],len(train));self.assertEqual(r['Validation models'][0][1],len(validation))
        self.assertAlmostEqual(r['Training models'][1][3],fit_mle(train,2)['ll'],places=10)
        target=[row[-1] for row in validation];expected,_=metrics(target,predict(fit_mle(train,2),validation),.5)
        self.assertAlmostEqual(r['Validation models'][1][2],expected['AUC'],places=12)
        for _,_,lo,hi,_,_ in r['Paired differences']:self.assertLessEqual(lo,hi)

    def test_invalid_response_separation_rank_and_inference_options_reject(self):
        with self.assertRaises(MathError):self.result(argument=[row[:-1]+[2 if i==0 else row[-1]] for i,row in enumerate(VALIDATION)])
        with self.assertRaises(MathError):fit_mle([[i,int(i>=5)] for i in range(10)],1)
        with self.assertRaises(MathError):fit_mle([[a,a,y] for a,b,y in TRAIN],2)
        with self.assertRaises(MathError):self.result('crossvalidation',3,0)
        with self.assertRaises(MathError):self.result('external',VALIDATION,10)
        with self.assertRaises(MathError):self.result('crossvalidation',96,100)
        args=[TRAIN,1,'external',VALIDATION,.5,.95,0,7,[len(TRAIN)+2,len(VALIDATION)+3]]
        r=calculate(Engine({}),'logisticcompare',args)
        self.assertEqual([r['Excluded training rows'],r['Excluded validation rows']],[2,3])
        args[-1]=[1,1]
        with self.assertRaises(MathError):calculate(Engine({}),'logisticcompare',args)

    def test_public_dispatch_exposes_same_sample_tables_and_comparison_plots(self):
        source=f'logisticcompare({TRAIN},1,external,{VALIDATION},0.5,0.95,0,7)'
        result=evaluate(source);report=result['statisticsReport']
        self.assertEqual(report['title'],'Nested logistic model comparison')
        self.assertEqual([p['kind'] for p in report['plots']],['roc-comparison','calibration-comparison','intervals'])
        self.assertEqual(report['plots'][0]['series'][0]['points'][0],[0,0])
        self.assertEqual(report['plots'][0]['series'][0]['points'][-1],[1,1])
        self.assertEqual(report['plots'][2]['reference'],0)
        for series in report['plots'][1]['series']:self.assertEqual(sum(p[2] for p in series['points']),len(VALIDATION))
        self.assertEqual([p['label'] for p in report['highlights']],['LRT χ²','LRT p','ΔAIC (B − A)','ΔBIC (B − A)'])

if __name__=='__main__':unittest.main()
