"""Attained extrema contracts shared by calculator, Python catalog and graph."""
import json
import unittest
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app/src/main/python'))
import sympy as s
import calc_engine
import symvacas_catalog as catalog
from calc_extrema import extrema_candidates
from calc_shared import MathError
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

    def test_exact_values_and_python_catalog_use_the_same_search(self):
        expression=binary('-',binary('^',x,number(4)),binary('*',number(2),x))
        result=self.calc(expression,lower=0,upper=2)
        self.assertTrue(result['ok'],result)
        self.assertEqual(0,s.simplify(s.sympify(result['exact'])+3*2**s.Rational(2,3)/4))
        variable=s.Symbol('x')
        self.assertEqual(0,catalog.minimum(s.Abs(variable),variable,-2,2))
        self.assertEqual(2,catalog.maximum(s.Abs(variable),variable,-2,2))
        with self.assertRaisesRegex(MathError,'not attained'):
            catalog.minimum(variable,variable,0,1,'open')

    def test_guards_are_scoped_to_the_selected_expression_and_bound_call(self):
        # An unrelated second curve must not exclude the selected curve's minimum.
        other=binary('/',number(1),x)
        result=self.graph(square,other)
        self.assertTrue(result['ok'],result); self.assertEqual([[0.,0.]],result['points'])
        first=call('minimum',binary('/',x,x),x,number(0),number(1))
        second=call('minimum',x,x,number(0),number(1))
        self.assertEqual('1',evaluate(binary('+',first,second))['exact'])
        restricted=node('restricted','',square,node('relation','>',x,number(0)))
        self.assertFalse(self.calc(restricted)['ok'])
        self.assertFalse(self.calc(x,assumptions={'x':['positive']})['ok'])
        parameter=node('symbol','p')
        result=self.graph(binary('/',number(1),binary('-',x,parameter)),parameters={'p':0})
        self.assertFalse(result['ok'],result); self.assertIn('unbounded',result['error'])

    def test_flat_piecewise_and_singleton_domains(self):
        variable=s.Symbol('x',real=True)
        plateau=s.Piecewise((5,s.Eq(variable,-1)),(5,s.Eq(variable,1)),(0,True))
        entries=extrema_candidates(plateau,variable,s.Interval(-1,1),'minimum')
        self.assertEqual([(0,0)],entries)
        for action in ('minimum','maximum'):
            self.assertEqual('4',self.calc(square,action,2,2)['exact'])
            self.assertFalse(self.calc(square,action,2,2,'open')['ok'])
        for lower,upper,mode in [(2,-2,None),(-2,2,'invalid')]:
            self.assertFalse(self.calc(square,lower=lower,upper=upper,mode=mode)['ok'])
        self.assertFalse(evaluate(call('minimum',x,x))['ok'])

    def test_help_keeps_polynomial_discriminant_separate_from_classification(self):
        root=Path(__file__).resolve().parents[1]
        sys.path.insert(0,str(root/'scripts'))
        from statistics_help import enrich_help
        for korean in (False,True):
            name='catalog_help'+('_ko' if korean else '')+'.md'
            text=(root/'app/src/main/assets'/name).read_text(encoding='utf-8')
            line=next(line for line in text.splitlines() if line.startswith('`discriminant(poly,x)`'))
            self.assertNotIn('LDA/QDA',line)
            self.assertIn('LDA/QDA',next(line for line in text.splitlines() if line.startswith('`discriminantanalysis`')))
            regenerated=enrich_help('`discriminant(poly,x)` — Discriminant analysis (LDA/QDA).',korean)
            self.assertNotIn('LDA/QDA',regenerated)


if __name__=='__main__': unittest.main()
