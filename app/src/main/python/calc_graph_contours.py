"""Reuse contour geometry when parameters provably change only axis scales."""
from collections import OrderedDict
from functools import lru_cache
import math
import sympy as s
from calc_graph_common import _finite_real, _square_free_graph, graph_function
from calc_graph_sampling import implicit_samples, simplify_samples
from calc_graph_shading import _join_boundary_segments

_scaled_contours = OrderedDict()


@lru_cache(maxsize=32)
def _contour_scaling(expression, x, y):
    parameters = sorted(expression.free_symbols-{x, y}, key=str)
    if not 1 <= len(parameters) <= 2 or not expression.is_polynomial(x, y): return None
    choices = parameters+[s.Integer(1)]
    for scale_x in choices:
        for scale_y in choices:
            normalized = expression.subs({x:x*scale_x, y:y*scale_y}, simultaneous=True)
            if normalized.free_symbols-{x, y}: continue
            if normalized != 0 and normalized.is_polynomial(x, y):
                polynomial = s.Poly(normalized, x, y)
                if polynomial.total_degree() <= 12:
                    return normalized, scale_x, scale_y
    return None


@lru_cache(maxsize=32)
def _contour_radius(expression, x, y):
    """Certify a finite box by bounding homogeneous terms on a unit circle."""
    polynomial = s.Poly(expression, x, y)
    degree = polynomial.total_degree()
    if degree<2 or degree%2: return None
    groups = {}
    for powers, coefficient in polynomial.terms():
        number = _finite_real(coefficient)
        if number is None: return None
        groups.setdefault(sum(powers), []).append((powers, coefficient, number))
    leading = groups[degree]
    sign = 1 if leading[0][2]>0 else -1
    if any(px%2 or py%2 or sign*number<=0 for (px, py), _, number in leading): return None
    pure = {(px, py):sign*number for (px, py), _, number in leading}
    if (degree, 0) not in pure or (0, degree) not in pure: return None
    lower_bound = min(pure[(degree, 0)], pure[(0, degree)])*2**(1-degree/2)
    bounds = {}
    for order, terms in groups.items():
        homogeneous = s.Add(*(coefficient*x**px*y**py for (px, py), coefficient, _ in terms))
        radial = next((coefficient for (px, py), coefficient, _ in terms if px==order), s.Integer(0))
        if order%2==0 and s.expand(homogeneous-radial*(x*x+y*y)**(order//2))==0:
            bound = abs(float(radial))
            if order==degree: lower_bound=bound
        else:
            bound = sum(abs(number)*(px/order)**(px/2)*(py/order)**(py/2)
                        for (px, py), _, number in terms) if order else sum(abs(number) for _, _, number in terms)
        if order<degree: bounds[order]=bound
    radius = 1.0
    for _ in range(32):
        if lower_bound*radius**degree > 1.01*sum(bound*radius**order for order, bound in bounds.items()):
            return radius
        radius *= 1.5
    return None


def scaled_contour(expression, x, y, sliders, xmin, xmax, ymin, ymax, count, logarithmic=False):
    specification = _contour_scaling(expression, x, y)
    if specification is None: return None
    normalized, axis_x, axis_y = specification
    radius = _contour_radius(normalized, x, y)
    if radius is None: return None
    sx = _finite_real(axis_x if axis_x == 1 else (sliders or {}).get(axis_x))
    sy = _finite_real(axis_y if axis_y == 1 else (sliders or {}).get(axis_y))
    if sx is None or sy is None: return None
    # A zero divisor leaves no defined points in the original equation. Avoid
    # a singular symbolic substitution and keep the animation clock moving.
    if sx == 0 or sy == 0: return []
    if xmax<-radius*abs(sx) or xmin>radius*abs(sx) or ymax<-radius*abs(sy) or ymin>radius*abs(sy): return []
    if logarithmic: return None
    needed = max(2*radius*abs(sx)*count/(xmax-xmin), 2*radius*abs(sy)*count/(ymax-ymin))
    if not math.isfinite(needed) or needed>512: return None
    density = 512
    key = (normalized, x, y, radius, density)
    points = _scaled_contours.get(key)
    if points is None:
        sampled = implicit_samples(graph_function(_square_free_graph(normalized, x, y), (x, y)), -radius, radius, -radius, radius, density)
        segments = [[sampled[i], sampled[i+1]] for i in range(0, len(sampled)-2, 3)]
        points = _join_boundary_segments(segments, -radius, radius, -radius, radius)
        # Simplify once with a conservative normalized tolerance. At the
        # largest projection allowed by needed<=512 this stays below 0.3px.
        inset = radius/16
        points, _ = simplify_samples(points, list(range(len(points))),
            {"graphKind":"implicit", "yMin":-inset, "yMax":inset}, -inset, inset)
        _scaled_contours[key] = points
        if len(_scaled_contours)>8: _scaled_contours.popitem(last=False)
    else:
        _scaled_contours.move_to_end(key)
    if any(point is not None and not (xmin<=point[0]*sx<=xmax and ymin<=point[1]*sy<=ymax) for point in points): return None
    return [[point[0]*sx, point[1]*sy] if point is not None else None for point in points]
