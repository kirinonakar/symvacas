import json
import math
import pathlib
import sys
import unittest
from unittest.mock import patch

import sympy as s

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]/'app/src/main/python'))
from calc_engine import dispatch
from calc_graph_radial_sine import sine_contour, _sine_specification, _circle_directions


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

    def test_cropped_arcs_cover_visible_circle_without_joining_across_the_view(self):
        view = (2, 4, -1, 1)
        curve = self.sample(False, 1, view)
        radii = {round(math.hypot(*p), 9) for p in curve if p is not None}
        expected = {round(math.sqrt(n*math.pi), 9) for n in range(2, 6)}
        self.assertEqual(expected, radii)
        for p in curve:
            if p is not None:
                self.assertTrue(2-1e-10 <= p[0] <= 4+1e-10 and abs(p[1]) <= 1+1e-10)
        # Independent dense angle reference checks both clipped sides of every
        # circle, rather than only checking residuals on generated vertices.
        segments = [(p, q) for p, q in zip(curve, curve[1:]) if p is not None and q is not None]
        for n in range(2, 6):
            radius = math.sqrt(n*math.pi)
            for i in range(1001):
                angle = 2*math.pi*i/1000
                point = (radius*math.cos(angle), radius*math.sin(angle))
                if not (2 <= point[0] <= 4 and abs(point[1]) <= 1): continue
                def distance(p, q):
                    dx, dy = q[0]-p[0], q[1]-p[1]
                    length = dx*dx+dy*dy
                    t = max(0, min(1, ((point[0]-p[0])*dx+(point[1]-p[1])*dy)/length)) if length else 0
                    return math.hypot(point[0]-p[0]-t*dx, point[1]-p[1]-t*dy)*400
                self.assertLess(min(distance(p, q) for p, q in segments), .201)
        tangent = self.sample(False, 1, (math.sqrt(math.pi), 4, -1, 1))
        self.assertIn([math.sqrt(math.pi), 0.0], tangent)
        # A panned view without the origin has no real locus for negative a.
        self.assertEqual([], self.sample(True, -1, view))

    def test_phase_offsets_and_factored_roots_keep_their_exact_zero_sets(self):
        for square_root in (False, True):
            for a in (-2, 2):
                for b in (-3, 3):
                    argument = self.a*self.q+b
                    expression = s.sin(s.sqrt(argument) if square_root else argument)
                    curve = sine_contour(expression, self.x, self.y, {self.a:a}, -2, 2, -2, 2)
                    radii = {round(math.hypot(*p), 9) for p in curve if p is not None}
                    expected = set()
                    for n in range(0 if square_root else -10, 11):
                        q = ((n*math.pi)**2 if square_root else n*math.pi)-b
                        q /= a
                        if 0 <= q <= 8: expected.add(round(math.sqrt(q), 9))
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

    def test_animation_reuses_certification_and_circle_trigonometry(self):
        _sine_specification.cache_clear()
        _circle_directions.cache_clear()
        for frame in range(12): self.sample(a=1+frame/100)
        self.assertEqual(1, _sine_specification.cache_info().misses)
        self.assertEqual(11, _sine_specification.cache_info().hits)
        self.assertGreater(_circle_directions.cache_info().hits, 100)
        self.assertLess(_circle_directions.cache_info().misses, 8)

    def test_dispatch_bypasses_grid_in_both_modes_and_keeps_zero_parameter_error(self):
        symbol = lambda name: {'kind':'symbol', 'value':name}
        number = lambda value: {'kind':'number', 'value':str(value)}
        binary = lambda op, left, right: {'kind':'binary', 'value':op, 'args':[left, right]}
        call = lambda name, arg: {'kind':'call', 'value':name, 'args':[arg]}
        q = binary('+', *(binary('^', symbol(axis), number(2)) for axis in 'xy'))
        phase = binary('*', symbol('a'), q)
        for kind in ('cartesian', 'implicit'):
            for tree in (binary('/', call('sin', phase), q), call('sin', call('sqrt', phase))):
                request = dict(action='graph', graphKind=kind, trees=[tree], angle='RAD',
                               min=-10, max=10, yMin=-5, yMax=5, samples=200)
                with patch('calc_graph_planar.implicit_samples', side_effect=AssertionError('grid used')):
                    for a in (1e-12, -1e-12, 1, -1, 4):
                        result = json.loads(dispatch(json.dumps({**request, 'parameters':{'a':a}})))
                        self.assertTrue(result['ok'], result)
                        self.assertEqual(['a'], result['parameters'])
                result = json.loads(dispatch(json.dumps({**request, 'parameters':{'a':0}})))
                self.assertFalse(result['ok'])
                self.assertIn('true everywhere', result['error'])


if __name__ == '__main__': unittest.main()
