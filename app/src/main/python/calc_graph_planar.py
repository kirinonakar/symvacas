"""2D graph requests: Cartesian, implicit, parametric, and polar curves."""
from calc_display import readable
from calc_limits import capped
from calc_shared import require
import math
import sympy as s
from calc_graph_common import (
    _finite_real,
    _square_free_graph,
    cartesian_branches,
    cartesian_curve,
    graph_expressions,
    graph_function,
    parameter_names,
    resolved_parameters,
    substitute_parameters,
)
from calc_graph_sampling import (
    adaptive_samples,
    implicit_samples,
    simplify_samples,
)
from calc_graph_shading import graph_shading


def contour_curve(expression, x, y, sliders, xmin, xmax, ymin, ymax, count):
    numeric = substitute_parameters(expression, sliders)
    require(numeric != 0, "Equation is true everywhere; enter a curve equation")
    program = _square_free_graph(expression, x, y)
    bound = substitute_parameters(program, sliders)
    if bound.is_polynomial(x, y):
        polynomial = s.Poly(bound, x, y)
        if polynomial.total_degree() <= 12:
            square_free = polynomial.sqf_part()
            if square_free.total_degree() != polynomial.total_degree():
                program, sliders = square_free.as_expr(), None
    return implicit_samples(graph_function(program, (x, y), sliders), xmin, xmax, ymin, ymax, count)


def graph_cartesian(engine, request, trees, xmin, xmax):
    for name in ("x","y"):
        if engine.symbol(name).is_real is not True:
            engine.symbols[name]=s.Symbol(name,real=True)
    x, y = engine.symbol("x"), engine.symbol("y")
    engine.bindings.update({"x": x, "y": y})
    raw = graph_expressions(engine, trees, ("x", "y"))
    curvespecs = [cartesian_curve(expression, x, y) for expression in raw]
    shade_items = request.get("shadings") or []
    shade_expressions = [graph_expressions(engine, item.get("trees") or [], ("x", "y")) for item in shade_items]
    all_expressions = [residual for _, residual in curvespecs]+[expression for group in shade_expressions for expression in group]
    bound_trees = [bound["tree"] for item in shade_items for key in ("xBounds","yBounds") for bound in item.get(key,[])]
    all_expressions += list(graph_expressions(engine,bound_trees,("x","y")))
    names = parameter_names(all_expressions, {"x", "y"})
    sliders = {symbol: value for symbol, value in resolved_parameters(engine, request, all_expressions, {"x", "y"}).items() if symbol not in (x, y)}
    count = capped(max(100, int(request.get("samples", 500))),1600)
    contour_count = capped(max(80, int(math.sqrt(count))*8),240)
    ymin, ymax = float(request.get("yMin", -5)), float(request.get("yMax", 5))
    require(math.isfinite(ymin) and math.isfinite(ymax) and ymax > ymin, "Invalid implicit y range")
    curves, implicit = [], []
    def sample(expression):
        function=graph_function(expression, (x,), sliders)
        # Split at explicit branch boundaries, including same-sign jumps and
        # narrow restricted intervals that a uniform grid can entirely miss.
        boundaries=set()
        resolved=substitute_parameters(expression,sliders)
        for piece in resolved.atoms(s.Piecewise):
            for _,condition in piece.args:
                for relation in condition.atoms(s.core.relational.Relational):
                    difference=relation.lhs-relation.rhs
                    if difference.free_symbols-set((x,)): continue
                    try:
                        polynomial=s.Poly(difference,x)
                        if not 1<=polynomial.degree()<=4: continue
                        for root in s.solve(difference,x):
                            value=_finite_real(root)
                            if value is not None and xmin<value<xmax: boundaries.add(value)
                    except (s.PolynomialError,NotImplementedError,ValueError): pass
        if not boundaries:
            points, parameters = adaptive_samples(function, xmin, xmax, count, "cartesian",screen_bounds=(xmin,xmax,ymin,ymax))
        else:
            breaks=[xmin]+sorted(boundaries)+[xmax];points=[];parameters=[]
            for low,high in zip(breaks,breaks[1:]):
                left=math.nextafter(low,high) if low in boundaries else low
                right=math.nextafter(high,low) if high in boundaries else high
                part,positions=adaptive_samples(function,left,right,max(100,int(count*(high-low)/(xmax-xmin))),"cartesian",screen_bounds=(xmin,xmax,ymin,ymax))
                for edge,index in ((low,0),(high,-1)):
                    if edge not in boundaries or part[index] is None: continue
                    try: actual=_finite_real(function(edge))
                    except (ValueError,TypeError,ZeroDivisionError,OverflowError): actual=None
                    if actual is not None and abs(actual-part[index][1])<=1e-8*max(1,abs(actual)):
                        part[index]=[edge,actual];positions[index]=edge
                if points:
                    try: exact=_finite_real(function(low))
                    except (ValueError,TypeError,ZeroDivisionError,OverflowError): exact=None
                    continuous=(exact is not None and points[-1] is not None and part[0] is not None
                                and abs(points[-1][1]-exact)<=1e-8*max(1,abs(exact))
                                and abs(part[0][1]-exact)<=1e-8*max(1,abs(exact)))
                    if not continuous: points.append(None);parameters.append(low)
                points.extend(part);parameters.extend(positions)
        return simplify_samples(points, parameters, request, xmin, xmax)[0]
    for function, residual in curvespecs:
        # A parameter may make a linear equation degenerate (e.g. a*y=x at a=0).
        if function is not None and not substitute_parameters(function, sliders).has(s.zoo, s.nan, s.oo, -s.oo):
            curves.append(sample(function)); implicit.append(False)
        else:
            curves.append(contour_curve(residual, x, y, sliders, xmin, xmax, ymin, ymax, contour_count)); implicit.append(True)
    result = {"curves": curves, "parameters": sorted(names), "implicitCurves": implicit}
    for order, prefix in ((1, "derivative"), (2, "secondDerivative")):
        selected = request.get(prefix+"Selected")
        if not isinstance(selected, int) or not 0 <= selected < len(curvespecs):
            continue
        function, residual = curvespecs[selected]
        branches = (function,) if function is not None else cartesian_branches(residual, y)
        require(branches, "Derivative graph requires branches expressible as y=f(x)")
        derivatives = tuple(s.diff(branch, x, order) for branch in branches)
        points = []
        for derivative in derivatives:
            if points: points.append(None)
            points.extend(sample(derivative))
        result.update({prefix+"CurveIndex": len(curves), prefix+"Selected": selected,
                       prefix+"Expression": readable(derivatives[0] if len(derivatives)==1 else s.Tuple(*derivatives))})
        curves.append(points)
    if "derivativeCurveIndex" not in result:
        index = request.get("derivativeCurveIndex")
        if isinstance(index, int) and 0 <= index < len(curvespecs):
            result["derivativeExpression"] = readable(curvespecs[index][0])
    if shade_items:
        result["shadings"] = graph_shading(engine, request, shade_items, shade_expressions, sliders, xmin, xmax)
    return result


