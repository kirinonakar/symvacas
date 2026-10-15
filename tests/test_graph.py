import json
import math
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "app/src/main/python"))
import calc_engine
from calc_graph import simplify_samples

def number(value): return {"kind": "number", "value": str(value)}
def symbol(name): return {"kind": "symbol", "value": name}
def binary(op, left, right): return {"kind": "binary", "value": op, "args": [left, right]}
def equation(left, right): return {"kind": "relation", "value": "=", "args": [left, right]}

x, y = symbol("x"), symbol("y")
x2, y2 = binary("^", x, number(2)), binary("^", y, number(2))
circle = equation(binary("+", x2, y2), number(1))

class ImplicitGraphTests(unittest.TestCase):


    def test_equation_intersections_include_periodic_tangent_contacts_and_endpoints(self):
        cosine={"kind":"call","value":"cos","args":[x]}
        constraint=equation(cosine,number(1))
        for trees in ((x,constraint),(constraint,x)):
            result=self.analyze(*trees,analysis="intersection",a=-2*math.pi,b=2*math.pi)
            self.assertTrue(result["ok"],result)
            self.assertEqual(3,result["count"])
            for point,at in zip(result["points"],(-2*math.pi,0,2*math.pi)):
                self.assertAlmostEqual(at,point[0],delta=1e-7)
                self.assertAlmostEqual(at,point[1],delta=1e-7)

    def test_absolute_intersections_use_real_coordinates_for_both_curve_orders(self):
        absolute={"kind":"call","value":"abs","args":[x]}
        line=binary("+",binary("*",binary("/",number(1),number(2)),x),number(2))
        for trees in ((absolute,line),(line,absolute)):
            result=self.analyze(*trees,analysis="intersection",a=-5,b=5)
            self.assertTrue(result["ok"],result)
            self.assertEqual(2,len(result["points"]))
            for point,expected in zip(result["points"],((-4/3,4/3),(4,4))):
                self.assertAlmostEqual(expected[0],point[0],delta=1e-7)
                self.assertAlmostEqual(expected[1],point[1],delta=1e-7)
        # A tangent contact also takes the derivative-search path.
        touching=self.analyze(absolute,number(0),analysis="intersection")
        self.assertTrue(touching["ok"],touching)
        self.assertEqual([[0.0,0.0]],touching["points"])


    def test_angle_analysis_rejects_corners_singular_points_and_undefined_coordinates(self):
        absolute={"kind":"call","value":"abs","args":[x]}
        for tree in (absolute,binary("/",number(1),x)):
            result=self.analyze(tree,analysis="tangentangle",a=0)
            self.assertFalse(result["ok"],result);self.assertIn("undefined",result["error"])
        result=self.analyze(absolute,number(0),analysis="intersectionangle")
        self.assertTrue(result["ok"],result);self.assertEqual([[0.0,0.0]],result["points"])
        self.assertIsNone(result["angles"][0]["value"])
        singular=equation(y2,x2)
        result=self.analyze(singular,equation(x,number(0)),analysis="intersectionangle")
        self.assertTrue(result["ok"],result);self.assertIsNone(result["angles"][0]["value"])
        vertical=self.analyze({"kind":"call","value":"sqrt","args":[x]},analysis="tangentangle",a=0)
        self.assertTrue(vertical["ok"],vertical);self.assertAlmostEqual(90,vertical["value"])


    def test_derivative_analysis_uses_the_selected_order_for_every_action(self):
        cubic=binary("-",binary("^",x,number(3)),binary("*",number(3),x))
        def analyze(action,order=1,**options):
            result=self.analyze(cubic,analysis=action,selectedDerivativeOrder=order,**options)
            self.assertTrue(result["ok"],result)
            self.assertEqual(order,result["selectedDerivativeOrder"])
            return result
        roots=analyze("root")["points"]
        self.assertEqual(2,len(roots))
        for point,expected in zip(roots,(-1,1)):self.assertAlmostEqual(expected,point[0],delta=1e-7)
        self.assertEqual([[0.0,-3.0]],analyze("minimum")["points"])
        self.assertEqual([[-2.0,9.0],[2.0,9.0]],analyze("maximum")["points"])
        self.assertEqual([],analyze("inflection")["points"])
        self.assertEqual([[0.0,-3.0]],analyze("yintercept",a=100,b=101)["points"])
        self.assertAlmostEqual(3,analyze("derivative",a=.5)["value"])
        tangent=analyze("tangent",a=.5)
        self.assertEqual([[.5,-2.25]],tangent["points"]);self.assertAlmostEqual(3,tangent["value"])
        integral=analyze("integral",a=-1,b=1)
        self.assertAlmostEqual(-4,integral["value"]);self.assertTrue(integral["integralFill"])
        self.assertAlmostEqual(.5*math.sqrt(37)+math.asinh(6)/12,analyze("arclength",a=0,b=1)["value"])
        self.assertEqual([[0.0,0.0]],analyze("root",2)["points"])
        self.assertAlmostEqual(6,analyze("derivative",2,a=.5)["value"])
        self.assertAlmostEqual(0,analyze("integral",2,a=-1,b=1)["value"])
        self.assertAlmostEqual(2*math.sqrt(37),analyze("arclength",2,a=-1,b=1)["value"])
        tangent=analyze("tangent",2,a=1)
        self.assertEqual([[1.0,6.0]],tangent["points"]);self.assertAlmostEqual(6,tangent["value"])


    def test_implicit_derivative_analysis_preserves_traced_branches_and_intersections(self):
        hint=[.25,-.25/math.sqrt(1-.25**2)]
        tangent=self.analyze(circle,analysis="tangent",a=0,selectedDerivativeOrder=1,tracePoint=hint)
        self.assertTrue(tangent["ok"],tangent);self.assertAlmostEqual(-1,tangent["value"])
        integral=self.analyze(circle,analysis="integral",a=-.5,b=.5,selectedDerivativeOrder=1,tracePoint=hint)
        self.assertTrue(integral["ok"],integral);self.assertAlmostEqual(0,integral["value"])
        ambiguous=self.analyze(circle,analysis="tangent",a=0,selectedDerivativeOrder=1,tracePoint=[0,0])
        self.assertFalse(ambiguous["ok"]);self.assertIn("choose a branch",ambiguous["error"])
        roots=self.analyze(circle,analysis="root",a=-.8,b=.8,selectedDerivativeOrder=1)
        self.assertTrue(roots["ok"],roots);self.assertEqual([[0.0,0.0]],roots["points"])
        intersections=self.analyze(circle,number(2),analysis="intersection",a=-.8,b=.8,selectedDerivativeOrder=2)
        self.assertTrue(intersections["ok"],intersections);self.assertEqual(2,len(intersections["points"]))
        for point in intersections["points"]:
            self.assertAlmostEqual(math.sqrt(1-2**(-2/3)),abs(point[0]),delta=1e-7);self.assertAlmostEqual(2,point[1],delta=1e-7)

    def test_derivative_integrals_respect_poles_and_allow_integrable_endpoints(self):
        pole=self.analyze(binary("/",number(1),x),analysis="integral",a=-1,b=1,selectedDerivativeOrder=1)
        self.assertFalse(pole["ok"]);self.assertIn("continuous interval",pole["error"])
        endpoint=self.analyze({"kind":"call","value":"sqrt","args":[x]},analysis="integral",a=0,b=1,selectedDerivativeOrder=1)
        self.assertTrue(endpoint["ok"],endpoint);self.assertAlmostEqual(1,endpoint["value"])


    def analyze(self, *trees, **options):
        return json.loads(calc_engine.dispatch(json.dumps({
            "action":"graphAnalysis", "graphKind":"cartesian", "trees":trees,
            "analysis":"root", "a":-2, "b":2, "selected":0, "other":1, **options,
        })))

    def test_cartesian_mixes_functions_equations_and_contours_without_y_sliders(self):
        with self.subTest(scenario='cartesian_mixes_functions_equations_and_contours_without_y_sliders'):
            line = binary("+",x,number(1))
            result = self.graph(line,equation(y,line),circle,equation(x,number(.3)),graphKind="cartesian",
                                variables={"x":number(8),"y":number(9)},parameters={"x":8,"y":9})
            self.assertTrue(result["ok"],result)
            self.assertEqual([],result["parameters"])
            self.assertEqual([False,False,True,True],result["implicitCurves"])
            self.assertEqual(result["curves"][0],result["curves"][1])
            self.assertTrue(all(abs(xx*xx+yy*yy-1)<1e-6 for xx,yy in self.points(result,2)))
            self.assertTrue(all(abs(xx-.3)<1e-6 for xx,yy in self.points(result,3)))
        with self.subTest(scenario='cartesian_circle_analysis_searches_both_branches_and_chooses_traced_tangents'):
            roots=self.analyze(circle)
            self.assertTrue(roots["ok"],roots);self.assertEqual(2,len(roots["points"]))
            self.assertAlmostEqual(-1,roots["points"][0][0]);self.assertAlmostEqual(1,roots["points"][1][0])
            for action,expected in (("minimum",-1),("maximum",1)):
                result=self.analyze(circle,analysis=action)
                self.assertTrue(result["ok"],result);self.assertEqual(1,len(result["points"]))
                self.assertAlmostEqual(0,result["points"][0][0]);self.assertAlmostEqual(expected,result["points"][0][1])
            for tree in (equation(y,number(0)),equation(x,number(0))):
                result=self.analyze(circle,tree,analysis="intersection")
                self.assertTrue(result["ok"],result);self.assertEqual(2,len(result["points"]))
            missing=self.analyze(circle,analysis="tangent",a=0,b=0)
            self.assertFalse(missing["ok"]);self.assertIn("choose a branch",missing["error"])
            for py in (-math.sqrt(.75),math.sqrt(.75)):
                result=self.analyze(circle,analysis="tangent",a=.5,b=.5,tracePoint=[.5,py])
                self.assertTrue(result["ok"],result);self.assertAlmostEqual(-.5/py,result["value"])
                self.assertAlmostEqual(py,result["points"][0][1]);self.assertEqual(2,len(result["line"]))
            result=self.analyze(circle,analysis="tangent",a=1,b=1)
            self.assertTrue(result["ok"],result);self.assertTrue(result["vertical"])
            result=self.analyze(circle,analysis="integral",a=-1,b=1,tracePoint=[0,1])
            self.assertTrue(result["ok"],result);self.assertAlmostEqual(math.pi/2,result["value"])

    def graph(self, *trees, **options):
        return json.loads(calc_engine.dispatch(json.dumps({
            "action": "graph", "graphKind": "implicit", "angle": "RAD", "trees": trees,
            "min": -2, "max": 2, "yMin": -2, "yMax": 2, **options,
        })))

    def points(self, result, index=0):
        self.assertTrue(result["ok"], result.get("error"))
        return [point for point in result["curves"][index] if point is not None]

    def test_rotating_rose_with_trigonometric_coefficients_plots_with_the_normal_budget(self):
        t = symbol("t")
        cosine = {"kind":"call", "value":"cos", "args":[t]}
        sine = {"kind":"call", "value":"sin", "args":[t]}
        real = binary("-", binary("^",x,number(3)), binary("*",number(3),binary("*",x,y2)))
        imaginary = binary("-", binary("*",number(3),binary("*",x2,y)), binary("^",y,number(3)))
        rose = equation(binary("^",binary("+",x2,y2),number(4)),
                        binary("^",binary("+",binary("*",real,cosine),binary("*",imaginary,sine)),number(2)))
        for kind in ("cartesian", "implicit"):
            for phase, samples in ((0,200),(.4,500),(1,200),(math.pi/2,200)):
                with self.subTest(kind=kind, phase=phase, samples=samples):
                    result = self.graph(rose,graphKind=kind,parameters={"t":phase},samples=samples,
                                        min=-10,max=10,yMin=-5,yMax=5)
                    points = self.points(result)
                    self.assertEqual(["t"],result["parameters"])
                    self.assertGreater(len(points),100)
                    petals = [[]]
                    for point in result["curves"][0]:
                        if point is None: petals.append([])
                        else: petals[-1].append(point)
                    self.assertEqual(6,len(petals))
                    for path in petals:
                        self.assertEqual([0.0,0.0],path[0])
                        self.assertEqual(path[0],path[-1])
                        self.assertGreaterEqual(sum(0<math.hypot(*point)<.3 for point in path),6)
                    for px, py in points:
                        radius2 = px*px+py*py
                        wave = (px**3-3*px*py*py)*math.cos(phase)+(3*px*px*py-py**3)*math.sin(phase)
                        self.assertLess(abs(radius2**4-wave**2),1e-6)
                    # Every petal must appear, not only the highly singular origin.
                    for petal in range(6):
                        angle = phase/3+petal*math.pi/3
                        peak = (math.cos(angle),math.sin(angle))
                        self.assertLess(min(math.dist(point,peak) for point in points),.15)

    def test_disconnected_branches_have_breaks_and_poles_are_not_curves(self):
        with self.subTest(scenario='disconnected_branches_have_breaks_and_poles_are_not_curves'):
            result = self.graph(equation(binary("*", x, y), number(1)))
            points = self.points(result)
            self.assertTrue(any(xx < 0 for xx, _ in points))
            self.assertTrue(any(xx > 0 for xx, _ in points))
            self.assertIn(None, result["curves"][0])
            self.assertTrue(all(abs(xx*yy-1) < 1e-6 for xx, yy in points))
            pole = binary("/", number(1), binary("-", x, number(.013)))
            self.assertEqual([], self.points(self.graph(equation(pole, number(0)))))
            domain = {"kind": "call", "value": "sqrt", "args": [x]}
            points = self.points(self.graph(equation(domain, y)))
            self.assertTrue(all(xx >= 0 and yy >= 0 and abs(math.sqrt(xx)-yy) < 1e-5 for xx, yy in points))
        with self.subTest(scenario='slider_frames_reuse_compiled_contour_and_keep_degenerate_repeated_factors'):
            from calc_graph import _compiled_graph
            _compiled_graph.cache_clear()
            radius=equation(binary("+",x2,y2),symbol("a"))
            for value in (1,1.1,1.2):
                self.assertGreater(len(self.points(self.graph(radius,parameters={"a":value},samples=200))),100)
            self.assertEqual(1,_compiled_graph.cache_info().misses)
            points=self.points(self.graph(equation(y2,symbol("a")),parameters={"a":0}))
            self.assertGreater(len(points),100)
            self.assertTrue(all(abs(point[1])<1e-6 for point in points))

