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
    def test_animated_sine_and_cosine_halfplane_keep_exact_boundary_and_small_fill(self):
        phase=op("+",x,sym("b"))
        sine=op("*",sym("a"),call("sin",phase))
        cosine=op("*",sym("a"),call("cos",phase))
        from calc_graph_common import _compiled_graph
        for a,b in ((1,0),(3,.7),(-3,1.2),(0,2)):
            result=self.run_graph(sine,rel(">",cosine,y),parameters={"a":a,"b":b},samples=200,min=-10,max=10,yMin=-5,yMax=5)
            self.assertEqual(["a","b"],result["parameters"])
            shade=result["shadings"][0]
            self.assertEqual(["dashed"],shade["boundaryStyles"])
            self.assertEqual(1,len(shade["fill"]))
            self.assertLess(len(json.dumps(result)),60000)
            for px,py in filter(None,result["curves"][0]):self.assertAlmostEqual(a*math.sin(px+b),py,delta=1e-10)
            for px,py in filter(None,shade["boundary"][0]):self.assertAlmostEqual(a*math.cos(px+b),py,delta=1e-10)
            for left,right in zip(shade["boundary"][0],shade["boundary"][0][1:]):
                if left is None or right is None: continue
                for fraction in (.25,.5,.75):
                    at=left[0]+(right[0]-left[0])*fraction
                    line=left[1]+(right[1]-left[1])*fraction
                    self.assertLessEqual(abs(line-a*math.cos(at+b))*800/10,.6)
            for polygon in shade["fill"]:
                for px,py in polygon:self.assertLessEqual(py,a*math.cos(px+b)+1e-9)
            if a==1: misses=_compiled_graph.cache_info().misses
        self.assertEqual(misses,_compiled_graph.cache_info().misses)

    def test_explicit_halfplane_clips_viewport_and_reverses_parameter_coefficient(self):
        for a in (-2,2,0):
            result=self.run_graph(rel("<=",op("*",sym("a"),y),x2),parameters={"a":a},samples=200)
            for polygon in result["shadings"][0]["fill"]:
                for px,py in polygon:
                    self.assertTrue(-4<=px<=4 and -4<=py<=4)
                    self.assertLessEqual(a*py-px*px,1e-8)
        # The boundary lies entirely above or below the viewport.
        for boundary,operator,full in ((10,"<",True),(-10,"<",False),(10,">",False),(-10,">",True)):
            shade=self.run_graph(rel(operator,y,num(boundary)))["shadings"][0]
            self.assertEqual([[]],shade["boundary"])
            area=sum(abs(sum(p[0]*q[1]-q[0]*p[1] for p,q in zip(poly,poly[1:]+poly[:1])))/2 for poly in shade["fill"])
            self.assertAlmostEqual(64 if full else 0,area)

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

    def test_animated_chained_sine_cosine_band_preserves_empty_regions_and_area(self):
        phase=op("+",x,sym("b"))
        sine=op("*",sym("a"),call("sin",phase))
        cosine=op("*",sym("a"),call("cos",phase))
        for a,b in ((1,0),(3,.7),(-3,1.2),(0,2),(6,2)):
            shade=self.run_graph(rel("<",rel("<",sine,y),cosine),parameters={"a":a,"b":b},
                min=-10,max=10,yMin=-5,yMax=5,samples=200)["shadings"][0]
            self.assertEqual(["dashed","dashed"],shade["boundaryStyles"])
            self.assertLessEqual(len(shade["fill"]),5)
            if a==0:
                self.assertEqual([],shade["fill"]);self.assertEqual([[],[]],shade["boundary"])
            for index,line in enumerate(shade["boundary"]):
                for px,py in filter(None,line):
                    self.assertAlmostEqual(a*(math.sin(px+b) if index==0 else math.cos(px+b)),py,delta=1e-8)
                    self.assertLessEqual(a*math.sin(px+b),py+1e-8)
                    self.assertLessEqual(py,a*math.cos(px+b)+1e-8)
                for left,right in zip(line,line[1:]):
                    if left is None or right is None: continue
                    for fraction in (.25,.5,.75):
                        at=left[0]+(right[0]-left[0])*fraction
                        interpolated=left[1]+(right[1]-left[1])*fraction
                        expected=a*(math.sin(at+b) if index==0 else math.cos(at+b))
                        self.assertLessEqual(abs(interpolated-expected)*800/10,.6)
            area=0
            for polygon in shade["fill"]:
                area+=abs(sum(p[0]*q[1]-q[0]*p[1] for p,q in zip(polygon,polygon[1:]+polygon[:1])))/2
                for px,py in polygon:
                    self.assertTrue(-10<=px<=10 and -5<=py<=5)
                    self.assertLessEqual(a*math.sin(px+b),py+1e-8)
                    self.assertLessEqual(py,a*math.cos(px+b)+1e-8)
                # The top and bottom chains share x positions; their midpoint
                # belongs to one connected band, never to an empty gap.
                top=polygon[:len(polygon)//2];bottom=list(reversed(polygon[len(polygon)//2:]))
                for upper,lower in zip(top,bottom):
                    self.assertEqual(upper[0],lower[0]);self.assertGreaterEqual(upper[1],lower[1])
            expected=sum(max(0,min(5,a*math.cos(-10+20*(i+.5)/20000+b))-max(-5,a*math.sin(-10+20*(i+.5)/20000+b))) for i in range(20000))*20/20000
            self.assertAlmostEqual(expected,area,delta=.08)

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
    def test_log_y_retains_real_values_and_simplifies_exponentials_in_log_coordinates(self):
        exponential=op("^",num(10),x)
        result=self.run_graph(exponential,yLog=True,yMin=.001,yMax=1000,min=-3,max=3)
        points=list(filter(None,result["curves"][0]))
        self.assertLessEqual(len(points),10)
        for px,py in points:self.assertAlmostEqual(px,math.log10(py),delta=1e-9)
        result=self.run_graph(x,yLog=True,yMin=.001,yMax=1,min=-1,max=1)
        points=list(filter(None,result["curves"][0]))
        self.assertGreater(len(points),10)
        self.assertTrue(all(py>0 for px,py in points))
        for px,py in points:self.assertAlmostEqual(px,py)
    def test_log_implicit_shading_and_derivatives_use_positive_actual_coordinates(self):
        result=self.run_graph(rel("=",circle,num(1)),yLog=True,yMin=.001,yMax=2,min=-2,max=2)
        self.assertTrue(result["curves"][0])
        for px,py in filter(None,result["curves"][0]):
            self.assertGreater(py,0);self.assertAlmostEqual(1,px*px+py*py,delta=1e-4)
        result=self.run_graph(rel("<",op("*",x,y),num(1)),yLog=True,yMin=.01,yMax=100)
        self.assertTrue(result["shadings"][0]["fill"])
        for polygon in result["shadings"][0]["fill"]:
            self.assertTrue(all(.00999<=point[1]<=100.001 for point in polygon))
        result=self.run_graph(x2,yLog=True,yMin=.01,yMax=10,derivativeSelected=0)
        for px,py in filter(None,result["curves"][result["derivativeCurveIndex"]]):
            self.assertGreater(py,0);self.assertAlmostEqual(2*px,py)
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
    def test_mixed_strictness_is_per_boundary_and_contours_are_connected(self):
        result=self.run_graph(rel("<=",rel("<",num(-1),x),num(1)))
        shade=result["shadings"][0]
        self.assertEqual(["dashed","solid"],shade["boundaryStyles"])
        for line,expected in zip(shade["boundary"],(-1,1)):
            self.assertNotIn(None,line)
            self.assertGreater(len(line),40)
            for px,py in line: self.assertAlmostEqual(expected,px)
            self.assertAlmostEqual(8,abs(line[-1][1]-line[0][1]))
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
    def test_explicit_shading_boundaries_keep_strictness(self):
        for strict in (True,False):
            result=self.run_graph(shadings=[{"mode":"halfplane","side":"below","strict":strict,"trees":[x]}])
            self.assertEqual(["dashed" if strict else "solid"],result["shadings"][0]["boundaryStyles"])
        constraints=[{"axis":axis,"side":side,"strict":strict} for axis,side,strict in
                     (("x","lower",True),("x","upper",False),("y","lower",False),("y","upper",True))]
        result=self.run_graph(shadings=[{"mode":"region","trees":[num(-1),num(1),num(-2),x],"constraints":constraints}])
        self.assertEqual(["solid","dashed","dashed","solid"],result["shadings"][0]["boundaryStyles"])
        for line in result["shadings"][0]["boundary"]:
            for px,py in filter(None,line):self.assertTrue(-1<=px<=1 and -2<=py<=px+1e-9)
        band={"mode":"band","trees":[x,num(2)],"xBounds":[{"side":"lower","tree":num(-1),"strict":True},
                {"side":"upper","tree":num(1),"strict":False}],"yBounds":[{"side":"upper","tree":num(0),"strict":True}]}
        shade=self.run_graph(shadings=[band])["shadings"][0]
        self.assertEqual(["solid","solid","dashed","dashed"],shade["boundaryStyles"])
        dashed=list(filter(None,shade["boundary"][2]))
        self.assertGreater(len(dashed),10)
        for px,py in dashed:self.assertEqual(0,py)
        self.assertEqual([[-1.,-1.],[-1.,0.]],shade["boundary"][-1])
        # A repeated inclusive constraint must not paint over a strict boundary.
        shade=self.run_graph(shadings=[{"mode":"region","trees":[num(1),num(1),num(1),num(1)],
            "constraints":[{"axis":axis,"side":"upper","strict":strict} for axis,strict in
                           (("x",True),("x",False),("y",True),("y",False))]}])["shadings"][0]
        for line,style in zip(shade["boundary"],shade["boundaryStyles"]):
            if style=="solid":self.assertFalse(any(point is not None for point in line))
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