def graph_implicit(engine, request, trees, xmin, xmax):
    """Contour F(x,y)=0 with finite, independently separated line segments."""
    ymin, ymax = float(request.get("yMin", -3)), float(request.get("yMax", 3))
    require(math.isfinite(ymin) and math.isfinite(ymax) and ymax > ymin, "Invalid implicit y range")
    require(1 <= len(trees) <= 20, "Enter one to twenty implicit equations")
    x, y = engine.symbol("x"), engine.symbol("y")
    engine.bindings.update({"x": x, "y": y})
    expressions = []
    for expression in graph_expressions(engine, trees, ("x", "y")):
        if isinstance(expression, s.Equality):
            expression = expression.lhs-expression.rhs
        require(isinstance(expression, s.Expr), "Enter an equation F(x,y)=0")
        expressions.append(expression)
    names = parameter_names(expressions, {"x", "y"})
    sliders = resolved_parameters(engine, request, expressions, {"x", "y"})
    # Coordinate names remain axes even if a previous graph stored slider values for them.
    sliders = {key: value for key, value in sliders.items() if key not in (x, y)}
    count = capped(max(80, int(math.sqrt(max(1, int(request.get("samples", 500))))*8)),240)
    curves = []
    for expression in expressions:
        curves.append(contour_curve(expression, x, y, sliders, xmin, xmax, ymin, ymax, count))
    return {"curves": curves, "implicit": True, "parameters": sorted(names)}


def graph_parametric(engine, request, trees, start, end, kind):
    """Sample single-parameter curves, retaining parameter positions for tracing."""
    var = engine.symbol(request.get("variable","x")); engine.bindings[str(var)] = var
    expressions = graph_expressions(engine, trees, (str(var),))
    names = parameter_names(expressions, {str(var)})
    sliders = resolved_parameters(engine, request, expressions, {str(var)})
    count = capped(max(100,int(request.get("samples",500))),1600)
    curves=[]
    curve_parameters=[]
    for expression in expressions:
        function=graph_function(expression, (var,), sliders)
        samples, sample_parameters = adaptive_samples(function, start, end, count, kind)
        samples, sample_parameters = simplify_samples(samples, sample_parameters, request, start, end)
        curves.append(samples)
        if kind in ("parametric","polar"): curve_parameters.append(sample_parameters)
    result = {"curves":curves,"parameters":sorted(names)}
    if curve_parameters: result["curveParameters"] = curve_parameters
    return result
