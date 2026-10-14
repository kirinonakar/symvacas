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
    def test_requested_four_rows_keep_source_indices_coordinates_and_parameters(self):
        result=self.run_graph(rel("=",y,x2),rel("=",circle,num(9)),rose,pair,derivativeSelected=0,
                              variables={"theta":num(99),"t":num(99)})
        self.assertEqual(["cartesian","cartesian","polar","parametric"],result["curveKinds"])
        self.assertEqual([],result["parameters"])
        self.assertEqual(4,result["derivativeCurveIndex"])
        for px,py in filter(None,result["curves"][0]): self.assertAlmostEqual(px*px,py)
        for px,py in filter(None,result["curves"][1]): self.assertAlmostEqual(9,px*px+py*py,delta=1e-4)
        for index in (2,3):
            positions=result["curveParameters"][index]
            self.assertEqual(len(positions),len(result["curves"][index]))
            for at,point in zip(positions,result["curves"][index]):
                if point is None: continue
                radius=2*math.cos(3*at) if index==2 else 1
                self.assertAlmostEqual(radius*math.cos(at),point[0],delta=1e-10)
                self.assertAlmostEqual(radius*math.sin(at),point[1],delta=1e-10)
    def test_parameter_interval_is_independent_of_cartesian_view_and_sliders(self):
        vector={"kind":"tuple","args":[t,op("*",sym("a"),t)]}
        result=self.run_graph(vector,rose,parameterMin=1,parameterMax=2,parameters={"a":3})
        self.assertEqual(["a"],result["parameters"])
        self.assertAlmostEqual(1,result["curveParameters"][0][0])
        self.assertAlmostEqual(2,result["curveParameters"][0][-1])
        for px,py in filter(None,result["curves"][0]): self.assertAlmostEqual(3*px,py)
    def test_t_and_theta_sampling_ranges_are_independent(self):
        result=self.run_graph(pair,rose,parameterMin=1,parameterMax=2,thetaMin=-.5,thetaMax=.5)
        self.assertAlmostEqual(1,result["curveParameters"][0][0])
        self.assertAlmostEqual(2,result["curveParameters"][0][-1])
        self.assertAlmostEqual(-.5,result["curveParameters"][1][0])
        self.assertAlmostEqual(.5,result["curveParameters"][1][-1])
        for at,point in zip(result["curveParameters"][1],result["curves"][1]):
            if point is not None:
                radius=2*math.cos(3*at)
                self.assertAlmostEqual(radius*math.cos(at),point[0],delta=1e-10)
                self.assertAlmostEqual(radius*math.sin(at),point[1],delta=1e-10)
    def test_disk_area_and_strict_boundary(self):
        result=self.run_graph(rel("<",circle,num(4)))
        self.assertEqual(["dashed"],result["curveStyles"])
        shade=result["shadings"][0];self.assertEqual(0,shade["sourceIndex"])
        area=0
        for polygon in shade["fill"]:
            area+=abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(polygon,polygon[1:]+polygon[:1])))/2
            for px,py in polygon: self.assertLessEqual(px*px+py*py,4.0001)
        self.assertAlmostEqual(4*math.pi,area,delta=.04)
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
    def test_other_mixed_rows_do_not_break_cartesian_or_parametric_analysis(self):
        request={"action":"graphAnalysis","graphKind":"cartesian","trees":[x2,rose,pair],"analysis":"minimum",
                 "selected":0,"a":-1,"b":1,"angle":"RAD"}
        result=json.loads(dispatch(json.dumps(request)));self.assertTrue(result["ok"],result)
        self.assertEqual([[0.,0.]],result["points"])
        request.update(selected=2,analysis="arclength",a=0,b=math.pi*2)
        result=json.loads(dispatch(json.dumps(request)));self.assertTrue(result["ok"],result)
        self.assertAlmostEqual(math.pi*2,result["value"],delta=1e-7)

if __name__=="__main__": unittest.main()
