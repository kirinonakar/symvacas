"""Regressions for real roots, domains, rank tests and bounded solvers."""
import json
import math
import random
import unittest
from unittest.mock import patch
import sympy as s
from test_graph import x, y, number, binary, equation
from test_advanced_statistics import tree
import calc_engine
from calc_evaluator import Engine
from calc_inference import fit_multivariate
from calc_logistic_float import fit as float_fit
from calc_runtime import Budget, SolverTimeLimit, solver_phase


def call(name,*args): return {'kind':'call','value':name,'args':list(args)}
def dispatch(source,**options): return json.loads(calc_engine.dispatch(json.dumps({'tree':source,**options})))


class RequestedImprovementsTests(unittest.TestCase):
    def test_real_odd_roots_values_and_graph_negative_half(self):
        for name in ('cbrt','nthroot'):
            args=[x]+([number(3)] if name=='nthroot' else [])
            self.assertEqual(dispatch(call(name,number(-8),*args[1:]))['exact'],'-2')
            result=json.loads(calc_engine.dispatch(json.dumps({'action':'graph','trees':[call(name,*args)],'min':-8,'max':8})))
            self.assertTrue(result['ok'],result)
            points=[p for p in result['curves'][0] if p is not None]
            self.assertTrue(any(p[0]<0 and p[1]<0 for p in points))
            self.assertAlmostEqual(points[0][1],-2)
        self.assertEqual(dispatch(call('nthroot',number(-32),number(5)))['exact'],'-2')
        self.assertEqual(dispatch(call('nthroot',number(-16),number(4)))['exact'],'2*(-1)**(1/4)')
        self.assertFalse(dispatch(call('nthroot',number(8),number(0)))['ok'])

    def test_cancelled_denominators_excluded_from_infinite_solution_sets(self):
        for denominator in (x,binary('-',x,number(2)),binary('-',binary('^',x,number(2)),number(1))):
            source=call('solve',equation(binary('/',denominator,denominator),number(1)),x)
            engine=Engine({}); answer=engine.build(source)
            self.assertIsInstance(answer,s.Complement)
            for root in s.solve(engine.build(denominator),engine.symbol('x')):
                self.assertEqual(answer.contains(root),s.false)
        source=call('solve',equation(binary('/',binary('^',x,number(2)),x),number(0)),x)
        self.assertEqual(dispatch(source)['exact'],'EmptySet')

    def test_real_derivatives_and_clear_errors(self):
        result=dispatch(call('diff',call('abs',x),x))
        self.assertEqual(result['exact'],'sign(x)')
        result=dispatch(call('diff',call('cbrt',x),x))
        self.assertTrue(result['ok'],result)
        self.assertNotIn('Derivative',result['exact']);self.assertNotIn('DiracDelta',result['exact'])
        engine=Engine({}); derivative=engine.build(call('diff',call('cbrt',x),x))
        variable=next(iter(derivative.free_symbols))
        self.assertEqual(derivative.subs(variable,-8),s.Rational(1,12))
        self.assertEqual(dispatch(call('diff',binary('^',x,number(2)),x))['exact'],'2*x')
        invalid=dispatch(tree('foo([1,2],[3,4])'))
        self.assertFalse(invalid['ok']);self.assertIn('Undefined function: foo',invalid['error'])
        source=call('limit',binary('/',number(1),x),x,number(0))
        result=dispatch(source)
        self.assertFalse(result['ok']);self.assertIn('left-hand limit = -oo',result['error']);self.assertIn('right-hand limit = oo',result['error'])
        self.assertEqual(dispatch(call('limit',binary('/',number(1),x),x,number(0),{'kind':'symbol','value':'right'}))['exact'],'oo')

    def test_rank_correlations_ties_exact_and_approximate(self):
        cases=[('pearson([1,2,3,4,5],[2,1,3,4,5])','r',.9,.0373860734684987),
               ('spearman([1,2,3],[1,2,3])','rho',1,1/3),
               ('kendall([1,2,3],[1,2,3])','tau-b',1,1/3),
               ('kendall([12,2,1,12,2],[1,4,7,1,0])','tau-b',-.47140452079103173,.2827454599327748),
               ('spearman([1,2,2,4,5],[2,1,3,4,5])','rho',.8207826816681233,2/15)]
        for source,key,coefficient,p in cases:
            result=dispatch(tree(source),precision=20)
            self.assertTrue(result['ok'],result)
            engine=Engine({}); value=engine.build(tree(source))
            self.assertAlmostEqual(float(value[key]),coefficient,places=12)
            self.assertAlmostEqual(float(value['p']),p,places=12)
            self.assertEqual(result['statisticsReport']['analysis'],source.split('(')[0])
        for name in ('pearson','spearman','kendall'):
            self.assertFalse(dispatch(tree(f'{name}([1,1],[2,3])'))['ok'])
            self.assertFalse(dispatch(tree(f'{name}([1,2],[2,3,4])'))['ok'])
        self.assertFalse(dispatch(tree('pearson([1,2],[2,3])'))['ok'])
        for tail,expected in [('both',0),('right',1),('left',0)]:
            value=Engine({}).build(tree(f'pearson([1,2,3],[3,2,1],{tail})'))
            self.assertEqual(float(value['r']),-1)
            self.assertEqual(float(value['p']),expected)

    def test_float_logistic_matches_high_precision_fit_and_influence(self):
        rng=random.Random(123)
        rows=[]
        for _ in range(80):
            predictors=[rng.uniform(-2,2),rng.uniform(-1,1)]
            probability=1/(1+math.exp(-(.3+.7*predictors[0]-.5*predictors[1])))
            rows.append([s.Float(v,30) for v in predictors]+[s.Integer(rng.random()<probability)])
        precise=Engine({'precision':20}); fast=Engine({'precision':20})
        fit_multivariate(precise,rows,logistic=True);float_fit(fast,rows)
        for old,new in zip(precise.regression_report['coefficients'],fast.regression_report['coefficients']):
            for key in ('estimate','se','p','low','high','vif'):
                if old[key] is not None:self.assertAlmostEqual(float(old[key]),float(new[key]),places=8)
        for old,new in zip(precise.regression_report['residuals'],fast.regression_report['residuals']):
            for key in ('fitted','standardized','deviance','leverage','cook'):
                self.assertAlmostEqual(float(old[key]),float(new[key]),places=8)

    def test_asymptotes_are_verified_and_holes_are_not_poles(self):
        cases=[(binary('/',number(1),x),['vertical','horizontal']),
               (call('tan',x),['vertical','vertical']),
               (binary('/',binary('+',binary('^',x,number(2)),number(1)),x),['vertical','oblique'])]
        for expression,expected in cases:
            result=json.loads(calc_engine.dispatch(json.dumps({'action':'graphAnalysis','trees':[expression],
                'analysis':'asymptotes','a':-2,'b':2})))
            self.assertTrue(result['ok'],result)
            self.assertCountEqual([item['kind'] for item in result['asymptotes']],expected)
            self.assertEqual(len(result['lines']),len(expected))
        hole=binary('/',binary('-',binary('^',x,number(2)),number(1)),binary('-',x,number(1)))
        result=json.loads(calc_engine.dispatch(json.dumps({'action':'graphAnalysis','trees':[hole],'analysis':'asymptotes','a':-2,'b':2})))
        self.assertTrue(result['ok'],result);self.assertFalse(any(item['kind']=='vertical' for item in result['asymptotes']))

    def test_solver_phase_returns_to_outer_budget(self):
        with Budget(2,steps=1000000) as budget:
            with self.assertRaises(SolverTimeLimit):
                with solver_phase(-1): pass
            budget.check()
        result=dispatch(call('dsolve',equation(call('diff',call('y',x),x),binary('+',binary('*',x,binary('^',call('y',x),number(2))),binary('^',call('y',x),number(3)))),call('y',x),x))
        self.assertFalse(result['ok'],result);self.assertIn('numerical differential-equation graph',result['error'])
        simple=dispatch(call('dsolve',equation(call('diff',call('y',x),x),call('y',x)),call('y',x),x))
        self.assertTrue(simple['ok'],simple)


if __name__=='__main__': unittest.main()
