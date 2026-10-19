"""Per-row domains and finite parameter families for spatial curves."""
from itertools import product
from functools import lru_cache
import math
import sympy as s
from calc_conditions import build_condition
from calc_limits import within_limit
from calc_shared import require
from calc_graph_common import _finite_real, graph_expressions, graph_function, parameter_names, resolved_parameters
from calc_graph3d import space_coordinate_trees, space_curve_samples


@lru_cache(maxsize=128)
def space_intervals(condition,start,end):
    """Reuse immutable domains across family members and animation frames."""
    domain=condition.as_set().intersect(s.Interval(start,end))
    intervals=list(domain.args) if isinstance(domain,s.Union) else [domain]
    intervals.sort(key=lambda interval:float(interval.inf) if interval!=s.EmptySet else math.inf)
    result=[]
    for interval in intervals:
        if not isinstance(interval,s.Interval):continue
        low,high=float(interval.start),float(interval.end)
        if interval.left_open:low=math.nextafter(low,high)
        if interval.right_open:high=math.nextafter(high,low)
        if high>low:result.append((low,high))
    return tuple(result)


@lru_cache(maxsize=64)
def affine_space_curve(expressions,t):
    """Certify a straight segment for every value of the other parameters."""
    try:
        return all(expression.is_polynomial(t) and s.Poly(expression,t).degree()<=1 for expression in expressions)
    except (s.PolynomialError,AttributeError):return False


def space_definition(tree):
    guards=[]
    while True:
        kind=tree.get('kind');args=tree.get('args',[])
        if kind=='group':tree=args[0]
        elif kind=='relation' and tree.get('value') in ('=','==') and args[0].get('kind')=='call':tree=args[1]
        elif kind=='piecewise' and tree.get('value')=='restriction':
            tree,guard=args[0]['args'];guards.append(guard)
        else:break
    def conditions(guard):
        if guard.get('kind') in ('group','list'):
            return [item for child in guard['args'] for item in conditions(child)]
        return [guard]
    families={};tests=[]
    for guard in guards:
        for item in conditions(guard):
            args=item.get('args',[])
            if item.get('kind')=='relation' and item.get('value') in ('=','==') and args[0].get('kind')=='symbol' and args[1].get('kind')=='list':
                name=args[0]['value']
                require(name not in ('t','pi','e','i','I','oo','true','false') and name not in families,'Invalid or duplicate curve family parameter')
                require(args[1]['args'],'Curve parameter lists must not be empty')
                families[name]=args[1]['args']
            else:tests.append(item)
    coordinates=space_coordinate_trees(tree)
    require(coordinates,'Enter a 3D curve [x(t),y(t),z(t)] or C(t)=(x(t),y(t),z(t))')
    return coordinates,families,tests


def sample_space_row(engine,request,tree,start,end,bounds):
    coordinates,families,tests=space_definition(tree)
    # A row-local family shadows both saved variables and old slider values.
    old=engine.bindings.copy()
    try:
        for name in families:engine.bindings[name]=engine.symbol(name)
        expressions=graph_expressions(engine,coordinates,('t',*families))
        guard=s.And(*(build_condition(engine.build,test) for test in tests))
        lists=[graph_expressions(engine,items,('t',*families)) for items in families.values()]
    finally:engine.bindings=old
    all_expressions=[*expressions,guard,*[item for values in lists for item in values]]
    excluded={'t',*families}
    names=parameter_names(all_expressions,excluded)
    sliders=resolved_parameters(engine,request,all_expressions,excluded)
    t=engine.symbol('t');family_symbols=tuple(engine.symbol(name) for name in families)
    sliders.pop(t,None)
    values=[]
    count=1
    for items in lists:
        require(all(isinstance(item,s.Expr) for item in items),'Curve parameter lists must contain finite real values')
        require(not any(item.free_symbols & {t,*family_symbols} for item in items),'Curve parameter lists must contain finite real values independent of t and family parameters')
        numbers=[_finite_real(item.subs(sliders) if item.free_symbols else item) for item in items]
        require(all(value is not None for value in numbers),'Curve parameter lists must contain finite real values')
        count*=len(numbers)
        require(within_limit(count,100),'Curve family limit: 100 curves per row')
        values.append(numbers)
    curves=[];positions=[]
    linear=affine_space_curve(expressions,t)
    for selection in product(*values):
        local={**sliders,**dict(zip(family_symbols,selection))}
        condition=guard.subs(local) if guard.free_symbols.intersection(local) else guard
        require(condition.free_symbols <= {t},'Curve restrictions must depend on t or graph parameters')
        intervals=space_intervals(condition,start,end)
        curve=[];parameters=[]
        fn=graph_function(expressions,(t,),local)
        for low,high in intervals:
            points,ts=space_curve_samples(fn,low,high,int(request.get('samples',500)),bounds,linear=linear)
            if parameters:
                curve.append(None);parameters.append((parameters[-1]+ts[0])/2)
            curve.extend(points);parameters.extend(ts)
        curves.append(curve);positions.append(parameters)
    return curves,positions,names
