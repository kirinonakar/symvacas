"""Independent likelihood and efficient-score references."""
import csv
import json
import unittest
from test_advanced_statistics import ROOT,run,evaluate
from calc_shared import MathError


class SEMExtrasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference=json.loads((ROOT/'tests/fixtures/sem_extras_reference.json').read_text())
        with (ROOT/'tests/fixtures/efa_study_habits_sample.csv').open(encoding='utf-8-sig',newline='') as file: data=list(csv.reader(file))
        cls.study=[[float(v) for v in row] for row in data[1:]]

    def test_ml_extraction_matches_independent_profile_likelihood_and_rotations(self):
        reference=self.reference['efaML']
        for rotation in ('none','oblimin'):
            fit=run('efa',self.study,2,rotation,'ml'); load=fit['loadings'];phi=fit['Factor correlations']
            for i,row in enumerate(reference['commonCovariance']):
                for j,expected in enumerate(row):
                    actual=sum(float(load[i][a]*phi[a][b]*load[j][b]) for a in range(2) for b in range(2))
                    self.assertAlmostEqual(actual,expected,delta=2e-5)
            self.assertAlmostEqual(float(fit['ML χ²']),reference['chiSquare'],places=5)
            for row,psi in zip(fit['Item diagnostics'],reference['uniquenesses']): self.assertAlmostEqual(float(row['Uniqueness']),psi,delta=2e-5)
            self.assertEqual(fit['ML df'],4)
        self.assertEqual(run('efa',self.study,2)['Extraction'],'Principal axis factoring (SMC start)')

    def test_modification_score_epc_and_freed_covariance_match_independent_calculation(self):
        case=self.reference['cfa'];rows=case['rows'];expected=case['expected']
        fit=run('cfa',rows,[1]*4,[],'complete',[],'configural','ml',[],1)
        row=next(row for row in fit['Modification indices'] if row.get('First indicator')=='feature:2' and row.get('Second indicator')=='feature:3')
        self.assertAlmostEqual(float(row['MI']),expected['MI'],places=4)
        self.assertAlmostEqual(float(row['Expected parameter change']),expected['EPC'],places=5)
        freed=run('cfa',rows,[1]*4,[],'complete',[],'configural','ml',[[2,3]],1)
        self.assertEqual(freed['df'],fit['df']-1)
        self.assertAlmostEqual(float(freed['χ²']),expected['freedChiSquare'],places=5)
        self.assertAlmostEqual(float(freed['Residual covariances'][0]['estimate']),expected['covariance'],delta=2e-5)
        self.assertFalse(any(row.get('First indicator')=='feature:2' and row.get('Second indicator')=='feature:3' for row in freed['Modification indices']))
        response=evaluate('cfa('+str(rows)+',[1,1,1,1],[],complete,[],configural,ml,[[2,3]],1)')
        edge=next(edge for edge in response['statisticsReport']['plots'][0]['edges'] if edge['source'].startswith('x'))
        self.assertEqual(edge['kind'],'covariance');self.assertEqual(len(edge['interval']),2)

    def test_identified_two_indicator_factors_are_allowed_and_unidentified_models_rejected(self):
        rows=self.reference['sem']['rows']
        selected=[[row[i] for i in (0,1,3,4)] for row in rows]
        fit=run('cfa',selected,[1,1,2,2]);self.assertEqual(fit['df'],1);self.assertEqual(len(fit['Loadings']),4)
        ordinal=[[sum(v>cut for cut in (-.7,0,.7)) for v in row] for row in selected]
        fit=run('cfa',ordinal,[1,1,2,2],[],'complete',[],'configural','wlsmv');self.assertEqual(fit['df'],1)
        selected=[[row[i] for i in (0,1,3,4,5,6,7,8)] for row in rows]
        fit=run('cfa',selected,[1,1,2,2,2,3,3,3],[[2,2]]);self.assertEqual(len(fit['Loadings']),9)
        with self.assertRaises(MathError): run('cfa',[row[:2] for row in rows],[1,1])
        with self.assertRaises(MathError): run('cfa',selected,[1,1,2,2,2,3,3,3],[[1,2],[2,2]])


if __name__=='__main__':unittest.main()
