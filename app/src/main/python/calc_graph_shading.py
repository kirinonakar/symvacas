"""Bounded graph shading and integration-interval fill polygons."""
from calc_limits import capped
from calc_shared import MathError, require
import math
import sympy as s
from calc_graph_common import (
    _finite_real,
    graph_function,
    substitute_parameters,
)
from calc_graph_sampling import adaptive_samples


def graph_shading(engine, request, items, groups, sliders, xmin, xmax):
    """[shade] regions: half-plane inequalities and bands between one or two curves."""
    ymin,ymax = float(request.get("yMin",-5)),float(request.get("yMax",5))
    require(math.isfinite(ymin) and math.isfinite(ymax) and ymax>ymin,"Shading needs a valid y range")
    span = ymax-ymin; low_edge,high_edge = ymin-span,ymax+span
    def clamp(value): return min(max(value,low_edge),high_edge)
    x = engine.symbol("x"); engine.bindings["x"] = x
    count = capped(max(200,int(request.get("samples",500))),1200)
    def endpoint(item, key, default):
        tree = item.get(key)
        if tree is None: return default
        number = _finite_real(s.N(substitute_parameters(engine.build(tree),sliders),engine.precision))
        require(number is not None,"Shading intervals must be finite numbers")
        return number
    def evaluate(function, at):
        try: return _finite_real(function(at))
        except (TypeError, ValueError, ZeroDivisionError, OverflowError): return None
    def samples(expression, a, b):
        function = graph_function(expression, (x,), sliders)
        points = []
        for index in range(count+1):
            at = a+(b-a)*index/count
            value = evaluate(function,at)
            points.append([at,value] if value is not None else None)
        return points
    shadings = []
    for item,group in zip(items,groups):
        mode = item.get("mode")
        a,b = endpoint(item,"a",xmin),endpoint(item,"b",xmax)
        require(a < b,"Shading intervals must be increasing")
        for bound in item.get("xBounds",[]):
            require(bound.get("side") in ("lower","upper"), "Invalid shading x bound")
            expression = engine.build(bound["tree"])
            require(not expression.has(x,engine.symbol("y")), "Shading x bounds must be constant")
            at = endpoint({"bound":bound["tree"]},"bound",0)
            if bound["side"] == "lower": a = max(a,at)
            else: b = min(b,at)
        if a >= b:
            shadings.append({"mode":mode,"boundary":[],"fill":[]})
            continue
        if mode == "region":
            constraints = item.get("constraints") or []
            require(len(group) == len(constraints) and group, "A shaded region needs inequalities")
            lower, upper, vertical = [], [], []
            left, right = max(a,xmin), min(b,xmax)
            for expression, constraint in zip(group,constraints):
                axis, side = constraint.get("axis"), constraint.get("side")
                require(axis in ("x","y") and side in ("lower","upper"), "Invalid shading constraint")
                require(not expression.has(engine.symbol("y")), "Shading boundaries cannot depend on y")
                if axis == "x":
                    require(not expression.has(x), "Shading x bounds must be constant")
                    at = _finite_real(substitute_parameters(expression,sliders).evalf(engine.precision))
                    require(at is not None, "Shading x bounds must be finite")
                    if side == "lower": left = max(left,at)
                    else: right = min(right,at)
                    vertical.append(at)
                else:
                    (lower if side == "lower" else upper).append(graph_function(expression,(x,),sliders))
            polygons, boundary, run = [], [], []
            if left < right:
                # Intersect every bound at each x; a contradictory region stays empty.
                for index in range(count+2):
                    at = left+(right-left)*min(index,count)/count
                    lows = [evaluate(fn,at) for fn in lower]
                    highs = [evaluate(fn,at) for fn in upper]
                    low = max([ymin]+lows) if all(v is not None for v in lows) else None
                    high = min([ymax]+highs) if all(v is not None for v in highs) else None
                    if index > count or low is None or high is None or low >= high:
                        if len(run) >= 2:
                            top = [[px,hi] for px,lo,hi in run]
                            bottom = [[px,lo] for px,lo,hi in run]
                            polygons.append(top+list(reversed(bottom)))
                        run = []
                    else: run.append([at,low,high])
                for expression, constraint in zip(group,constraints):
                    if constraint["axis"] == "y" and polygons:
                        line = []
                        for point in samples(expression,left,right):
                            if point is not None:
                                at,value = point
                                lows,highs = [evaluate(fn,at) for fn in lower],[evaluate(fn,at) for fn in upper]
                                if not all(v is not None for v in lows+highs) or not max([ymin]+lows)-1e-9 <= value <= min([ymax]+highs)+1e-9: point = None
                            line.append(point)
                        boundary.append(line)
                for at in vertical:
                    if left <= at <= right:
                        lows = [evaluate(fn,at) for fn in lower]
                        highs = [evaluate(fn,at) for fn in upper]
                        if all(v is not None for v in lows+highs):
                            lo,hi = max([ymin]+lows),min([ymax]+highs)
                            if lo < hi: boundary.append([[at,lo],[at,hi]])
            shadings.append({"mode":mode,"boundary":boundary,"fill":polygons})
        elif mode == "halfplane":
            require(len(group) == 1,"A shaded inequality needs one boundary curve")
            boundary = samples(group[0],a,b)
            edge = low_edge if item.get("side") == "below" else high_edge
            polygons=[]; run=[]
            for point in boundary+[None]:
                value = None if point is None else point[1]
                if value is None:
                    if len(run) >= 2: polygons.append(run+[[run[-1][0],edge],[run[0][0],edge]])
                    run=[]
                    continue
                run.append([point[0],clamp(value)])
            shadings.append({"mode":mode,"boundary":[boundary],"fill":polygons})
        elif mode == "band":
            require(1 <= len(group) <= 2,"[shade] takes one or two functions")
            first = samples(group[0],a,b)
            second = samples(group[1],a,b) if len(group) == 2 else [[point[0],0.0] if point else None for point in first]
            lower,upper = [],[]
            for bound in item.get("yBounds",[]):
                require(bound.get("side") in ("lower","upper"), "Invalid shading y bound")
                expression = engine.build(bound["tree"])
                require(not expression.has(engine.symbol("y")), "Shading boundaries cannot depend on y")
                (lower if bound["side"] == "lower" else upper).append(graph_function(expression,(x,),sliders))
            runs=[]; run=[]; previous=None
            for index in range(len(first)):
                low = None if first[index] is None else first[index][1]
                high = None if second[index] is None else second[index][1]
                at = a+(b-a)*index/count
                lows,highs = [evaluate(fn,at) for fn in lower],[evaluate(fn,at) for fn in upper]
                if low is None or high is None or any(v is None for v in lows+highs):
                    if len(run) >= 2: runs.append(run)
                    run=[]; previous=None
                    continue
                low,high = max([min(low,high)]+lows),min([max(low,high)]+highs)
                current = [at,low,high]
                if previous is not None and (previous[2]-previous[1])*(high-low)<0:
                    # Retain the entry/exit point when clipping changes within a sample.
                    delta = previous[2]-previous[1]
                    fraction = delta/(delta-(high-low))
                    px = previous[0]+(at-previous[0])*fraction
                    py = previous[1]+(low-previous[1])*fraction
                    run.append([px,clamp(py),clamp(py)])
                if low <= high:
                    run.append([at,clamp(low),clamp(high)])
                else:
                    if len(run) >= 2: runs.append(run)
                    run=[]
                previous = current
            if len(run) >= 2: runs.append(run)
            polygons = []; boundaries = [[],[]]
            for segment in runs:
                top = [[at,max(low,high)] for at,low,high in segment]
                bottom = [[at,min(low,high)] for at,low,high in segment]
                polygons.append(top+list(reversed(bottom)))
                for line,points in zip(boundaries,(bottom,top)):
                    if line: line.append(None)
                    line.extend(points)
            shadings.append({"mode":mode,"boundary":boundaries if lower or upper else [first,second if len(group) == 2 else None],"fill":polygons})
        else:
            raise MathError("Unknown shading mode")
    return shadings


