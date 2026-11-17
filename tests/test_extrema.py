"""Attained extrema contracts shared by calculator, Python catalog and graph."""
import json
import unittest
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app/src/main/python'))
import sympy as s
import calc_engine
from test_calculator_conventions import call, evaluate, node, number

x=node('symbol','x')
def binary(op,left,right): return node('binary',op,left,right)
square=binary('^',x,number(2))


class ExtremaTests(unittest.TestCase):
    def calc(self,expression,action='minimum',lower=-2,upper=2,mode=None,**options):
        args=[expression,x,number(lower),number(upper)]
        if mode: args.append(node('symbol',mode))
        return evaluate(call(action,*args),**options)

    def graph(self,*expressions,action='minimum',**options):
        return json.loads(calc_engine.dispatch(json.dumps({'action':'graphAnalysis',
            'trees':expressions,'analysis':action,'a':-2,'b':2,**options})))

    def test_calculator_graph_parity_for_cusps_and_domain_boundaries(self):
        for expression,wanted in [(call('abs',x),0),(call('sqrt',x),0),
                                  (binary('-',square,call('abs',x)),s.Rational(-1,4))]:
            for action in ('minimum','maximum'):
                with self.subTest(expression=expression,action=action):
                    calc=self.calc(expression,action,variables={'x':number(99)})
                    graph=self.graph(expression,action=action)
                    self.assertTrue(calc['ok'],calc); self.assertTrue(graph['ok'],graph)
                    actual=s.sympify(calc['exact'])
                    if action=='minimum': self.assertEqual(wanted,actual)
                    self.assertTrue(graph['points'])
                    for _,value in graph['points']: self.assertAlmostEqual(float(actual),value)

    def test_poles_and_cancelled_denominators_never_become_attained_extrema(self):
        hole=binary('*',square,binary('/',x,x))
        for expression in (binary('/',number(1),x),hole):
            for result in (self.calc(expression),self.graph(expression),self.graph(expression)):
                self.assertFalse(result['ok'],result)
                self.assertRegex(result['error'],'unbounded|not attained')
        pole=binary('/',number(1),square)
        self.assertEqual(s.Rational(1,4),s.sympify(self.calc(pole)['exact']))
        self.assertEqual([[-2.,.25],[2.,.25]],self.graph(pole)['points'])
        self.assertFalse(self.calc(pole,'maximum')['ok'])
        self.assertFalse(self.graph(pole,action='maximum')['ok'])
        self.assertEqual('1',self.calc(binary('/',x,x))['exact'])

    def test_open_and_half_open_intervals_distinguish_bounds_from_extrema(self):
        for mode,min_ok,max_ok in [('closed',True,True),('open',False,False),
                                    ('leftopen',False,True),('rightopen',True,False)]:
            for action,ok in [('minimum',min_ok),('maximum',max_ok)]:
                with self.subTest(mode=mode,action=action):
                    result=self.calc(x,action,0,1,mode,variables={mode:number(99)})
                    self.assertEqual(ok,result['ok'],result)
                    if ok: self.assertEqual('0' if action=='minimum' else '1',result['exact'])
                    else: self.assertIn('not attained',result['error'])
        self.assertEqual('0',self.calc(call('abs',x),mode='open')['exact'])
        self.assertFalse(self.calc(call('abs',x),'maximum',mode='open')['ok'])
        for action in ('minimum','maximum'):
            self.assertEqual('7',self.calc(number(7),action,mode='open')['exact'])


if __name__=='__main__': unittest.main()
