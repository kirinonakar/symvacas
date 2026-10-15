"""Independent Bayesian-bootstrap moments and PCA visualization contracts."""
import math
from pathlib import Path
import sys
import unittest
import sympy as s

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app/src/main/python'))
from calc_advanced_statistics import advanced
from calc_evaluator import Engine
from calc_shared import MathError

class BayesianBootstrapTests(unittest.TestCase):
    def compare(self,first,second,mode='independent',statistic='mean',draws=20000):
        engine=Engine({})
        return advanced(engine,'bayesbootstrap',[first,second,s.Symbol(statistic),.95,draws,7,s.Symbol(mode)])

    def test_independent_column_difference_matches_analytic_moments_and_probability(self):
        result=self.compare([0,1],[0,2])
        self.assertEqual(.5,float(result['estimate']))
        self.assertAlmostEqual(.5,float(result['posterior mean']),delta=.02)
        self.assertAlmostEqual(math.sqrt(5/12),float(result['posterior SD']),delta=.01)
        self.assertAlmostEqual(.75,float(result['P(difference > 0)']),delta=.015)
        self.assertAlmostEqual(.25,float(result['P(difference < 0)']),delta=.015)
        self.assertEqual(0,float(result['P(difference = 0)']))
        self.assertAlmostEqual(1,sum(float(result[key]) for key in ('P(difference > 0)','P(difference < 0)','P(difference = 0)')))
        unequal=self.compare([0,1],[1,2,3],draws=100)
        self.assertEqual(2,int(unequal['n A']));self.assertEqual(3,int(unequal['n B']))

    def test_paired_columns_keep_joint_row_weights_and_constant_differences(self):
        result=self.compare([0,1],[1,0],mode='paired')
        self.assertAlmostEqual(0,float(result['posterior mean']),delta=.02)
        self.assertAlmostEqual(1/math.sqrt(3),float(result['posterior SD']),delta=.01)
        self.assertAlmostEqual(.5,float(result['P(difference > 0)']),delta=.015)
        shift=self.compare([2,10,-1],[7,15,4],mode='paired',draws=100)
        self.assertEqual([5,5],list(map(float,shift['credible interval'])))
        self.assertEqual(0,float(shift['posterior SD']))
        for statistic in ('mean','median','variance','stdev'):
            same=self.compare([2,10,-1],[2,10,-1],mode='paired',statistic=statistic,draws=100)
            self.assertEqual([0,0],list(map(float,same['credible interval'])))
            self.assertEqual(1,float(same['P(difference = 0)']))
            self.assertEqual(0,float(same['P(difference < 0)']))
            self.assertEqual(0,float(same['P(difference > 0)']))

    def run_bootstrap(self,data,statistic='mean',level=.95,draws=20000,seed=7):
        engine=Engine({})
        result=advanced(engine,'bayesbootstrap',[data,s.Symbol(statistic),level,draws,seed])
        return result,engine.statistics_plots[0]

    def test_uniform_two_point_mean_matches_exact_posterior_and_histogram_mass(self):
        result,plot=self.run_bootstrap([0,1])
        self.assertEqual(.5,float(result['estimate']))
        self.assertAlmostEqual(.5,float(result['posterior mean']),delta=.01)
        self.assertAlmostEqual(1/math.sqrt(12),float(result['posterior SD']),delta=.01)
        for actual,expected in zip(result['credible interval'],(.025,.975)):self.assertAlmostEqual(expected,float(actual),delta=.01)
        self.assertEqual(20000,sum(plot['counts']))
        self.assertEqual(len(plot['counts'])+1,len(plot['edges']))
        self.assertAlmostEqual(float(result['posterior SD'])/math.sqrt(20000),float(result['posterior mean MCSE']))
        again,_=self.run_bootstrap([0,1]);self.assertEqual(result,again)
        changed,_=self.run_bootstrap([0,1],seed=8);self.assertNotEqual(result,changed)


    def test_invalid_parameters_are_rejected(self):
        for data,statistic,level,draws,seed in (([1],'mean',.95,100,0),([1,2],'bad',.95,100,0),([1,2],'mean',1,100,0),([1,2],'mean',.95,99,0),([1,2],'mean',.95,100,-1)):
            with self.assertRaises(MathError):self.run_bootstrap(data,statistic,level,draws,seed)
