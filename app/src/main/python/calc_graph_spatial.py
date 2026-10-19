"""3D graph request handling; geometric samplers live in calc_graph3d."""
from calc_limits import capped
from calc_shared import require
from functools import lru_cache
import math
import sympy as s
from calc_graph_common import (
    _finite_real,
    graph_expressions,
    graph_function,
    parameter_names,
    resolved_parameters,
)


def graph_space(engine,request,trees,start,end):
    from calc_graph3d import space_coordinate_trees,space_curve_samples
    require(1<=len(trees)<=5,"Enter one to five 3D curves [x(t),y(t),z(t)]")
    coordinates=[space_coordinate_trees(tree) for tree in trees]
    require(all(coordinates),"Enter a 3D curve [x(t),y(t),z(t)] or C(t)=(x(t),y(t),z(t))")
    t=engine.symbol('t');engine.bindings['t']=t
    flat=graph_expressions(engine,[coordinate for group in coordinates for coordinate in group],('t',))
    names=parameter_names(flat,{'t'});sliders=resolved_parameters(engine,request,flat,{'t'})
    bounds=tuple((float(request.get(low,default[0])),float(request.get(high,default[1]))) for low,high,default in (
        ('xMin','xMax',(-5,5)),('yMin','yMax',(-5,5)),('surfaceZMin','surfaceZMax',(-5,5))))
    require(all(math.isfinite(low) and math.isfinite(high) and high>low for low,high in bounds),'Enter finite increasing ranges')
    curves=[];parameters=[]
    for i in range(0,len(flat),3):
        curve,positions=space_curve_samples(graph_function(tuple(flat[i:i+3]),(t,),sliders),start,end,int(request.get('samples',500)),bounds)
        curves.append(curve);parameters.append(positions)
    zs=[p[2] for curve in curves for p in curve if p]
    return {'surface':[],'spaceCurves':curves,'curveParameters':parameters,'parameters':sorted(names),
            'zMin':min(zs) if zs else -1,'zMax':max(zs) if zs else 1}


@lru_cache(maxsize=64)
def axis_quadric(expression,axes):
    try:
        polynomial=s.Poly(expression,*axes)
        allowed={(0,0,0),(2,0,0),(0,2,0),(0,0,2),(1,0,0),(0,1,0),(0,0,1)}
        if not set(polynomial.monoms())<=allowed:return None
        quadratic=tuple(polynomial.coeff_monomial(axis**2) for axis in axes)
        if any(value==0 for value in quadratic):return None
        return quadratic+tuple(polynomial.coeff_monomial(axis) for axis in axes)+(polynomial.coeff_monomial(1),)
    except (s.PolynomialError,ValueError,TypeError):return None


@lru_cache(maxsize=64)
def continuous_surface_expression(expression):
    """Draw proven removable sine quotients using their continuous extension.

    Only cancel polynomial factors: probing nearby values could incorrectly fill
    poles or multivariate singularities whose limit depends on direction.
    This is a rendering program; the calculator's expression stays unchanged.
    """
    def extend(term):
        numerator, denominator = s.fraction(term)
        if denominator == 1 or not denominator.is_polynomial():
            return term
        for factor in s.Mul.make_args(numerator):
            if factor.func != s.sin or not factor.args[0].is_polynomial():
                continue
            argument = factor.args[0]
            coefficient = s.cancel((numerator/factor)*argument/denominator)
            if coefficient.is_polynomial():
                return coefficient*s.sinc(argument)
        return term
    return expression.replace(lambda term: isinstance(term,s.Mul), extend)


@lru_cache(maxsize=32)
def surface_coordinates(low,high,count):
    return tuple(low+(high-low)*index/count for index in range(count+1))


def graph_surface(engine, request, trees, xmin, xmax):
    require(1<=len(trees)<=5,"Enter one to five surface expressions z=f(x,y) or F(x,y,z)=0")
    if len(trees)==1:
        return graph_surface_single(engine,request,trees[0],xmin,xmax)
    surfaces=[graph_surface_single(engine,request,tree,xmin,xmax) for tree in trees]
    return {'surface':[], 'surfaces':surfaces,
            'parameters':sorted({name for surface in surfaces for name in surface['parameters']}),
            'zMin':min(surface['zMin'] for surface in surfaces),
            'zMax':max(surface['zMax'] for surface in surfaces)}


