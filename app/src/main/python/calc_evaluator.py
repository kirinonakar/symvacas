"""Validated expression AST evaluation and calculator functions."""
from calc_limits import limits_removed, within_limit
from calc_conditions import build_condition
import random
import statistics
import math
from collections import Counter
import sympy as s
from sympy.core.relational import Relational
from sympy.core.function import AppliedUndef
from sympy.calculus.util import continuous_domain, function_range
from quantities import Quantity, quantity, convert_quantity
from calc_shared import (CONSTANTS, UNITS, MathError, canonical_function_name,
                         coordinates, discrete_fourier, dms_parts, flatten,
                         initial_conditions, inverse_mellin_transform,
                         inverse_z_transform, matrix, mellin_transform,
                         numeric_derivative, numeric_integral, ode_equation, require, sexagesimal_value, z_transform)
from calc_statistics import distribution_value, fit_custom_regression, fit_regression, pearson_correlation, statistical_test, shape_statistics, summary_frequencies, binary_summary, overall_summary
from calc_advanced_statistics import FUNCTIONS as ADVANCED_STATISTICS, advanced
from calc_finance import finance_value
from calc_integrals import rational_trig_primitive, log_arctan_primitive
from calc_solutions import affine_exponential_solutions
from calc_number_theory import bounded_divisors
from calc_extrema import extrema_candidates
from calc_statistics_report import BASIC as BASIC_STATISTICS

MAX_EXACT_DIGITS = 100000
MAX_NUMERIC_EXPONENT = 100000
SET_CONSTANTS = {"S."+name:getattr(s.S,name) for name in
                 ("Reals","Complexes","Integers","Rationals","Naturals","Naturals0")}

def _ast_symbols(node):
    if node.get("kind") == "symbol": yield node
    for child in node.get("args", []): yield from _ast_symbols(child)

def _is_percentage(node):
    while node.get("kind") in ("group", "unary") and len(node.get("args", [])) == 1:
        node = node["args"][0]
    return node.get("kind") == "call" and node.get("value") == "percent"

def _real_calculus(node):
    return (node.get("kind") == "call" and node.get("value") in ("abs", "sign", "cbrt", "nthroot")
            or any(_real_calculus(child) for child in node.get("args", [])))

def oversized_rational_power(base, exponent):
    """Estimate the larger exact numerator/denominator before SymPy expands it."""
    if limits_removed() or not (base.is_Rational and exponent.is_Integer): return False
    if base in (0, 1, -1): return False
    magnitude = max(abs(int(base.p)), int(base.q))
    log_magnitude=math.log10(magnitude)
    power=abs(exponent)
    if power > MAX_EXACT_DIGITS/log_magnitude: return True
    return int(power)*log_magnitude + 1 > MAX_EXACT_DIGITS

def has_oversized_power(value):
    return isinstance(value,s.Basic) and any(
        oversized_rational_power(power.base,power.exp)
        for power in value.atoms(s.Pow) if power.base.is_Rational and power.exp.is_Integer)

