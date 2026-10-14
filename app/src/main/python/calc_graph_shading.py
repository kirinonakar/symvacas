"""Bounded graph shading and integration-interval fill polygons."""
from calc_limits import capped
from calc_shared import MathError, require
import math
import sympy as s
from functools import lru_cache
from calc_graph_common import (
    _finite_real,
    graph_function,
    substitute_parameters,
)
from calc_graph_sampling import adaptive_samples, simplify_samples


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
                    vertical.append((at,constraint))
                else:
                    (lower if side == "lower" else upper).append(graph_function(expression,(x,),sliders))
            polygons, boundary, styles, run = [], [], [], []
            strict_y = [graph_function(expr,(x,),sliders) for expr,constraint in zip(group,constraints)
                        if constraint["axis"]=="y" and constraint.get("strict")]
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
                                if point is not None and not constraint.get("strict") and any((v:=evaluate(fn,at)) is not None and abs(v-value)<=1e-9*max(1,abs(value)) for fn in strict_y): point = None
                            line.append(point)
                        boundary.append(line)
                        styles.append("dashed" if constraint.get("strict") else "solid")
                for at,constraint in vertical:
                    if not constraint.get("strict") and any(other.get("strict") and abs(px-at)<=1e-9*max(1,abs(at)) for px,other in vertical): continue
                    if left <= at <= right:
                        lows = [evaluate(fn,at) for fn in lower]
                        highs = [evaluate(fn,at) for fn in upper]
                        if all(v is not None for v in lows+highs):
                            lo,hi = max([ymin]+lows),min([ymax]+highs)
                            if lo < hi:
                                boundary.append([[at,lo],[at,hi]])
                                styles.append("dashed" if constraint.get("strict") else "solid")
            shadings.append({"mode":mode,"boundary":boundary,"boundaryStyles":styles,"fill":polygons})
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
            shadings.append({"mode":mode,"boundary":[boundary],"boundaryStyles":["dashed" if item.get("strict") else "solid"],"fill":polygons})
        elif mode == "band":
            require(1 <= len(group) <= 2,"[shade] takes one or two functions")
            first = samples(group[0],a,b)
            second = samples(group[1],a,b) if len(group) == 2 else [[point[0],0.0] if point else None for point in first]
            lower,upper,bound_functions = [],[],[]
            for bound in item.get("yBounds",[]):
                require(bound.get("side") in ("lower","upper"), "Invalid shading y bound")
                expression = engine.build(bound["tree"])
                require(not expression.has(engine.symbol("y")), "Shading boundaries cannot depend on y")
                function = graph_function(expression,(x,),sliders)
                (lower if bound["side"] == "lower" else upper).append(function)
                bound_functions.append((function,bound))
            runs=[]; run=[]; previous=None; envelopes=[]
            for index in range(len(first)):
                low = None if first[index] is None else first[index][1]
                high = None if second[index] is None else second[index][1]
                at = a+(b-a)*index/count
                lows,highs = [evaluate(fn,at) for fn in lower],[evaluate(fn,at) for fn in upper]
                if low is None or high is None or any(v is None for v in lows+highs):
                    envelopes.append(None)
                    if len(run) >= 2: runs.append(run)
                    run=[]; previous=None
                    continue
                low,high = max([min(low,high)]+lows),min([max(low,high)]+highs)
                envelopes.append((low,high) if low <= high else None)
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
            polygons = []
            for segment in runs:
                top = [[at,max(low,high)] for at,low,high in segment]
                bottom = [[at,min(low,high)] for at,low,high in segment]
                polygons.append(top+list(reversed(bottom)))
            boundaries = [first,second if len(group) == 2 else None]
            styles = ["solid","solid"]
            if bound_functions:
                # Draw each actual boundary with its own inclusion rule. A clipped
                # envelope can switch between a function and a strict inequality.
                candidates = [(first,False),(second,False)]+[
                    ([[point[0],evaluate(fn,point[0])] if point else None for point in first],bound.get("strict",False))
                    for fn,bound in bound_functions]
                boundaries,styles = [],[]
                for points,strict in candidates:
                    line=[]
                    for point,envelope in zip(points,envelopes):
                        visible = point is not None and point[1] is not None and envelope is not None
                        if visible:
                            low,high = envelope; value = point[1]
                            tolerance = 1e-9*max(1,abs(value),abs(low),abs(high))
                            visible = abs(value-low)<=tolerance or abs(value-high)<=tolerance
                            # Strictness wins when coincident constraints meet.
                            if visible and not strict:
                                visible = not any(bound.get("strict") and (v:=evaluate(fn,point[0])) is not None and abs(v-value)<=tolerance for fn,bound in bound_functions)
                        line.append([point[0],clamp(point[1])] if visible else None)
                    boundaries.append(line);styles.append("dashed" if strict else "solid")
                if not polygons: boundaries,styles = [[],[]],["solid","solid"]
            for bound in item.get("xBounds",[]):
                at = endpoint({"bound":bound["tree"]},"bound",0)
                if not bound.get("strict") and any(other.get("strict") and abs(endpoint({"bound":other["tree"]},"bound",0)-at)<=1e-9*max(1,abs(at)) for other in item.get("xBounds",[])): continue
                if a <= at <= b and xmin <= at <= xmax:
                    values = [evaluate(graph_function(expr,(x,),sliders),at) for expr in group]
                    if len(values)==1: values.append(0.)
                    lows,highs = [evaluate(fn,at) for fn in lower],[evaluate(fn,at) for fn in upper]
                    if all(v is not None for v in values+lows+highs):
                        low,high = max([min(values)]+lows),min([max(values)]+highs)
                        if low < high:
                            boundaries.append([[at,clamp(low)],[at,clamp(high)]])
                            styles.append("dashed" if bound.get("strict") else "solid")
            shadings.append({"mode":mode,"boundary":boundaries,"boundaryStyles":styles,"fill":polygons})
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


