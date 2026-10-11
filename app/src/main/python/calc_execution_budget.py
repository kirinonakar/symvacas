"""Work-proportional limits for explicitly requested SEM bootstrap refits."""
import math


def bootstrap_work(request):
    variables=request.get('variables',{})
    def number(node,depth=0):
        if not isinstance(node,dict) or depth>8: return 0.
        try:
            if node.get('kind')=='number': return float(node['value'])
            if node.get('kind')=='symbol': return number(variables.get(node.get('value')),depth+1)
            if node.get('kind')=='unary': return (-1 if node.get('value')=='-' else 1)*number(node['args'][0],depth+1)
        except (ValueError,TypeError,KeyError,IndexError): pass
        return 0.
    def visit(node):
        if not isinstance(node,dict): return 0,0
        args=node.get('args',[]); count=work=0
        if node.get('kind')=='call' and node.get('value')=='sem' and len(args)>10:
            samples=number(args[10])
            if math.isfinite(samples) and samples>=20 and samples==int(samples):
                count=min(int(samples),10000)
                p=len(args[1].get('args',[])) or 6
                ordinal=args[7].get('value')=='wlsmv'
                work=count*max(10,p*p)*(4 if ordinal else 1)
        for arg in args:
            extra,seconds=visit(arg); count+=extra;work+=seconds
        return count,work
    return visit(request.get('tree',{}))
