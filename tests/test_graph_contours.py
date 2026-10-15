"""Scaled implicit contours: topology, near-zero axes, and cache isolation."""
import math
import pathlib
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]/"app/src/main/python"))
import sympy as s
import calc_graph_contours as contours
from calc_graph_planar import contour_curve
from calc_graph_sampling import implicit_samples


class ScaledContourTests(unittest.TestCase):
    def setUp(self):
        self.x, self.y = s.symbols("x y", real=True)
        self.a, self.b = s.symbols("a b")
        x, y, a, b = self.x, self.y, self.a, self.b
        self.heart = (-1+y**2/b**2+x**2/a**2)**3-x**2*y**3/(a**2*b**3)
        contours._scaled_contours.clear()

    def curve(self, a, b, expression=None, **bounds):
        return contour_curve(self.heart if expression is None else expression, self.x, self.y,
            {self.a:s.Float(a), self.b:s.Float(b)}, bounds.get("xmin", -10), bounds.get("xmax", 10),
            bounds.get("ymin", -5), bounds.get("ymax", 5), 112, bounds.get("logarithmic", False))

    def test_heart_reuses_complete_outline_through_tiny_negative_and_zero_axes(self):
        with patch.object(contours, "implicit_samples", wraps=implicit_samples) as sampler:
            for a,b in ((2,2),(1e-6,2),(2,1e-12),(-1e-80,1e-100),(0,1),(1,0),(-2,-2)):
                points = list(filter(lambda point:point is not None, self.curve(a,b)))
                if a==0 or b==0:
                    self.assertEqual([], points);continue
                normalized = [(px/a, py/b) for px,py in points]
                self.assertGreater(len(normalized),100)
                for u,v in normalized:
                    self.assertLess(abs((u*u+v*v-1)**3-u*u*v**3),1e-7)
                self.assertLess(min(u for u,v in normalized),-1.13)
                self.assertGreater(max(u for u,v in normalized),1.13)
                self.assertLess(min(v for u,v in normalized),-.99)
                self.assertGreater(max(v for u,v in normalized),1.23)
                for cusp in ((0,1),(0,-1)):
                    self.assertLess(min(math.dist(point,cusp) for point in normalized),.001)
            self.assertEqual(1,sampler.call_count,'shrinking or reflecting axes must not resample a huge viewport')

    def test_clipped_and_logarithmic_views_preserve_actual_roots(self):
        self.curve(1,1)
        with patch("calc_graph_planar.implicit_samples", wraps=implicit_samples) as sampler:
            clipped = self.curve(1,1,xmin=-.2,xmax=.2)
            self.assertEqual(0,sampler.call_count,'clipping reuses cached geometry instead of resampling the viewport')
            for px,py in filter(lambda point:point is not None,clipped):
                self.assertTrue(-.2<=px<=.2 and -5<=py<=5)
                self.assertLess(abs((px*px+py*py-1)**3-px*px*py**3),1e-5)
            positive = self.curve(1,1,ymin=.01,ymax=5,logarithmic=True)
            self.assertEqual(1,sampler.call_count)
            for px,py in filter(lambda point:point is not None,positive):
                self.assertGreater(py,0)
                self.assertLess(abs((px*px+py*py-1)**3-px*px*py**3),1e-5)
            self.assertEqual([],self.curve(1,1e-100,ymin=.01,ymax=5,logarithmic=True))
            self.assertEqual([],self.curve(0,1,ymin=.01,ymax=5,logarithmic=True))
            self.assertEqual(1,sampler.call_count)

    def test_all_viewport_edges_and_reflections_keep_roots_and_separate_visible_paths(self):
        self.curve(2,2)
        viewports = ((-10,10,-5,5),(-1,3,-2,2),(-3,1,-2,2),(-2,2,-1,3),(-2,2,-3,1))
        reference=[]
        for i in range(2401):
            u=-1.2+i/1000
            coefficient=abs(u)**(2/3)
            discriminant=coefficient*coefficient-4*u*u+4
            if discriminant>=0:
                reference.extend((u,(coefficient+sign*math.sqrt(discriminant))/2) for sign in (-1,1))
        with patch("calc_graph_planar.implicit_samples", side_effect=AssertionError('viewport grid must not restart at an edge')):
            for a,b in ((4.9,4.9),(-4.9,4.9),(4.9,-4.9),(-4.9,-4.9),(2,2),(-2,-2)):
                for xmin,xmax,ymin,ymax in viewports:
                    curve=self.curve(a,b,xmin=xmin,xmax=xmax,ymin=ymin,ymax=ymax)
                    expected=any(xmin<=u*a<=xmax and ymin<=v*b<=ymax for u,v in reference)
                    self.assertEqual(expected,bool(curve))
                    for point in curve:
                        if point is None: continue
                        px,py=point;u,v=px/a,py/b
                        self.assertTrue(xmin<=px<=xmax and ymin<=py<=ymax)
                        self.assertLess(abs((u*u+v*v-1)**3-u*u*v**3),1e-7)
                    for first,last in zip(curve,curve[1:]):
                        if first is not None and last is not None:
                            self.assertLess(math.dist((first[0]/a,first[1]/b),(last[0]/a,last[1]/b)),.3)
            strip=self.curve(1,1,xmin=-.2,xmax=.2)
            self.assertIn(None,strip,'separate top and bottom arcs must not connect across the clipped edge')
            edges=[point for point in strip if point is not None and abs(abs(point[0])-.2)<1e-12]
            self.assertGreaterEqual(len(edges),4)

    def test_changed_shape_and_repeated_factors_keep_their_own_geometry(self):
        self.curve(2,2)
        changed = self.curve(2,2,self.heart+s.Rational(1,5))
        self.assertEqual(2,len(contours._scaled_contours))
        for px,py in filter(lambda point:point is not None,changed):
            u,v=px/2,py/2
            self.assertLess(abs((u*u+v*v-1)**3-u*u*v**3+.2),1e-6)
        ellipse = (self.x**2/self.a**2+self.y**2/self.b**2-1)**2
        for px,py in filter(lambda point:point is not None,self.curve(2,1,ellipse)):
            self.assertLess(abs(px*px/4+py*py-1),1e-6)
        unbounded = self.x*self.y/(self.a*self.b)-1
        self.assertIsNone(contours.scaled_contour(unbounded,self.x,self.y,{self.a:2,self.b:2},-10,10,-5,5,112))


if __name__=="__main__": unittest.main()
