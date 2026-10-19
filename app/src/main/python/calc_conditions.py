"""Boolean guards shared by piecewise expressions and graph restrictions."""
import sympy as s
from sympy.core.relational import Relational
from calc_shared import require


def build_condition(build, tree):
    kind=tree.get('kind');args=tree.get('args',[])
    if kind=='group':return build_condition(build,args[0])
    if kind=='list':return s.And(*(build_condition(build,item) for item in args))
    if kind=='relation' and args[0].get('kind')=='relation':
        left,right=args
        return s.And(build_condition(build,left),build_condition(build,{**tree,'args':[left['args'][1],right]}))
    result=build(tree)
    require(isinstance(result,(Relational,s.logic.boolalg.Boolean)),'Piecewise condition must be a relation')
    return s.simplify(result) if not result.free_symbols else result