class GraphDispatchTests(unittest.TestCase):

    def graph(self, kind, tree, **options):
        result = json.loads(calc_engine.dispatch(json.dumps({
            "action": "graph", "graphKind": kind, "trees": [tree], "angle": "RAD",
            "min": 0, "max": 2*math.pi, **options,
        })))
        self.assertTrue(result["ok"], result.get("error"))
        return result


class GraphPerformanceTests(unittest.TestCase):

    def test_simplification_never_bridges_breaks_or_loses_a_closed_loop(self):
        points = [[-1,-1], [0,0], None, [1,1], [2,2]]
        result, parameters = simplify_samples(points, list(range(5)), {}, -2, 2)
        self.assertEqual(points, result)
        self.assertEqual(list(range(5)), parameters)
        circle = [[math.cos(i*2*math.pi/500), math.sin(i*2*math.pi/500)] for i in range(501)]
        result, parameters = simplify_samples(circle, list(range(501)), {"graphKind": "parametric", "xMin": -2, "xMax": 2}, 0, 2*math.pi)
        self.assertGreater(len(result), 30)
        self.assertEqual(circle[0], result[0]); self.assertEqual(circle[-1], result[-1])
        self.assertEqual(result, [circle[i] for i in parameters])

if __name__ == "__main__":
    unittest.main()
