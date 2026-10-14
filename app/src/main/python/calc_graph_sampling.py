"""Numerical curve sampling and viewport simplification, independent of requests' ASTs."""
from calc_limits import capped
from calc_shared import require
import math
import sympy as s
from calc_graph_common import _finite_real


def regression_samples(engine, value, rows, request):
    xs = [point for point in (_finite_real(row[0]) for row in rows) if point is not None]
    require(len(xs)>=2,"Regression requires x,y pairs")
    low,high = min(xs),max(xs)
    if high<=low: low-=1.0; high+=1.0
    padding=(high-low)*0.05
    start,end=low-padding,high+padding
    count=capped(max(120,int(request.get("samples",240))),600)
    if getattr(engine, "regression_predict", None) is not None:
        function = lambda x: engine.regression_predict([x])
    else:
        x=next(iter(value.free_symbols),engine.symbol("x"))
        function=s.lambdify(x,value,modules="math",cse=True,docstring_limit=0)
    curve=[]
    for index in range(count+1):
        at=start+(end-start)*index/count
        try: y=float(function(at))
        except (TypeError,ValueError,ZeroDivisionError,OverflowError): continue
        if math.isfinite(y) and abs(y)<1e100: curve.append([at,y])
    return curve


def implicit_samples(function, xmin, xmax, ymin, ymax, count):
    """Refine a quadtree near the contour, then march its smallest triangles.

    Probe edge midpoints and centers as well as corners to catch closed loops
    and domain boundaries. Cache shared vertices and root refinements.
    """
    def value(point):
        try:
            return _finite_real(function(*point))
        except (TypeError, ValueError, ZeroDivisionError, OverflowError):
            return None
    # Eight fine cells per coarse cell: retain requested density without
    # rounding an entire plane up to the next power of two.
    resolution = max(8, int(math.ceil(count/8))*8)
    xs = [xmin+(xmax-xmin)*i/resolution for i in range(resolution+1)]
    ys = [ymin+(ymax-ymin)*i/resolution for i in range(resolution+1)]
    values = {}
    def sample(point):
        if point not in values:
            values[point] = value((xs[point[0]], ys[point[1]]))
        return values[point]
    edges = {}
    def crossing(a, b):
        va, vb = sample(a), sample(b)
        if va is None or vb is None or va != 0 and vb != 0 and (va < 0) == (vb < 0): return None
        key = tuple(sorted((a, b)))
        if key in edges: return edges[key]
        pa, pb = [xs[a[0]], ys[a[1]]], [xs[b[0]], ys[b[1]]]
        root = None
        if va is not None and vb is not None:
            if va == 0: root = pa
            elif vb == 0: root = pb
            elif (va < 0) != (vb < 0):
                scale = max(abs(va), abs(vb))
                for iteration in range(20):
                    # Secant interpolation converges quickly on smooth edges;
                    # periodic bisection safeguards very unbalanced brackets.
                    fraction = .5 if iteration % 3 == 2 else max(.001, min(.999, abs(va)/(abs(va)+abs(vb))))
                    middle = [pa[0]+(pb[0]-pa[0])*fraction, pa[1]+(pb[1]-pa[1])*fraction]
                    vm = value(middle)
                    if vm is None: break
                    if abs(vm) <= scale*1e-7:
                        root = middle
                        break
                    if (va < 0) == (vm < 0): pa, va = middle, vm
                    else: pb, vb = middle, vm
                else:
                    if abs(vm) <= scale*1e-4: root = middle
        edges[key] = root
        return root
    curve = []
    def cell(col, row, width):
        a, b, c, d = (col,row), (col+width,row), (col+width,row+width), (col,row+width)
        corners = (a,b,c,d)
        if width > 1:
            half = width//2
            probes = corners+((col+half,row), (col+width,row+half),
                              (col+half,row+width), (col,row+half), (col+half,row+half))
            samples = [sample(p) for p in probes]
            finite = [v for v in samples if v is not None]
            if not finite: return
            low, high = min(finite), max(finite)
            # Uniform, far-from-zero cells need no more evaluations. Nearby
            # same-sign cells still descend, including loops inside a cell.
            if len(finite) == len(probes) and (low > 0 or high < 0):
                if min(abs(low), abs(high)) > 1.5*(high-low): return
            for dx, dy in ((0,0), (half,0), (half,half), (0,half)):
                cell(col+dx, row+dy, half)
            return
        for triangle in ((a,b,c), (a,c,d)):
            samples = [sample(p) for p in triangle]
            if None in samples or min(samples) > 0 or max(samples) < 0: continue
            roots = []
            for i in range(3):
                root = crossing(triangle[i], triangle[(i+1)%3])
                if root is not None and root not in roots: roots.append(root)
            if len(roots) == 2: curve.extend([roots[0], roots[1], None])
    width = 8
    for row in range(0, resolution, width):
        for col in range(0, resolution, width):
            cell(col, row, width)
    return curve