def _join_boundary_segments(segments, xmin, xmax, ymin, ymax, logarithmic=False):
    """Stitch triangle edges into paths so dash phase survives cell boundaries."""
    def key(point):
        y_fraction = ((math.log10(point[1])-math.log10(ymin))/(math.log10(ymax)-math.log10(ymin))
                      if logarithmic else (point[1]-ymin)/(ymax-ymin))
        return (round((point[0]-xmin)/(xmax-xmin)*1e9),round(y_fraction*1e9))
    nodes,edges = {},set()
    for a,b in segments:
        ka,kb = key(a),key(b)
        edge = tuple(sorted((ka,kb)))
        if ka == kb or edge in edges: continue
        edges.add(edge)
        for start,end,point in ((ka,kb,a),(kb,ka,b)):
            if start not in nodes: nodes[start] = (point,set())
            nodes[start][1].add(end)
    result=[]
    def walk(start):
        line=[nodes[start][0]]; current=start
        while nodes[current][1]:
            following=nodes[current][1].pop()
            nodes[following][1].discard(current)
            line.append(nodes[following][0]);current=following
            if current == start or len(nodes[current][1]) != 1: break
        if len(line)>1:
            if result: result.append(None)
            result.extend(line)
    # Start open contours at endpoints; then consume closed contours.
    for start,(_,neighbors) in nodes.items():
        if len(neighbors)!=2:
            while neighbors: walk(start)
    for start,(_,neighbors) in nodes.items():
        while neighbors: walk(start)
    return result


@lru_cache(maxsize=64)
def _explicit_inequality(expression, x, y):
    """Recognize continuous y half-planes without changing residual signs."""
    try:
        polynomial = s.Poly(expression, y)
        if polynomial.degree() != 1: return None
        coefficient, constant = polynomial.all_coeffs()
        if coefficient.has(x, y): return None
        boundary = -constant/coefficient
        def continuous(expr):
            if not expr.has(x): return True
            if expr == x: return True
            if expr.func in (s.Add, s.Mul, s.sin, s.cos, s.exp, s.Abs):
                return all(continuous(arg) for arg in expr.args)
            if expr.is_Pow and expr.exp.is_Integer and expr.exp >= 0:
                return continuous(expr.base)
            return False
        # Poles, domain cuts, piecewise jumps, and nonlinear y constraints keep
        # the general triangle clipper, including its undefined-cell behavior.
        return (coefficient, boundary) if continuous(boundary) else None
    except s.PolynomialError:
        return None


