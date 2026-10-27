import json
import math
import pathlib
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]/"app/src/main/python"))
import calc_engine
import sympy as s
from calc_graph_algebraic import affine_samples, odd_power_contour


def number(value): return {"kind":"number", "value":str(value)}
def symbol(name): return {"kind":"symbol", "value":name}
def binary(op, left, right): return {"kind":"binary", "value":op, "args":[left, right]}
def equation(left, right): return {"kind":"relation", "value":"=", "args":[left, right]}

x, y, a = map(symbol, ("x", "y", "a"))
line = binary("*", binary("/", number(1), a), x)
cubic = equation(binary("+", binary("^", x, number(2)), binary("^", y, number(3))), a)
cubic_sum = equation(binary("+", binary("^", x, number(3)), binary("^", y, number(3))), a)
cubic_square = equation(binary("+", binary("^", x, number(3)), binary("^", y, number(2))), a)


class AlgebraicGraphTests(unittest.TestCase):
    def graph(self, *trees, **options):
        result = json.loads(calc_engine.dispatch(json.dumps({"action":"graph", "graphKind":"cartesian",
            "trees":trees, "angle":"RAD", "min":-10, "max":10, "yMin":-5, "yMax":5,
            "samples":200, **options})))
        self.assertTrue(result["ok"], result)
        return result

    def test_reported_animation_keeps_real_branches_and_undefined_zero_divisor(self):
        for value in (0, 1e-12, -1e-12, .01, -.01, 1, -1, 5):
            with self.subTest(a=value):
                # The cubic avoids a plane search even at a=0. The undefined
                # bare line can still use the existing fallback at that frame.
                with patch("calc_graph_planar.implicit_samples", side_effect=AssertionError("plane search")):
                    self.graph(cubic, parameters={"a":value})
                result = self.graph(line, cubic, parameters={"a":value})
                self.assertEqual(["a"], result["parameters"])
                self.assertEqual([value == 0, True], result["implicitCurves"])
                straight, curve = result["curves"]
                if value == 0:
                    self.assertEqual([], straight)
                else:
                    self.assertLessEqual(len(straight), 4)
                    self.assertIn([0.0, 0.0], straight)
                    for px, py in straight: self.assertAlmostEqual(px, value*py, delta=1e-12)
                self.assertTrue(curve)
                self.assertLess(len(curve), 350)
                for px, py in filter(lambda p:p is not None, curve):
                    self.assertAlmostEqual(value, px*px+py**3, delta=1e-9)
                    self.assertTrue(-10-1e-9 <= px <= 10+1e-9 and -5-1e-9 <= py <= 5+1e-9)
                if value > 0:
                    for root in (-math.sqrt(value), math.sqrt(value)):
                        self.assertTrue(any(point is not None and abs(point[0]-root)<1e-12 and point[1]==0 for point in curve))

    def test_contour_preserves_subpixel_shape_and_narrow_viewport_sections(self):
        self.check_contour_shape(cubic, 2)

    def test_cubic_sum_preserves_shape_at_zero_and_nearly_vertical_tangents(self):
        self.check_contour_shape(cubic_sum, 3)

    def test_cubic_square_preserves_both_branches_cusp_and_narrow_sections(self):
        self.check_contour_shape(cubic_square, 3, 2)

    def check_contour_shape(self, tree, x_power, y_power=3):
        views = [(-10,10,-5,5), (-2,2,-.01,.01), (.999,1.001,-.005,.005),
                 (-.001,.001,-.0001,.0001), (2,4,-4,-1), (-3,3,1,2)]
        for value in (-1, 0, 1e-12, -1e-12, .5, 1, 5):
            for xmin,xmax,ymin,ymax in views:
                with self.subTest(a=value, view=(xmin,xmax,ymin,ymax)):
                    curve = self.graph(tree, parameters={"a":value}, min=xmin,max=xmax,yMin=ymin,yMax=ymax)["curves"][0]
                    segments = [(p,q) for p,q in zip(curve,curve[1:]) if p is not None and q is not None]
                    # Probe in both coordinates to cover the nearly vertical parts.
                    expected = []
                    for index in range(201):
                        px = xmin+(xmax-xmin)*index/200
                        v = value-px**x_power
                        if y_power == 3:
                            expected.append((px, math.cbrt(v)))
                        elif v >= 0:
                            expected.extend(((px, math.sqrt(v)),(px,-math.sqrt(v))))
                        py = ymin+(ymax-ymin)*index/200
                        squared = value-py**y_power
                        if x_power == 3:
                            expected.append((math.cbrt(squared),py))
                        elif squared >= 0:
                            expected.extend(((math.sqrt(squared),py),(-math.sqrt(squared),py)))
                    sx,sy = 800/(xmax-xmin),800/(ymax-ymin)
                    def distance(point,p,q):
                        dx,dy = (q[0]-p[0])*sx,(q[1]-p[1])*sy
                        vx,vy = (point[0]-p[0])*sx,(point[1]-p[1])*sy
                        t = max(0,min(1,(vx*dx+vy*dy)/(dx*dx+dy*dy))) if dx or dy else 0
                        return math.hypot(vx-t*dx,vy-t*dy)
                    for point in expected:
                        if xmin <= point[0] <= xmax and ymin <= point[1] <= ymax:
                            self.assertTrue(segments, (value,point,curve))
                            self.assertLess(min(distance(point,p,q) for p,q in segments), .35, (value,point))

    def test_cubic_square_animation_bypasses_grid_in_both_graph_modes(self):
        for kind in ("cartesian", "implicit"):
            for value in (0, 1e-12, -1e-12, .01, -.01, 1, -1, 5):
                with self.subTest(kind=kind, a=value):
                    with patch("calc_graph_planar.implicit_samples", side_effect=AssertionError("plane search")):
                        result = self.graph(cubic_square, parameters={"a":value}, graphKind=kind)
                    curve = result["curves"][0]
                    self.assertEqual(["a"],result["parameters"])
                    self.assertTrue(curve)
                    self.assertLess(len(curve),350)
                    for px,py in filter(lambda p:p is not None,curve):
                        self.assertAlmostEqual(value,px**3+py**2,delta=1e-9)
                        self.assertTrue(-10-1e-9<=px<=10+1e-9 and -5-1e-9<=py<=5+1e-9)
                    targets = [(math.cbrt(value),0)]
                    if value >= 0: targets.extend(((0,math.sqrt(value)),(0,-math.sqrt(value))))
                    for target in targets:
                        self.assertTrue(any(p is not None and math.dist(p,target)<1e-12 for p in curve))
                    self.assertTrue(any(p is not None and p[1]>0 for p in curve))
                    self.assertTrue(any(p is not None and p[1]<0 for p in curve))

    def test_transposed_contour_keeps_degenerate_coefficients_and_log_domain(self):
        varying = equation(binary("+",binary("*",a,binary("^",x,number(3))),binary("^",y,number(2))),number(1))
        result = self.graph(varying,parameters={"a":0})
        points = [p for p in result["curves"][0] if p is not None]
        self.assertTrue(any(py>0 for px,py in points))
        self.assertTrue(any(py<0 for px,py in points))
        self.assertTrue(all(abs(abs(py)-1)<1e-7 for px,py in points))
        result = self.graph(cubic_square,parameters={"a":1},yLog=True,yMin=.01,yMax=5)
        self.assertTrue(any(p is not None for p in result["curves"][0]))
        self.assertTrue(all(p is None or p[1]>0 for p in result["curves"][0]))

    def test_cubic_sum_animation_bypasses_grid_and_keeps_axis_contacts(self):
        for kind in ("cartesian", "implicit"):
            for value in (0, 1e-12, -1e-12, .01, -.01, 1, -1, 5):
                with self.subTest(kind=kind, a=value):
                    with patch("calc_graph_planar.implicit_samples", side_effect=AssertionError("plane search")):
                        result = self.graph(cubic_sum, parameters={"a":value}, graphKind=kind)
                    self.assertEqual(["a"],result["parameters"])
                    curve = result["curves"][0]
                    self.assertTrue(curve)
                    self.assertLess(len(curve), 250)
                    for px,py in filter(lambda p:p is not None,curve):
                        self.assertAlmostEqual(value,px**3+py**3,delta=1e-9)
                        self.assertTrue(-10-1e-9<=px<=10+1e-9 and -5-1e-9<=py<=5+1e-9)
                    root = math.cbrt(value)
                    for target in ((root,0),(0,root)):
                        self.assertTrue(any(p is not None and math.dist(p,target)<1e-12 for p in curve))

    def test_cubic_sum_parameter_coefficients_preserve_degeneracies(self):
        sx,sy,sa,sb = s.symbols("x y a b",real=True)
        expression = sa*sx**3+sb*sy**3-1
        for ax,by in ((-2,3),(2,-3),(0,1)):
            curve = odd_power_contour(expression,sx,sy,{sa:ax,sb:by},-2,2,-2,2,112)
            self.assertIsNotNone(curve)
            self.assertTrue(curve)
            for px,py in filter(lambda p:p is not None,curve):
                self.assertAlmostEqual(1,ax*px**3+by*py**3,delta=1e-9)
        self.assertIsNone(odd_power_contour(expression,sx,sy,{sa:1,sb:0},-2,2,-2,2,112))
        # Extra cubic terms require finding all real crossings; retain fallback.
        self.assertIsNone(odd_power_contour(sx**3-sx+sy**3,sx,sy,{},-2,2,-2,2,112))

    def test_degenerate_coefficients_use_full_contour_and_logarithmic_sampling(self):
        varying = equation(binary("+",binary("^",x,number(2)),binary("*",a,binary("^",y,number(3)))),number(1))
        result = self.graph(varying,parameters={"a":0})
        points = [p for p in result["curves"][0] if p is not None]
        self.assertTrue(points)
        self.assertTrue(all(abs(abs(px)-1)<1e-7 for px,py in points))
        for tree in (line,cubic):
            result = self.graph(tree,parameters={"a":1},yLog=True,yMin=.01,yMax=5)
            self.assertTrue(any(p is not None for p in result["curves"][0]))
            self.assertTrue(all(p is None or p[1]>0 for p in result["curves"][0]))

    def test_direct_sampling_rejects_poles_and_preserves_shifted_lines(self):
        sx,sy,sa = s.symbols("x y a",real=True)
        self.assertIsNone(odd_power_contour(sx**2+sy**3-1/sx,sx,sy,{},-2,2,-2,2,112))
        self.assertIsNone(odd_power_contour(sa*sy**3+sx**2-1,sx,sy,{sa:0},-2,2,-2,2,112))
        self.assertEqual([[-3,-7],[-2,0],[0,14],[5,49]],affine_samples(7*sx+14,sx,{},-3,5))
        self.assertIsNone(affine_samples(sx+1,sx,{},-3,5,True))

    def test_other_odd_powers_and_coefficient_signs_keep_the_real_zero_set(self):
        sx,sy,sa = s.symbols("x y a",real=True)
        for degree in (3,5,7,9,11):
            for coefficient in (-2,2):
                expression = coefficient*sy**degree+sa*sx*sx+.3*sx-1
                for value in (-1,0,1):
                    points = odd_power_contour(expression,sx,sy,{sa:value},-2,2,-2,2,112)
                    self.assertIsNotNone(points)
                    self.assertTrue(points)
                    for px,py in filter(lambda p:p is not None,points):
                        self.assertAlmostEqual(0,coefficient*py**degree+value*px*px+.3*px-1,delta=1e-9)
        cartesian = self.graph(cubic,parameters={"a":.5})
        implicit = self.graph(cubic,parameters={"a":.5},graphKind="implicit")
        self.assertEqual(cartesian["curves"],implicit["curves"])


if __name__ == "__main__": unittest.main()
