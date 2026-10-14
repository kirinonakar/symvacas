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
from calc_graph_shading import graph_shading, inequality_shading


def planar_tree_spec(tree):
    """Classify each Cartesian row before building an equation or vector."""
    body = tree
    if tree.get("kind") == "relation" and tree.get("value") in ("=", "=="):
        head, rhs = tree["args"]
        if head.get("kind") == "symbol" and head.get("value") == "r":
            return "polar", rhs
        if head.get("kind") == "call" and head.get("value") == "r":
            return "polar", rhs
        if rhs.get("kind") in ("tuple", "list"):
            body = rhs
    if body.get("kind") in ("tuple", "list") and len(body.get("args", [])) == 2:
        return "parametric", body
    if tree.get("kind") == "relation" and tree.get("value") in ("<", "<=", ">", ">="):
        return "inequality", tree
    return "cartesian", tree


def inequality_parts(engine, tree):
    # Chained relations are nested AST nodes, not boolean-valued operands.
    if tree.get("kind") != "relation":
        return engine.build(tree), []
    left, before = inequality_parts(engine, tree["args"][0])
    right, after = inequality_parts(engine, tree["args"][1])
    op = tree["value"]
    require(op in ("<", "<=", ">", ">="), "Enter an inequality using <, <=, > or >=")
    return right, before + [(left-right if op.startswith("<") else right-left, op in ("<", ">"))] + after


def contour_curve(expression, x, y, sliders, xmin, xmax, ymin, ymax, count, logarithmic=False):
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
    function=graph_function(program, (x, y), sliders)
    if logarithmic:
        points=implicit_samples(lambda px,py:function(px,10**py),xmin,xmax,math.log10(ymin),math.log10(ymax),count)
        return [[p[0],10**p[1]] if p is not None else None for p in points]
    return implicit_samples(function, xmin, xmax, ymin, ymax, count)