def _explicit_inequality_shading(parts, x, y, sliders, xmin, xmax, ymin, ymax, samples, logarithmic):
    specifications = [_explicit_inequality(expr, x, y) for expr, _ in parts]
    if any(spec is None for spec in specifications): return None
    coefficients = [_finite_real(substitute_parameters(spec[0], sliders)) for spec in specifications]
    if any(value is None or value == 0 for value in coefficients): return None
    lower = [i for i, value in enumerate(coefficients) if value < 0]
    upper = [i for i, value in enumerate(coefficients) if value > 0]
    function = graph_function(tuple(spec[1] for spec in specifications), (x,), sliders)
    evaluated = {}
    def evaluate(at):
        if at not in evaluated:
            try:
                values = function(at)
                evaluated[at] = values if all(math.isfinite(value) and abs(value)<1e100 for value in values) else None
            except (TypeError, ValueError, ZeroDivisionError, OverflowError): evaluated[at] = None
        return evaluated[at]
    def envelope(values):
        return max([ymin]+[values[i] for i in lower]), min([ymax]+[values[i] for i in upper])
    # Refine both envelopes in one pass. Only screen-space curvature matters
    # for this continuous fill; avoid two samplers with duplicate midpoint work.
    count = capped(max(100, samples), 512)
    max_points = capped(max(samples+1, 1200), 1800)
    positions = {xmin+(xmax-xmin)*i/count for i in range(count+1)}
    view_low, view_high = (math.log10(ymin), math.log10(ymax)) if logarithmic else (ymin, ymax)
    scale = 800/(view_high-view_low)
    def projected(at):
        values = evaluate(at)
        if values is None: return None
        clipped = tuple(min(ymax, max(ymin, value)) for value in envelope(values))
        return tuple(math.log10(value) for value in clipped) if logarithmic else clipped
    def refine(left, right, before, after, depth=0):
        if depth >= 16 or len(positions)>=max_points: return
        middle = (left+right)/2
        if middle in (left, right): return
        actual = projected(middle)
        if before is None and after is None and actual is None: return
        split = before is None or after is None or actual is None
        if not split:
            split = any(abs(actual[i]-(before[i]+after[i])/2)*scale>.2 for i in (0, 1))
        if split:
            positions.add(middle)
            refine(left, middle, before, actual, depth+1)
            refine(middle, right, actual, after, depth+1)
    coarse = sorted(positions)
    previous = projected(coarse[0])
    for left, right in zip(coarse, coarse[1:]):
        following = projected(right)
        refine(left, right, previous, following)
        previous = following
    sampled = sorted(positions)
    positions = {xmin, xmax}
    for side, indices in enumerate((lower, upper)):
        if not indices: continue
        points = [[at, min(ymax, max(ymin, envelope(evaluate(at))[side]))] if evaluate(at) is not None else None for at in sampled]
        _, parameters = simplify_samples(points, sampled,
            {"graphKind":"cartesian", "yMin":ymin, "yMax":ymax, "yLog":logarithmic}, xmin, xmax)
        positions.update(parameters)
    positions = sorted(positions)
    values = [evaluate(at) for at in positions]
    # Retain viewport crossings and changes in the ordering of boundaries.
    # These roots separate disconnected bands instead of bridging empty areas.
    comparisons = [(i, None, edge) for i in range(len(parts)) for edge in (ymin, ymax)]
    comparisons += [(i, j, None) for i in range(len(parts)) for j in range(i)]
    nodes = []
    for index, (at, current) in enumerate(zip(positions, values)):
        if index and current is not None and values[index-1] is not None:
            left, previous = positions[index-1], values[index-1]
            crossings = []
            for i, j, edge in comparisons:
                before = previous[i]-(edge if j is None else previous[j])
                after = current[i]-(edge if j is None else current[j])
                if before == 0 or after == 0 or (before < 0) == (after < 0): continue
                low, high, va, vb = left, at, before, after
                for iteration in range(32):
                    fraction = .5 if iteration % 3 == 2 else max(.05, min(.95, abs(va)/(abs(va)+abs(vb))))
                    middle = low+(high-low)*fraction
                    actual = evaluate(middle)
                    if actual is None: return None
                    delta = actual[i]-(edge if j is None else actual[j])
                    if abs(delta) <= 1e-12*max(1, abs(actual[i])): break
                    if (va < 0) == (delta < 0): low, va = middle, delta
                    else: high, vb = middle, delta
                else:
                    return None
                crossing = list(actual)
                if j is None: crossing[i] = edge
                else: crossing[i] = crossing[j] = (actual[i]+actual[j])/2
                crossings.append((middle, tuple(crossing)))
            nodes.extend(sorted(crossings, key=lambda item:item[0]))
        nodes.append((at, current))
    fill, boundaries, run = [], [[] for _ in parts], []
    def flush():
        if len(run) > 1:
            top = [[px, hi] for px, lo, hi in run]
            bottom = [[px, lo] for px, lo, hi in reversed(run)]
            fill.append(top+bottom)
        run.clear()
    previous = None
    for node_index, (at, current) in enumerate(nodes):
        lo, hi = envelope(current) if current is not None else (0, -1)
        for i, boundary in enumerate(boundaries):
            value = current[i] if current is not None else None
            tolerance = 1e-9*max(1, abs(value)) if value is not None else 0
            visible = value is not None and ymin <= value <= ymax and lo-tolerance <= value <= hi+tolerance
            if visible and lo == hi and any(strict and abs(current[j]-lo)<=tolerance for j, (_, strict) in enumerate(parts)):
                # Keep the endpoint of a real band at a crossing, but suppress
                # wholly empty strict bands such as 0 < y < 0.
                neighbors = [nodes[j][1] for j in (node_index-1, node_index+1) if 0<=j<len(nodes)]
                visible = any(values is not None and (bounds:=envelope(values))[0]<bounds[1] for values in neighbors)
            if visible and not parts[i][1]:
                visible = not any(strict and abs(current[j]-value)<=tolerance for j, (_, strict) in enumerate(parts))
            if visible: boundary.append([at, value])
            elif boundary and boundary[-1] is not None: boundary.append(None)
        if current is None:
            flush(); previous = None; continue
        lo, hi = min(ymax, max(ymin, lo)), min(ymax, max(ymin, hi))
        point = [at, lo, hi]
        if lo < hi:
            if not run and previous is not None: run.append(previous)
            run.append(point)
        else:
            if run and lo == hi: run.append(point)
            flush()
        previous = point if lo <= hi else None
    flush()
    curve = []
    for boundary in boundaries:
        if boundary and boundary[-1] is None: boundary.pop()
        if curve and boundary: curve.append(None)
        curve.extend(boundary)
    return {"mode":"inequality", "fill":fill, "boundary":boundaries,
            "boundaryStyles":["dashed" if strict else "solid" for _,strict in parts], "curve":curve}


def inequality_shading(parts, x, y, sliders, xmin, xmax, ymin, ymax, samples, logarithmic=False):
    """Clip bounded triangles by signed residuals, preserving holes and undefined cells.

    Full cells become horizontal strips to bound transport size. Boundary cells
    retain subcell polygons; no square-free transform may change an inequality's sign.
    """
    if 1 <= len(parts) <= 4:
        explicit = _explicit_inequality_shading(parts, x, y, sliders, xmin, xmax, ymin, ymax, samples, logarithmic)
        if explicit is not None: return explicit
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
    fill, segments = [], [[] for _ in parts]
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
                            segments[k].append([[a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])] for t in (lo,hi)])
        previous = current
    boundaries = [_join_boundary_segments(lines,xmin,xmax,ymin,ymax,logarithmic) for lines in segments]
    curve=[]
    for line in boundaries:
        if curve and line: curve.append(None)
        curve.extend(line)
    return {"mode":"inequality", "fill":fill, "boundary":boundaries,
            "boundaryStyles":["dashed" if strict else "solid" for _,strict in parts], "curve":curve}
