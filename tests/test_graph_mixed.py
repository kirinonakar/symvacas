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


    def test_explicit_log_halfplane_keeps_full_regions_below_nonpositive_boundary(self):
        for operator,full in ((">",True),("<",False)):
            shade=self.run_graph(rel(operator,y,num(-1)),yLog=True,yMin=.01,yMax=100)["shadings"][0]
            self.assertEqual([[]],shade["boundary"])
            self.assertEqual(full,bool(shade["fill"]))
            for poly in shade["fill"]:
                for px,py in poly:self.assertTrue(.01<=py<=100)
        shade=self.run_graph(rel(">",y,call("sin",x)),yLog=True,yMin=.01,yMax=10,samples=200)["shadings"][0]
        for poly in shade["fill"]:
            for px,py in poly:self.assertGreaterEqual(py-math.sin(px),-1e-8)
        for px,py in filter(None,shade["boundary"][0]):self.assertAlmostEqual(py,math.sin(px),delta=1e-8)

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
    def test_log_y_rejects_nonpositive_bounds(self):
        result=json.loads(dispatch(json.dumps({"action":"graph","graphKind":"cartesian","trees":[x],"min":-1,"max":1,"yLog":True,"yMin":0,"yMax":10})))
        self.assertFalse(result["ok"]);self.assertIn("Log y requires",result["error"])
    def test_disk_area_and_strict_boundary(self):
        result=self.run_graph(rel("<",circle,num(4)))
        self.assertEqual(["dashed"],result["curveStyles"])
        shade=result["shadings"][0];self.assertEqual(0,shade["sourceIndex"])
        area=0
        for polygon in shade["fill"]:
            area+=abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(polygon,polygon[1:]+polygon[:1])))/2
            for px,py in polygon: self.assertLessEqual(px*px+py*py,4.0001)
        self.assertAlmostEqual(4*math.pi,area,delta=.04)
        line=shade["boundary"][0]
        self.assertEqual(["dashed"],shade["boundaryStyles"])
        self.assertNotIn(None,line)
        self.assertGreater(len(line),100)
        self.assertEqual(line[0],line[-1])
        for a,b in zip(line,line[1:]): self.assertLess(math.dist(a,b),.15)
    def test_dashed_disconnected_contours_remain_separate_closed_paths(self):
        expression=op("+",op("^",op("-",x2,num(1)),num(2)),y2)
        shade=self.run_graph(rel("<",expression,num(.1)))["shadings"][0]
        paths=[[]]
        for point in shade["boundary"][0]:
            if point is None: paths.append([])
            else: paths[-1].append(point)
        self.assertEqual(2,len(paths))
        for path in paths:
            self.assertEqual(path[0],path[-1])
            self.assertGreater(len(path),20)
            for a,b in zip(path,path[1:]):self.assertLess(math.dist(a,b),.2)
    def test_reversed_and_chained_inequalities_empty_full_and_undefined(self):
        result=self.run_graph(rel("<=",op("-",x2,num(2)),y))
        self.assertEqual(["solid"],result["curveStyles"])
        for polygon in result["shadings"][0]["fill"]:
            for px,py in polygon: self.assertGreaterEqual(py-px*px+2,-.0001)
        result=self.run_graph(rel("<",rel("<",num(-1),x),num(1)))
        for polygon in result["shadings"][0]["fill"]:
            for px,py in polygon: self.assertLessEqual(abs(px),1.00001)
        result=self.run_graph(rel("<",op("^",circle,num(2)),num(0)))
        self.assertEqual([],result["shadings"][0]["fill"])
        result=self.run_graph(rel(">=",op("^",circle,num(2)),num(0)))
        self.assertTrue(result["shadings"][0]["fill"])
        result=self.run_graph(rel("<",call("sqrt",x),y))
        for polygon in result["shadings"][0]["fill"]:
            for px,py in polygon: self.assertGreaterEqual(px,0)

if __name__=="__main__": unittest.main()
