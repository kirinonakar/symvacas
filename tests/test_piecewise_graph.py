"""Graph dispatch checks using trees exported by the actual Kotlin parser."""
import json
import math
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import sympy as s

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app/src/main/python'))
from calc_engine import dispatch
from calc_evaluator import Engine
from calc_graph_common import piecewise_boundaries

TREES={case['source']:case['tree'] for case in json.loads((ROOT/'build/math-cases.json').read_text(encoding='utf-8'))}

class PiecewiseGraphTests(unittest.TestCase):
    def test_animated_exponential_branches_keep_domains_without_symbolic_rebinding(self):
        source='f(x)={0<=x<=TR:1-e^(-x/T1),TR<x<TR+TE:(1-e^(-TR/T1))*e^(-(x-TR)/T2)}'
        for tr,te,t1,t2 in [(3,4,1,2),(2.25,.00001,.5,1),(-1,3,2,1),(2,-1,1,2),(0,2,1,2),(3,4,1,0),(3,4,0,2)]:
            with self.subTest(parameters=(tr,te,t1,t2)), patch('calc_graph_planar.substitute_parameters',side_effect=AssertionError('Piecewise frames must not rebind the entire expression')), patch('calc_graph_common.s.solve',side_effect=AssertionError('Linear branch cuts must not invoke a symbolic solver')):
                curve=self.graph(source,min=-2,max=10,samples=200,parameters={'TR':tr,'TE':te,'T1':t1,'T2':t2})
                finite=list(filter(None,curve))
                if t1==0:
                    self.assertEqual([],finite);continue
                self.assertGreaterEqual(len(finite),2)
                for x,y in finite:
                    if 0<=x<=tr: expected=1-math.exp(-x/t1)
                    else:
                        self.assertTrue(tr<x<tr+te)
                        self.assertNotEqual(0,t2)
                        expected=(1-math.exp(-tr/t1))*math.exp(-(x-tr)/t2)
                    self.assertAlmostEqual(expected,y,delta=1e-9*max(1,abs(expected)))
                for first,second in zip(curve,curve[1:]):
                    if first and second:
                        middle=(first[0]+second[0])/2
                        self.assertTrue(0<=middle<=tr or tr<middle<tr+te and t2!=0)

    def test_cached_boundary_polynomials_follow_parameter_and_degree_changes(self):
        x,a,b,c=s.symbols('x a b c',real=True)
        expression=s.Piecewise((1,a*x*x+b*x+c<0),(2,True))
        for values,expected in [((1,0,-4),{-2.,2.}),((0,2,-4),{2.}),((0,0,-4),set()),((1,0,4),set()),((1,0,-9),{-3.,3.})]:
            sliders=dict(zip((a,b,c),values))
            self.assertEqual(expected,piecewise_boundaries(expression,x,sliders,-5,5))

    def graph(self,source,**options):
        tree=TREES[source]
        if tree.get('kind')=='relation' and tree['args'][0].get('kind')=='call': tree=tree['args'][1]
        result=json.loads(dispatch(json.dumps({'action':'graph','graphKind':'cartesian','trees':[tree],
                                             'min':-100,'max':4000,'yMin':-1,'yMax':2,**options})))
        self.assertTrue(result['ok'],result.get('error'))
        self.assertEqual([False],result['implicitCurves'])
        return result['curves'][0]

    def test_narrow_domain_is_sampled_and_chained_inequalities_work_in_both_directions(self):
        points=list(filter(None,self.graph('y=x{0.0001<=x<=0.0002}',min=0,max=100)))
        self.assertGreaterEqual(len(points),2)
        self.assertEqual(.0001,points[0][0]);self.assertEqual(.0002,points[-1][0])
        points=list(filter(None,self.graph('y=x{3000>=x>=0}')))
        self.assertEqual(0,points[0][0]);self.assertEqual(3000,points[-1][0])

    def test_same_sign_jump_never_has_a_connecting_segment(self):
        curve=self.graph('y={x<0:1,2}',min=-1,max=1)
        self.assertIn(None,curve)
        self.assertTrue(any(point and point[1]==1 for point in curve))
        self.assertTrue(any(point and point[1]==2 for point in curve))
        for first,second in zip(curve,curve[1:]):
            if first and second:self.assertEqual(first[1],second[1])

    def test_inactive_branch_is_lazy_and_domain_guards_respect_branch_priority(self):
        engine=Engine({});engine.bindings['x']=s.Integer(0)
        self.assertEqual(5,engine.build(TREES['{x<0:1/x,5}']))
        self.assertEqual([],engine.conditions)
        engine=Engine({});x=engine.symbol('x')
        value=engine.build(TREES['{x<1:5,x>-1:1/x,0}'])
        self.assertEqual(5,value.subs(x,0))
        self.assertTrue(all(s.simplify(guard.subs(x,0))==s.true for guard in engine.conditions))
