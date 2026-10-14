"""Curve analysis: roots, extrema, intersections, tangents, and integrals.

Explicit and implicit branch analysis stay together because they recursively
reuse the same analysis dispatcher and traced-branch rules."""
from calc_extrema import extrema_candidates
from calc_limits import within_limit
from calc_shared import MathError, numeric_integral, require
import math
import sympy as s
from calc_graph_common import (
    _finite_real,
    _square_free_graph,
    bind_graph_parameters,
    cartesian_branches,
    cartesian_curve,
    graph_expressions,
    resolved_parameters,
    substitute_parameters,
)
from calc_graph_shading import integral_fill


def interval_extrema(expression, variable, lower, upper, action, coordinates=(), conditions=()):
    """Return graph coordinates from the shared exact extrema search."""
    interval=s.Interval(s.Rational(lower),s.Rational(upper))
    return [float(at) for at,_ in extrema_candidates(expression,variable,interval,action,coordinates,conditions)]


def polynomial_real_roots(expression, variable):
    """Isolate real roots numerically without constructing quartic radical formulas.

    Exact rational coefficients retain repeated/tangent roots and avoid nroots'
    convergence failures at multiple roots. None means a non-polynomial target.
    """
    try:
        numerator = s.together(expression).as_numer_denom()[0]
        polynomial = s.Poly(numerator, variable)
        if polynomial.degree()>32 or any(coefficient.free_symbols for coefficient in polynomial.all_coeffs()): return None
        require(not polynomial.is_zero, "Select two different curves")
        return [float((low+high)/2) for (low,high),_ in polynomial.to_exact().intervals(eps=s.Rational(1,10**20))]
    except (s.PolynomialError, s.polys.polyerrors.DomainError, NotImplementedError): return None


def _graph_direction(dx, dy):
    if dx is None or dy is None: return None
    length = math.hypot(dx, dy)
    return (dx/length, dy/length) if math.isfinite(length) and length > 0 else None


def _cartesian_tangent_direction(curve, x, y, px, py, precision):
    function, residual = curve
    def finite(expression):
        try: return _finite_real(expression.evalf(precision))
        except (TypeError, ValueError, OverflowError): return None
    if function is not None:
        derivative = s.diff(function, x)
        slope = finite(derivative.subs(x, px))
        if slope is not None and not function.has(s.Abs, s.Piecewise):
            return _graph_direction(1.0, slope)
        # Check both one-sided tangents at corners and vertical endpoints.
        directions = []
        approach = s.Dummy('approach',positive=True)
        for side in ('-', '+'):
            try:
                at = s.Rational(str(px))
                nearby = at+approach if side == '+' else at-approach
                # Substituting a positive offset resolves Piecewise conditions
                # before SymPy's limit routine selects a boundary branch.
                ordinate = finite(s.limit(function.subs(x,nearby),approach,0,dir='+'))
                if ordinate is None: continue
                if abs(ordinate-py) > 1e-7*max(1,abs(py)): return None
                limit = s.limit(derivative.subs(x,nearby),approach,0,dir='+')
                direction = (0.0,1.0) if limit in (s.oo,-s.oo) else _graph_direction(1.0,finite(limit))
                if direction is not None: directions.append(direction)
            except (NotImplementedError, ValueError, TypeError): continue
        if not directions: return None
        if any(abs(directions[0][0]*dy-directions[0][1]*dx)>1e-7 for dx,dy in directions[1:]): return None
        return directions[0]
    residual = _square_free_graph(residual,x,y)
    substitutions = {x:px,y:py}
    return _graph_direction(finite(s.diff(residual,y).subs(substitutions)), finite(-s.diff(residual,x).subs(substitutions)))


