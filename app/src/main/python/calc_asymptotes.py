"""Verified vertical, horizontal and oblique asymptotes of real functions."""
import math
import sympy as s
from calc_shared import require
from calc_runtime import solver_phase, SolverTimeLimit


def analyze(expression, x, a, b, request):
    from calc_display import display_tree, readable
    xmin=float(request.get("xMin",a)); xmax=float(request.get("xMax",b))
    ymin=float(request.get("yMin",-10)); ymax=float(request.get("yMax",10))
    require(all(math.isfinite(v) for v in (xmin,xmax,ymin,ymax)) and xmin<xmax and ymin<ymax,"Invalid graph viewport")
    items=[]; lines=[]; notes=[]
    def add(kind,equation,line,direction=None):
        text=readable(equation)
        existing=next((item for item in items if item["exact"]==text),None)
        if existing:
            if direction: existing["directions"].append(direction)
            return
        item={"kind":kind,"exact":text,"tree":display_tree(equation),"directions":[direction] if direction else []}
        items.append(item); lines.append(line)
    def limit(expr,point,direction="+"):
        try: return s.limit(expr,x,point,dir=direction)
        except (ValueError,NotImplementedError,TypeError): return None
    try:
        with solver_phase(5):
            if expression.is_rational_function(x): expression=s.cancel(expression)
            singular=s.singularities(expression,x,domain=s.S.Reals).intersect(s.Interval(a,b))
            if isinstance(singular,s.FiniteSet):
                candidates=sorted(singular,key=lambda v:float(v))
                for point in candidates[:80]:
                    if any(limit(expression,point,direction) in (s.oo,-s.oo) for direction in ("-","+")):
                        at=float(point)
                        add("vertical",s.Eq(x,point,evaluate=False),[[at,ymin],[at,ymax]])
                if len(candidates)>80: notes.append("First 80 singularities checked; narrow the interval to check more.")
            elif singular is not s.S.EmptySet:
                notes.append("The symbolic singularities could not be enumerated in this interval.")
            for point,direction in ((s.oo,"+infinity"),(-s.oo,"-infinity")):
                slope=limit(expression/x,point)
                if slope is None or slope.is_real is not True or slope.is_finite is not True: continue
                intercept=limit(expression-slope*x,point)
                if intercept is None or intercept.is_real is not True or intercept.is_finite is not True: continue
                rhs=slope*x+intercept
                if limit(expression-rhs,point)!=0: continue
                m,c=float(slope),float(intercept)
                line=[[xmin,m*xmin+c],[xmax,m*xmax+c]]
                if all(math.isfinite(v) for p in line for v in p):
                    add("horizontal" if slope==0 else "oblique",s.Eq(s.Symbol("y"),rhs,evaluate=False),line,direction)
    except (NotImplementedError,ValueError,TypeError):
        notes.append("Some asymptotes could not be verified symbolically.")
    except SolverTimeLimit:
        notes.append("Asymptote analysis reached its method time limit; verified results are shown.")
    return {"analysis":"asymptotes","points":[],"asymptotes":items,"lines":lines,"count":len(items),
            "note":" ".join(notes)}
