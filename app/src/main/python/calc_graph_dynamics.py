"""Sequence recurrence evaluation and differential-equation solution graphs."""
from calc_limits import within_limit
from calc_shared import require
from sympy.core.function import AppliedUndef
import math
import sympy as s
from calc_graph_common import (
    _finite_real,
    graph_expressions,
    graph_function,
    parameter_names,
    resolved_parameters,
    substitute_parameters,
)


def graph_sequence(engine, request, trees, start, end):
    require(start >= 0 and within_limit(end,2000), "Sequence range must be between 0 and 2000")
    first, last = math.ceil(start), math.floor(end)
    require(last >= first and within_limit(last-first,1200), "Sequence range is too large")
    n = engine.symbol("n"); engine.bindings["n"] = n
    engine.allow_sequence_calls = True
    expressions = graph_expressions(engine, trees, ("n",))
    names = parameter_names(expressions, {"n"})
    sliders = resolved_parameters(engine, request, expressions, {"n"})
    seed_trees = request.get("initialTrees", [])
    seeds = []
    for tree in seed_trees[:20]:
        value = engine.build(tree)
        numeric = _finite_real(s.N(value, engine.precision))
        require(numeric is not None, "Initial sequence values must be finite real numbers")
        seeds.append(numeric)
    require(expressions, "Enter a sequence rule")
    curves = []
    for curve_index, expression in enumerate(expressions):
        if not expression.atoms(AppliedUndef):
            function = graph_function(expression, (n,), sliders)
            curve = []
            for index in range(last+1):
                try: value = _finite_real(function(index))
                except (TypeError, ValueError, ZeroDivisionError, OverflowError): value = None
                require(value is not None, "Sequence rule did not produce a finite real value")
                if index >= first: curve.append([index, value])
            curves.append(curve)
            continue
        expression = substitute_parameters(expression, sliders)
        function_name = "u" if len(expressions) == 1 else "u%d" % (curve_index+1)
        sequence = {}
        recursive_calls = expression.atoms(AppliedUndef)
        for index, value in enumerate(seeds): sequence[index] = value
        for index in range(last+1):
            if recursive_calls and index in sequence:
                pass
            else:
                current = expression.subs(n, s.Integer(index))
                replacements = {}
                for call in current.atoms(AppliedUndef):
                    name = call.func.__name__
                    require(name in ("u", function_name), "A sequence rule may only refer to its own previous terms")
                    require(len(call.args) == 1 and call.args[0].is_Integer, "Sequence references need integer indices")
                    previous_index = int(call.args[0])
                    require(previous_index < index and previous_index in sequence,
                            "Provide enough initial values for every previous-term reference")
                    replacements[call] = s.Float(sequence[previous_index], engine.precision)
                value = _finite_real(s.N(current.xreplace(replacements), engine.precision))
                require(value is not None, "Sequence rule did not produce a finite real value")
                sequence[index] = value
        curves.append([[index, sequence[index]] for index in range(first, last+1) if index in sequence])
    return {"curves": curves, "discrete": True, "parameters": sorted(names)}


def graph_differential(engine, request, trees, start, end):
    require(len(trees) == 1, "Enter one derivative rule dy/dt=f(t,y)")
    t, y = engine.symbol("t"), engine.symbol("y")
    engine.bindings.update({"t":t, "y":y})
    expression = graph_expressions(engine, trees, ("t", "y"))[0]
    names = parameter_names([expression], {"t","y"})
    fn = graph_function(expression, (t,y), resolved_parameters(engine, request, [expression], {"t","y"}))
    ymin, ymax = float(request.get("yMin", -5)), float(request.get("yMax", 5))
    t0 = float(request.get("t0", 0))
    require(math.isfinite(ymin) and math.isfinite(ymax) and ymax > ymin, "Invalid solution y range")
    require(math.isfinite(t0) and start <= t0 <= end, "Initial time must be inside the t range")
    initials = request.get("initialValues", [1])
    require(1 <= len(initials) <= 20, "Enter between one and twenty initial y values")
    def slope(at, value):
        try: return _finite_real(fn(at,value))
        except (TypeError, ValueError, ZeroDivisionError, OverflowError): return None
    curves=[]
    for initial in initials:
        y0 = _finite_real(initial)
        require(y0 is not None, "Initial y values must be finite real numbers")
        def integrate(bound):
            distance = bound-t0
            steps = max(40, min(500, int(240*abs(distance)/(end-start))+40))
            h = distance/steps
            points = [[t0,y0]]
            at, value = t0, y0
            for _ in range(steps):
                k1=slope(at,value)
                k2=slope(at+h/2,value+h*k1/2) if k1 is not None else None
                k3=slope(at+h/2,value+h*k2/2) if k2 is not None else None
                k4=slope(at+h,value+h*k3) if k3 is not None else None
                if None in (k1,k2,k3,k4): break
                value += h*(k1+2*k2+2*k3+k4)/6
                at += h
                if not math.isfinite(value) or abs(value)>1e100: break
                points.append([at,value])
            return points
        left=integrate(start); right=integrate(end)
        curves.append(list(reversed(left[1:]))+[[t0,y0]]+right[1:])
    fields=[]
    nx, ny = 17, 11
    for ix in range(nx):
        at=start+(end-start)*(ix+0.5)/nx
        for iy in range(ny):
            value=ymin+(ymax-ymin)*(iy+0.5)/ny
            dy=slope(at,value)
            if dy is not None: fields.append([at,value,dy])
    return {"curves":curves,"fields":fields,"differential":True,"parameters":sorted(names)}
