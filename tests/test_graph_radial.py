import math
import pathlib
import sys
import unittest

import sympy as s

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"app/src/main/python"))
from calc_graph_radial import radial_contour


class RadialContourTests(unittest.TestCase):
    def setUp(self):
        self.x,self.y,self.t = s.symbols("x y t",real=True)

    def expression(self,order=3):
        x,y,t = self.x,self.y,self.t
        real,imaginary = s.expand((x+s.I*y)**order).as_real_imag()
        return (x*x+y*y)**(order+1)-(real*s.cos(t)+imaginary*s.sin(t))**2

    def sample(self,expression,phase,view=(-2,2,-2,2)):
        return radial_contour(expression,self.x,self.y,{self.t:phase},*view)

    def test_petals_are_closed_at_the_origin_and_chords_resolve_the_inner_branches(self):
        for order in (1,2,3,5):
            expression = self.expression(order)
            for phase in (0,.7,math.pi/2):
                with self.subTest(order=order,phase=phase):
                    view = (-1.2,1.2,-.8,.8)
                    curve = self.sample(expression,phase,view)
                    self.assertIsNotNone(curve)
                    paths = [[]]
                    for point in curve:
                        if point is None: paths.append([])
                        else: paths[-1].append(point)
                    self.assertEqual(2*order,len(paths))
                    sx,sy = 800/(view[1]-view[0]),800/(view[3]-view[2])
                    for petal,path in enumerate(paths):
                        self.assertEqual([0.0,0.0],path[0])
                        self.assertEqual(path[0],path[-1])
                        for index in range(101):
                            # Independent dense polar reference, including both
                            # inner edges; residuals alone are weak near r=0.
                            offset = (index/100-.5)*math.pi/order
                            angle = phase/order+petal*math.pi/order+offset
                            radius = math.cos(order*offset)
                            point = (radius*math.cos(angle)*sx,radius*math.sin(angle)*sy)
                            def distance(a,b):
                                a = (a[0]*sx,a[1]*sy); b = (b[0]*sx,b[1]*sy)
                                dx,dy = b[0]-a[0],b[1]-a[1]
                                fraction = max(0,min(1,((point[0]-a[0])*dx+(point[1]-a[1])*dy)/(dx*dx+dy*dy)))
                                return math.hypot(point[0]-a[0]-fraction*dx,point[1]-a[1]-fraction*dy)
                            self.assertLess(min(distance(a,b) for a,b in zip(path,path[1:])),.21)


if __name__ == "__main__": unittest.main()
