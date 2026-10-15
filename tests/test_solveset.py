import json
import pathlib
import sys
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"app/src/main/python"))
import sympy as s
from calc_engine import Engine, dispatch, contains_heavy_call
import symvacas_catalog as catalog


def node(kind,value="",*args): return {"kind":kind,"value":str(value),"args":list(args)}
def symbol(name): return node("symbol",name)
def number(value): return node("number",value)
def call(name,*args): return node("call",name,*args)
def binary(op,a,b): return node("binary",op,a,b)
def domain(name): return node("relation","=",symbol("domain"),symbol("S."+name))
def evaluate(tree,**options): return json.loads(dispatch(json.dumps({"tree":tree,**options})))


class SolvesetTests(unittest.TestCase):
    def test_periodic_families_cover_every_real_branch_and_satisfy_equation(self):
        x=symbol("x")
        expression=binary("+",call("sin",x),binary("*",number(3),call("cos",x)))
        tree=call("solveset",expression,x,domain("Reals"))
        engine=Engine({"variables":{"x":number(99)}})
        result=engine.build(tree)
        families=result.args if isinstance(result,s.Union) else (result,)
        self.assertTrue(all(isinstance(f,s.ImageSet) and f.base_set==s.S.Integers for f in families))
        roots=[f.lamda(k) for f in families for k in range(-4,5)]
        for root in roots:
            self.assertEqual(0,s.trigsimp(s.sin(root)+3*s.cos(root)))
        for k in range(-5,6):
            expected=-s.atan(3)+k*s.pi
            self.assertTrue(any(s.simplify(root-expected)==0 for root in roots),expected)
        response=evaluate(tree,variables={"x":number(99)})
        self.assertTrue(response["ok"],response)
        self.assertIn("∈ ℤ",response["exact"])
        self.assertNotIn("ImageSet",response["exact"])
        self.assertEqual("rows",response["tree"]["kind"])
        self.assertTrue(contains_heavy_call(tree))

    def test_defaults_equations_and_positional_or_named_domains(self):
        x=symbol("x")
        expression=binary("+",binary("^",x,number(2)),number(1))
        self.assertEqual("{-I, I}",evaluate(call("solveset",expression,x))["exact"])
        equation=node("relation","=",expression,number(0))
        for arg in (domain("Reals"),symbol("S.Reals")):
            self.assertEqual("EmptySet",evaluate(call("solveset",equation,x,arg))["exact"])
        roots=binary("-",binary("^",x,number(2)),number(2))
        self.assertEqual("EmptySet",evaluate(call("solveset",roots,x,domain("Integers")))["exact"])
        self.assertEqual("{1}",evaluate(call("solveset",binary("-",x,number(1)),x,domain("Naturals")))["exact"])
        for name in ("Reals","Complexes","Integers","Rationals","Naturals","Naturals0"):
            self.assertEqual(getattr(s.S,name),Engine({}).build(symbol("S."+name)))

    def test_domain_exclusions_survive_simplification(self):
        x=symbol("x")
        fraction=binary("/",binary("-",binary("^",x,number(2)),number(1)),binary("-",x,number(1)))
        response=evaluate(call("solveset",binary("-",fraction,number(2)),x,domain("Reals")))
        self.assertTrue(response["ok"],response)
        self.assertEqual("EmptySet",response["exact"])

    def test_invalid_domains_keywords_variables_and_arity_are_rejected(self):
        x=symbol("x")
        for args in ((x,), (x,number(1)), (x,x,number(2)), (x,x,domain("Reals"),number(1)),
                     (x,x,node("relation","=",symbol("unknown"),symbol("S.Reals"))),
                     (node("relation","<",x,number(1)),x,domain("Reals"))):
            with self.subTest(args=args): self.assertFalse(evaluate(call("solveset",*args))["ok"])

    def test_unresolved_sets_remain_honest_and_python_catalog_accepts_keyword(self):
        x=symbol("x")
        result=evaluate(call("solveset",binary("-",call("sin",x),x),x,domain("Reals")))
        self.assertTrue(result["ok"],result)
        self.assertIn("ConditionSet",result["exact"])
        self.assertIn("unresolved",result["note"])
        self.assertEqual(s.FiniteSet(-2,2),catalog.solveset(catalog.x**2-4,catalog.x,domain=catalog.S.Reals))
        with self.assertRaises(TypeError): catalog.solveset(catalog.x,catalog.x,unknown=s.S.Reals)


if __name__=="__main__": unittest.main()