def graph_cartesian(engine, request, trees, xmin, xmax):
    for name in ("x","y"):
        if engine.symbol(name).is_real is not True:
            engine.symbols[name]=s.Symbol(name,real=True)
    x, y = engine.symbol("x"), engine.symbol("y")
    engine.bindings.update({"x": x, "y": y})
    specs = [planar_tree_spec(tree) for tree in trees]
    for name in {"t", "theta"} if any(kind in ("parametric", "polar") for kind, _ in specs) else set():
        engine.symbols[name] = s.Symbol(name, real=True)
        engine.bindings[name] = engine.symbol(name)
    raw, inequalities = [], {}
    for index, (kind, tree) in enumerate(specs):
        if kind == "inequality":
            inequalities[index] = inequality_parts(engine, tree)[1]
            raw.append(s.Integer(0))
        else:
            raw.append(graph_expressions(engine, [tree], ("x", "y", "t", "theta"))[0])
    curvespecs = [cartesian_curve(expression, x, y) if kind == "cartesian" else (None, s.Integer(0))
                  for (kind, _), expression in zip(specs, raw)]
    shade_items = request.get("shadings") or []
    shade_expressions = [graph_expressions(engine, item.get("trees") or [], ("x", "y")) for item in shade_items]
    all_expressions = list(raw)+[expr for parts in inequalities.values() for expr, _ in parts]+[expression for group in shade_expressions for expression in group]
    bound_trees = [bound["tree"] for item in shade_items for key in ("xBounds","yBounds") for bound in item.get(key,[])]
    all_expressions += list(graph_expressions(engine,bound_trees,("x","y")))
    planar_expressions = [expression for (kind, _), expression in zip(specs, raw) if kind in ("cartesian", "inequality")]
    planar_expressions += [expr for parts in inequalities.values() for expr, _ in parts]
    planar_expressions += [expr for group in shade_expressions for expr in group]
    planar_expressions += list(graph_expressions(engine,bound_trees,("x","y")))
    parameter_expressions = [expression for (kind, _), expression in zip(specs, raw) if kind in ("parametric", "polar")]
    names = parameter_names(planar_expressions, {"x", "y"}) | parameter_names(parameter_expressions, {"t", "theta"})
    parameter_sliders = resolved_parameters(engine, request, all_expressions, {"x", "y", "t", "theta"})
    for name in names: parameter_sliders.setdefault(engine.symbol(name), s.Float(1.0, engine.precision))
    sliders = {symbol: value for symbol, value in parameter_sliders.items() if symbol not in (x, y)}
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
            points, parameters = adaptive_samples(function, xmin, xmax, count, "cartesian",screen_bounds=(xmin,xmax,ymin,ymax),logarithmic=bool(request.get("yLog")))
        else:
            breaks=[xmin]+sorted(boundaries)+[xmax];points=[];parameters=[]
            for low,high in zip(breaks,breaks[1:]):
                left=math.nextafter(low,high) if low in boundaries else low
                right=math.nextafter(high,low) if high in boundaries else high
                part,positions=adaptive_samples(function,left,right,max(100,int(count*(high-low)/(xmax-xmin))),"cartesian",screen_bounds=(xmin,xmax,ymin,ymax),logarithmic=bool(request.get("yLog")))
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
    curve_parameters, curve_kinds, styles, natural_shadings = [], [], [], []
    for index, ((kind, _), expression, (function, residual)) in enumerate(zip(specs, raw, curvespecs)):
        positions = None
        if kind in ("parametric", "polar"):
            t, theta = engine.symbol("t"), engine.symbol("theta")
            if kind == "polar": expression = expression.subs(theta, t)
            require(kind != "parametric" or isinstance(expression, (tuple, list)) and len(expression) == 2,
                    "Enter a pair (x(t), y(t))")
            low_key, high_key = ("thetaMin", "thetaMax") if kind == "polar" else ("parameterMin", "parameterMax")
            start = float(request.get(low_key, request.get("parameterMin", 0)))
            end = float(request.get(high_key, request.get("parameterMax", 2*math.pi)))
            require(math.isfinite(start) and math.isfinite(end) and end > start, "Invalid parameter range")
            points, positions = adaptive_samples(graph_function(expression, (t,), parameter_sliders), start, end, count, kind,screen_bounds=(xmin,xmax,ymin,ymax),logarithmic=bool(request.get("yLog")))
            points, positions = simplify_samples(points, positions, request, start, end)
            implicit.append(False)
        elif kind == "inequality":
            region = inequality_shading(inequalities[index], x, y, sliders, xmin, xmax, ymin, ymax, count,bool(request.get("yLog")))
            region["sourceIndex"] = index
            natural_shadings.append(region)
            points = region.pop("curve")
            implicit.append(True)
        elif function is not None and not substitute_parameters(function, sliders).has(s.zoo, s.nan, s.oo, -s.oo):
            points = sample(function); implicit.append(False)
        else:
            points = contour_curve(residual, x, y, sliders, xmin, xmax, ymin, ymax, contour_count,bool(request.get("yLog"))); implicit.append(True)
        curves.append(points)
        curve_parameters.append(positions)
        curve_kinds.append(kind)
        styles.append("dashed" if kind == "inequality" and any(strict for _, strict in inequalities[index]) else "solid")
    result = {"curves": curves, "parameters": sorted(names), "implicitCurves": implicit,
              "curveKinds": curve_kinds, "curveStyles": styles}
    if any(positions is not None for positions in curve_parameters): result["curveParameters"] = curve_parameters
    for order, prefix in ((1, "derivative"), (2, "secondDerivative")):
        selected = request.get(prefix+"Selected")
        if not isinstance(selected, int) or not 0 <= selected < len(curvespecs):
            continue
        require(specs[selected][0] == "cartesian", "Derivative graphs require a Cartesian curve")
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
    result["shadings"] = natural_shadings
    if shade_items:
        result["shadings"] += [{**shade, "shadeIndex": index} for index, shade in enumerate(graph_shading(engine, request, shade_items, shade_expressions, sliders, xmin, xmax))]
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
        curves.append(contour_curve(expression, x, y, sliders, xmin, xmax, ymin, ymax, count,bool(request.get("yLog"))))
    return {"curves": curves, "implicit": True, "parameters": sorted(names)}


def graph_parametric(engine, request, trees, start, end, kind):
    """Sample single-parameter curves, retaining parameter positions for tracing."""
    var = engine.symbol(request.get("variable","x")); engine.bindings[str(var)] = var
    if kind == "polar":
        trees = [planar_tree_spec(tree)[1] if planar_tree_spec(tree)[0] == "polar" else tree for tree in trees]
        engine.bindings["theta"] = var
    expressions = graph_expressions(engine, trees, (str(var),))
    names = parameter_names(expressions, {str(var)})
    sliders = resolved_parameters(engine, request, expressions, {str(var)})
    count = capped(max(100,int(request.get("samples",500))),1600)
    curves=[]
    curve_parameters=[]
    for expression in expressions:
        function=graph_function(expression, (var,), sliders)
        samples, sample_parameters = adaptive_samples(function, start, end, count, kind,logarithmic=bool(request.get("yLog")))
        samples, sample_parameters = simplify_samples(samples, sample_parameters, request, start, end)
        curves.append(samples)
        if kind in ("parametric","polar"): curve_parameters.append(sample_parameters)
    result = {"curves":curves,"parameters":sorted(names)}
    if curve_parameters: result["curveParameters"] = curve_parameters
    return result
