"""Numerical correctness regressions from the source review."""
import json
import math
import random
import unittest
from test_advanced_statistics import run, tree
from test_calculator_conventions import evaluate, call, number, node
import sympy as s
import calc_engine
from calc_evaluator import Engine
from calc_graph import interval_extrema
from calc_shared import MathError, dms_parts, numeric_derivative, sexagesimal_value
from calc_statistics_report import statistics_report


class ReviewRegressionTests(unittest.TestCase):
    def test_crossvalidation_matches_closed_form_penalties(self):
        rows=[[i,2+3*i] for i in range(12)]
        order=list(range(len(rows))); random.Random(7).shuffle(order)
        for model,ratio in [('lasso',1),('ridge',0),('elasticnet',.3)]:
            alpha=2.; expected=[0.]*len(rows)
            for fold in range(3):
                test=order[fold::3]; train=[row for i,row in enumerate(rows) if i not in test]
                mx=sum(row[0] for row in train)/len(train); my=sum(row[1] for row in train)/len(train)
                scale=math.sqrt(sum((row[0]-mx)**2 for row in train)/len(train))
                covariance=sum((row[0]-mx)/scale*(row[1]-my) for row in train)/len(train)
                beta=max(0,covariance-alpha*ratio)/(1+alpha*(1-ratio))
                for i in test: expected[i]=my+beta*(rows[i][0]-mx)/scale
            options=[alpha,ratio] if model=='elasticnet' else alpha
            result=run('crossvalidate',rows,3,7,'random',model,options)
            for actual,wanted in zip(result['out-of-fold predictions'],expected):
                self.assertAlmostEqual(float(actual),wanted,places=8)

    def test_stratification_rejects_short_classes_and_balances_folds(self):
        with self.assertRaisesRegex(MathError,'reduce the fold count'):
            run('crossvalidate',[[i,i%2] for i in range(8)],5,0,'stratified','logistic',.5)
        # Restarting both classes at fold 0 would make 4/4/2/2 instead of 3/3/3/3.
        result=run('crossvalidate',[[i,0] for i in range(6)]+[[i+6,1] for i in range(6)],4,0,'stratified','logistic',.5)
        self.assertEqual(len(result['fold log loss']),4)
        self.assertEqual(result['fold sizes'],[3,3,3,3])
        self.assertTrue(all(math.isfinite(v) for v in result['fold log loss']))

    def test_complex_frobenius_norm_uses_absolute_squares(self):
        result=evaluate(call('frob',node('list','',number(1),node('symbol','i'))))
        self.assertTrue(result['ok'],result)
        self.assertEqual(result['exact'],'sqrt(2)')

    def test_chi_square_validates_counts_and_totals(self):
        for source,error in [('chi2test([-2,12],[5,5])','nonnegative integers'),
                             ('chi2test([2.5,7.5],[5,5])','nonnegative integers'),
                             ('chi2test([2,8],[4,5])','matching totals'),
                             ('chi2test([2,8],[0,10])','positive')]:
            with self.assertRaisesRegex(MathError,error): Engine({}).build(tree(source))
        valid=Engine({}).build(tree('chi2test([2,8],[4.5,5.5])'))
        self.assertAlmostEqual(float(valid['chi-square']),float(s.Rational(250,99)))
        # Expected frequencies are fractional, and totals allow rounding noise.
        Engine({}).build(tree('chi2test([2,8],[4.50000000001,5.5])'))
        Engine({}).build(tree('chi2test([2.0,8.0],[4.5,5.5])'))

    def test_negative_dms_roundtrip_and_ans(self):
        for value in map(s.Rational,('-12.5','-.5','-.00001','0','.00001','.5','12.5')):
            self.assertEqual(sexagesimal_value(dms_parts(value)),value)
            parts=dms_parts(value)
            source=node('sexagesimal','',*(number(part) for part in parts))
            result=evaluate(source)
            self.assertTrue(result['ok'],result)
            answer=Engine({}).build(result['resultAst'])
            self.assertEqual(answer,value)
            reused=evaluate(node('symbol','Ans'),variables={'Ans':result['resultAst']})
            self.assertTrue(reused['ok'],reused)
            self.assertEqual(s.sympify(reused['exact']),value)
            if value<0:
                self.assertEqual(result['tree']['kind'],'unary')
                self.assertEqual(result['tree']['value'],'-')
        self.assertEqual(Engine({}).build(tree('sexagesimal(-12,30,0)')),s.Rational(-25,2))
        self.assertEqual(Engine({}).build(tree('sexagesimal(0,-30,0)')),s.Rational(-1,2))

    def test_numerical_derivative_rejects_corners_jumps_and_poles(self):
        x=s.Symbol('x',real=True)
        for expr in (s.Abs(x),s.sign(x),1/x,s.Piecewise((1,s.Eq(x,0)),(x,True)),s.real_root(x,3)):
            with self.subTest(expr=expr),self.assertRaisesRegex(MathError,'Derivative undefined'):
                numeric_derivative(expr,x,s.Integer(0),30)
        for expr,point,expected in [(x**2,0,0),(s.sin(x),0,1),(s.Abs(x),2,1),(x*s.Abs(x),0,0),(s.Abs(x)**s.Rational(3,2),0,0)]:
            self.assertAlmostEqual(float(numeric_derivative(expr,x,s.Integer(point),30)),expected,places=10)
        near_pole=numeric_derivative(1/x,x,s.Rational(1,10**13),30)
        self.assertAlmostEqual(float(near_pole)/-1e26,1.,places=10)

    def test_global_extrema_check_all_domain_boundaries(self):
        x=s.Symbol('x',real=True)
        for expr in (1/x,1/(x-s.Rational(1,3)),s.tan(x)):
            for action in ('minimum','maximum'):
                with self.subTest(expr=expr,action=action),self.assertRaisesRegex(MathError,'unbounded'):
                    interval_extrema(expr,x,-2,2,action)
        self.assertEqual(interval_extrema(1/x**2,x,-1,1,'minimum'),[-1.,1.])
        with self.assertRaisesRegex(MathError,'unbounded'):
            interval_extrema(1/x**2,x,-1,1,'maximum')
        self.assertEqual(interval_extrema(s.Abs(x),x,-1,1,'minimum'),[0.])
        self.assertEqual(interval_extrema(s.sqrt(x),x,-1,1,'minimum'),[0.])
        jump=s.Piecewise((x,x<0),(x+2,True))
        self.assertEqual(interval_extrema(jump,x,-1,1,'minimum'),[-1.])
        self.assertEqual(interval_extrema(jump,x,-1,1,'maximum'),[1.])
        missing=s.Piecewise((1,s.Eq(x,0)),(x**2,True))
        with self.assertRaisesRegex(MathError,'not attained'):
            interval_extrema(missing,x,-1,1,'minimum')
        request={'action':'graphAnalysis','trees':[node('binary','/',number(1),node('symbol','x'))],
                 'analysis':'minimum','a':-1,'b':1}
        result=json.loads(calc_engine.dispatch(json.dumps(request)))
        self.assertFalse(result['ok']); self.assertIn('unbounded',result['error'])

    def test_sem_diagnostics_are_presentation_and_fit_p_is_labelled(self):
        value={'n':100,'Loadings':[],'Structural paths':[],'CFI':.986,'RMSEA':.052,'SRMR':.04,'p':.22,
               'diagnostics':{'Optimization convergence':'Passed','Parameter identification':'Passed'}}
        report=statistics_report('sem',value,20)
        self.assertEqual([item['label'] for item in report['highlights']],['CFI','RMSEA','SRMR','χ² p'])
        self.assertTrue(any(section['title']=='Model diagnostics' for section in report['sections']))
        self.assertEqual(value['p'],.22)


if __name__=='__main__': unittest.main()