def simplify_samples(points, parameters, request, start, end):
    """Collapse collinear samples within 0.3 screen pixels; retain breaks/features."""
    xmin, xmax = float(request.get("xMin", start)), float(request.get("xMax", end))
    ymin, ymax = float(request.get("yMin", -5)), float(request.get("yMax", 5))
    if not all(map(math.isfinite, (xmin, xmax, ymin, ymax))) or xmax <= xmin or ymax <= ymin:
        return points, parameters
    source_points = points
    if request.get("yLog"):
        if ymin <= 0: return points, parameters
        points = [[p[0], math.log10(p[1])] if p is not None and p[1] > 0 else None for p in points]
        ymin, ymax = math.log10(ymin), math.log10(ymax)
    sx, sy = 800/(xmax-xmin), 800/(ymax-ymin)
    keep = set()
    def reduce_run(first, last):
        keep.update((first, last))
        if request.get("graphKind", "cartesian") == "cartesian":
            # A slope corridor gives a linear-time, bounded vertical error
            # for monotone x. Each omitted point constrains the final segment.
            anchor, low, high = first, -math.inf, math.inf
            for i in range(first+1, last+1):
                dx = (points[i][0]-points[anchor][0])*sx
                dy = (points[i][1]-points[anchor][1])*sy
                if dx <= 0: keep.add(i); anchor, low, high = i, -math.inf, math.inf; continue
                slope = dy/dx
                if slope < low or slope > high:
                    keep.add(i-1)
                    anchor, low, high = i-1, -math.inf, math.inf
                    dx = (points[i][0]-points[anchor][0])*sx
                    dy = (points[i][1]-points[anchor][1])*sy
                low, high = max(low, (dy-.3)/dx), min(high, (dy+.3)/dx)
            return
        stack = [(first, last)]
        while stack:
            left, right = stack.pop()
            if right-left < 2: continue
            a, b = points[left], points[right]
            dx, dy = (b[0]-a[0])*sx, (b[1]-a[1])*sy
            length2 = dx*dx+dy*dy
            best, index = .3*.3, None
            for i in range(left+1, right):
                px, py = (points[i][0]-a[0])*sx, (points[i][1]-a[1])*sy
                at = max(0, min(1, (px*dx+py*dy)/length2)) if length2 else 0
                distance2 = (px-at*dx)**2+(py-at*dy)**2
                if distance2 > best: best, index = distance2, i
            if index is not None:
                keep.add(index)
                stack.extend(((left,index), (index,right)))
    first = None
    for i, point in enumerate(points):
        if point is None:
            keep.add(i)
            if first is not None: reduce_run(first, i-1)
            first = None
            continue
        if first is None: first = i
        # Preserve exact axis hits and sampled extrema for tracing and fitting.
        feature = any(value == 0 and (
            i > 0 and points[i-1] is not None and points[i-1][axis] != 0 or
            i+1 < len(points) and points[i+1] is not None and points[i+1][axis] != 0
        ) for axis, value in enumerate(point))
        if i > 0 and i+1 < len(points) and points[i-1] is not None and points[i+1] is not None:
            feature |= any((point[axis]-points[i-1][axis])*(points[i+1][axis]-point[axis]) < 0 for axis in (0,1))
        if feature:
            reduce_run(first, i)
            first = i
    if first is not None: reduce_run(first, len(points)-1)
    indices = sorted(keep)
    return [source_points[i] if points[i] is not None else None for i in indices], [parameters[i] for i in indices]


