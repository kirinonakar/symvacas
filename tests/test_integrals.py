"""Derivative and domain checks for the rational trig substitution fallback."""
import json
import pathlib
import sys
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"app/src/main/python"))
import sympy as s
import calc_engine
from calc_integrals import rational_trig_primitive
from calc_shared import numeric_integral

def node(kind,value="",*args):
    return {"kind":kind,"value":str(value),"args":list(args)}

def evaluate(tree,**options):
    return json.loads(calc_engine.dispatch(json.dumps({"tree":tree,**options})))


class PiecewiseNumericIntegralTests(unittest.TestCase):
    def test_quadrature_splits_root_cusps_and_disjoint_domains(self):
        x = s.Symbol("x", real=True)
        root = s.Piecewise((x**s.Rational(1, 3), x >= 0), (-(-x)**s.Rational(1, 3), True))
        self.assertAlmostEqual(48.75, float(numeric_integral(root, x, -8, 27, 30)), delta=1e-12)
        base = 5-x**2
        curve = s.Piecewise((base**s.Rational(1, 3), base >= 0), (-(-base)**s.Rational(1, 3), True))
        result = numeric_integral(curve, x, -3, 3, 50)
        self.assertTrue(result.is_real and result.is_finite)
        self.assertAlmostEqual(4.65378418486832451445, float(result), delta=1e-12)

    def test_piecewise_preserves_cancellation_small_values_and_complex_parts(self):
        x = s.Symbol("x", real=True)
        tiny = s.Rational(1, 10**100)
        expression = s.Piecewise((x, x < 0), (x+tiny, True))
        self.assertEqual(s.Float(tiny, 30), numeric_integral(expression, x, -1, 1, 30))
        complex_curve = s.Piecewise((s.I*x, x < 0), (2*s.I*x, True))
        self.assertEqual(0, numeric_integral(complex_curve, x, -1, 1, 30)-s.I/2)
        constant = s.Piecewise((s.Float(1), x < 0), (s.Integer(1), True))
        self.assertEqual(0, numeric_integral(constant, x, -1, 1, 30)-2)


class RationalTrigIntegralTests(unittest.TestCase):
    def test_primitives_differentiate_to_original_integrands(self):
        x=s.Symbol("x")
        expressions=[s.sqrt(s.tan(x)),s.sqrt(s.tan(2*x+1)),s.sqrt(s.tan(-2*x+1)),
                     s.sqrt(s.cot(x)),1/s.sqrt(s.tan(x)),s.tan(x)**s.Rational(1,3)]
        for expression in expressions:
            with self.subTest(expression=expression):
                primitive,conditions,note=rational_trig_primitive(expression,x)
                self.assertFalse(primitive.has(s.Integral))
                self.assertEqual(0,s.trigsimp(s.simplify(s.diff(primitive,x)-expression)))
                self.assertIn(s.Eq(s.im(x),0),conditions)
                self.assertIn("continuous real interval",note)
        t=s.Symbol("t",positive=True)
        formula=(s.atan(s.sqrt(2)*t-1)+s.atan(s.sqrt(2)*t+1))/s.sqrt(2)+s.log((t**2-s.sqrt(2)*t+1)/(t**2+s.sqrt(2)*t+1))/(2*s.sqrt(2))
        self.assertEqual(0,s.cancel(s.diff(formula,t)-2*t**2/(1+t**4)))

    def test_dispatch_preserves_constant_parameters_and_branch_guards_in_ans(self):
        x=node("symbol","x")
        integrand=node("call","sqrt",node("call","tan",x))
        result=evaluate(node("call","integrate",integrand,x),variables={"x":node("number",99)})
        self.assertTrue(result["ok"],result)
        self.assertNotIn("Integral",result["exact"])
        self.assertIn("atan",result["exact"])
        self.assertIn(" + C",result["exact"])
        self.assertIn("tan(x) > 0",result["conditions"])
        self.assertEqual(["x"],result["resultAst"]["parameters"])
        engine=calc_engine.Engine({"angle":"DEG"})
        primitive=engine.build(result["resultAst"])
        self.assertEqual(0,s.simplify(s.diff(primitive,engine.symbol("x"))-s.sqrt(s.tan(engine.symbol("x")))))
        for argument in ("0.5", "3.5"):
            applied=evaluate(node("call","Ans",node("number",argument)),variables={"Ans":result["resultAst"]},angle="DEG")
            self.assertTrue(applied["ok"],applied)
            self.assertIn("C",applied["exact"])
        for argument in ("-0.5", "0", "2"):
            self.assertFalse(evaluate(node("call","Ans",node("number",argument)),variables={"Ans":result["resultAst"]})["ok"])
        imaginary=evaluate(node("call","Ans",node("symbol","i")),variables={"Ans":result["resultAst"]})
        self.assertFalse(imaginary["ok"],imaginary)

if __name__=="__main__":
    unittest.main()
