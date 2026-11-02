"""Positional Cox contracts through public dispatch, data fitting and generated help."""
import json
import pathlib
import sys
import unittest

from test_advanced_statistics import tree

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app/src/main/python'))
from calc_engine import dispatch
from calc_evaluator import Engine
from calc_advanced_survival import calculate, cox_options
from calc_survival_contract import CONTRACTS

ROWS = [[1,1,1],[2,1,2],[3,0,1],[4,1,2],[5,1,1],[6,0,2],[7,1,2],[8,1,1]]


def evaluate(name, suffix='', rows=ROWS):
    return json.loads(dispatch(json.dumps({'tree':tree(name+'('+str(rows)+suffix+')')})))


class SurvivalOptionsTests(unittest.TestCase):
    def test_defaults_and_trailing_omissions_do_not_swap_positions(self):
        self.assertEqual(cox_options('survivalanalysis',[ROWS]), dict(coxEnabled=0,ties='efron',entryColumn=-1,phCheck=1))
        self.assertEqual(cox_options('cox',[ROWS]), dict(ties='efron',entryColumn=-1,phCheck=1))
        for args, expected in [([ROWS,1],('efron',-1,1)),([ROWS,1,'breslow'],('breslow',-1,1)),
                               ([ROWS,1,'breslow',-1],('breslow',-1,1)),([ROWS,1,'breslow',-1,0],('breslow',-1,0))]:
            with self.subTest(args=args[1:]):
                parsed=cox_options('survivalanalysis',args)
                self.assertEqual(tuple(parsed[key] for key in ('ties','entryColumn','phCheck')), expected)

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

    def test_generated_catalog_has_full_signatures_and_structured_positions(self):
        schema=json.loads((ROOT/'app/src/main/assets/advanced_statistics.json').read_text(encoding='utf-8'))
        for name in ('survivalanalysis','cox'):
            item=next(item for item in schema if item['id']==name)
            self.assertEqual(item['signature'],CONTRACTS[name]['signature'])
            self.assertEqual([arg['position'] for arg in item['arguments']],list(range(1,len(item['arguments'])+1)))
            for file in ('catalog_help.md','catalog_help_ko.md'):
                help_text=(ROOT/'web'/file).read_text(encoding='utf-8')
                self.assertIn('`'+item['signature']+'`',help_text)


if __name__=='__main__':
    unittest.main()