def implicit_analysis(engine, request, curves, x, y, numeric, zeroes, tangent_point):
    """Analyze all branches for searches; use the traced point for a local branch."""
    selected, other = int(request.get("selected", 0)), int(request.get("other", 1))
    action = request.get("analysis", "root")
    a, b = float(request.get("a", -10)), float(request.get("b", 10))
    function, residual = curves[selected]
    residual = _square_free_graph(residual, x, y)
    def finite(expression):
        try: return _finite_real(expression.evalf(engine.precision))
        except (TypeError, ValueError, OverflowError): return None
    def solutions(expression, variable):
        try: return s.solve(expression, variable)
        except (NotImplementedError, ValueError, TypeError): return []
    def valid(px, py, expressions=(residual,)):
        for expression in expressions:
            value = finite(expression.subs({x: px, y: py}))
            if value is None or abs(value)>1e-6: return False
        return True
    def collect(points):
        found = []
        for point in sorted(points):
            if all(math.hypot(point[0]-old[0], point[1]-old[1])>1e-6 for old in found): found.append(point)
        return {"analysis": action, "points": found[:80], "count": min(80,len(found)), "truncated": len(found)>80, "implicit": True}
    if action == "root":
        target = residual.subs(y, 0)
        require(target != 0, "The curve lies on the x axis; roots are not isolated")
        positions = zeroes(numeric(target, x))
        positions += [value for value in (finite(root) for root in solutions(target, x)) if value is not None and a-1e-9 <= value <= b+1e-9]
        return collect([[px, 0.0] for px in positions if valid(px, 0)])
    if action == "yintercept":
        target = residual.subs(x, 0)
        require(target != 0, "The curve lies on the y axis; intercepts are not isolated")
        ymin, ymax = float(request.get("yMin",-5)),float(request.get("yMax",5))
        require(math.isfinite(ymin) and math.isfinite(ymax) and ymin < ymax, "Invalid y range")
        # Reuse the numerical root search on the y viewport, then include exact roots.
        search = graph_analysis(engine,{**request,"trees":[],"selected":0,"analysis":"root","a":ymin,"b":ymax},(target.subs(y,x),))
        positions = [point[0] for point in search["points"]]
        positions += [value for value in (finite(root) for root in solutions(target,y)) if value is not None]
        return collect([[0.0,py] for py in positions if valid(0,py)])
    if action == "intersection":
        target = curves[other][1]
        # Substitute a known function first: a parabola against a circle becomes
        # one quartic whose real roots can be isolated quickly at current sliders.
        explicit = function if function is not None else curves[other][0]
        if explicit is not None:
            reduced = (target if function is not None else residual).subs(y,explicit)
            positions = polynomial_real_roots(reduced,x)
            if positions is not None:
                value=numeric(explicit,x)
                return collect([[px,py] for px in positions for py in [value(px)] if py is not None and a-1e-9 <= px <= b+1e-9 and valid(px,py,(residual,target))])
        require(residual-target != 0, "Select two different curves")
        try: pairs = s.solve((residual, target), (x, y), dict=True)
        except (NotImplementedError, ValueError, TypeError): pairs = []
        points = []
        for pair in pairs:
            px, py = finite(pair.get(x,s.nan)), finite(pair.get(y,s.nan))
            if px is not None and py is not None and a-1e-9 <= px <= b+1e-9 and valid(px,py,(residual,target)): points.append([px,py])
        if points: return collect(points)
        # Numerical branch searches also cover transcendental intersections.
        first = (function,) if function is not None else cartesian_branches(residual, y)
        second = (curves[other][0],) if curves[other][0] is not None else cartesian_branches(target, y)
        require(first and second or pairs, "These curves cannot be analyzed as y=f(x) branches")
        for left in first:
            for right in second:
                response = graph_analysis(engine, {**request,"selected":0,"other":1}, (left,right))
                points.extend(point for point in response["points"] if valid(*point,(residual,target)))
        return collect(points)
    if action in ("derivative", "tangent", "tangentangle"):
        ordinates = [value for value in (finite(root) for root in solutions(residual.subs(x,s.Float(a)), y)) if value is not None and valid(a,value)]
        require(ordinates, "Curve is undefined at this x coordinate")
        hint = request.get("tracePoint")
        require(len(ordinates)==1 or isinstance(hint,(list,tuple)) and len(hint)==2, "Tap a point on the curve to choose a branch")
        py = min(ordinates, key=lambda value:abs(value-float(hint[1]))) if hint else ordinates[0]
        horizontal, vertical = finite(s.diff(residual,x).subs({x:a,y:py})), finite(s.diff(residual,y).subs({x:a,y:py}))
        require(horizontal is not None and vertical is not None and math.hypot(horizontal,vertical)>1e-12, "Tangent is undefined at this point")
        slope = -horizontal/vertical if abs(vertical)>1e-12 else None
        if action in ("tangent", "tangentangle"): return {**tangent_point(a,py,slope,(vertical,-horizontal)),"implicit":True}
        payload = {"analysis":action,"points":[[a,py]],"implicit":True}
        if slope is None: payload["vertical"]=True
        else: payload["value"]=slope
        return payload
    branches = (function,) if function is not None else cartesian_branches(residual, y)
    require(branches, "This curve cannot be analyzed as y=f(x) branches")
    if action in ("integral", "arclength"):
        hint = request.get("tracePoint")
        if len(branches)>1:
            require(isinstance(hint,(list,tuple)) and len(hint)==2, "Tap a point on the curve to choose a branch")
            candidates = [(abs(value-float(hint[1])),branch) for branch in branches for value in [finite(branch.subs(x,float(hint[0])))] if value is not None]
            require(candidates, "Curve is undefined at this x coordinate")
            branches = (min(candidates,key=lambda pair:pair[0])[1],)
        return {**graph_analysis(engine,{**request,"selected":0},branches),"implicit":True}
    points = []
    for branch in branches:
        try:
            response = graph_analysis(engine,{**request,"selected":0},(branch,))
            points.extend(point for point in response["points"] if valid(*point))
        except MathError:
            # A branch may have no real values inside the requested interval.
            continue
    if action in ("minimum", "maximum"):
        require(points, "No finite values in this range")
        limit = (min if action=="minimum" else max)(py for _,py in points)
        points = [point for point in points if abs(point[1]-limit)<=max(1e-8,abs(limit)*1e-8)]
    return collect(points)


