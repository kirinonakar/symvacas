"""Direct sampling of algebraic curves with a known real branch."""
from functools import lru_cache
import math
import sympy as s
from calc_graph_common import _finite_real, graph_function


@lru_cache(maxsize=64)
def _affine_coefficients(expression, x):
    try:
        polynomial = s.Poly(expression, x)
        if polynomial.degree() <= 1:
            return polynomial.nth(1), polynomial.nth(0)
    except s.PolynomialError:
        pass
    return None


def affine_samples(expression, x, sliders, xmin, xmax, logarithmic=False):
    # Logarithmic projection bends lines; retain adaptive sampling there.
    if logarithmic: return None
    coefficients = _affine_coefficients(expression, x)
    if coefficients is None: return None
    try:
        slope, intercept = graph_function(coefficients, (), sliders)()
        if any(_finite_real(value) is None for value in (slope, intercept)): return None
        positions = {xmin, xmax}
        if xmin < 0 < xmax: positions.add(0.0)
        if slope:
            zero = -intercept/slope
            if xmin < zero < xmax: positions.add(zero)
        points = [[at, slope*at+intercept] for at in sorted(positions)]
        if all(_finite_real(point[1]) is not None for point in points): return points
    except (ValueError, TypeError, ZeroDivisionError, OverflowError):
        pass
    return None


@lru_cache(maxsize=64)
def _odd_power_coefficients(expression, x, y):
    # Polynomial coordinates exclude poles and other missing-domain points.
    # C*y**n + A*x**2 + B*x + D = 0 has one real y branch for odd n.
    # Also accept A*x**3 + D, whose viewport crossings have one real root.
    if not expression.is_polynomial(x, y): return None
    polynomial = s.Poly(expression, y)
    degree = polynomial.degree()
    if degree not in (3, 5, 7, 9, 11): return None
    if any(polynomial.nth(index) != 0 for index in range(1, degree)): return None
    coefficient = polynomial.nth(degree)
    constant = s.Poly(polynomial.nth(0), x)
    if coefficient.has(x): return None
    x_degree = 2
    if constant.degree() > 2:
        if constant.degree() != 3 or constant.nth(2) != 0 or constant.nth(1) != 0: return None
        x_degree = 3
    return degree, x_degree, (constant.nth(x_degree), constant.nth(1), constant.nth(0), coefficient)


def _quadratic_roots(a, b, c):
    if a == 0: return (-c/b,) if b else ()
    discriminant = b*b-4*a*c
    if discriminant < 0: return ()
    q = -.5*(b+math.copysign(math.sqrt(discriminant), b))
    return (q/a, c/q) if q else (-b/(2*a),)


def _sample_power_branch(function, low, high, bounds, count):
    """Bound chord error in screen space, including nearly vertical tangents."""
    xmin, xmax, ymin, ymax = bounds
    sx, sy = 800/(xmax-xmin), 800/(ymax-ymin)
    points = [[low, function(low)]]
    probes = 0
    def refine(first, last, depth):
        nonlocal probes
        probes += 3
        if probes > 16384: raise OverflowError
        dx, dy = (last[0]-first[0])*sx, (last[1]-first[1])*sy
        length = math.hypot(dx, dy)
        middle = None
        error = 0.0
        for fraction in (.25, .5, .75):
            at = first[0]+(last[0]-first[0])*fraction
            point = [at, function(at)]
            if fraction == .5: middle = point
            if length:
                error = max(error, abs(dx*(point[1]-first[1])*sy-dy*(point[0]-first[0])*sx)/length)
        if error > .15 and depth < 28 and first[0] < middle[0] < last[0]:
            refine(first, middle, depth+1)
            refine(middle, last, depth+1)
        else:
            points.append(last)
    intervals = max(4, min(32, count//8))
    for index in range(1, intervals+1):
        at = high if index == intervals else low+(high-low)*index/intervals
        refine(points[-1], [at, function(at)], 0)
    return points


def odd_power_contour(expression, x, y, sliders, xmin, xmax, ymin, ymax, count, logarithmic=False):
    if logarithmic: return None
    specification = _odd_power_coefficients(expression, x, y)
    if specification is None: return None
    degree, x_degree, coefficients = specification
    try:
        a, b, d, c = graph_function(coefficients, (), sliders)()
        if not c or any(_finite_real(value) is None for value in (a, b, d, c)): return None
        known = {}
        def function(at):
            if at in known: return known[at]
            value = -(a*at*at*at+d)/c if x_degree == 3 else -((a*at+b)*at+d)/c
            result = math.cbrt(value) if degree == 3 else math.copysign(abs(value)**(1/degree), value)
            if not math.isfinite(result): raise OverflowError
            return result
        # Cut at viewport edges and vertical tangents before adaptive sampling.
        # This preserves narrow visible sections even as parameters cross zero.
        cuts = {xmin, xmax}
        for level in (ymin, 0.0, ymax):
            constant = d+c*level**degree
            roots = ((math.cbrt(-constant/a),) if a else ()) if x_degree == 3 else _quadratic_roots(a, b, constant)
            for root in roots:
                if xmin <= root <= xmax:
                    if root in known and known[root] != level: return None
                    cuts.add(root); known[root] = level
        if x_degree == 3:
            # Split at the horizontal tangent as well as the y=0 crossing;
            # otherwise a nearly straight S curve can hide its small bend.
            if xmin < 0 < xmax: cuts.add(0.0)
        elif a:
            vertex = -b/(2*a)
            if xmin < vertex < xmax: cuts.add(vertex)
        cuts = sorted(cuts)
        points = []
        previous = None
        visible_edges = set()
        for low, high in zip(cuts, cuts[1:]):
            if not ymin <= function((low+high)/2) <= ymax: continue
            part = _sample_power_branch(function, low, high, (xmin, xmax, ymin, ymax), count)
            if points and previous != low: points.append(None)
            points.extend(part if previous != low else part[1:])
            previous = high
            visible_edges.update((low, high))
        # Preserve isolated contacts with a viewport edge.
        for at in cuts:
            if at not in visible_edges and ymin <= function(at) <= ymax:
                point = [at, function(at)]
                points.extend((None, point, point[:], None))
        return points
    except (ValueError, TypeError, ZeroDivisionError, OverflowError):
        # Degenerate coefficients and extreme ranges keep the general contour path.
        return None
