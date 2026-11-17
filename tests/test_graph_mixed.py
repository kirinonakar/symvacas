import json
import math
import pathlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"app/src/main/python"))
from calc_engine import dispatch


def num(v): return {"kind":"number","value":str(v)}
def sym(v): return {"kind":"symbol","value":v}
def op(v,a,b,kind="binary"): return {"kind":kind,"value":v,"args":[a,b]}
def rel(v,a,b): return op(v,a,b,"relation")
def call(v,a): return {"kind":"call","value":v,"args":[a]}
x,y,t,theta=map(sym,("x","y","t","theta"))
x2,y2=op("^",x,num(2)),op("^",y,num(2))
circle=op("+",x2,y2)
pair={"kind":"tuple","args":[call("cos",t),call("sin",t)]}
rose=rel("=",sym("r"),op("*",num(2),call("cos",op("*",num(3),theta))))

class MixedGraphTests(unittest.TestCase):
    def run_graph(self,*trees,**options):
        result=json.loads(dispatch(json.dumps({"action":"graph","graphKind":"cartesian","trees":trees,
            "min":-4,"max":4,"yMin":-4,"yMax":4,"samples":500,"angle":"RAD",**options})))
        self.assertTrue(result["ok"],result)
        return result

    def test_grouped_nonlinear_constraints_keep_parameters_and_empty_intersections(self):
        bounds={"kind":"list","args":[rel("<",{"kind":"group","args":[circle]},sym("a")),rel(">=",y,num(0))]}
        result=self.run_graph(bounds,parameters={"a":4})
        self.assertEqual(["a"],result["parameters"])
        shade=result["shadings"][0]
        self.assertEqual(["dashed","solid"],shade["boundaryStyles"])
        self.assertTrue(shade["fill"])
        for polygon in shade["fill"]:
            for px,py in polygon:
                self.assertLessEqual(px*px+py*py,4.001)
                self.assertGreaterEqual(py,-1e-8)
        empty={"kind":"list","args":[rel(">",x,num(1)),rel("<",x,num(0))]}
        self.assertEqual([],self.run_graph(empty)["shadings"][0]["fill"])

    def test_animated_affine_intersection_keeps_exact_area_and_compact_geometry(self):
        bounds={"kind":"list","args":[rel("<",rel("<",num(-1),x),num(1)),
            rel("<",rel("<",num(-1),y),op("*",sym("a"),x))]}
        for a in (0,1e-12,-1e-12,1,-1,2.3,-2.3,4,-4):
            for xmin,xmax,ymin,ymax in ((-10,10,-5,5),(-.25,.75,-.5,1.5)):
                result=self.run_graph(bounds,parameters={"a":a},samples=200,min=xmin,max=xmax,yMin=ymin,yMax=ymax)
                self.assertEqual(["a"],result["parameters"])
                shade=result["shadings"][0]
                self.assertEqual(["dashed"]*4,shade["boundaryStyles"])
                self.assertLessEqual(len(shade["fill"]),1)
                self.assertLessEqual(sum(len(polygon) for polygon in shade["fill"]),8)
                area=0
                for polygon in shade["fill"]:
                    area+=abs(sum(p[0]*q[1]-q[0]*p[1] for p,q in zip(polygon,polygon[1:]+polygon[:1])))/2
                    for px,py in polygon:
                        self.assertTrue(max(xmin,-1)-1e-10<=px<=min(xmax,1)+1e-10)
                        self.assertTrue(max(ymin,-1)-1e-10<=py<=min(ymax,a*px)+1e-10)
                # Integrate the piecewise linear height independently, including viewport crossings.
                low,high=max(xmin,-1),min(xmax,1)
                knots=sorted({low,high}|{edge/a for edge in (-1,ymin,ymax) if a and low<edge/a<high})
                height=lambda px:max(0,min(ymax,a*px)-max(ymin,-1))
                expected=sum((right-left)*(height(left)+height(right))/2 for left,right in zip(knots,knots[1:]))
                self.assertAlmostEqual(expected,area,delta=1e-9)
                for index,line in enumerate(shade["boundary"]):
                    for px,py in filter(None,line):
                        residual=(px+1,px-1,py+1,py-a*px)[index]
                        self.assertAlmostEqual(0,residual,delta=1e-9)


    def test_explicit_halfplane_excludes_domain_cuts_and_variable_y_coefficients(self):
        import sympy as s
        from calc_graph_shading import _explicit_inequality
        sx,sy=s.symbols("x y",real=True)
        for expression in (sy-1/sx,sy-s.tan(sx),sy-s.sqrt(sx),sx*sy-1,sy-s.Piecewise((0,sx<0),(1,True)),sy**2-sx):
            self.assertIsNone(_explicit_inequality(expression,sx,sy))


    def test_explicit_band_coincident_strictness_and_log_clipping(self):
        # An inclusive copy must not paint over a strict boundary.
        shade=self.run_graph(rel(">=",rel("<",y,num(1)),y))["shadings"][0]
        self.assertEqual(["dashed","solid"],shade["boundaryStyles"])
        self.assertEqual([],shade["boundary"][1])
        for source in (rel("<",rel("<",num(1),y),num(0)),rel("<",rel("<",num(0),y),num(0))):
            shade=self.run_graph(source)["shadings"][0]
            self.assertEqual([],shade["fill"]);self.assertFalse(any(any(line) for line in shade["boundary"]))
        shade=self.run_graph(rel("<",rel("<=",num(-1),y),call("sin",x)),yLog=True,yMin=.01,yMax=10,samples=200)["shadings"][0]
        for polygon in shade["fill"]:
            for px,py in polygon:
                self.assertTrue(.01<=py<=10);self.assertLessEqual(py,math.sin(px)+1e-8)
if __name__=="__main__": unittest.main()
