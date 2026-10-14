"""Control constructors and expression literals shared by schema authors."""
import ast

def field(key,label,ko,type_,default,choices=None,when=None):
    result=dict(key=key,label=label,ko=ko,type=type_,default=default)
    if choices: result['choices']=[dict(id=id_,label=en,ko=ko_) for id_,en,ko_ in choices]
    if when: result['when']=when
    return result
def col(key,en,ko,default): return field(key,en,ko,'column',default)
def multi(key,en,ko): return field(key,en,ko,'columns','auto')

def literal(node):
    if isinstance(node,ast.Name) and node.id=='NA': return 'NA'
    if isinstance(node,(ast.List,ast.Tuple)): return [literal(element) for element in node.elts]
    return ast.literal_eval(node)