class Engine:
    def __init__(self, request):
        self.request = request
        self.precision = max(3, min(200, int(request.get("precision", 30))))
        # Display digits limit only what the result view shows; the numeric work keeps self.precision.
        self.display_digits = max(1, min(self.precision, int(request.get("displayDigits", self.precision))))
        self.angle = request.get("angle", "RAD")
        self.variables = request.get("variables", {})
        self.functions = request.get("functions", {})
        self.resolving = set()
        self.symbols = {}
        self.visited = 0
        self.note = ""
        self.conditions = []
        self.bindings = {}
        # Request-local references to validated numeric datasets. Data cells
        # have their own row/column bounds and do not consume expression nodes.
        self.statistics_datasets = {}
        self.preparing_statistics = set()
        self.regression_parameters = []
        self.regression_report = None
        self.allow_sequence_calls = False
        self.assumptions = request.get("assumptions", {})
        self.solution_step_inputs = []
        self.solution_step_nodes = set()
        pending = [request.get("tree", {})]
        while pending:
            current = pending.pop()
            if isinstance(current, dict):
                self.solution_step_nodes.add(id(current))
                pending.extend(current.get("args", []))
    def symbol(self, name):
        if name not in self.symbols:
            options = {k: True for k in self.assumptions.get(name, []) if k in ("real", "positive", "negative", "integer", "nonzero")}
            self.symbols[name] = s.Symbol(name, **options)
        return self.symbols[name]
    def solve_system(self, equations, variables):
        """Retry unsupported real-valued terms without making other variables real."""
        try:
            return s.solve(equations,variables,dict=True)
        except (ValueError, NotImplementedError):
            expressions=equations if isinstance(equations,list) else [equations]
            unknowns=variables if isinstance(variables,list) else [variables]
            functions=set().union(*(expr.atoms(s.Abs,s.sign,s.floor,s.ceiling,s.Piecewise) for expr in expressions))
            affected=set().union(*(function.free_symbols for function in functions))
            replacements={var:s.Dummy(str(var),**var.assumptions0,real=True)
                          for var in unknowns if isinstance(var,s.Symbol) and var in affected and var.is_real is None}
            if not replacements: raise
            mapped=[expr.xreplace(replacements) for expr in expressions]
            result=s.solve(mapped,[var.xreplace(replacements) for var in unknowns],dict=True)
            restore={replacement:original for original,replacement in replacements.items()}
            self.note="Automatic real-domain solving for "+", ".join(map(str,replacements))+"; other variables keep their original domain."
            return [{key.xreplace(restore):value.xreplace(restore) for key,value in solution.items()} for solution in result]
    def has_explicit_angle(self, node, seen=()):
        # 사용자가 쓴 각도 표시(π, °, ʳ, ᵍ)만 인정한다. 안쪽 DEG/GRAD 변환이 값을 만들며
        # 끼워 넣은 π를 명시적 라디안으로 오인하면 중첩 호출에서 모드 변환이 누락된다.
        if not isinstance(node, dict): return False
        if node.get("value") in ("degree", "pi", "rad", "gradian"): return True
        if node.get("kind") == "symbol":
            name = node.get("value")
            stored = self.variables.get(name) if isinstance(self.variables, dict) else None
            return (name not in self.bindings and name not in seen and name not in ("e", "i", "I", "oo", "true", "false")
                    and name not in CONSTANTS and isinstance(stored, dict) and self.has_explicit_angle(stored, seen + (name,)))
        return any(self.has_explicit_angle(child, seen) for child in node.get("args", []))
    def number(self, value):
        require(within_limit(len(value.lstrip("-")), MAX_EXACT_DIGITS), "Number too large")
        if "e" in value.lower():
            mantissa, exponent = value.lower().split("e", 1)
            exponent = int(exponent)
            if not within_limit(abs(exponent), MAX_NUMERIC_EXPONENT):
                raise MathError("Decimal exponent limit: 100000")
            coefficient = s.Rational(mantissa)
            if oversized_rational_power(s.Integer(10), s.Integer(exponent)):
                power=s.Pow(10, exponent, evaluate=False)
                return power if coefficient == 1 else s.Mul(coefficient, power, evaluate=False)
        number = s.Rational(value)
        max_bits=math.ceil(MAX_EXACT_DIGITS*math.log2(10))
        require(within_limit(abs(number.p).bit_length(), max_bits) and within_limit(number.q.bit_length(), max_bits), "Number size limit")
        return number

    def prepare_statistics_dataset(self, node, column_major=False):
        """Cache numeric vectors/tables and separately parsed, guarded cell ASTs."""
        packed = self.request.get('statisticsDatasets', {})
        if node.get('kind') == 'symbol' and node.get('value') in packed:
            if id(node) in self.statistics_datasets: return
            rows = packed[node['value']]
            require(isinstance(rows,list), 'Numeric statistics dataset expected')
            table = bool(rows) and all(isinstance(row,list) for row in rows)
            cells = rows if table else [rows]
            require(within_limit(len(rows),101 if column_major else 5000) and
                    (not table or all(within_limit(len(row),5000 if column_major else 101) for row in cells)),
                    'Statistics dataset limit: 5000 rows and 101 columns')
            require(all(isinstance(cell,str) or isinstance(cell,dict) and isinstance(cell.get('kind'),str) and isinstance(cell.get('args',[]),list) for row in cells for cell in row),
                    'Numeric statistics dataset expected')
            name=node['value']
            require(name not in self.preparing_statistics, 'Cyclic statistics dataset reference')
            self.preparing_statistics.add(name)
            try: values = [[self.number(cell) if isinstance(cell,str) else self.build(cell) for cell in row] for row in cells]
            finally: self.preparing_statistics.remove(name)
            self.statistics_datasets[id(node)] = (node, values if table else values[0])
            return
        if node.get("kind") == "symbol" and node.get("value") not in self.bindings:
            node = self.variables.get(node.get("value"), node)
        if node.get("kind") != "list" or id(node) in self.statistics_datasets:
            return
        rows = node.get("args", [])
        table = bool(rows) and all(row.get("kind") == "list" for row in rows)
        cells = [row.get("args", []) for row in rows] if table else [rows]
        def literal(cell):
            return (cell.get("kind") == "number" or
                    cell.get("kind") == "unary" and cell.get("value") in ("+", "-")
                    and len(cell.get("args", [])) == 1 and cell["args"][0].get("kind") == "number")
        if not all(literal(cell) for row in cells for cell in row):
            return
        require(within_limit(len(rows),101 if column_major else 5000) and
                (not table or all(within_limit(len(row),5000 if column_major else 101) for row in cells)),
                "Statistics dataset limit: 5000 rows and 101 columns")
        def value(cell):
            if cell["kind"] == "number": return self.number(cell["value"])
            return (-1 if cell["value"] == "-" else 1)*self.number(cell["args"][0]["value"])
        values = [[value(cell) for cell in row] for row in cells]
        self.statistics_datasets[id(node)] = (node, values if table else values[0])

    def build(self, node, depth=0):
        self.visited += 1
        require(within_limit(depth,99) and within_limit(self.visited,12000), "Expression complexity limit")
        if id(node) in self.statistics_datasets: return self.statistics_datasets[id(node)][1]
        kind, value = node["kind"], node.get("value", "")
        args = node.get("args", [])
        build = lambda a: self.build(a, depth + 1)
        if kind == "number": return self.number(value)
        if kind == "symbol":
            if value in SET_CONSTANTS: return SET_CONSTANTS[value]
            if value in self.request.get('statisticsDatasets',{}):
                self.prepare_statistics_dataset(node)
                return self.statistics_datasets[id(node)][1]
            if value in self.bindings: return self.bindings[value]
            constants = {"pi": s.pi, "e": s.E, "i": s.I, "I": s.I, "oo": s.oo, "true": s.true, "false": s.false}
            if value in constants: return constants[value]
            if value in CONSTANTS:
                entry=CONSTANTS[value]
                if not entry[3]:
                    self.note="Uses a measured CODATA 2022 value with published precision."
                    return s.Float(entry[1],12)
                return s.Rational(entry[1]) if value != "hbar" else s.Rational(CONSTANTS["hP"][1])/(2*s.pi)
            if value in self.variables:
                require(value not in self.resolving, "Cyclic variable definition")
                self.resolving.add(value)
                result = build(self.variables[value])
                self.resolving.remove(value)
                return result
            if value=="Ans": raise MathError("Ans has no reusable result yet")
            return self.symbol(value)
        if kind == "constant":
            return {"pi":s.pi,"E":s.E,"I":s.I,"oo":s.oo,"-oo":-s.oo,"EmptySet":s.S.EmptySet,"True":s.true,"False":s.false}[value]
        if kind == "snapshot_symbol": return self.symbol(value)
        if kind == "answer_call":
            return self.call_answer(args[0], [build(a) for a in args[1:]])
        if kind == "float": return s.Float(value,self.precision)
        if kind == "piecewise":
            branches=[]; previous=s.false
            for branch in args:
                require(branch.get('kind')=='tuple' and len(branch.get('args',[]))==2,'Invalid piecewise branch')
                body, guard=branch['args']; test=build_condition(build,guard)
                if test == s.false: continue
                selected=s.And(test,s.Not(previous))
                if selected == s.false: continue
                old_conditions=self.conditions
                self.conditions=[]
                try:
                    result=build(body)
                    local_guards=self.conditions
                finally: self.conditions=old_conditions
                # Domain guards apply only where this branch is selected.
                for local in local_guards:
                    self.conditions.append(s.Or(s.Not(selected),local))
                branches.append((result,test))
                previous=s.Or(previous,test)
                if test == s.true: break
            return s.Piecewise(*branches) if branches else s.nan
        if kind == "restricted":
            result=build(args[0])
            for guard in args[1:]:
                condition=build(guard)
                require(condition!=s.false,"Domain ERROR: excluded value")
                if condition!=s.true: self.conditions.append(condition)
            return result
        if kind == "quantity": return Quantity(build(args[0]),tuple(node["dimensions"]),node.get("absolute",False))
        if kind == "frozen_call":
            old_angle=self.angle
            self.angle="RAD"
            try: return self.call(value,[build(a) for a in args],args)
            finally: self.angle=old_angle
        if kind == "set": return s.FiniteSet(*(build(a) for a in args))
        if kind == "mapping": return {build(pair["args"][0]):build(pair["args"][1]) for pair in args}
        if kind == "group": return build(args[0])
        if kind == "list": return [build(a) for a in args]
        if kind == "tuple": return tuple(build(a) for a in args)
        if kind == "unary": return (-1 if value == "-" else 1)*build(args[0])
        if kind == "sexagesimal":
            require(len(args) == 3, "DMS input requires degrees, minutes and seconds")
            values=[build(a) for a in args]
            require(all(getattr(item,"is_number",False) and not item.has(s.I) for item in values), "DMS fields must be real numbers")
            return sexagesimal_value(values)
        if kind in ("binary", "relation"):
            require(value != ":=", "Use STO for variables or the Variables editor for functions")
            a, b = map(build, args)
            if isinstance(a, list): a = matrix(a)
            if isinstance(b, list): b = matrix(b)
            # Add/subtract a percentage of the left operand; standalone percent
            # and multiplication/division still use the fraction x/100.
            if value in ("+", "-") and _is_percentage(args[1]):
                b = s.Mul(a,b,evaluate=False) if has_oversized_power(a) or has_oversized_power(b) else a*b
            if value == "+":
                if has_oversized_power(a) or has_oversized_power(b):
                    return s.Add(a,b,evaluate=False)
                return a+b
            if value == "-":
                if has_oversized_power(a) or has_oversized_power(b):
                    return s.Add(a,s.Mul(-1,b,evaluate=False),evaluate=False)
                return a-b
            if value == "*":
                if has_oversized_power(a) or has_oversized_power(b):
                    return s.Mul(a,b,evaluate=False)
                return a*b
            if value == "∠": return self.call("polar",[a,b],args)
            if value == "/":
                require(b != 0, "Division by zero")
                if getattr(b, "free_symbols", None): self.conditions.append(s.Ne(b, 0, evaluate=False))
                return a/b
            if value == "^":
                require(not (a == 0 and b == 0), "Undefined: 0^0")
                if getattr(a, "is_Rational", False) and getattr(b, "is_Integer", False):
                    if oversized_rational_power(a, b): return s.Pow(a, b, evaluate=False)
                elif getattr(a, "is_number", False) and getattr(b, "is_number", False):
                    require(within_limit(abs(b), MAX_NUMERIC_EXPONENT), "Exponent limit: 100000")
                return a**b
            if value == "mod": require(b != 0, "Division by zero"); return s.Mod(a,b)
            relations = {"=": s.Eq, "==": s.Eq, "!=": s.Ne, "<": s.Lt, ">": s.Gt, "<=": s.Le, ">=": s.Ge, "->": s.Eq}
            if value in relations: return relations[value](a,b,evaluate=False)
            raise MathError("Unknown operator")
        require(kind == "call", "Unknown AST node")
        # Preserve bound variable identity even if the user stored x previously.
        scoped = value in ("diff", "integrate", "limit", "series", "taylor", "sum", "product", "solve", "solveset", "nsolve", "nintegrate", "nderivative", "minimum", "maximum", "collect", "subs", "domain", "range", "coeff", "quo", "rem", "resultant", "discriminant", "charpoly", "roots", "real_roots", "rsolve", "gradient", "divergence", "curl", "hessian", "jacobian", "laplacian", "dsolve", "desolve", "laplace", "ilaplace", "fourier", "ifourier", "ztrans", "invztrans", "mellin", "invmellin", "pdsolve") and len(args) > 1
        old = self.bindings.copy()
        if value=="solve" and len(args)==1: self.bindings["x"]=self.symbol("x")
        if scoped:
            if value in ("dsolve", "desolve", "laplace", "fourier", "ilaplace", "ifourier",
                         "ztrans", "invztrans", "mellin", "invmellin"):
                candidates = list(args[1:3])
            else:
                varnode = args[1]
                candidates = varnode.get("args", []) if varnode["kind"] == "list" else [varnode]
                if varnode["kind"] == "tuple": candidates = varnode["args"][:1]
                if varnode["kind"] == "relation": candidates = [varnode["args"][0]]
                if value in ("rsolve", "pdsolve") and varnode["kind"] == "call": candidates = varnode.get("args", [])
            for n in candidates:
                if n["kind"] == "symbol":
                    independent=self.symbol(n["value"])
                    if value in ("minimum","maximum") and independent.is_real is not True:
                        independent=s.Symbol(n["value"],real=True)
                    elif value == "diff" and independent.is_real is None and _real_calculus(args[0]):
                        independent=s.Symbol(n["value"],**independent.assumptions0,real=True)
                        self.note="Differentiated over the real domain."
                    self.bindings[n["value"]] = independent
        try:
            if value in ("impute", "cfa", "sem"):
                # NA is a missing-data token inside these analyses; elsewhere it
                # retains its existing Avogadro-constant meaning.
                self.bindings["NA"] = self.symbol("NA")
            if value not in self.functions and value in BASIC_STATISTICS | ADVANCED_STATISTICS | {"regression"}:
                for index,argument in enumerate(args):
                    if value!='modelcompare' or index not in (2,3,8):
                        column_major = value == 'stats' and index == 0 and len(args) == 3 and args[1].get('kind') == 'symbol' and args[1].get('value') == 'overall'
                        column_major = column_major or value in ('ttest2', 'ttestpaired') and index in (1, 2) and len(args) >= 4 and args[3].get('kind') == 'symbol' and args[3].get('value') == 'batch'
                        if value in ('ztest2','chi2independence','fisherexact','mannwhitney','wilcoxon','kruskal','anova','welchanova'):
                            markers=[at for at,item in enumerate(args) if item.get('kind')=='symbol' and item.get('value')=='batch']
                            column_major=column_major or bool(markers) and (index>=3 if value=='ztest2' else True) and index<markers[0]
                        self.prepare_statistics_dataset(argument, column_major=column_major)
            if value == "regression" and len(args) > 1 and args[1].get("kind") == "symbol" and args[1].get("value") == "custom":
                require(len(args) in (4, 5), "Use regression(data,custom,model,x,initials)")
                constants = {"pi": s.pi, "e": s.E, "i": s.I, "I": s.I}
                require(args[3].get("kind") == "symbol" and args[3].get("value") not in constants,
                        "Choose an independent variable")
                rows = build(args[0])
                independent = self.symbol(args[3]["value"])
                names = {n["value"] for root in (args[2], *args[4:]) for n in _ast_symbols(root)}
                for name in names:
                    self.bindings[name] = constants[name] if name in constants else self.symbol(name)
                expression = build(args[2])
                options = build(args[4]) if len(args) == 5 else None
                return fit_custom_regression(self, rows, expression, independent, options)
            condition_start=len(self.conditions)
            if value=='modelcompare' and value not in self.functions:
                from calc_model_comparison import literal_options
                values=[a['value'] if index in (2,3) and a.get('kind')=='symbol' else literal_options(self,a) if index==8 else build(a) for index,a in enumerate(args)]
            elif value in ("minimum","maximum") and value not in self.functions:
                values=[s.Symbol(a['value']) if index==4 and a.get('kind')=='symbol' else build(a) for index,a in enumerate(args)]
            elif value=="solveset" and value not in self.functions:
                require(len(args) in (2,3), "Use solveset(expr,x[,domain=S.Complexes])")
                domain_node=args[2] if len(args)==3 else None
                if domain_node is not None and domain_node.get("kind")=="relation":
                    require(domain_node.get("value")=="=" and domain_node["args"][0].get("kind")=="symbol"
                            and domain_node["args"][0].get("value")=="domain", "solveset only accepts the domain keyword")
                    domain_node=domain_node["args"][1]
                values=[build(a) for a in args[:2]]+([build(domain_node)] if domain_node is not None else [])
            else:values = [build(a) for a in args]
            if value=="subs" and len(values)==3:
                updated=[condition.subs(values[1],values[2]) for condition in self.conditions[condition_start:]]
                require(all(c!=s.false for c in updated),"Domain ERROR: substitution at an excluded value")
                self.conditions[condition_start:]=[c for c in updated if c!=s.true]
                return values[0].subs(values[1],values[2])
            result = self.call(value, values, args, conditions=self.conditions[condition_start:])
            if value in ("minimum","maximum") and value not in self.functions:
                # The bound variable has been eliminated from this scalar result.
                self.conditions[condition_start:]=[c for c in self.conditions[condition_start:] if not c.has(values[1])]
            if (self.request.get("equationSteps") and node is self.request.get("tree")
                    and value in ("solve", "nsolve", "dsolve", "desolve", "pdsolve") and len(values) > 1):
                self.equation_step_input = (value, values)
            if (self.request.get("solutionSteps") and id(node) in self.solution_step_nodes
                    and value in ("solve", "nsolve", "dsolve", "desolve", "pdsolve", "diff", "integrate", "limit") and len(values) > 1):
                record=(value, values, result, getattr(self,"integral_strategy",None))
                if len(self.solution_step_inputs)<6: self.solution_step_inputs.append(record)
                elif node is self.request.get("tree"): self.solution_step_inputs[-1]=record
            if node is self.request.get("tree") and value in ("solve", "integrate") and len(values) > 1:
                self.guidance_input = (value, values, result)
            elif node is self.request.get("tree") and value == "solve" and len(values) == 1 and not isinstance(values[0],list):
                variables=sorted(values[0].free_symbols,key=str)
                if len(variables)==1: self.guidance_input=(value,[values[0],variables[0]],result)
            return result
        finally:
            self.bindings = old
    def call(self, name, a, nodes, conditions=None):
        if name == "Ans":
            require("Ans" in self.variables, "Ans has no reusable result yet")
            return self.call_answer(self.variables["Ans"], a)
        # arcsin/arccos/arctan 계열 별칭은 사용자 정의 함수가 없을 때만 정식 이름으로 정규화한다.
        if name not in self.functions:
            name = canonical_function_name(name)
        if self.allow_sequence_calls and (name == "u" or name in ("u1", "u2", "u3", "u4", "u5", "u6")):
            require(len(a) == 1, "Sequence references take one integer index")
            return s.Function(name)(a[0])
        if name=="rnd":
            require(not a,"rnd expects no arguments")
            return s.Float(str(random.random()),self.precision)
        if name=="eng":return a[0]
        if name=="pol":
            z=a[0]+s.I*a[1];angle=s.arg(z)*{"DEG":180/s.pi,"GRAD":200/s.pi}.get(self.angle,1)
            return [s.Abs(z),angle]
        if name=="rec":
            z=self.call("polar",a,nodes)
            return [s.re(z),s.im(z)]
        if name=="randInt":
            require(len(a)==2 and all(x.is_Integer for x in a) and a[0]<=a[1],"Enter integer lower and upper bounds")
            return s.Integer(random.randint(int(a[0]),int(a[1])))
        if name=="sexagesimal":
            require(len(a) == 3, "DMS input requires degrees, minutes and seconds")
            return sexagesimal_value(a)
        if name=="dms":
            if len(a)==3:return self.call("sexagesimal",a,nodes)
            return dms_parts(a[0])
        if name=="qty": return quantity(a[0],nodes[1]["value"],UNITS)
        if name=="mixed":
            require(all(v.is_Integer for v in a) and a[2]>0 and 0<=a[1],"Mixed fractions require integer parts and a positive denominator")
            return a[0]+(-1 if a[0]<0 else 1)*a[1]/a[2]
        if name in ("arg","rectpolar"):
            angle=s.arg(a[0])
            if not angle.free_symbols: angle *= {"DEG":180/s.pi,"GRAD":200/s.pi}.get(self.angle,1)
            return angle if name=="arg" else [s.Abs(a[0]),angle]
        if name=="polar":
            theta=a[1]
            if not self.has_explicit_angle(nodes[1]) and not theta.free_symbols: theta *= {"DEG":s.pi/180,"GRAD":s.pi/200}.get(self.angle,1)
            return a[0]*(s.cos(theta)+s.I*s.sin(theta))
        if name in ("sin", "cos", "tan", "sec", "csc", "cot"):
            arg = a[0]
            if not self.has_explicit_angle(nodes[0]) and not getattr(arg, "free_symbols", set()):
                arg *= {"DEG": s.pi/180, "GRAD": s.pi/200}.get(self.angle, 1)
            return getattr(s,name)(arg)
        if name=="atan2":
            result=s.atan2(a[0],a[1])
            return result * ({"DEG":180/s.pi,"GRAD":200/s.pi}.get(self.angle,1) if not result.free_symbols else 1)
        if name in ("asin", "acos", "atan"):
            result = getattr(s,name)(*a)
            return result * ({"DEG": 180/s.pi, "GRAD":200/s.pi}.get(self.angle, 1) if not result.free_symbols else 1)
        if name in ("round","roundh"):
            require(len(a) in (1,2),name+" expects a number and optional decimal places")
            require(a[0].is_number and a[0].is_real,name+" requires a real number")
            require(len(a)==1 or a[1].is_Integer,name+" requires integer decimal places")
            places=int(a[1]) if len(a)==2 else 0
            require(within_limit(abs(places),200),name+" decimal places must be between -200 and 200")
            # Scale an exact rational before rounding so the result does not inherit
            # SymPy's low-precision Float from Number.round().
            number=a[0] if isinstance(a[0],s.Rational) else s.Rational(str(s.N(a[0],max(self.precision,abs(places)+5))))
            scale=s.Integer(10)**places
            scaled=number*scale
            units=(s.sign(scaled)*s.floor(s.Abs(scaled)+s.Rational(1,2)) if name=="roundh"
                   else round(scaled))
            rounded=s.Rational(units,1)/scale
            return rounded if rounded.is_Integer else s.Float(rounded,max(self.precision,15,len(str(abs(rounded.p)))))
        if name == "nthroot":
            require(len(a)==2 and a[1]!=0,"nthroot expects an expression and a nonzero root order")
            return s.real_root(a[0],a[1]) if a[1].is_integer and a[1].is_odd else s.root(a[0],a[1])
        basic = {"sqrt": s.sqrt, "cbrt": lambda x: s.real_root(x,3), "abs": s.Abs,
                 "floor": s.floor, "ceil": s.ceiling, "ceiling": s.ceiling, "iPart": s.floor, "frac": s.frac,
                 "sign": s.sign, "gamma": s.gamma,
                 "erf":s.erf,"erfc":s.erfc,"Ei":s.Ei,"Si":s.Si,"Ci":s.Ci,"zeta":s.zeta,
                 "lambertw": s.LambertW, "beta": s.beta, "digamma": s.digamma, "polygamma": s.polygamma,
                 "fibonacci": s.fibonacci, "lucas": s.lucas, "bernoulli": s.bernoulli, "harmonic": s.harmonic,
                 "subfactorial": s.subfactorial, "totient": s.totient, "divisor_sigma": s.divisor_sigma,
                 "primepi": s.primepi, "nextprime": s.nextprime, "prevprime": s.prevprime,
                 "besselj": s.besselj, "bessely": s.bessely, "besseli": s.besseli, "besselk": s.besselk,
                 "ln": s.log, "log": lambda x, b=10: s.log(x,b), "exp": s.exp, "polylog": s.polylog,
                 "sinc": s.sinc, "sinh": s.sinh, "cosh": s.cosh, "tanh": s.tanh, "asinh": s.asinh, "acosh": s.acosh, "atanh": s.atanh,
                 "conj": s.conjugate, "re": s.re, "im": s.im, "arg": s.arg,
                 "simplify": s.simplify, "expand": s.expand, "factor": s.factor, "collect": s.collect,
                 "diff": s.diff, "gcd": s.gcd, "lcm": s.lcm, "nCr": s.binomial,
                 "percent": lambda x: x/100, "degree": lambda x: x*s.pi/180,
                 "rad":lambda x:x,"gradian":lambda x:x*s.pi/200,
                 "quotient": lambda x,y: s.floor(x/y), "remainder": s.Mod,
                 "polar": lambda r,t: r*(s.cos(t)+s.I*s.sin(t)), "rectpolar": lambda z: [s.Abs(z),s.arg(z)]}
        if name in ("log","ln"): require(a[0]!=0,"Domain ERROR: logarithm of zero")
        if name=="log" and len(a)>1: require(a[1] not in (0,1),"Domain ERROR: invalid logarithm base")
        if name == "diff":
            if len(a)==2 and isinstance(a[1],s.Symbol) and a[1].is_real:
                root=nodes[0]
                if root.get("kind")=="call" and root.get("value") in ("cbrt","nthroot"):
                    order=s.Integer(3) if root["value"]=="cbrt" else self.build(root["args"][1])
                    if order.is_Integer and order.is_odd and order>1 and a[0]==s.real_root(a[1],order):
                        self.conditions.append(s.Ne(a[1],0))
                        return 1/(order*s.Abs(a[1])**(1-1/order))
            result=s.diff(*a)
            if len(a)==2 and isinstance(a[1],s.Symbol) and a[1].is_real:
                # A continuous real root has no distributional jump at zero.
                # Remove only delta terms whose multiplier vanishes there.
                delta=s.DiracDelta(a[1])
                coefficient=s.expand(result).coeff(delta)
                if coefficient.subs(a[1],0)==0: result=result.xreplace({delta:s.Integer(0)})
            return result
        if name in basic: return basic[name](*a)
        if name in ("mod","divmod"):
            require(len(a)==2,name+" expects two arguments")
            require(a[1]!=0,"Division by zero")
            if name=="mod": return s.Mod(a[0],a[1])
            return [s.floor(a[0]/a[1]),s.Mod(a[0],a[1])]
        if name in ("prime", "isprime"):
            require(len(a)==1, name+" expects one integer")
            require(a[0].is_Integer, name+" requires an integer")
            if name=="prime":
                require(1<=a[0] and within_limit(a[0],100000), "prime index must be between 1 and 100000")
                return s.Integer(s.prime(int(a[0])))
            # SymPy gives a definitive primality result below 2**64.
            if limits_removed() and abs(a[0])>=2**64:
                self.note="Above 2^64, isprime uses a probable-prime test."
            require(limits_removed() or abs(a[0])<2**64, "isprime requires an integer with |n| < 2^64")
            return s.true if s.isprime(a[0]) else s.false
        if name == "factorial" and getattr(a[0], "is_Integer", None) is not True:
            # A symbolic factorial (for example the Z-transform of 1/n!) stays unevaluated
            # instead of being rejected, while non-integer numeric input remains an error.
            require(getattr(a[0], "is_integer", False) is not False, "factorial requires an integer argument")
            return s.factorial(a[0])
        if name in ("factorial", "nPr", "factorint", "divisors"):
            if name in ("factorint","divisors"):
                require(len(a)==1,name+" expects one positive integer")
                require(a[0].is_Integer and a[0]>0,name+" requires a positive integer")
            else:
                require(a[0].is_Integer and 0 <= a[0] and within_limit(a[0],10000),
                        name+" requires an integer from 0 to 10000")
            if name == "factorial": return s.factorial(a[0])
            if name == "nPr":
                require(a[1].is_Integer and 0 <= a[1] <= a[0], "nPr requires 0 ≤ r ≤ n")
                return s.factorial(a[0])/s.factorial(a[0]-a[1])
            require(a[0]>0,"Factorization and divisors require a positive integer")
            if name == "factorint":
                factors=[s.Pow(s.Integer(p),s.Integer(k),evaluate=False) if k>1 else s.Integer(p)
                         for p,k in s.factorint(a[0]).items()]
                return s.Mul(*factors,evaluate=False)
            return bounded_divisors(a[0])
        if name == "subs": return a[0].subs(a[1],a[2])
        if name in ("apart","partfrac"):
            require(len(a)==2, name+" expects an expression and variable")
            return s.apart(a[0],a[1])
        if name in ("together","cancel","trigsimp","trigexpand","powsimp","powdenest","hyperexpand"):
            transforms={"together":s.together,"cancel":s.cancel,"trigsimp":s.trigsimp,
                        "trigexpand":s.expand_trig,"powsimp":s.powsimp,"powdenest":s.powdenest,
                        "hyperexpand":s.hyperexpand}
            require(len(a)==1, name+" expects one expression")
            return transforms[name](a[0])
        if name=="nsimplify":
            require(len(a)==1,"nsimplify expects one expression")
            return s.nsimplify(a[0])
        if name=="taylor":
            require(len(a)==4,"taylor expects expression, variable, point and order")
            return s.series(a[0],a[1],a[2],int(a[3]))
        if name in ("comDenom","numden"):
            numerator,denominator=s.fraction(s.together(a[0]))
            return denominator if name=="comDenom" else [numerator,denominator]
        if name=="coeff":
            require(len(a) in (2,3),"coeff expects an expression, variable and optional power")
            return a[0].coeff(a[1]) if len(a)==2 else a[0].coeff(a[1],int(a[2]))
        if name in ("quo","rem"):
            require(len(a)==3,name+" expects two polynomials and a variable")
            quotient,remainder=s.div(a[0],a[1],a[2])
            return quotient if name=="quo" else remainder
        if name=="resultant":
            require(len(a)==3,"resultant expects two expressions and a variable")
            return s.resultant(a[0],a[1],a[2])
        if name=="discriminant":
            require(len(a)==2,"discriminant expects a polynomial and variable")
            return s.discriminant(a[0],a[1])
        if name=="domain":
            require(len(a)==2,"domain expects an expression and variable")
            return continuous_domain(a[0],a[1],s.S.Reals)
        if name=="range":
            require(len(a)==2,"range expects an expression and variable")
            return function_range(a[0],a[1],s.S.Reals)
        if name in ("roots","real_roots"):
            require(len(a)==2,"roots expects a polynomial and a variable")
            if name=="roots":
                solutions=s.roots(a[0],a[1])
                if not solutions: self.note="No rational roots were found."
                return [[root,s.Integer(multiplicity)] for root,multiplicity in sorted(solutions.items(),key=lambda item:str(item[0]))]
            return list(s.real_roots(a[0],a[1]))
        if name=="rsolve":
            require(len(a) in (2,3),"rsolve expects an equation, a sequence such as y(n), and optional initial conditions")
            dependent=a[1]
            require(isinstance(dependent,AppliedUndef),"rsolve needs a sequence term such as y(n)")
            equation=ode_equation(a[0])
            if len(a)==3:
                items=a[2] if isinstance(a[2],(list,tuple)) else [a[2]]
                initial={}
                for item in items:
                    require(isinstance(item,s.Equality),"Initial conditions must be equations")
                    initial[item.lhs]=item.rhs
                return s.rsolve(equation,dependent,initial)
            return s.rsolve(equation,dependent)
        if name == "integrate":
            self.integral_strategy = None
            require(len(a) in (2,4), "integrate expects a variable or integration bounds")
            spec = a[1] if len(a)==2 else (a[1],a[2],a[3])
            result = s.integrate(a[0],spec)
            if result.has(s.Integral) and len(a)==2 and isinstance(a[1],s.Symbol):
                substituted=log_arctan_primitive(a[0],a[1])
                if substituted is not None: self.integral_strategy="log_arctan_polylog"
                else: substituted=rational_trig_primitive(a[0],a[1])
                if substituted is not None:
                    result,conditions,note=substituted
                    self.conditions.extend(conditions)
                    self.note=note
            if result.has(s.Integral): self.note = "Symbolic solution not found for the remaining integral. For a definite value, use nintegrate(expr,x,a,b) with finite bounds in the expression domain."
            elif len(a)==2 and not isinstance(a[1], (list,tuple)): result += self.symbol("C")
            return result
        if name in ("dsolve","desolve"):
            require(len(a) in (3,4), "dsolve expects equation, dependent function and independent variable")
            require(isinstance(a[2], s.Symbol), "dsolve independent variable must be a symbol")
            equation=ode_equation(a[0]); dependent=a[1]
            function=dependent.func if isinstance(dependent, AppliedUndef) else dependent
            conditions=initial_conditions(a[3],dependent,a[2]) if len(a)==4 else None
            from calc_runtime import solver_phase, SolverTimeLimit
            from sympy.solvers.ode import classify_ode
            function=function(a[2]) if isinstance(function,type) else function
            try:
                with solver_phase(3):
                    classification=classify_ode(equation,function,dict=True)
                hint=classification.get("default")
                require(hint and hint != "lie_group",
                        "No practical symbolic ODE method was found. Try the numerical differential-equation graph with an initial value.")
                with solver_phase(8):
                    return s.dsolve(equation,func=function,hint=hint,ics=conditions)
            except SolverTimeLimit as exc:
                raise MathError("Symbolic ODE solving stopped after its method time limit. Try the numerical differential-equation graph with an initial value.") from exc
        if name in ("laplace","fourier"):
            require(len(a)==3, name+" expects an expression, time variable and transform variable")
            result=(s.laplace_transform if name=="laplace" else s.fourier_transform)(a[0],a[1],a[2])
            if isinstance(result, tuple):
                value, conditions = result[0], result[1:]
            else:
                value, conditions = result, ()
            meaningful=[str(condition) for condition in conditions if condition not in (s.true,0)]
            if meaningful: self.note="Transform conditions: "+", ".join(meaningful)
            return value
        if name in ("ilaplace","ifourier"):
            require(len(a)==3, name+" expects a transformed expression, transform variable and time variable")
            result=(s.inverse_laplace_transform if name=="ilaplace" else s.inverse_fourier_transform)(a[0],a[1],a[2])
            if isinstance(result, tuple):
                value, conditions = result[0], result[1:]
            else:
                value, conditions = result, ()
            meaningful=[str(condition) for condition in conditions if condition not in (s.true,0)]
            if meaningful: self.note="Transform conditions: "+", ".join(meaningful)
            return value
        if name in ("fft","ifft"):
            require(len(a)==1, name+" expects a list of samples")
            return discrete_fourier(a[0], inverse=name=="ifft")
        if name in ("ztrans","invztrans"):
            require(len(a)==3, name+" expects an expression, its index and the transform variable")
            require(isinstance(a[1],s.Symbol) and isinstance(a[2],s.Symbol), name+" variables must be symbols")
            if name=="ztrans":
                value,note=z_transform(a[0],a[1],a[2])
                if note: self.note=note
                return value
            return inverse_z_transform(a[0],a[1],a[2])
        if name in ("mellin","invmellin"):
            require(len(a) in (3,5), name+" expects an expression, its variable and the transform variable, with an optional strip")
            require(isinstance(a[1],s.Symbol) and isinstance(a[2],s.Symbol), name+" variables must be symbols")
            if name=="mellin":
                value,note=mellin_transform(a[0],a[1],a[2])
                if note: self.note=note
                return value
            strip=(a[3],a[4]) if len(a)==5 else None
            value,used=inverse_mellin_transform(a[0],a[1],a[2],strip)
            self.note="Convergence strip: "+str(used)
            return value
        if name=="pdsolve":
            require(len(a) in (2,3), "pdsolve expects an equation, a function such as u(x,y) and an optional hint")
            require(isinstance(a[1],AppliedUndef), "pdsolve needs a function such as u(x,y)")
            equation=ode_equation(a[0])
            try:
                result=s.pdsolve(equation,a[1],hint=str(a[2])) if len(a)==3 else s.pdsolve(equation,a[1])
            except NotImplementedError:
                raise MathError("This partial differential equation is outside the supported solver")
            if isinstance(result,dict):
                solutions=list(result.values())
                require(solutions,"No solution was found for this partial differential equation")
                return solutions[0] if len(solutions)==1 else solutions
            return result
        if name == "limit":
            if isinstance(a[1],Relational): var,point = a[1].lhs,a[1].rhs; direction = str(a[2]) if len(a)>2 else "+-"
            else: var,point = a[1],a[2]; direction = str(a[3]) if len(a)>3 else "+-"
            direction = {"left":"-","right":"+","both":"+-"}.get(direction,direction)
            if direction == "+-" and point.is_finite is True:
                left=s.limit(a[0],var,point,dir="-")
                right=s.limit(a[0],var,point,dir="+")
                equal=True if left==right else (left-right).equals(0)
                if equal is False:
                    raise MathError("Two-sided limit does not exist: left-hand limit = "+str(left)+
                                    ", right-hand limit = "+str(right)+". Use left or right for a one-sided limit.")
                if equal is True: return left
            return s.limit(a[0],var,point,dir=direction)
        if name == "series": return s.series(a[0],a[1],a[2] if len(a)>2 else 0,int(a[3]) if len(a)>3 else 6)
        if name in ("sum", "product"):
            spec = tuple(a[1]) if len(a)==2 else tuple(a[1:])
            return (s.summation if name=="sum" else s.product)(a[0],spec)
        if name == "piecewise": return s.Piecewise(*(tuple(x) for x in a))
        if name == "solveset":
            require(len(a) in (2,3), "Use solveset(expr,x[,domain=S.Complexes])")
            require(isinstance(a[1],s.Symbol), "solveset requires one variable")
            require(isinstance(a[0],(s.Expr,s.Equality)) or a[0] in (s.true,s.false), "solveset requires one expression or equation")
            domain=a[2] if len(a)==3 else s.S.Complexes
            require(isinstance(domain,s.Set), "solveset domain must be a set, such as S.Reals, S.Complexes or S.Integers")
            result=s.solveset(a[0],a[1],domain=domain)
            # Preserve exclusions collected before expression simplification.
            for condition in (self.conditions if conditions is None else conditions):
                if not condition.has(a[1]): continue
                if isinstance(condition,s.Unequality):
                    result=result-s.solveset(condition.lhs-condition.rhs,a[1],domain=domain)
                else: result=result.intersect(s.ConditionSet(a[1],condition,domain))
            if result.has(s.ConditionSet): self.note="Symbolic solution not found; ConditionSet describes unresolved solutions, not proof that a root exists."
            return result
        if name == "solve":
            require(1<=len(a)<=3, "Use solve(eq,x[,real|complex|integer])")
            requested_domain = None
            if len(a)==3:
                domains = {"real":s.S.Reals, "complex":s.S.Complexes, "integer":s.S.Integers}
                require(str(a[2]) in domains, "solve domain must be real, complex or integer")
                requested_domain = domains[str(a[2])]
                require(not isinstance(a[0],list) and isinstance(a[1],s.Symbol)
                        and (not isinstance(a[0],Relational) or isinstance(a[0],s.Equality)),
                        "An explicit solve domain requires one equation and one variable")
            symbols=set().union(*(e.free_symbols for e in a[0])) if isinstance(a[0],list) else a[0].free_symbols
            var = a[1] if len(a)>1 else sorted(symbols,key=str)
            if isinstance(var,list) and len(var)==1: var = var[0]
            if isinstance(a[0],list): return self.solve_system(a[0],var)
            if isinstance(a[0],Relational) and not isinstance(a[0],s.Equality): return s.reduce_inequalities(a[0],var)
            expr = a[0].lhs-a[0].rhs if isinstance(a[0],s.Equality) else a[0]
            if isinstance(var,list): return self.solve_system(expr,var)
            domain=s.S.Integers if var.is_integer else s.S.Reals if var.is_real else s.S.Complexes
            if var.is_positive: domain=domain.intersect(s.Interval.open(0,s.oo))
            elif var.is_negative: domain=domain.intersect(s.Interval.open(-s.oo,0))
            if var.is_nonzero: domain=domain-s.FiniteSet(0)
            if requested_domain is not None: domain=domain.intersect(requested_domain)
            automatic_real = requested_domain is None and domain.is_subset(s.S.Reals) is not True
            real_domain = domain.intersect(s.S.Reals)
            real_note = "Solved over the real domain automatically; the complex-domain solver could not resolve this expression."
            try:
                result = s.solveset(expr,var,domain=domain)
            except (ValueError, NotImplementedError) as exc:
                if automatic_real:
                    result = s.solveset(expr,var,domain=real_domain)
                    domain = real_domain
                    self.note = real_note
                elif expr.has(s.Abs) and not domain.is_subset(s.S.Reals):
                    raise MathError("The complex-domain solver cannot handle this absolute-value equation. Use solve(eq,"+str(var)+",real), or omit the domain for automatic real solving.") from exc
                else:
                    raise
            # solveset can leave even algebraic logarithm equations unresolved.
            # solve has a separate logarithm strategy; accept its finite roots
            # only when substitution into the original equation is conclusive.
            expanded = s.expand_log(expr) if result.has(s.ConditionSet) and expr.has(s.log) else expr
            functions = sorted((f for f in expanded.atoms(s.Function) if f.has(var)),key=s.default_sort_key)
            coefficients = [expanded.coeff(f) for f in functions]
            remainder = expanded - s.Add(*(coefficient*f for coefficient,f in zip(coefficients,functions)))
            # Rational multiples of logarithms of rational functions have a
            # finite algebraic candidate equation. Avoid treating general
            # transcendental equations (log(x)=x, for example) as finite sets.
            finite_log_equation = (functions and all(f.func == s.log and f.args[0].is_rational_function(var) for f in functions)
                                   and not remainder.has(var) and all(not coefficient.has(var) for coefficient in coefficients)
                                   and coefficients[0] != 0 and all(s.simplify(coefficient/coefficients[0]).is_Rational for coefficient in coefficients))
            if result.has(s.ConditionSet) and finite_log_equation:
                try:
                    candidate_variable = s.Dummy("log_solution")
                    candidates = s.solve(expr.xreplace({var:candidate_variable}),candidate_variable)
                except (NotImplementedError, ValueError):
                    candidates = []
                if candidates:
                    checks = [s.checksol(expr,var,root) for root in candidates]
                    membership = [domain.contains(root) for root in candidates]
                    if all(check is not None for check in checks) and all(inside in (s.true,s.false) for inside in membership):
                        result = s.FiniteSet(*(root for root,check,inside in zip(candidates,checks,membership) if check and inside == s.true))
            # A complex ConditionSet can sometimes resolve in the real domain
            # for non-holomorphic functions. Do not replace arbitrary unresolved
            # complex equations with only their real roots (e.g. exp(x)=x).
            real_functions = (s.Abs, s.sign, s.floor, s.ceiling, s.Piecewise)
            if (automatic_real and domain != real_domain and result.has(s.ConditionSet)
                    and any(function.has(var) for function in expr.atoms(*real_functions))):
                try:
                    real_result = s.solveset(expr,var,domain=real_domain)
                except (ValueError, NotImplementedError):
                    real_result = None
                if real_result is not None and not real_result.has(s.ConditionSet):
                    result = real_result
                    domain = real_domain
                    self.note = real_note
            if result.has(s.ConditionSet):
                lambert_family=affine_exponential_solutions(expr,var,domain)
                if lambert_family is not None:
                    result,self.note=lambert_family
                elif expr.has(s.exp,s.log):
                    # solve() can expose useful Lambert W roots without
                    # enumerating every branch. Never label this a complete set.
                    try:
                        candidates=s.solve(expr,var)
                    except (ValueError,NotImplementedError):
                        candidates=[]
                    verified=[root for root in candidates if root.has(s.LambertW)
                              and domain.contains(root)==s.true and s.checksol(expr,var,root) is True]
                    if verified:
                        result=s.FiniteSet(*verified)
                        self.note="Partial solutions from the auxiliary solver; additional Lambert W branches may exist. This is not the complete solution set."
            if isinstance(result,s.FiniteSet):
                result=s.FiniteSet(*(root for root in result if all(condition.subs(var,root)!=s.false for condition in self.conditions)))
            else:
                for condition in (self.conditions if conditions is None else conditions):
                    if not condition.has(var): continue
                    if isinstance(condition,s.Unequality):
                        excluded=s.solveset(condition.lhs-condition.rhs,var,domain=domain)
                        result=s.Complement(result,excluded)
                    else:
                        result=result.intersect(s.ConditionSet(var,condition,domain))
            if result.has(s.ConditionSet): self.note = (self.note+" " if self.note else "")+"Symbolic solution not found; ConditionSet describes unresolved solutions, not proof that a root exists. For a real root, try nsolve(expr,x,a,b) on a continuous interval with a sign change."
            return result
        if name == "nsolve":
            expr = a[0].lhs-a[0].rhs if isinstance(a[0],s.Equality) else a[0]
            if len(a)==4:
                # Bracketing does not lose convergence merely due to a zero derivative.
                result=s.nsolve(expr,a[1],(a[2],a[3]),solver="bisect",prec=max(20,self.precision+10),maxsteps=max(100,4*(self.precision+10)))
            else: result=s.nsolve(expr,a[1],a[2],prec=max(20,self.precision+10),maxsteps=max(100,4*(self.precision+10)))
            require(all(c.subs(a[1],result)!=s.false for c in self.conditions),"No solution found in the expression domain")
            return s.N(result,self.precision)
        if name=="nderivative":
            require(len(a) in (3,4), "nderivative expects an expression, variable and point")
            result=numeric_derivative(a[0],a[1],a[2],self.precision,a[3] if len(a)==4 else None)
            self.note += ' Numerical derivative approximation; agreement of sampled left/right differences is not proof of differentiability.'
            return result
        if name in ("nintegrate", "minimum", "maximum"):
            if name in ("minimum", "maximum"):
                require(len(a) in (4,5), name+" expects expr,x,a,b and optional closed/open/leftopen/rightopen")
                require(isinstance(a[1],s.Symbol), "Choose an independent variable")
                mode=str(a[4]) if len(a)==5 else "closed"
                require(mode in ("closed","open","leftopen","rightopen"), "Use closed, open, leftopen or rightopen")
                require(a[2].is_extended_real is True and a[3].is_extended_real is True and a[2]<=a[3], "Invalid extrema interval")
                interval=s.Interval(a[2],a[3],left_open=mode in ("open","leftopen"),right_open=mode in ("open","rightopen"))
                entries=extrema_candidates(a[0],a[1],interval,name,conditions=self.conditions if conditions is None else conditions)
                return entries[0][1]
            result = numeric_integral(a[0],a[1],a[2],a[3],self.precision)
            require(not result.has(s.Integral), "Numerical convergence failed")
            return result
        if name=="normalize":
            vector=matrix(a[0]);length=vector.norm()
            require(length!=0,"Domain ERROR: zero vector cannot be normalized")
            return vector/length
        if name=="gradient":
            coords=coordinates(a[1])
            return [s.diff(a[0],var) for var in coords]
        if name in ("divergence","curl"):
            coords=coordinates(a[1]); field=matrix(a[0])
            if field.rows==1 and field.cols==len(coords): field=field.T
            require(field.cols==1 and field.rows==len(coords), "Vector field dimension does not match coordinates")
            if name=="divergence":
                return s.Add(*(s.diff(field[index],coords[index]) for index in range(len(coords))))
            if field.rows==2:
                return s.diff(field[1],coords[0])-s.diff(field[0],coords[1])
            require(field.rows==3,"Curl supports two or three dimensional vector fields")
            return s.Matrix([s.diff(field[2],coords[1])-s.diff(field[1],coords[2]),
                             s.diff(field[0],coords[2])-s.diff(field[2],coords[0]),
                             s.diff(field[1],coords[0])-s.diff(field[0],coords[1])])
        if name=="hessian":
            coords=coordinates(a[1])
            return s.Matrix([[s.diff(a[0],coords[row],coords[column]) for column in range(len(coords))] for row in range(len(coords))])
        if name=="jacobian":
            coords=coordinates(a[1])
            return matrix(a[0]).jacobian(coords)
        if name=="laplacian":
            coords=coordinates(a[1])
            return s.Add(*(s.diff(a[0],var,var) for var in coords))
        if name=="charpoly":
            require(len(a) in (1,2), "charpoly expects a matrix and optional variable")
            m=matrix(a[0]); variable=a[1] if len(a)==2 else s.Symbol("lambda")
            return m.charpoly(variable).as_expr()
        if name=="identity":
            require(len(a)==1 and a[0].is_Integer and 0<a[0] and within_limit(a[0],32), "identity size must be an integer from 1 to 32")
            return s.eye(int(a[0]))
        if name=="diag":
            require(len(a)==1 and isinstance(a[0],(list,tuple)), "diag expects a list of diagonal entries")
            return s.diag(*a[0])
        matrix_ops = {"det": lambda m: m.det(), "inverse": lambda m: m.inv(), "transpose": lambda m: m.T,
                      "rank": lambda m: s.Integer(m.rank()), "trace": lambda m: m.trace(), "rref": lambda m: m.rref()[0],
                      "ref": lambda m: m.echelon_form(), "lu": lambda m: list(m.LUdecomposition()),
                      "eigenvalues": lambda m: [[k,s.Integer(v)] for k,v in m.eigenvals().items()],
                      "eigenvectors": lambda m: [[v,s.Integer(k),vec] for v,k,vec in m.eigenvects()],
                      "norm": lambda m: m.norm(), "qr": lambda m: list(m.QRdecomposition()),
                      "cholesky": lambda m: m.cholesky(hermitian=False), "nullspace": lambda m: list(m.nullspace()),
                      "cofactor": lambda m: m.cofactor_matrix(), "adjugate": lambda m: m.adjugate(),
                      "rowspace": lambda m: list(m.rowspace()), "singularvalues": lambda m: list(m.singular_values()),
                      "frob": lambda m: s.sqrt(sum(s.Abs(item)**2 for item in m)),
                      "jordan": lambda m: list(m.jordan_form()), "dim": lambda m: [m.rows,m.cols],
                      "pinv": lambda m: m.pinv(), "ctranspose": lambda m: m.H,
                      "svd": lambda m: list(m.singular_value_decomposition())}
        if name in matrix_ops: return matrix_ops[name](matrix(a[0]))
        if name in ("dot", "cross", "angle", "projection", "linsolve"):
            u,v = matrix(a[0]),matrix(a[1])
            if name == "dot": return u.dot(v)
            if name == "cross": return u.cross(v)
            if name == "angle":
                require(u.norm()!=0 and v.norm()!=0,"Domain ERROR: zero vector has no direction")
                result=s.acos(u.dot(v)/(u.norm()*v.norm()))
                return result if result.free_symbols else result*{"DEG":180/s.pi,"GRAD":200/s.pi}.get(self.angle,1)
            if name == "projection": return v*(u.dot(v)/v.dot(v))
            return u.inv()*v
        if name in ("skewness", "kurtosis"):
            require(len(a) in (1,2), name+" expects a data list and optional correction (0 or 1)")
            correction = a[1] if len(a)==2 else s.Integer(1)
            require(getattr(correction,"is_Integer",False) and correction in (0,1), "correction must be 0 (moment) or 1 (sample corrected)")
            skew, kurt = shape_statistics(a[0], bool(correction))
            value = skew if name=="skewness" else kurt
            require(value is not s.nan, name+" requires variation"+(" and at least "+("3" if name=="skewness" else "4")+" values" if correction else ""))
            return value
        if name in ("mean", "median", "mode", "variance", "stdev", "sumdata", "quartiles", "stats"):
            if name == 'stats' and len(a) == 3 and nodes[1].get('kind') == 'symbol' and nodes[1].get('value') == 'overall':
                summary = overall_summary(a[0], a[2])
                self.statistics_full_tables = summary
                result = {key: rows[:50] for key, rows in summary.items()}
                if any(len(rows) > 50 for rows in summary.values()):
                    result['Output note'] = 'Plain Output previews up to 50 rows per table; the formatted report and Copy include all rows.'
                return result
            dispersion = name in ("variance", "stdev")
            require(len(a) in ((1,2) if dispersion or name=="stats" else (1,)), name+" expects a data list"+(" and optional ddof (0 or 1)" if dispersion else ""))
            data = flatten(a[0]); n = len(data)
            require(n>0,"Enter at least one data value")
            if name=="stats":
                if len(a)==2:
                    require(nodes[1].get('kind')=='symbol' and nodes[1].get('value')=='categorical', "stats option must be categorical")
                if len(a)==2 or binary_summary(data):
                    self.statistics_summary_frequencies=summary_frequencies(data)
                    return {"n":s.Integer(n), "Category count":s.Integer(len(self.statistics_summary_frequencies))}
            ddof = a[1] if dispersion and len(a)==2 else s.Integer(1 if dispersion else 0)
            require(getattr(ddof,"is_Integer",False) and ddof in (0,1), "ddof must be 0 (population) or 1 (sample)")
            require(n>ddof,"Sample variance and standard deviation require at least two data values")
            avg = sum(data)/n; var = sum((x-avg)**2 for x in data)/(n-ddof)
            ordered = sorted(data)
            med = s.Rational(1,2)*(ordered[(n-1)//2]+ordered[n//2])
            if name == "mean": return avg
            if name == "median": return med
            if name in ("mode", "stats"):
                # Numeric literals with different precision still share a frequency.
                keys = [s.Rational(str(value)) if value.is_Float else value for value in data]
                counts = Counter(keys)
                representatives = dict(zip(keys, data))
                frequency = max(counts.values())
                modes = sorted(representatives[value] for value, count in counts.items() if count==frequency)
                if name == "mode": return modes
                # The existing mode computation identifies distinct numeric values.
                # Do not compute a categorical frequency/percentage table at 10 or more.
                if len(counts)<10:self.statistics_summary_frequencies=summary_frequencies(data)
                elif hasattr(self,'statistics_summary_frequencies'):del self.statistics_summary_frequencies
            if name == "variance": return var
            if name == "stdev": return s.sqrt(var)
            if name == "sumdata": return sum(data)
            quartiles = [s.Rational(str(x)) for x in statistics.quantiles(ordered,method="inclusive")] if n>1 else [data[0]]*3
            if name == "quartiles": return quartiles
            skew, kurt = shape_statistics(data)
            return {"n": s.Integer(n), "sum": sum(data), "mean": avg, "median": med, "mode(s)": modes, "population variance": var,
                    "population SD": s.sqrt(var), "sample variance": var*n/(n-1) if n>1 else s.nan,
                    "sample SD": s.sqrt(var*n/(n-1)) if n>1 else s.nan, "skewness (sample corrected)": skew,
                    "excess kurtosis (sample corrected)": kurt, "quartiles (inclusive)": quartiles}
        if name in ("covariance","correlation"):
            require(len(a) in ((2,3) if name=="covariance" else (2,)), name+" expects two data lists"+(" and optional ddof (0 or 1)" if name=="covariance" else ""))
            xs=flatten(a[0]); ys=flatten(a[1])
            require(len(xs)==len(ys),"Covariance and correlation require equal data lengths")
            n=len(xs)
            require(n>0,"Enter paired data")
            ddof=a[2] if len(a)==3 else s.Integer(1 if name=="covariance" else 0)
            require(getattr(ddof,"is_Integer",False) and ddof in (0,1), "ddof must be 0 (population) or 1 (sample)")
            require(n>ddof,"Sample covariance requires at least two paired values")
            mx=sum(xs)/n; my=sum(ys)/n
            covariance=sum((x-mx)*(y-my) for x,y in zip(xs,ys))/(n-ddof)
            if name=="covariance": return covariance
            return pearson_correlation(xs,ys)
        if name == "regression":
            require(len(a) in (1,2,3), "Use regression(data,model[,options])")
            rows = a[0]; mode = str(a[1]) if len(a)>1 else "linear"
            require(len(a)<3 or mode in ("polynomial", "logistic", "ridge", "lasso", "elasticnet", "logisticridge", "logisticlasso", "logisticelasticnet", "randomforest", "randomforestclassifier", "randomforestregressor", "svm", "svc", "svr", "bayeslinear", "bayeslogistic"), "Options require polynomial, logistic (firth), Bayesian or machine learning regression")
            return fit_regression(self, rows, mode, a[2] if len(a)>2 else None)
        if name == "convert":
            if len(a)==2 and isinstance(a[0],Quantity):
                self.note="Result in "+nodes[1]["value"]
                return convert_quantity(a[0],nodes[1]["value"],UNITS)
            src,dst = nodes[1]["value"],nodes[2]["value"]
            require(src in UNITS and dst in UNITS,"Unknown unit")
            d1,f1,o1 = UNITS[src]; d2,f2,o2 = UNITS[dst]
            require(d1==d2,"Unit dimension mismatch")
            base = a[0]*f1+o1
            if d1=="temperature": require(base>=0,"Temperature below absolute zero")
            self.note = "Result in " + dst
            return s.simplify((base-o2)/f2)
        if name in ("normpdf", "normcdf", "invnorm", "tpdf", "tcdf", "invt", "chi2pdf", "chi2cdf", "fpdf", "fcdf",
                    "binompdf", "binomcdf", "poissonpdf", "poissoncdf", "geometpdf", "geometcdf",
                    "exppdf", "expcdf", "unifpdf", "unifcdf", "gammapdf", "gammacdf", "betapdf", "betacdf",
                    "lognormpdf", "lognormcdf", "hgeompdf", "hgeomcdf", "nbinompdf", "nbinomcdf", "weibullpdf", "weibullcdf", "cauchypdf", "cauchycdf", "invcauchy"):
            return distribution_value(self, name, a)
        if name in ADVANCED_STATISTICS:
            result=advanced(self, name, a)
            self.statistics_inputs=(name,a,nodes)
            return result
        if name in ("ttest", "ttest2", "ttestpaired", "ztest", "ztest2", "chi2test", "chi2independence", "fisherexact", "anova", "welchanova", "tukey", "gameshowell", "shapiro", "normaltest", "wilcoxon", "mannwhitney", "kruskal", "tinterval", "zinterval"):
            result=statistical_test(self, name, a, nodes)
            self.statistics_inputs=(name,a,nodes)
            return result
        if name in ("tvmfv", "tvmpv", "tvmpmt", "tvmn", "tvmrate", "npv", "irr", "amort", "cagr"):
            return finance_value(self, name, a, nodes)
        if name in self.functions:
            function = self.functions[name]
            require(len(function["parameters"])==len(a),"Function argument count mismatch")
            require(name not in self.resolving,"Recursive function definition")
            old = self.bindings.copy(); self.bindings.update(zip(function["parameters"],a)); self.resolving.add(name)
            try: return self.build(function["body"])
            finally: self.bindings = old; self.resolving.remove(name)
        if name.isidentifier():
            require(all(isinstance(value,s.Expr) for value in a),
                    "Undefined function: "+name+". Define it before passing lists or matrices.")
            return s.Function(name)(*a)
        raise MathError("Unknown function: " + name)

    def call_answer(self, body, arguments):
        """Apply a saved symbolic answer without resolving its frozen symbols."""
        require("Ans" not in self.resolving, "Recursive answer definition")
        start = len(self.conditions)
        self.resolving.add("Ans")
        try:
            expression = self.build(body)
        finally:
            self.resolving.remove("Ans")
        require(isinstance(expression, s.Expr), "Ans is not a function")
        parameters = body.get("parameters")
        if parameters is None:
            symbols = sorted(expression.free_symbols, key=s.default_sort_key)
            require(len(symbols) == 1, "Ans is not a single-variable function")
        else:
            symbols = [self.symbol(name) for name in parameters]
        require(len(symbols) == len(arguments), "Function argument count mismatch")
        replacements = dict(zip(symbols, arguments))
        guards = [guard.xreplace(replacements) for guard in self.conditions[start:]]
        require(all(guard != s.false for guard in guards), "Domain ERROR: excluded value")
        self.conditions[start:] = [guard for guard in guards if guard != s.true]
        return expression.xreplace(replacements)