def graph_analysis(engine, request, _expressions=None, _derivative_primitive=None):
    bind_graph_parameters(engine,request)
    kind = request.get("graphKind","cartesian")
    # Every analysis may differentiate (including searches for tangent roots).
    # Real plot coordinates keep Abs derivatives out of complex re/im terms.
    axes = ("x","y") if kind == "cartesian" else (request.get("variable","t"),)
    for name in axes:
        if engine.symbol(name).is_real is not True:
            engine.symbols[name] = s.Symbol(name,real=True)
    if _expressions is not None:
        # Numerical solver guidance also supplies already-built expressions.
        # Remap their coordinates to the same symbols used by this analysis.
        replacements = {symbol:engine.symbol(str(symbol)) for expression in _expressions
                        for symbol in expression.free_symbols if str(symbol) in axes}
        _expressions = tuple(expression.xreplace(replacements) for expression in _expressions)
        if _derivative_primitive is not None:
            _derivative_primitive = _derivative_primitive.xreplace(replacements)
    trees = request.get("trees",[])
    selected_order = request.get("selectedDerivativeOrder", 0)
    pair_analysis = request.get("analysis") in ("intersection", "intersectionangle")
    other_order = request.get("otherDerivativeOrder", 0) if pair_analysis else 0
    require(isinstance(selected_order,int) and selected_order in (0,1,2) and isinstance(other_order,int) and other_order in (0,1,2), "Invalid derivative order")
    if _expressions is None and (selected_order or other_order):
        require(kind == "cartesian", "Derivative analysis requires Cartesian curves")
        selected, other = int(request.get("selected",0)), int(request.get("other",1))
        require(0 <= selected < len(trees), "Select a function")
        if pair_analysis: require(0 <= other < len(trees), "Select two different functions")
        x, y = engine.symbol("x"), engine.symbol("y")
        engine.bindings.update({"x":x,"y":y})
        raw = list(graph_expressions(engine,trees,("x","y")))
        targets = {}
        primitives = {}
        def target(index, order):
            if not order: return index
            key = (index,order)
            if key not in targets:
                function, residual = cartesian_curve(raw[index],x,y)
                branches = (function,) if function is not None else cartesian_branches(residual,y)
                require(branches, "Derivative graph requires branches expressible as y=f(x)")
                derivative_primitives = {s.diff(branch,x,order):s.diff(branch,x,order-1) for branch in branches}
                derivatives = tuple(derivative_primitives)
                if index == selected and order == selected_order and len(derivatives)>1 and request.get("analysis") in ("derivative","tangent","tangentangle","integral","arclength"):
                    hint = request.get("tracePoint")
                    require(isinstance(hint,(list,tuple)) and len(hint)==2, "Tap a point on the curve to choose a branch")
                    hint_x,hint_y = map(float,hint)
                    require(math.isfinite(hint_x) and math.isfinite(hint_y), "Invalid trace point")
                    sliders = {symbol:value for symbol,value in resolved_parameters(engine,request,raw,{"x","y"}).items() if symbol not in (x,y)}
                    candidates = []
                    for branch in derivatives:
                        value = _finite_real(substitute_parameters(branch,sliders).subs(x,hint_x).evalf(engine.precision))
                        if value is not None: candidates.append((abs(value-hint_y),branch))
                    candidates.sort(key=lambda pair:pair[0])
                    require(candidates, "Curve is undefined at this x coordinate")
                    require(len(candidates)==1 or candidates[1][0]-candidates[0][0]>1e-8, "Tap a point on the curve to choose a branch")
                    derivatives = (candidates[0][1],)
                # A product retains every y branch for intersection/search analysis;
                # local tangents and integrals use the existing traced-branch rule.
                expression = derivatives[0] if len(derivatives)==1 else s.prod(y-branch for branch in derivatives)
                targets[key] = len(raw)
                raw.append(expression)
                if len(derivatives)==1: primitives[targets[key]] = derivative_primitives[derivatives[0]]
            return targets[key]
        resolved = {key:value for key,value in request.items() if key not in ("selectedDerivativeOrder","otherDerivativeOrder")}
        resolved["selected"] = target(selected,selected_order)
        if pair_analysis: resolved["other"] = target(other,other_order)
        response = graph_analysis(engine,resolved,tuple(raw),primitives.get(resolved["selected"]))
        response.update(selected=selected,selectedDerivativeOrder=selected_order)
        if pair_analysis: response.update(other=other,otherDerivativeOrder=other_order)
        return response
    require(kind in ("cartesian","parametric","polar"), "Analysis supports Cartesian, parametric and polar curves")
    selected = int(request.get("selected", 0)); other = int(request.get("other", 1))
    size = len(trees) if _expressions is None else len(_expressions)
    require(0 <= selected < size, "Select a function")
    action = request.get("analysis", "root")
    require(action in ("root","yintercept","intersection","intersectionangle","minimum","maximum","inflection","derivative","tangent","tangentangle","integral","arclength","asymptotes"), "Unknown graph analysis")
    require(action != "asymptotes" or kind == "cartesian", "Asymptotes require a Cartesian function")
    require(not pair_analysis or kind == "cartesian", "Intersections need two Cartesian functions")
    if pair_analysis: require(0 <= other < size and other != selected, "Select two different functions")
    fixed_intercept = action == "yintercept" and kind == "cartesian"
    a = 0.0 if fixed_intercept else float(request.get("a", -10)); b = a if fixed_intercept else float(request.get("b", 10))
    singled = action in ("derivative", "tangent", "tangentangle") or fixed_intercept
    require(math.isfinite(a) and math.isfinite(b) and (singled or a < b) and within_limit(abs(b-a),1e9), "Invalid analysis range")
    def numeric(expr, variable):
        raw = s.lambdify(variable, expr, modules="math", cse=True, docstring_limit=0)
        def value(at):
            try:
                result = float(raw(at))
                return result if math.isfinite(result) else None
            except (TypeError, ValueError, ZeroDivisionError, OverflowError): return None
        return value
    def zeroes(fn):
        count = 1200
        xs = [a+(b-a)*i/count for i in range(count+1)]
        ys = [fn(at) for at in xs]
        roots = []
        def add(at):
            if not roots or all(abs(at-old)>max(1e-8,abs(b-a)*1e-6) for old in roots): roots.append(at)
        for i in range(count):
            left,right = xs[i],xs[i+1]; yl,yr = ys[i],ys[i+1]
            if yl is None or yr is None: continue
            if abs(yl) < 1e-9: add(left)
            if yl*yr < 0:
                lo,hi = left,right; low = yl
                for _ in range(55):
                    mid = (lo+hi)/2; middle = fn(mid)
                    if middle is None: break
                    if low*middle <= 0: hi=mid
                    else: lo=mid; low=middle
                root=(lo+hi)/2; residual=fn(root)
                if residual is not None and abs(residual) < 1e-6: add(root)
        if ys[-1] is not None and abs(ys[-1]) < 1e-9: add(b)
        return sorted(roots)
    def tangent_point(px, py, slope, direction=None):
        xmin=float(request.get("xMin",-10)); xmax=float(request.get("xMax",10))
        ymin=float(request.get("yMin",-10)); ymax=float(request.get("yMax",10))
        if not all(math.isfinite(value) for value in (xmin,xmax,ymin,ymax)) or xmax <= xmin or ymax <= ymin: xmin,xmax,ymin,ymax = -10,10,-10,10
        payload = {"analysis":action,"points":[[px,py]]}
        if action == "tangentangle":
            direction = _graph_direction(*(direction if direction is not None else (1.0,slope)))
            require(direction is not None, "Tangent is undefined at this point")
            radians = math.atan2(direction[1],direction[0]) % math.pi
            payload.update(value=math.degrees(radians),radians=radians,unit="deg")
        if slope is None: payload["vertical"]=True
        elif action != "tangentangle": payload["value"]=slope
        if direction is not None:
            dx,dy = direction
            speed = math.hypot(dx,dy)
            if speed > 1e-12:
                length = 1.6*max(xmax-xmin,ymax-ymin)
                payload["line"] = [[px-dx/speed*length,py-dy/speed*length],[px+dx/speed*length,py+dy/speed*length]]
        elif slope is None or abs(slope) > 1e6:
            payload["line"] = [[px,ymin],[px,ymax]]
        else:
            payload["line"] = [[xmin,py+slope*(xmin-px)],[xmax,py+slope*(xmax-px)]]
        return payload
    if kind == "cartesian":
        x, y = engine.symbol("x"), engine.symbol("y")
        engine.bindings.update({"x":x,"y":y})
        extrema_conditions=engine.conditions[:]
        if action in ("minimum","maximum") and _expressions is None:
            # Cached expressions cannot recover domain guards lost during
            # simplification. Collect guards for only the selected curve.
            raw=[]
            previous_conditions=engine.conditions
            try:
                for index,tree in enumerate(trees):
                    engine.conditions=[]
                    raw.append(engine.build(tree))
                    if index==selected: extrema_conditions=engine.conditions[:]
            finally: engine.conditions=previous_conditions
        else:
            raw = graph_expressions(engine, trees, ("x","y")) if _expressions is None else _expressions
        sliders = {symbol:value for symbol,value in resolved_parameters(engine,request,raw,{"x","y"}).items() if symbol not in (x,y)}
        curves = [cartesian_curve(substitute_parameters(expression,sliders),x,y) for expression in raw]
        if action == "asymptotes":
            require(curves[selected][0] is not None,"Asymptotes require an explicit function y=f(x)")
            from calc_asymptotes import analyze
            return analyze(curves[selected][0],x,a,b,request)
        if action == "intersectionangle":
            response = graph_analysis(engine,{**request,"analysis":"intersection"},tuple(substitute_parameters(expression,sliders) for expression in raw))
            angles = []
            for px,py in response["points"]:
                first = _cartesian_tangent_direction(curves[selected],x,y,px,py,engine.precision)
                second = _cartesian_tangent_direction(curves[other],x,y,px,py,engine.precision)
                if first is None or second is None:
                    angles.append({"value":None,"radians":None,"error":"Tangent is undefined at this point"})
                else:
                    cross = abs(first[0]*second[1]-first[1]*second[0])
                    dot = abs(first[0]*second[0]+first[1]*second[1])
                    radians = math.atan2(cross,dot)
                    angles.append({"value":math.degrees(radians),"radians":radians})
            return {**response,"analysis":action,"angles":angles,"unit":"deg"}
        if curves[selected][0] is None or action=="intersection" and curves[other][0] is None:
            return implicit_analysis(engine,request,curves,x,y,numeric,zeroes,tangent_point)
        expressions = [function for function,_ in curves]
        expression = expressions[selected]
        target = expression-expressions[other] if action == "intersection" else expression
        if action == "intersection": require(target != 0, "The curves coincide; intersections are not isolated")
        if action == "root": require(expression != 0, "The curve lies on the x axis; roots are not isolated")
        value = numeric(expression, x)
        if action == "yintercept":
            intercept = value(0)
            points = [[0.0,intercept]] if intercept is not None else []
            return {"analysis":action,"points":points,"count":len(points)}
        if action == "derivative":
            derivative = numeric(s.diff(expression, x), x)(a)
            require(derivative is not None and value(a) is not None, "Derivative is undefined at this point")
            return {"analysis":action,"points":[[a,value(a)]],"value":derivative}
        if action in ("tangent", "tangentangle"):
            require(value(a) is not None, "Tangent is undefined at this point")
            direction = _cartesian_tangent_direction(curves[selected],x,y,a,value(a),engine.precision) if action == "tangentangle" else None
            if action == "tangentangle": require(direction is not None, "Tangent is undefined at this point")
            return tangent_point(a, value(a), numeric(s.diff(expression, x), x)(a),direction)
        if action == "inflection":
            second = numeric(s.diff(expression, x, 2), x)
            step = max(1e-7,(b-a)*1e-4)
            positions = []
            for at in zeroes(second):
                left,right = second(at-step),second(at+step)
                if left is not None and right is not None and left*right < 0: positions.append(at)
            points = [[at,value(at)] for at in positions if value(at) is not None][:80]
            return {"analysis":action,"points":points,"count":len(points),"truncated":len(positions)>80}
        if action == "arclength":
            slope = s.diff(expression, x)
            result = numeric_integral(s.sqrt(1+slope**2), x, a, b, engine.precision)
            require(result.is_real and result.is_finite, "Numerical convergence failed")
            return {"analysis":action,"points":[],"value":float(result)}
        if action == "integral":
            result = None
            if _derivative_primitive is not None:
                from sympy.calculus.util import continuous_domain
                primitive = substitute_parameters(_derivative_primitive,sliders)
                continuous = primitive_continuous = None
                try:
                    continuous = (s.Interval.open(a,b)-continuous_domain(expression,x,s.S.Reals)).is_empty
                    primitive_continuous = (s.Interval(a,b)-continuous_domain(primitive,x,s.S.Reals)).is_empty
                except (NotImplementedError, ValueError, TypeError): pass
                require(continuous is not False, "Integral crosses a discontinuity; choose a continuous interval")
                if continuous is True and primitive_continuous is True:
                    # The stored primitive avoids relative-accuracy failure for
                    # cancelling integrals, after checking for domain breaks.
                    exact = primitive.xreplace({value:s.Rational(value) for value in primitive.atoms(s.Float)})
                    result = (exact.subs(x,s.Rational(b))-exact.subs(x,s.Rational(a))).evalf(engine.precision,strict=True)
            if result is None: result = numeric_integral(expression, x, a, b, engine.precision)
            require(result.is_real and result.is_finite, "Numerical convergence failed")
            return {"analysis":action,"points":[],"value":float(result),"integralFill":integral_fill(expression,x,a,b)}
        tested = numeric(target, x)
        if action in ("root", "intersection"):
            positions = zeroes(tested)
            # A tangent intersection has no sign change. Its derivative identifies a zero minimum.
            try:
                for at in zeroes(numeric(s.diff(target, x), x)):
                    residual=tested(at)
                    if residual is not None and abs(residual) < 1e-7 and all(abs(at-old)>max(1e-8,abs(b-a)*1e-6) for old in positions): positions.append(at)
            except (TypeError,ValueError): pass
            positions.sort()
        else:
            guards=[substitute_parameters(c,sliders) for c in extrema_conditions]
            positions = interval_extrema(expression,x,a,b,action,conditions=guards)
        points = [[at,value(at)] for at in positions if value(at) is not None][:80]
        return {"analysis":action,"points":points,"count":len(points),"truncated":len(positions)>80}
    variable = engine.symbol(request.get("variable","t")); engine.bindings[str(variable)] = variable
    raw = engine.build(trees[selected])
    sliders = resolved_parameters(engine, request, [raw], {str(variable)})
    if kind == "polar":
        radius = substitute_parameters(raw, sliders)
        require(isinstance(radius, s.Expr), "Enter a polar radius r(t)")
        first, second = radius*s.cos(variable), radius*s.sin(variable)
    else:
        pair = substitute_parameters(raw, sliders)
        require(isinstance(pair,(list,tuple)) and len(pair)==2, "Parametric curves are [x(t), y(t)] pairs")
        first, second = pair
    dfirst, dsecond = s.diff(first, variable), s.diff(second, variable)
    xvalue, yvalue = numeric(first, variable), numeric(second, variable)
    dxvalue, dyvalue = numeric(dfirst, variable), numeric(dsecond, variable)
    def point(at):
        px,py = xvalue(at),yvalue(at)
        return [px,py] if px is not None and py is not None else None
    if action == "root":
        points = [point(at) for at in zeroes(yvalue)]
    elif action == "yintercept":
        require(first != 0, "The curve lies on the y axis; intercepts are not isolated")
        positions = zeroes(xvalue)
        for at in zeroes(dxvalue):
            value = xvalue(at)
            if value is not None and abs(value) < 1e-7 and all(abs(at-old)>1e-6 for old in positions): positions.append(at)
        points = [[0.0, yvalue(at)] for at in sorted(positions) if yvalue(at) is not None]
        points = [item for i,item in enumerate(points) if all(abs(item[1]-old[1])>1e-6 for old in points[:i])]
    elif action in ("minimum", "maximum"):
        target = radius if kind == "polar" else second
        guards=[substitute_parameters(c,sliders) for c in engine.conditions]
        positions = interval_extrema(target,variable,a,b,action,(first,second),guards)
        points = [point(at) for at in positions]
    elif action == "inflection":
        curvature = dfirst*s.diff(dsecond, variable)-dsecond*s.diff(dfirst, variable)
        points = [point(at) for at in zeroes(numeric(curvature, variable))]
    elif action in ("derivative", "tangent", "tangentangle"):
        current = point(a)
        require(current is not None, "Curve is undefined at this parameter")
        horizontal, vertical = dxvalue(a), dyvalue(a)
        slope = None if horizontal is None or vertical is None or abs(horizontal) < 1e-12 else vertical/horizontal
        if action == "derivative":
            payload = {"analysis":action,"points":[current]}
            if slope is None: payload["vertical"]=True
            else: payload["value"]=slope
            return payload
        direction = None if horizontal is None or vertical is None else (horizontal,vertical)
        return tangent_point(current[0], current[1], slope, direction)
    elif action == "integral":
        integrand = radius**2/2 if kind == "polar" else second*dfirst
        result = numeric_integral(integrand, variable, a, b, engine.precision)
        require(result.is_real and result.is_finite, "Numerical convergence failed")
        return {"analysis":action,"points":[],"value":float(result)}
    else:
        result = numeric_integral(s.sqrt(dfirst**2+dsecond**2), variable, a, b, engine.precision)
        require(result.is_real and result.is_finite, "Numerical convergence failed")
        return {"analysis":action,"points":[],"value":float(result)}
    found = [item for item in points if item is not None]
    points = found[:80]
    return {"analysis":action,"points":points,"count":len(points),"truncated":len(found)>80}
