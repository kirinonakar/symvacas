"""Symbolic graph programs, bounded caches, coordinates, and parameter binding."""
from calc_shared import require
from collections import OrderedDict
from functools import lru_cache
import json
import math
import sympy as s

_graph_programs = OrderedDict()


def graph_expressions(engine, trees, axes):
    """Reuse symbolic programs across frames; all evaluation context is in the key."""
    context = {"trees": trees, "axes": axes, "precision": engine.precision,
               "displayDigits": engine.display_digits, "angle": engine.angle,
               "variables": engine.variables, "functions": engine.functions,
               "assumptions": engine.assumptions, "sequence": engine.allow_sequence_calls,
               "bindings": {name:s.srepr(value) for name,value in engine.bindings.items()}}
    key = json.dumps(context, sort_keys=True, separators=(",", ":"))
    # Random calls must run anew, including those inside stored definitions.
    cacheable = not any('"value":"'+name+'"' in key for name in ("rnd", "rand", "randInt"))
    if cacheable and key in _graph_programs:
        _graph_programs.move_to_end(key)
        return _graph_programs[key]
    def freeze(value):
        return tuple(freeze(item) for item in value) if isinstance(value, (list, tuple)) else value
    expressions = tuple(freeze(engine.build(tree)) for tree in trees)
    if cacheable:
        _graph_programs[key] = expressions
        if len(_graph_programs) > 32: _graph_programs.popitem(last=False)
    return expressions


@lru_cache(maxsize=64)
def _compiled_graph(axes, expression):
    """Bounded cache of immutable symbolic programs, never engine/request state."""
    return s.lambdify(axes, expression, modules="math", cse=True, docstring_limit=0)


@lru_cache(maxsize=64)
def _square_free_graph(expression, x, y):
    if expression.is_polynomial(x, y):
        polynomial = s.Poly(expression, x, y)
        # GCDs over symbolic expression coefficients (e.g. sin(t), cos(t))
        # can exhaust the graph budget. Keep the reusable sampling program;
        # contour_curve also checks repeated factors after binding sliders.
        if polynomial.domain.is_EX and expression.free_symbols-{x, y}:
            return expression
        if polynomial.total_degree() <= 12:
            square_free = polynomial.sqf_part()
            if square_free.total_degree() != polynomial.total_degree():
                return square_free.as_expr()
    return expression


def graph_function(expression, axes, sliders=None):
    # Keep slider values as numeric arguments so animation doesn't recompile.
    if isinstance(expression, (list, tuple)):
        expression = tuple(expression)
        symbols = set().union(*(item.free_symbols for item in expression))
    else:
        symbols = expression.free_symbols
    parameters = tuple(sorted(symbols-set(axes), key=str))
    if not parameters:
        return _compiled_graph(tuple(axes), expression)
    values = tuple(float((sliders or {})[symbol]) for symbol in parameters)
    raw = _compiled_graph(tuple(axes)+parameters, expression)
    return lambda *args: raw(*args, *values)


def bind_graph_parameters(engine, request):
    # A visible graph parameter takes precedence over a separately stored variable.
    for name in request.get("parameters",{}): engine.bindings[str(name)]=engine.symbol(str(name))


def _finite_real(value):
    try:
        value = float(value)
        return value if math.isfinite(value) and abs(value) < 1e100 else None
    except (TypeError, ValueError, ZeroDivisionError, OverflowError):
        return None


def parameter_values(engine, request):
    """Slider values for free graph parameters such as a, b and c."""
    sliders = {}
    for name, value in (request.get("parameters") or {}).items():
        number = _finite_real(value)
        if number is not None:
            sliders[engine.symbol(str(name))] = s.Float(number, engine.precision)
    return sliders


def resolved_parameters(engine, request, expressions, excluded):
    """Slider values plus unit defaults so a curve still plots before its sliders move."""
    sliders = parameter_values(engine, request)
    for name in parameter_names(expressions, excluded):
        sliders.setdefault(engine.symbol(name), s.Float(1.0, engine.precision))
    return sliders


def parameter_names(expressions, excluded):
    """Free symbols that the graphing panel can expose as sliders."""
    names = set()
    for expression in expressions:
        if isinstance(expression, (list, tuple)):
            names |= parameter_names(expression, excluded)
            continue
        for symbol in getattr(expression, "free_symbols", set()):
            if str(symbol) not in excluded: names.add(str(symbol))
    return names


def substitute_parameters(expression, sliders):
    if not sliders: return expression
    if isinstance(expression, (list, tuple)):
        return [substitute_parameters(item, sliders) for item in expression]
    return expression.subs(sliders) if getattr(expression, "subs", None) else expression


@lru_cache(maxsize=64)
def _piecewise_boundary_polynomials(expression, x):
    """Compile branch topology once, independently of animated slider values."""
    polynomials = set()
    for piece in expression.atoms(s.Piecewise):
        for _, condition in piece.args:
            for relation in condition.atoms(s.core.relational.Relational):
                difference = relation.lhs-relation.rhs
                try:
                    polynomial = s.Poly(difference, x)
                    if 1 <= polynomial.degree() <= 4:
                        polynomials.add(tuple(polynomial.all_coeffs()))
                except s.PolynomialError:
                    pass
    return tuple(polynomials)


def piecewise_boundaries(expression, x, sliders, xmin, xmax):
    boundaries = set()
    for coefficients in _piecewise_boundary_polynomials(expression, x):
        try:
            values = list(graph_function(coefficients, (), sliders)())
            if any(_finite_real(value) is None for value in values): continue
            # Parameter changes may lower the polynomial's degree, including
            # turning an entire condition into a constant.
            while values and values[0] == 0: values.pop(0)
            if len(values) <= 1: continue
            if len(values) == 2:
                roots = [-values[1]/values[0]]
            else:
                # Retain symbolic root handling for nonlinear branch cuts;
                # only their coefficients need binding, never the branch body.
                polynomial = s.Poly.from_list(values, x)
                roots = s.solve(polynomial.as_expr(), x)
            for root in roots:
                value = _finite_real(root)
                if value is not None and xmin < value < xmax: boundaries.add(value)
        except (KeyError, s.PolynomialError, NotImplementedError, ValueError, TypeError, ZeroDivisionError, OverflowError):
            pass
    return boundaries


@lru_cache(maxsize=128)
def cartesian_curve(expression, x, y):
    """A bare f(x) means y=f(x); equations and expressions using y define contours."""
    if isinstance(expression, s.Equality):
        residual = expression.lhs-expression.rhs
    else:
        require(isinstance(expression, s.Expr), "Enter a function y=f(x) or an equation F(x,y)=0")
        if not expression.has(y): return expression, y-expression
        residual = expression
    require(isinstance(residual, s.Expr) and residual != 0, "Equation is true everywhere; enter a curve equation")
    # Keep ordinary equations on the fast function sampler and analysis path.
    try:
        polynomial = s.Poly(residual, y)
        if polynomial.degree() == 1:
            coefficient, constant = polynomial.all_coeffs()
            return -constant/coefficient, residual
    except s.PolynomialError: pass
    return None, residual


@lru_cache(maxsize=64)
def cartesian_branches(residual, y):
    try:
        return tuple(branch for branch in s.solve(residual, y) if isinstance(branch, s.Expr) and not branch.has(y))
    except (NotImplementedError, ValueError, TypeError): return ()
