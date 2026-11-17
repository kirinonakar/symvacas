import json
import pathlib
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'app/src/main/python'))
import calc_engine
from calc_limits import computation_limits, limits_removed
from calc_runtime import Budget
from calc_advanced_common import integer, vector

def number(value):
    return {'kind': 'number', 'value': str(value)}

def call(name, *args):
    return {'kind': 'call', 'value': name, 'args': list(args)}

def run(tree, **options):
    return json.loads(calc_engine.dispatch(json.dumps({'tree': tree, **options})))

class ComputationLimitsTests(unittest.TestCase):
    def test_time_and_workload_are_unlimited_but_cancellation_still_works(self):
        budgets = []
        def capture(seconds, steps, control):
            budget = Budget(seconds, steps, control)
            budgets.append(budget)
            return budget
        with patch.object(calc_engine, 'Budget', capture):
            result = run(number(2), removeComputationLimit=True, budget=-1)
        self.assertTrue(result['ok'], result)
        self.assertEqual(float('inf'), budgets[0].deadline)
        self.assertEqual(float('inf'), budgets[0].steps)
        self.assertFalse(limits_removed())
        class Cancelled:
            def isCancelled(self): return True
        result = json.loads(calc_engine.dispatch(json.dumps({
            'tree': number(2), 'removeComputationLimit': True}), Cancelled()))
        self.assertEqual('Calculation cancelled', result['error'])
        self.assertFalse(limits_removed())
        self.assertFalse(run(number(2), budget=-1)['ok'])

    def test_matrix_and_dataset_capacity_can_be_removed(self):
        tree = call('identity', number(33))
        self.assertFalse(run(tree)['ok'])
        result = run(tree, removeComputationLimit=True)
        self.assertTrue(result['ok'], result)
        self.assertEqual(33, len(result['tree']['args']))
        tree = call('mean', {'kind': 'symbol', 'value': 'data'})
        options = {'statisticsDatasets': {'data': ['2'] * 5001}}
        self.assertFalse(run(tree, **options)['ok'])
        self.assertEqual('2', run(tree, removeComputationLimit=True, **options)['exact'])

    def test_only_capacity_parts_of_input_checks_are_removed(self):
        with computation_limits(True):
            self.assertEqual(6000, len(vector([1] * 6000)))
            self.assertEqual(30000, integer(30000, 100, 20000, capacity=True))
            with self.assertRaises(ValueError): integer(2, 0, 1)
            with self.assertRaises(ValueError): vector([], 2)
        for tree in (call('factorial', number(-1)), call('identity', number(0)),
                     {'kind': 'binary', 'value': '/', 'args': [number(1), number(0)]}):
            self.assertFalse(run(tree, removeComputationLimit=True)['ok'])