def integral_fill(expression, variable, a, b):
    """Sample the integration interval independently of the simplified viewport curve."""
    points, _ = adaptive_samples(graph_function(expression,(variable,)),a,b,400,"cartesian")
    polygons, segment = [], []
    def flush():
        if len(segment)>1: polygons.append([[segment[0][0],0.0],*segment,[segment[-1][0],0.0]])
        segment.clear()
    for point in points:
        if point is None: flush()
        else: segment.append(point)
    flush()
    return polygons


def inequality_shading(parts, x, y, sliders, xmin, xmax, ymin, ymax, samples, logarithmic=False):
    """Clip bounded triangles by signed residuals, preserving holes and undefined cells.

    Full cells become horizontal strips to bound transport size. Boundary cells
    retain subcell polygons; no square-free transform may change an inequality's sign.
    """
    functions = [graph_function(expr, (x, y), sliders) for expr, _ in parts]
    def inside(value, index): return value < 0 if parts[index][1] else value <= 0
    count = min(128, max(40, int(math.sqrt(samples))*4))
    dx, dy = (xmax-xmin)/count, (ymax-ymin)/count
    def values(px, py):
        try:
            result = [_finite_real(fn(px, py)) for fn in functions]
            return result if all(v is not None for v in result) else None
        except (TypeError, ValueError, ZeroDivisionError, OverflowError): return None
    def y_at(j): return 10**(math.log10(ymin)+(math.log10(ymax)-math.log10(ymin))*j/count) if logarithmic else ymin+j*dy
    def row(j):
        return [(xmin+i*dx, y_at(j), values(xmin+i*dx, y_at(j))) for i in range(count+1)]
    fill, boundary = [], []
    previous = row(0)
    for j in range(count):
        current = row(j+1); run = None
        for i in range(count+1):
            cell = [previous[i], previous[i+1], current[i+1], current[i]] if i < count else []
            full = bool(cell) and all(p[2] is not None and all(inside(v,k) for k,v in enumerate(p[2])) for p in cell)
            if full:
                if run is None: run = i
                continue
            if run is not None:
                fill.append([[xmin+run*dx,y_at(j)],[xmin+i*dx,y_at(j)],
                             [xmin+i*dx,y_at(j+1)],[xmin+run*dx,y_at(j+1)]])
                run = None
            if not cell: continue
            for ids in ((0,1,2),(0,2,3)):
                triangle = [cell[k] for k in ids]
                if any(p[2] is None for p in triangle): continue
                polygon = triangle
                for k in range(len(parts)):
                    clipped = []
                    a = polygon[-1] if polygon else None
                    for b in polygon:
                        va, vb = a[2][k], b[2][k]
                        if inside(va,k) != inside(vb,k):
                            t = va/(va-vb)
                            clipped.append((a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1]),
                                            [u+t*(v-u) for u,v in zip(a[2],b[2])]))
                        if inside(vb,k): clipped.append(b)
                        a = b
                    polygon = clipped
                if len(polygon) >= 3: fill.append([[p[0],p[1]] for p in polygon])
                # Keep only boundary segments belonging to the intersection.
                for k in range(len(parts)):
                    crossings = []
                    for a,b in zip(triangle,triangle[1:]+triangle[:1]):
                        va,vb = a[2][k],b[2][k]
                        if inside(va,k) != inside(vb,k):
                            t = va/(va-vb)
                            crossings.append((a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1]),
                                              [u+t*(v-u) for u,v in zip(a[2],b[2])]))
                    if len(crossings) == 2:
                        a,b = crossings; lo,hi = 0.,1.
                        for l in range(len(parts)):
                            if l == k: continue
                            va,vb = a[2][l],b[2][l]
                            if not inside(va,l) and not inside(vb,l): hi = -1; break
                            if inside(va,l) != inside(vb,l):
                                t=va/(va-vb)
                                if not inside(va,l): lo=max(lo,t)
                                else: hi=min(hi,t)
                        if lo < hi:
                            boundary += [[a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])] for t in (lo,hi)] + [None]
        previous = current
    return {"mode":"inequality", "fill":fill, "boundary":[], "curve":boundary}
