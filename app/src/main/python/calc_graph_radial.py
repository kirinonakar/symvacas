"""Certified polar sampling for polynomial harmonic roses."""
from functools import lru_cache
import math
import sympy as s
from calc_graph_common import _finite_real, graph_function
from calc_limits import capped


@lru_cache(maxsize=64)
def _rose_specification(expression, x, y):
    """Prove F=c*r^(2n+2)+d*(A*Re(z^n)+B*Im(z^n))^2.

    Its nonnegative polar radius is sqrt(-d/c)*abs(A*cos(nθ)+B*sin(nθ)).
    Matching every polynomial coefficient avoids accepting a similar-looking
    equation with additional branches or a different locus.
    """
    terms = s.Add.make_args(expression)
    if len(terms) != 2: return None
    for radial, angular in (terms, terms[::-1]):
        c, radial = radial.as_independent(x, y)
        d, angular = angular.as_independent(x, y)
        if not radial.is_Pow or radial.base != x*x+y*y or not radial.exp.is_Integer: continue
        order = int(radial.exp)-1
        if not 1 <= order <= 8 or not angular.is_Pow or angular.exp != 2: continue
        try: polynomial = s.Poly(angular.base, x, y)
        except s.PolynomialError: continue
        if any(sum(powers) != order for powers, _ in polynomial.terms()): continue
        a = polynomial.coeff_monomial(x**order)
        b = polynomial.coeff_monomial(x**(order-1)*y)/order
        if all(s.expand(polynomial.coeff_monomial(x**(order-k)*y**k)
                        - (a if k%2 == 0 else b)*(-1)**(k//2)*math.comb(order,k)) == 0
               for k in range(order+1)):
            return order, (c, d, a, b)
    return None


@lru_cache(maxsize=32)
def _rose_geometry(order, density):
    """Closed petals with exact origin endpoints; immutable across frames."""
    points = []
    for petal in range(2*order):
        if points: points.append(None)
        center = petal*math.pi/order
        points.append((0.0, 0.0))
        for index in range(1,density):
            offset = (index/density-.5)*math.pi/order
            radius = math.cos(order*offset)
            angle = center+offset
            points.append((radius*math.cos(angle),radius*math.sin(angle)))
        points.append((0.0, 0.0))
    return tuple(points)


def radial_contour(expression, x, y, sliders, xmin, xmax, ymin, ymax, logarithmic=False):
    if logarithmic: return None
    specification = _rose_specification(expression, x, y)
    if specification is None: return None
    order, coefficients = specification
    values = [_finite_real(value) for value in graph_function(coefficients, (), sliders)()]
    if any(value is None for value in values): return None
    c, d, a, b = values
    # A vanished radial coefficient changes the locus into lines. Let the
    # general contour path handle that degeneration rather than dropping it.
    if c == 0: return None
    scale = -d/c
    if scale <= 0: return [[0.0,0.0]]
    amplitude = math.sqrt(scale)*math.hypot(a,b)
    if not math.isfinite(amplitude): return None
    if amplitude == 0: return [[0.0,0.0]]
    if xmin>amplitude or xmax<-amplitude or ymin>amplitude or ymax<-amplitude: return []
    # The second derivative of a unit petal is bounded by n²+1. Choose a
    # nominal 0.2px chord tolerance at 800px, subject to the graph point budget.
    pixels = amplitude*max(800/(xmax-xmin),800/(ymax-ymin))
    if not math.isfinite(pixels): return None
    needed = max(16,math.ceil(math.pi/order*math.sqrt((order*order+1)*pixels/1.6)))
    density = 2**math.ceil(math.log2(needed))
    density = capped(density,2**math.floor(math.log2(max(16,1600//(2*order)))))
    angle = math.atan2(b,a)/order
    cosine, sine = amplitude*math.cos(angle), amplitude*math.sin(angle)
    return [[cosine*p[0]-sine*p[1],sine*p[0]+cosine*p[1]] if p is not None else None
            for p in _rose_geometry(order,density)]
