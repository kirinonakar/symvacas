import math
import pathlib
import sys
import unittest

import sympy as s

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]/'app/src/main/python'))
from calc_graph_radial_sine import sine_contour


class RadialSineTests(unittest.TestCase):
    def setUp(self):
        self.x, self.y = s.symbols('x y', real=True)
        self.a = s.Symbol('a')
        self.q = self.x**2+self.y**2

    def sample(self, square_root=False, a=1, view=(-10, 10, -5, 5)):
        expression = s.sin(s.sqrt(self.a*self.q)) if square_root else s.sin(self.a*self.q)/self.q
        return sine_contour(expression, self.x, self.y, {self.a:a}, *view)

    def test_rings_have_all_visible_radii_and_no_connections_between_rings(self):
        for square_root in (False, True):
            for a in (.01, .3, 1, 4, -1):
                with self.subTest(square_root=square_root, a=a):
                    curve = self.sample(square_root, a)
                    paths = [[]]
                    for point in curve:
                        if point is None: paths.append([])
                        else: paths[-1].append(point)
                    paths = [path for path in paths if path]
                    radii = set()
                    for path in paths:
                        radius = math.hypot(*path[0])
                        radii.add(round(radius, 9))
                        self.assertTrue(square_root or radius > 0)
                        for x, y in path:
                            self.assertLessEqual(abs(x), 10+1e-10)
                            self.assertLessEqual(abs(y), 5+1e-10)
                            self.assertAlmostEqual(radius, math.hypot(x, y), delta=1e-10)
                        for p, q in zip(path, path[1:]):
                            # Sagitta against the exact circle at 80 pixels/unit.
                            mid = math.hypot((p[0]+q[0])/2, (p[1]+q[1])/2)
                            self.assertLessEqual((radius-mid)*80, .201)
                    if square_root:
                        expected = {0.0}
                        if a > 0:
                            expected |= {round(n*math.pi/math.sqrt(a), 9)
                                         for n in range(1, math.floor(math.sqrt(125*a)/math.pi)+1)}
                    else:
                        expected = {round(math.sqrt(n*math.pi/abs(a)), 9)
                                    for n in range(1, math.floor(abs(a)*125/math.pi)+1)}
                    self.assertEqual(expected, radii)

    def test_only_certified_expressions_use_the_shortcut_and_degeneracies_fall_back(self):
        x, y, a, q = self.x, self.y, self.a, self.q
        for expression in (s.sin(a*x*x+y*y), s.sin(a*q)+x, s.sin(a*q)/(q-1),
                           s.cos(a*q), s.sin(a*q)/x):
            self.assertIsNone(sine_contour(expression, x, y, {a:1}, -2, 2, -2, 2))
        for square_root in (False, True):
            self.assertIsNone(self.sample(square_root, 0))
        self.assertIsNone(sine_contour(s.sin(a*q), x, y, {a:1}, -2, 2, .01, 2, True))
        self.assertIsNone(self.sample(False, 1e5))  # bounded output, general fallback


if __name__ == '__main__': unittest.main()
