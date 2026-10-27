import json
import pathlib
import sys
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app/src/main/python'))
from calc_execution_budget import bootstrap_work
import calc_engine
from calc_runtime import Budget


class ExecutionBudgetTests(unittest.TestCase):
    def test_shared_android_web_python_budget_cases(self):
        cases = json.loads((ROOT / 'tests/fixtures/execution_budget.json').read_text())
        for case in cases:
            with self.subTest(case=case['name']):
                self.assertEqual((case['samples'], case['seconds']), bootstrap_work(case['request']))

    def test_sem_engine_deadline_precedes_client_timeout(self):
        cases = json.loads((ROOT / 'tests/fixtures/execution_budget.json').read_text())
        for case in cases:
            if not case['samples']:
                continue
            budgets = []
            def capture(seconds, steps, control):
                budgets.append(seconds)
                return Budget(seconds, steps, control)
            # Inspect the actual dispatch budget without doing bootstrap refits.
            with self.subTest(case=case['name']), patch.object(calc_engine, 'Budget', capture):
                with patch.object(calc_engine.Engine, 'build', side_effect=ValueError('test stops evaluation')):
                    calc_engine.dispatch(json.dumps(case['request']))
                self.assertEqual(60 + case['seconds'], budgets[0])
                self.assertEqual(5000, case['timeoutMillis'] - budgets[0] * 1000)
