"""Analytic zero contours for certified radial sine expressions."""
from functools import lru_cache
import math
import sympy as s
from calc_graph_common import _finite_real, graph_function
from calc_limits import within_limit


@lru_cache(maxsize=64)
def _sine_specification(expression, x, y):
    scale, body = expression.as_independent(x, y)
    numerator, denominator = s.fraction(body)
    # Keep the original puncture: sin(a*r²)/r² is undefined at the origin.
    if denominator not in (s.Integer(1), x*x+y*y) or numerator.func != s.sin:
        return None
    phase = numerator.args[0]
    multiplier, dependent = phase.as_independent(x, y)
    square_root = dependent.is_Pow and dependent.exp == s.S.Half
    # SymPy can factor sqrt(a*(x²+y²)) into sqrt(a)*sqrt(x²+y²).
    # sin(z)=0 iff z=n*pi; squaring this factored phase preserves its zero
    # set, including the single origin when its square is negative elsewhere.
    if square_root: phase = s.expand(multiplier**2*dependent.base)
    try: polynomial = s.Poly(phase, x, y)
    except s.PolynomialError: return None
    a = polynomial.coeff_monomial(x*x)
    b = polynomial.coeff_monomial(1)
    if a == 0 or s.expand(phase-a*(x*x+y*y)-b) != 0: return None
    return (scale, a, b), square_root, denominator != 1


@lru_cache(maxsize=32)
def _circle_directions(density):
    return tuple((math.cos(2*math.pi*i/density), math.sin(2*math.pi*i/density))
                 for i in range(density))


def _circle_arcs(radius, xmin, xmax, ymin, ymax):
    """Clip in angle space so no chord joins different visible arcs or rings."""
    cuts = {0.0, 2*math.pi}
    for edge in (xmin, xmax):
        if -radius <= edge <= radius:
            angle = math.acos(edge/radius)
            cuts.update((angle, 2*math.pi-angle))
    for edge in (ymin, ymax):
        if -radius <= edge <= radius:
            angle = math.asin(edge/radius) % (2*math.pi)
            cuts.update((angle, (math.pi-angle) % (2*math.pi)))
    cuts = sorted(cuts)
    arcs = []
    for start, end in zip(cuts, cuts[1:]):
        mid = (start+end)/2
        px, py = radius*math.cos(mid), radius*math.sin(mid)
        if xmin <= px <= xmax and ymin <= py <= ymax:
            if arcs and arcs[-1][1] == start: arcs[-1][1] = end
            else: arcs.append([start, end])
    # A ring can touch an edge without having a visible interval (e.g. the
    # nearest circle in a panned view). Retain that isolated contact as well.
    for angle in cuts[:-1]:
        if any(start <= angle <= end for start, end in arcs): continue
        px, py = radius*math.cos(angle), radius*math.sin(angle)
        if xmin <= px <= xmax and ymin <= py <= ymax: arcs.append([angle, angle])
    arcs.sort()
    return arcs


def sine_contour(expression, x, y, sliders, xmin, xmax, ymin, ymax, logarithmic=False):
    if logarithmic: return None
    specification = _sine_specification(expression, x, y)
    if specification is None: return None
    coefficients, square_root, punctured = specification
    try: values = [_finite_real(v) for v in graph_function(coefficients, (), sliders)()]
    except (ValueError, TypeError, ZeroDivisionError, OverflowError): return None
    if any(v is None for v in values): return None
    scale, a, b = values
    # At zero the equation may hold everywhere. Preserve the general path's
    # validation rather than returning a misleading finite collection of rings.
    if scale == 0 or a == 0: return None
    nearest = lambda low, high: 0 if low <= 0 <= high else min(abs(low), abs(high))
    rmin = math.hypot(nearest(xmin, xmax), nearest(ymin, ymax))
    rmax = math.hypot(max(abs(xmin), abs(xmax)), max(abs(ymin), abs(ymax)))
    low, high = sorted((a*rmin*rmin+b, a*rmax*rmax+b))
    if not all(map(math.isfinite, (low, high))): return None
    if square_root:
        if high < 0: return []
        low, high = math.sqrt(max(0, low)), math.sqrt(high)
    first, last = math.ceil(low/math.pi), math.floor(high/math.pi)
    # Above the analytic path's bounded output budget use the general sampler.
    if not within_limit(last-first+1, 512): return None
    result = []
    pixels_per_unit = max(800/(xmax-xmin), 800/(ymax-ymin))
    for index in range(first, last+1):
        phase = index*math.pi
        squared = ((phase*phase if square_root else phase)-b)/a
        if squared < 0: continue
        radius = math.sqrt(squared)
        if not rmin <= radius <= rmax: continue
        if radius == 0:
            if not punctured:
                if result: result.append(None)
                result.append([0.0, 0.0])
            continue
        # r*(1-cos(step/2)) <= r*step²/8: at most 0.2 nominal
        # screen pixels of chord error, including at clipped arc endpoints.
        needed = max(16, math.ceil(2*math.pi*math.sqrt(radius*pixels_per_unit/1.6)))
        density = 2**math.ceil(math.log2(needed))
        if not within_limit(density, 8192): return None
        directions = _circle_directions(density)
        step = 2*math.pi/density
        for start, end in _circle_arcs(radius, xmin, xmax, ymin, ymax):
            if result: result.append(None)
            point = lambda angle: [radius*math.cos(angle), radius*math.sin(angle)]
            result.append(point(start))
            for vertex in range(math.floor(start/step)+1, math.ceil(end/step)):
                dx, dy = directions[vertex % density]
                result.append([radius*dx, radius*dy])
            # Close full rings exactly, avoiding a sin(2*pi) seam.
            result.append(point(start) if end-start == 2*math.pi else point(end))
    return result
