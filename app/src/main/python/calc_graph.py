"""Graph request dispatcher and compatibility imports for the shared engine.

Implementation modules depend on common symbolic programs and numerical
samplers, never on this facade. Android, Web, and existing callers keep
using graph(), graph_analysis(), and the historical helper imports here."""
from calc_shared import require
import math
import sympy as s
from calc_graph_analysis import (
    _cartesian_tangent_direction,
    _graph_direction,
    graph_analysis,
    implicit_analysis,
    interval_extrema,
    polynomial_real_roots,
)
from calc_graph_planar import (
    contour_curve,
    graph_cartesian,
    graph_implicit,
    graph_parametric,
)
from calc_graph_common import (
    _compiled_graph,
    _finite_real,
    _graph_programs,
    _square_free_graph,
    bind_graph_parameters,
    cartesian_branches,
    cartesian_curve,
    graph_expressions,
    graph_function,
    parameter_names,
    parameter_values,
    resolved_parameters,
    substitute_parameters,
)
from calc_graph_dynamics import (
    graph_differential,
    graph_sequence,
)
from calc_graph_sampling import (
    adaptive_samples,
    implicit_samples,
    regression_samples,
    simplify_samples,
)
from calc_graph_shading import (
    graph_shading,
    integral_fill,
)
from calc_graph_spatial import (
    axis_quadric,
    graph_space,
    graph_surface,
    graph_surface_single,
)


def graph(engine, request):
    bind_graph_parameters(engine,request)
    kind = request.get("graphKind","cartesian")
    axes={"cartesian":("x","y"),"implicit":("x","y"),"surface":("x","y","z"),
          "space":("t",),"differential":("t","y")}.get(kind,(request.get("variable","x"),))
    if kind != "sequence":
        for name in axes:
            if engine.symbol(name).is_real is not True: engine.symbols[name]=s.Symbol(name,real=True)
    trees = request.get("trees",[])
    start,end = float(request.get("min",-10)),float(request.get("max",10))
    require(math.isfinite(start) and math.isfinite(end) and end>start,"Invalid graph range")
    if request.get("yLog") and kind not in ("surface", "space"):
        ymin,ymax=float(request.get("yMin",.01)),float(request.get("yMax",10))
        require(math.isfinite(ymin) and math.isfinite(ymax) and 0 < ymin < ymax, "Log y requires 0 < y min < y max")
    if kind == "implicit":
        return graph_implicit(engine, request, trees, start, end)
    if kind == "cartesian":
        return graph_cartesian(engine, request, trees, start, end)
    if kind == "sequence":
        return graph_sequence(engine, request, trees, start, end)
    if kind == "surface":
        return graph_surface(engine, request, trees, start, end)
    if kind == "space":
        return graph_space(engine,request,trees,start,end)
    if kind == "differential":
        return graph_differential(engine, request, trees, start, end)
    return graph_parametric(engine, request, trees, start, end, kind)