def adaptive_samples(function, start, end, base_count, kind="cartesian",screen_bounds=None,logarithmic=False):
    """Sample coarsely first, then add points where the curve bends or breaks."""
    def point(at):
        try:
            if kind == "parametric":
                x, y = map(float, function(at))
            else:
                y = float(function(at)); x = at
                if kind == "polar": x, y = y*math.cos(at), y*math.sin(at)
            return [x, y] if (not logarithmic or y > 0) and math.isfinite(x) and math.isfinite(y) and abs(x) < 1e100 and abs(y) < 1e100 else None
        except (TypeError, ValueError, ZeroDivisionError, OverflowError):
            return None
    if logarithmic and screen_bounds:
        screen_bounds=(*screen_bounds[:2],math.log10(screen_bounds[2]),math.log10(screen_bounds[3]))
    intervals = capped(max(100, base_count),512)
    values = {start + (end-start)*i/intervals: None for i in range(1,intervals)}
    # Preserve nextafter endpoints: interpolation can round an open endpoint
    # back onto the excluded boundary, especially when that boundary is zero.
    values.update({start:None,end:None})
    for at in values:
        values[at] = point(at)
    max_points = capped(max(base_count+1, 1200),1800)
    def refine(left, right, depth):
        # A fixed seven levels loses narrow visible sections when zoomed out
        # (e.g. x**23-4 in a million-unit range). Offscreen pruning keeps deeper
        # viewport refinement bounded by the existing point budget.
        if depth >= (48 if screen_bounds else 4) or len(values) >= max_points:
            return
        middle = (left+right)/2
        if middle==left or middle==right: return
        actual = point(middle)
        a, b = values[left], values[right]
        if logarithmic:
            a=[a[0],math.log10(a[1])] if a is not None else None
            b=[b[0],math.log10(b[1])] if b is not None else None
            actual=[actual[0],math.log10(actual[1])] if actual is not None else None
        # Skip all-undefined probes and monotone probes well outside the view.
        # Keep a full viewport of margin and still refine turns near reentry.
        if screen_bounds and a is None and b is None and actual is None:
            return
        if screen_bounds and a is not None and b is not None and actual is not None:
            _,_,view_low,view_high=screen_bounds
            margin=view_high-view_low
            monotone=min(a[1],b[1])<=actual[1]<=max(a[1],b[1])
            if monotone and (max(a[1],b[1],actual[1])<view_low-margin or min(a[1],b[1],actual[1])>view_high+margin):
                return
        split = a is None or b is None or actual is None
        if a is not None and b is not None and actual is not None:
            linear = ((a[0]+b[0])/2, (a[1]+b[1])/2)
            span = max(abs(b[0]-a[0]), abs(b[1]-a[1]), 1e-9)
            error = max(abs(actual[0]-linear[0]), abs(actual[1]-linear[1]))/span
            split = error > 0.012 or abs(b[1]-a[1]) > 0.22*max(abs(end-start),1e-9)
            if screen_bounds:
                _,_,view_low,view_high=screen_bounds
                if min(a[1],b[1],actual[1])<=view_high and max(a[1],b[1],actual[1])>=view_low:
                    split=split or abs(actual[1]-linear[1])*800/(view_high-view_low)>.2
        if split:
            values[middle] = point(middle) if logarithmic else actual
            refine(left, middle, depth+1)
            refine(middle, right, depth+1)
    coarse = sorted(values)
    for left, right in zip(coarse, coarse[1:]):
        refine(left, right, 0)
    positions = sorted(values)
    if kind == "cartesian":
        # A long segment may be perfectly linear after simplification. Encode
        # discontinuities explicitly instead of making renderers discard every
        # steep segment (which would also hide straight lines and tangents).
        for left, right in zip(positions, positions[1:]):
            a, b = values[left], values[right]
            if a is None or b is None or (a[1] < 0) == (b[1] < 0) or abs(b[1]-a[1]) <= .22*max(end-start, 1e-9): continue
            lo, hi, low = left, right, a[1]
            tolerance = max(min(abs(a[1]), abs(b[1]))*1e-6, 1e-12)
            for _ in range(48):
                middle = (lo+hi)/2
                actual = point(middle)
                if actual is None: break
                if abs(actual[1]) <= tolerance: break
                if (actual[1] < 0) == (low < 0): lo, low = middle, actual[1]
                else: hi = middle
            else:
                actual = None
            if actual is None: values[(left+right)/2] = None
        positions = sorted(values)
    return [values[at] for at in positions], positions