def graph_surface_single(engine, request, tree, xmin, xmax):
    from calc_graph_parametric_surface import parametric_surface_tree, surface_definition_expressions, graph_parametric_surface
    parametric = parametric_surface_tree(tree)
    local_expression = None
    if parametric is not None:
        expressions = surface_definition_expressions(engine, parametric)
        if len(expressions) == 3:
            return graph_parametric_surface(engine, request, expressions)
        local_expression = expressions[0]
    ymin, ymax = float(request.get("surfaceYMin", -3)), float(request.get("surfaceYMax", 3))
    require(math.isfinite(ymin) and math.isfinite(ymax) and ymax > ymin, "Invalid surface y range")
    x, y, z = engine.symbol("x"), engine.symbol("y"), engine.symbol("z")
    engine.bindings.update({"x":x, "y":y, "z":z})
    expression = local_expression if local_expression is not None else graph_expressions(engine, [tree], ("x", "y", "z"))[0]
    if isinstance(expression,s.Equality):
        implicit=not (expression.lhs==z and not expression.rhs.has(z))
        expression=expression.lhs-expression.rhs if implicit else expression.rhs
    else:
        implicit=isinstance(expression,s.Expr) and expression.has(z)
    require(isinstance(expression,s.Expr),"Enter one surface expression z=f(x,y) or F(x,y,z)=0")
    if implicit:
        from calc_graph3d import implicit_surface_samples
        require(expression!=0,"Equation is true everywhere; enter a surface equation")
        zmin,zmax=float(request.get('surfaceZMin',ymin)),float(request.get('surfaceZMax',ymax))
        require(math.isfinite(zmin) and math.isfinite(zmax) and zmax>zmin,"Invalid surface z range")
        axes={"x","y","z"}
        names=parameter_names([expression],axes)
        sliders=resolved_parameters(engine,request,[expression],axes)
        count=max(12,min(32,int(request.get('surfaceSamples',26))))
        coefficients=axis_quadric(expression,(x,y,z))
        if coefficients is not None:
            try:values=[_finite_real(v) for v in graph_function(coefficients,(),sliders)()]
            except (ValueError,TypeError,ZeroDivisionError,OverflowError):values=[]
            require(len(values)==7 and all(v is not None for v in values),'Surface parameters must give finite real coefficients')
            q,linear,constant=values[:3],values[3:6],values[6]
            if all(v!=0 for v in q) and (all(v>0 for v in q) or all(v<0 for v in q)):
                center=[-b/(2*a) for a,b in zip(q,linear)]
                level=sum(a*c*c for a,c in zip(q,center))-constant
                ratios=[level/a for a in q]
                from calc_graph3d import ellipsoid_samples
                vertices,triangles,normals=ellipsoid_samples(center,[math.sqrt(v) for v in ratios],count) if all(v>0 and math.isfinite(v) for v in ratios) else ([],[],[])
                return {'surface':[],'surfaceVertices':vertices,'surfaceTriangles':triangles,'surfaceNormals':normals,
                        'implicitSurface':True,'convexSurface':True,'surfaceSamples':count,'parameters':sorted(names),'zMin':zmin,'zMax':zmax}
        fn=graph_function(expression,(x,y,z),sliders)
        vertices,triangles,count,normals=implicit_surface_samples(fn,((xmin,xmax),(ymin,ymax),(zmin,zmax)),int(request.get('surfaceSamples',26)))
        return {"surface":[],"surfaceVertices":vertices,"surfaceTriangles":triangles,"surfaceNormals":normals,"implicitSurface":True,
                "zMin":zmin,"zMax":zmax,"surfaceSamples":count,"parameters":sorted(names)}
    names = parameter_names([expression], {"x","y"})
    sliders=resolved_parameters(engine, request, [expression], {"x","y"})
    count = capped(max(12, int(request.get("surfaceSamples", 26))),96)
    from calc_graph_surface import radial_sine_surface, angular_surface
    angular=angular_surface(expression,x,y,sliders,xmin,xmax,ymin,ymax,count)
    if angular is not None:return {**angular,'parameters':sorted(names)}
    radial=radial_sine_surface(expression,x,y,sliders,xmin,xmax,ymin,ymax,count) if request.get('surfaceAutoZ',True) else None
    if radial is not None:return {**radial,'parameters':sorted(names)}
    fn = graph_function(continuous_surface_expression(expression), (x,y), sliders)
    xs,ys=surface_coordinates(xmin,xmax,count),surface_coordinates(ymin,ymax,count)
    compact=request.get('surfaceCompactGrid',False)
    mesh = []
    for yy in ys:
        points = []
        for xx in xs:
            try: z = _finite_real(fn(xx,yy))
            except (TypeError, ValueError, ZeroDivisionError, OverflowError): z = None
            points.append(z if compact else [xx,yy,z] if z is not None else None)
        mesh.append(points)
    values = [point if compact else point[2] for row in mesh for point in row if point is not None]
    require(values, "Surface has no finite values in this range")
    if compact:return {"surface":[],"surfaceGrid":{"x":xs,"y":ys,"z":mesh},"zMin":min(values),"zMax":max(values),"surfaceSamples":count,"parameters":sorted(names)}
    return {"surface":mesh,"zMin":min(values),"zMax":max(values),"surfaceSamples":count,"parameters":sorted(names)}
