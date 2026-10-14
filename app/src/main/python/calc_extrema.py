"""Shared attained extrema search for calculator and graph analysis."""
import sympy as s
from calc_shared import MathError, require


def extrema_candidates(expression, variable, interval, action, coordinates=(), conditions=()):
    """Return exact (position, value) pairs attaining the requested extremum.

    Unknown domains/stationary sets are rejected rather than declaring sampled
    candidates to be global extrema. Piecewise branches are handled separately.
    """
    from sympy.calculus.util import continuous_domain
    # Python catalog calls also supply unconstrained SymPy symbols.
    if variable.is_real is not True:
        real_variable=s.Symbol(str(variable),real=True)
        mapping={variable:real_variable}
        expression=expression.xreplace(mapping)
        coordinates=tuple(expr.xreplace(mapping) for expr in coordinates)
        conditions=tuple(condition.xreplace(mapping) for condition in conditions)
        variable=real_variable
    require(action in ("minimum","maximum"), "Invalid extrema action")
    require(interval is not s.S.EmptySet, 'No '+action+' exists: the interval is empty')
    require(isinstance(interval,(s.Interval,s.FiniteSet)), "Invalid extrema interval")
    if isinstance(interval,s.FiniteSet):
        require(len(interval)==1, "Invalid extrema interval")
    endpoints=list(interval) if isinstance(interval,s.FiniteSet) else [interval.start,interval.end]
    breaks=set(endpoints)

    def components(domain):
        if domain is s.S.EmptySet: return []
        if isinstance(domain,s.Union):
            return [part for item in domain.args for part in components(item)]
        require(isinstance(domain,(s.Interval,s.FiniteSet)),
                'Could not verify the domain for global extrema; choose a simpler interval')
        return [domain]

    def domain_of(expr, region):
        if isinstance(expr,s.Piecewise):
            domains=[]
            for branch,branch_region in expr.as_expr_set_pairs(domain=region):
                domains.append(domain_of(branch,branch_region))
                for part in components(branch_region):
                    if isinstance(part,s.Interval): breaks.update((part.start,part.end))
                    else: breaks.update(part)
            return s.Union(*domains)
        for piece in expr.atoms(s.Piecewise):
            for _,branch_region in piece.as_expr_set_pairs(domain=region):
                for part in components(branch_region):
                    if isinstance(part,s.Interval): breaks.update((part.start,part.end))
        return continuous_domain(expr,variable,region)

    try:
        domain=interval
        if variable.is_positive: domain=domain.intersect(s.Interval.open(0,s.oo))
        elif variable.is_negative: domain=domain.intersect(s.Interval.open(-s.oo,0))
        elif variable.is_nonzero: domain=domain-s.FiniteSet(0)
        for condition in conditions:
            condition=s.simplify(condition)
            require(condition.free_symbols <= {variable},
                    'Could not verify the domain for global extrema; assign parameter values')
            restriction=condition.as_set() if condition.free_symbols else (s.S.Reals if condition==s.true else s.S.EmptySet)
            domain=domain.intersect(restriction)
        for expr in (expression,*coordinates): domain=domain.intersect(domain_of(expr,interval))
        for part in components(domain):
            if isinstance(part,s.Interval): breaks.update((part.start,part.end))
            else: breaks.update(part)
        # Cusps can be attained extrema without a zero first derivative.
        for absolute in expression.atoms(s.Abs):
            zeroes=s.solveset(absolute.args[0],variable,domain=interval)
            require(isinstance(zeroes,s.FiniteSet) or zeroes is s.S.EmptySet,
                    'Could not isolate all cusp candidates for global extrema')
            breaks.update(zeroes)
        boundaries=sorted(breaks)
        candidates=set(boundaries); limits=[]
        for left,right in zip(boundaries,boundaries[1:]):
            if left.is_finite and right.is_finite: middle=(left+right)/2
            elif right.is_finite: middle=right-1
            elif left.is_finite: middle=left+1
            else: middle=s.Integer(0)
            if domain.contains(middle) is not s.true: continue
            branch=expression
            # Select using an interior point so strict Piecewise inequalities
            # do not make SymPy select the wrong branch at a boundary.
            for _ in range(len(expression.atoms(s.Piecewise,s.Abs))+1):
                selected={}
                for piece in branch.atoms(s.Piecewise):
                    for term,condition in piece.args:
                        if condition.subs(variable,middle) is s.true:
                            selected[piece]=term; break
                # All Abs zeroes are interval boundaries. On the open segment,
                # use its fixed sign so derivatives reduce to smooth branches
                # and constant/flat segments need no isolated stationary set.
                for absolute in branch.atoms(s.Abs):
                    inside=absolute.args[0]
                    sample=inside.subs(variable,middle)
                    if sample.is_positive is True: selected[absolute]=inside
                    elif sample.is_negative is True: selected[absolute]=-inside
                if not selected: break
                branch=branch.xreplace(selected)
            derivative=s.diff(branch,variable)
            if derivative!=0:
                stationary=s.solveset(derivative,variable,domain=s.Interval.open(left,right))
                require(isinstance(stationary,s.FiniteSet) or stationary is s.S.EmptySet,
                        'Could not isolate all stationary candidates for global extrema; choose a simpler interval')
                candidates.update(stationary)
            else:
                # An open flat segment still attains its value at interior points.
                flat_value=branch.subs(variable,middle)
                if not any(domain.contains(at) is s.true and s.simplify(expression.subs(variable,at)-flat_value)==0 for at in (left,right)):
                    candidates.add(middle)
            limits.extend((s.limit(branch,variable,left,dir='+'),s.limit(branch,variable,right,dir='-')))
        entries=[]
        for at in candidates:
            if domain.contains(at) is not s.true: continue
            value=expression.subs(variable,at)
            if value.is_real is True and value.is_finite is True: entries.append((at,value))
        if any(value == (-s.oo if action=='minimum' else s.oo) for value in limits):
            raise MathError('No '+action+' exists: function is unbounded in this range')
        require(entries,'No '+action+' exists: finite bound is not attained in this range')
        pick=min if action=='minimum' else max
        bound=pick(value for _,value in entries)
        for value in limits:
            require(value.is_extended_real is True and not value.has(s.Limit),
                    'Could not verify boundary limits for global extrema')
            exceeds=value<bound if action=='minimum' else value>bound
            require(exceeds is not s.true,'No '+action+' exists: boundary bound is not attained')
            require(exceeds is s.false,'Could not compare boundary limits for global extrema')
        return sorted((at,value) for at,value in entries if s.simplify(value-bound)==0)
    except (NotImplementedError,TypeError,ValueError) as exc:
        if isinstance(exc,MathError): raise
        raise MathError('Could not verify global extrema on this domain; choose a simpler interval') from exc

