import sympy as s
import itertools
import json
import math
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / "app/src/main/python"))
import symvacas_catalog as calc
import calc_engine

SCHEMA = json.loads((ROOT / "app/src/main/assets/probability.json").read_text(encoding="utf-8"))

class ProbabilityTests(unittest.TestCase):
    def run_probability(self, category="distribution", distribution="normal", operation="le", **values):
        return json.loads(calc_engine.dispatch(json.dumps(dict(action="probability",category=category,distribution=distribution,operation=operation,values=values))))

    def value(self, **request):
        response = self.run_probability(**request)
        self.assertTrue(response["ok"],response)
        return float(response["value"])

    def test_discrete_distributions_preserve_integer_and_degenerate_boundaries(self):
        with self.subTest(scenario='binomial_integer_and_noninteger_boundaries'):
            for x in [0,1,2,2.3,3,5,6,-1]:
                probabilities=[math.comb(5,k)/32 for k in range(6)]
                for operation,predicate in [("le",lambda k:k<=x),("lt",lambda k:k<x),("ge",lambda k:k>=x),("gt",lambda k:k>x),("eq",lambda k:k==x)]:
                    self.assertAlmostEqual(self.value(distribution="binomial",operation=operation,n=5,p="50%",x=x),sum(v for k,v in enumerate(probabilities) if predicate(k)),places=14)
            self.assertAlmostEqual(self.value(distribution="binomial",operation="between",n=5,p="1/2",lower="1.2",upper="3.8"),0.625)
        with self.subTest(scenario='degenerate_distributions'):
            for distribution,values,point in [("binomial",dict(n=5,p=0),0),("binomial",dict(n=5,p=1),5),("binomial",dict(n=0,p="0.5"),0),("poisson",dict(rate=0),0),("geometric",dict(p=1),1),("hypergeometric",dict(population=1,successes=1,draws=1),1)]:
                for op,expected in [("eq",1),("le",1),("lt",0),("ge",1),("gt",0)]:
                    self.assertEqual(self.value(distribution=distribution,operation=op,x=point,**values),expected)
                self.assertEqual(self.value(distribution=distribution,operation="quantile",q="0.5",**values),point)

    def test_dice_and_draw_probabilities_match_enumerated_outcomes(self):
        with self.subTest(scenario='dice_sum_matches_enumerated_outcomes'):
            rolls=list(itertools.product(range(1,5),repeat=3))
            for x in range(1,14):
                for operation,predicate in [("eq",lambda s:s==x),("le",lambda s:s<=x),("ge",lambda s:s>=x)]:
                    expected=sum(predicate(sum(roll)) for roll in rolls)/len(rolls)
                    self.assertEqual(self.value(category="dice",operation=operation,dice=3,sides=4,x=x),expected)
        with self.subTest(scenario='draw_operations_match_enumeration_and_hypergeometric'):
            for population in range(1,7):
                for marked in range(population+1):
                    for draws in range(population+1):
                        counts=[sum(item<marked for item in choice) for choice in itertools.combinations(range(population),draws)]
                        for op,distribution_op in [("exactly","eq"),("atLeast","ge"),("atMost","le"),("atLeastOne","ge"),("allMarked","eq")]:
                            for k in ([1] if op=="atLeastOne" else [marked] if op=="allMarked" else range(marked+2)):
                                expected=sum(x==k if distribution_op=="eq" else x>=k if distribution_op=="ge" else x<=k for x in counts)/len(counts)
                                result=self.run_probability(category="draw",operation=op,population=population,marked=marked,draws=draws,k=k)
                                self.assertTrue(result["ok"],result)
                                self.assertEqual(float(result["value"]),expected)
                                self.assertEqual(float(result["value"]),self.value(distribution="hypergeometric",operation=distribution_op,population=population,successes=marked,draws=draws,x=k))
            for op,distribution_op,k in [("exactly","eq",3),("atLeast","ge",3),("atMost","le",3),("atLeastOne","ge",1)]:
                self.assertEqual(self.value(category="draw",operation=op,population=100,marked=10,draws=20,k=k),self.value(distribution="hypergeometric",operation=distribution_op,population=100,successes=10,draws=20,x=k))

    def test_events_detect_ambiguity_conflicts_and_zero_conditioning_events(self):
        cases=[('intersection',dict(pa='.4',pb='.5'),'unique answer'),
               ('conditional',dict(pa='.4',pb='.5'),'unique answer'),
               ('union',dict(pa='.4',pb='.5',intersection='.6'),'inconsistent'),
               ('neither',dict(union='.7',neither='.2'),'inconsistent'),
               ('union',dict(pa='0',pb='.5',reverse='.4'),'zero probability'),
               ('conditional',dict(pb='0',intersection='0'),'zero probability'),
               ('reverse',dict(pa='0',intersection='0'),'zero probability'),
               ('intersection',dict(pa='.4',pb='.5',conditional='.4',reverse='.6'),'inconsistent')]
        for operation,values,error in cases:
            with self.subTest(operation=operation,values=values):
                response=self.run_probability(category='events',operation=operation,**values)
                self.assertFalse(response['ok'],response)
                self.assertIn(error,response['error'])
        # No absolute epsilon should merge distinct probabilities, even in tiny events.
        response=self.run_probability(category='events',operation='intersection',pb='1e-60',conditional='1/3')
        self.assertTrue(response['ok'],response)
        self.assertEqual(response['fraction'],f'1/{3*10**60}')
        self.assertFalse(self.run_probability(category='events',operation='union',pa='1e-60',intersection='2e-60')['ok'])
        self.assertFalse(self.run_probability(category='events',operation='neither',union='1.000000000000000000000000000000000000000000000001')['ok'])

    def test_new_quantiles_preserve_accuracy_across_scales(self):
        with self.subTest(scenario='new_quantiles_preserve_accuracy_across_scales'):
            for kind,params in [("gamma",dict(shape=2,scale="1e-60")),("gamma",dict(shape="0.1",scale="1e60")),
                                ("weibull",dict(shape=2,scale="1e-60")),("beta",dict(alpha="0.01",beta=3)),
                                ("lognormal",dict(mu=-200,sigma=1)),("lognormal",dict(mu=0,sigma=20))]:
                for q in ["0.001","0.5","0.999"]:
                    with self.subTest(distribution=kind,params=params,q=q):
                        result=self.run_probability(distribution=kind,operation="quantile",q=q,**params)
                        self.assertTrue(result["ok"],result)
                        self.assertAlmostEqual(self.value(distribution=kind,x=result["value"],**params),float(q),places=14)
        with self.subTest(scenario='extreme_tails_keep_small_probabilities'):
            tail=self.value(operation="gt",mu=0,sigma=1,x=10)
            self.assertAlmostEqual(tail/7.619853024160526e-24,1,places=13)
            interval=self.value(operation="between",mu=0,sigma=1,lower=9,upper=10)
            self.assertGreater(interval,1e-19)
            self.assertLess(interval,2e-19)
            self.assertAlmostEqual(self.value(category="repeat",operation="atLeastOne",n=10,p="1e-30")/1e-29,1,places=14)
            self.assertEqual(self.value(operation="between",mu=0,sigma=1,lower="-inf",upper="inf"),1)

class CauchyCatalogTests(unittest.TestCase):

    def test_invalid_parameters_bounds_and_arities(self):
        for name,args in [('cauchypdf',[]),('cauchypdf',[1,2]),('cauchycdf',[2,1]),('cauchycdf',[1,0,0]),('invcauchy',[-.1]),('invcauchy',[1.1]),
                          ('cauchypdf',[1,s.oo,1]),('cauchypdf',[1,0,s.oo]),('cauchycdf',[s.I]),('invcauchy',[s.nan]),('cauchypdf',[1,0,-1])]:
            with self.subTest(name=name,args=args):
                with self.assertRaises(calc_engine.MathError): getattr(calc,name)(*args)

if __name__ == "__main__": unittest.main()
