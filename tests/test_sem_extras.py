"""Independent likelihood, efficient-score and full-refit bootstrap references."""
import csv
import json
import math
import unittest
from unittest.mock import patch
from test_advanced_statistics import ROOT,run,evaluate
from calc_statistics_report import statistics_report
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

    def test_modification_indices_default_and_explicit_off_skip_computation(self):
        rows=self.reference['cfa']['rows']
        ordinal=json.loads((ROOT/'tests/fixtures/sem_estimation_reference.json').read_text())['cases'][0]['arguments']
        with patch('calc_advanced_sem_extras.normal_mi',side_effect=AssertionError('MI must stay off')),patch('calc_advanced_sem_extras.ordinal_mi',side_effect=AssertionError('MI must stay off')):
            for args in ([rows,[1]*4],[rows,[1]*4,[],'complete',[],'configural','ml',[],0],ordinal):
                fit=run('cfa',*args)
                self.assertNotIn('Modification indices',fit);self.assertNotIn('MI method',fit)

    def test_indirect_effects_and_bootstrap_match_independent_complete_model_refits(self):
        case=self.reference['sem'];args=[case['rows'],[1,1,1,2,2,2,3,3,3],[[1,2],[2,3],[1,3]],[],'complete',[],'configural','ml',[],0,case['samples'],case['seed']]
        fit=run('sem',*args);self.assertEqual(fit['Bootstrap successful'],case['samples']);self.assertEqual(fit['Bootstrap failed'],0)
        for kind,key in [('Direct effect','direct'),('Indirect effect','indirect'),('Total effect','total')]:
            row=next(row for row in fit['Effects'] if row['term']=='1 → 3' and row['Effect']==kind)
            self.assertAlmostEqual(float(row['Estimate']),case['expected'][key],delta=2e-5)
            self.assertTrue(all(math.isfinite(float(v)) for v in row['CI95']))
            for actual,expected in zip(row['Bootstrap CI95'],case['bootstrap'][key]):self.assertAlmostEqual(float(actual),expected,delta=5e-5)
            if key=='indirect':
                self.assertAlmostEqual(float(row['Standardized estimate']),case['expected']['standardizedIndirect'],delta=2e-5)
                for actual,expected in zip(row['Standardized bootstrap CI95'],case['bootstrap']['standardizedIndirect']): self.assertAlmostEqual(float(actual),expected,delta=5e-5)

    def test_residual_pair_validation_and_bootstrap_failure_accounting(self):
        rows=self.reference['cfa']['rows']
        for pairs in ([[2,2]],[[2,3],[3,2]],[[1,5]]):
            with self.assertRaises(MathError): run('cfa',rows,[1]*4,[],'complete',[],'configural','ml',pairs)
        from calc_advanced_sem_extras import bootstrap
        result={'Effects':[{'term':'1 → 2','Effect':'Indirect effect','Estimate':0.,'Standardized estimate':0.}]}
        calls=[]
        def failing(engine,name,args,fast=False): calls.append(args[0]);raise MathError('Singular resample')
        bootstrap(None,'sem',[rows,[1]*4,[[1,2]]],result,failing,20,7)
        self.assertEqual(len(calls),20);self.assertEqual(result['Bootstrap successful'],0);self.assertEqual(result['Bootstrap failed'],20)
        self.assertIsNone(result['Effects'][0]['Bootstrap CI95']);self.assertIn('Bootstrap warning',result)

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


class StatisticsDetailTests(unittest.TestCase):
    def test_metadata_moves_below_tables_without_mutating_values_or_numeric_fields(self):
        value={'n':100,'Estimator':'Normal-theory covariance ML (N divisor)','Extraction':'Principal components (correlation PCA)',
               'Parallel method':'Horn normal simulation; SMC-reduced common roots',
               'RMSEA convention':'N−G denominator, group multiplier G; uncorrected normal-theory index','inference df':12,
               'coefficients':[{'term':'A long user variable name '+('x'*100),'estimate':.2,'Inference':'Gaussian-kernel sandwich / Hall–Sheather','SE':.1}]}
        original=json.dumps(value);report=statistics_report('quantreg',value,15)
        self.assertEqual(json.dumps(value),original)
        strings=[cell for section in report['sections'] for row in section['rows'] for cell in row if isinstance(cell,str)]
        self.assertNotIn(value['Estimator'],strings);self.assertNotIn(value['Extraction'],strings);self.assertNotIn(value['RMSEA convention'],strings)
        self.assertIn('inference df',strings);self.assertIn(value['coefficients'][0]['term'],strings)
        details={row['label']:row for row in report['details']}
        self.assertEqual(details['Parallel method']['text'],value['Parallel method'])
        self.assertEqual(details['Inference']['context'][0]['value'],value['coefficients'][0]['term'])
        self.assertNotIn('Inference',report['sections'][1]['columns'])


if __name__=='__main__':unittest.main()
