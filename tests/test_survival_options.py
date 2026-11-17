"""Positional Cox contracts through public dispatch and data fitting."""
import json
import pathlib
import sys
import unittest

from test_advanced_statistics import tree

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app/src/main/python'))
from calc_engine import dispatch
from calc_evaluator import Engine
from calc_advanced_survival import calculate
from calc_survival_contract import CONTRACTS

ROWS = [[1,1,1],[2,1,2],[3,0,1],[4,1,2],[5,1,1],[6,0,2],[7,1,2],[8,1,1]]


def evaluate(name, suffix='', rows=ROWS):
    return json.loads(dispatch(json.dumps({'tree':tree(name+'('+str(rows)+suffix+')')})))


class SurvivalOptionsTests(unittest.TestCase):
    def test_explicit_cox_on_and_off_and_ph_flags(self):
        off=evaluate('survivalanalysis')
        self.assertTrue(off['ok'],off)
        self.assertIsNone(off['survival']['cox'])
        on=evaluate('survivalanalysis',',1,efron,-1,1')
        self.assertTrue(on['ok'],on)
        self.assertNotIn('error',on['survival']['cox'])
        self.assertTrue(on['survival']['ph'])
        no_check=evaluate('survivalanalysis',',1,breslow,-1,0')
        self.assertTrue(no_check['ok'],no_check)
        self.assertFalse(no_check['survival']['ph'])
        self.assertNotIn('PH test p',no_check['survival']['cox'])

    def test_wrong_options_identify_the_slot_and_complete_signature(self):
        cases=[('survivalanalysis',',efron,1,-1,1',2),('survivalanalysis',',1,-1,efron,1',3),
               ('survivalanalysis',',1,efron,0,1',4),('survivalanalysis',',1,efron,1,1',4),
               ('survivalanalysis',',1,efron,3,1',4),('survivalanalysis',',1,efron,-1,2',5),
               ('cox',',1,-1,1',2),('cox',',efron,0,1',3),('cox',',efron,1,1',3),('cox',',efron,-1,2',4)]
        for name, suffix, slot in cases:
            with self.subTest(name=name,suffix=suffix):
                result=evaluate(name,suffix)
                self.assertFalse(result['ok'],result)
                self.assertIn(f'argument {slot}',result['error'])
                self.assertIn(CONTRACTS[name]['signature'],result['error'])
        too_many=evaluate('cox',',1,efron,-1,1')
        self.assertFalse(too_many['ok'])
        self.assertIn('no coxEnabled flag',too_many['error'])

    def test_entry_time_layouts_fit_and_missing_group_is_explained(self):
        delayed=[[t,e,0,g] for t,e,g in ROWS]
        result=evaluate('survivalanalysis',',1,efron,2,1',delayed)
        self.assertTrue(result['ok'],result)
        self.assertTrue(result['survival']['truncation'])
        self.assertNotIn('error',result['survival']['cox'])
        invalid=evaluate('survivalanalysis',',1,efron,2,1')
        self.assertFalse(invalid['ok'])
        self.assertIn('[time,event,entry,group,predictors...]',invalid['error'])
        base=[[t,e,g-1] for t,e,g in ROWS]
        starts=[[t,e,0,g-1] for t,e,g in ROWS]
        first=calculate(Engine({}),'cox',[base,'efron',-1,0])
        second=calculate(Engine({}),'cox',[starts,'efron',2,0])
        self.assertAlmostEqual(first['coefficients'][0]['estimate'],second['coefficients'][0]['estimate'],places=10)


if __name__=='__main__':
    unittest.main()
