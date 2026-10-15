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


@lru_cache(maxsize=32)
def _contour_boundary_function(expression, x, y):
    program = _square_free_graph(expression, x, y)
    return graph_function((program, s.diff(program, x), s.diff(program, y)), (x, y))


def _clip_scaled_contour(points, sx, sy, xmin, xmax, ymin, ymax, function, radius, density):
    """Clip cached paths, refining only their intersections with viewport edges."""
    left, right = sorted((xmin/sx, xmax/sx))
    bottom, top = sorted((ymin/sy, ymax/sy))
    def code(point):
        return (1 if point[0]<left else 2 if point[0]>right else 0) | (4 if point[1]<bottom else 8 if point[1]>top else 0)
    def boundary(first, last, axis, edge):
        delta = last[axis]-first[axis]
        if delta == 0: return None
        other = 1-axis
        fraction = (edge-first[axis])/delta
        point = list(first)
        point[axis] = edge
        point[other] += fraction*(last[other]-first[other])
        # The chord is already within the cached pixel tolerance. Newton
        # projection keeps a clipped endpoint on the actual implicit curve.
        margin = radius/density/8
        low = max((left, bottom)[other], min(first[other],last[other])-margin)
        high = min((right, top)[other], max(first[other],last[other])+margin)
        best, error = point[:], math.inf
        for _ in range(12):
            value, dx, dy = function(*point)
            if abs(value)<error: best, error = point[:], abs(value)
            if error<=1e-12: break
            derivative = (dx, dy)[other]
            if derivative == 0 or not math.isfinite(derivative): break
            candidate = point[other]-value/derivative
            if not low<=candidate<=high or candidate==point[other]: break
            point[other] = candidate
        return best
    result, previous = [], None
    def gap():
        if result and result[-1] is not None: result.append(None)
    def transformed(point):
        return [min(xmax,max(xmin,point[0]*sx)), min(ymax,max(ymin,point[1]*sy))]
    for point in points:
        if point is None:
            previous=None;gap();continue
        if previous is None:
            previous=point;continue
        first, last = previous, point
        previous = point
        accepted = False
        for _ in range(8):
            ca, cb = code(first), code(last)
            if not (ca | cb): accepted=True;break
            if ca & cb: break
            outside = ca or cb
            axis = 1 if outside & 12 else 0
            edge = top if outside & 8 else bottom if outside & 4 else right if outside & 2 else left
            intersection = boundary(first,last,axis,edge)
            if intersection is None: break
            if ca: first=intersection
            else: last=intersection
        if not accepted:
            gap();continue
        a, b = transformed(first), transformed(last)
        if result and result[-1] is not None and result[-1]!=a: gap()
        if not result or result[-1] is None: result.append(a)
        if result[-1]!=b: result.append(b)
        if code(point): gap()
    if result and result[-1] is None: result.pop()
    return result


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
    if not math.isfinite(needed) or needed>2048: return None
    density = 512 if needed<=512 else 2**math.ceil(math.log2(needed))
    key = (normalized, x, y, radius, density)
    points = _scaled_contours.get(key)
    if points is None:
        for finer in (1024, 2048):
            if finer<=density: continue
            candidate = (normalized, x, y, radius, finer)
            if candidate in _scaled_contours:
                key=candidate;density=finer;points=_scaled_contours[candidate];break
    if points is None:
        sampled = implicit_samples(graph_function(_square_free_graph(normalized, x, y), (x, y)), -radius, radius, -radius, radius, density)
        segments = [[sampled[i], sampled[i+1]] for i in range(0, len(sampled)-2, 3)]
        points = _join_boundary_segments(segments, -radius, radius, -radius, radius)
        # Simplify once with a conservative normalized tolerance. At the
        # largest projection allowed by needed<=density this stays below 0.3px.
        inset = radius*32/density
        points, _ = simplify_samples(points, list(range(len(points))),
            {"graphKind":"implicit", "yMin":-inset, "yMax":inset}, -inset, inset)
        _scaled_contours[key] = points
        if len(_scaled_contours)>8: _scaled_contours.popitem(last=False)
    else:
        _scaled_contours.move_to_end(key)
    if any(point is not None and not (xmin<=point[0]*sx<=xmax and ymin<=point[1]*sy<=ymax) for point in points):
        return _clip_scaled_contour(points, sx, sy, xmin, xmax, ymin, ymax, _contour_boundary_function(normalized,x,y), radius, density)
    return [[point[0]*sx, point[1]*sy] if point is not None else None for point in points]
