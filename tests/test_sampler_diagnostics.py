"""Portable sampler diagnostics against an independent ArviZ reference."""
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app/src/main/python'))
from calc_nuts import rank_diagnostics


class SamplerDiagnosticsTests(unittest.TestCase):
    def test_rank_folded_rhat_and_ess_match_arviz(self):
        fixture=json.loads((ROOT/'tests/fixtures/sampler_diagnostics_reference.json').read_text())
        for case in fixture['cases']:
            with self.subTest(case=case['name']):
                actual=rank_diagnostics(case['chains'])
                for key,value in case['expected'].items():
                    self.assertAlmostEqual(actual[key],value,delta=1e-8*max(1,value),msg=key)
        self.assertEqual(rank_diagnostics([[1.]*100,[1.]*100]),{'rHat':None,'bulkEss':0.,'tailEss':0.,'ess':0.})


if __name__=='__main__': unittest.main()
