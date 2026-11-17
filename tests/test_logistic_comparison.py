"""Paired validation, refitted CV, numerical guards and public report regression tests."""
import json
import math
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app/src/main/python'))
from calc_logistic_comparison import calculate, folds_for
from calc_evaluator import Engine

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


if __name__=='__main__':unittest.main()
