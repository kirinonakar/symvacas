import collections
import json
import math
import pathlib
import sys
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'app/src/main/python'))
from calc_engine import dispatch

def num(value):return {'kind':'number','value':str(value)}
def sym(value):return {'kind':'symbol','value':value}
def binary(op,a,b):return {'kind':'binary','value':op,'args':[a,b]}
def call(name,*args):return {'kind':'call','value':name,'args':list(args)}
def equation(a,b):return {'kind':'relation','value':'=','args':[a,b]}
def add(*terms):
    result=terms[0]
    for term in terms[1:]:result=binary('+',result,term)
    return result

class Graph3dTests(unittest.TestCase):

    def run_graph(self,tree,kind='surface',**options):
        result=json.loads(dispatch(json.dumps({'action':'graph','graphKind':kind,'trees':[tree],
            'min':-2,'max':2,'surfaceYMin':-2,'surfaceYMax':2,'surfaceZMin':-2,'surfaceZMax':2,'surfaceSamples':20,**options})))
        self.assertTrue(result['ok'],result.get('error'))
        return result

    def test_sine_square_root_surface_preserves_real_domain(self):
        argument=add(*(binary('*',sym('a'),binary('^',sym(axis),num(2))) for axis in 'xy'))
        tree=call('sin',call('sqrt',argument))
        for a in (0,1,4):
            result=self.run_graph(tree,parameters={'a':a},surfaceSamples=48)
            self.assertEqual(49,len(result['surface']))
            for row in result['surface']:
                for x,y,z in row:self.assertAlmostEqual(math.sin(math.sqrt(a*(x*x+y*y))),z,delta=1e-12)
        for a in (1,5,20,100):
            options=dict(parameters={'a':a},min=-3,max=3,surfaceYMin=-3,surfaceYMax=3,surfaceSamples=96)
            web=self.run_graph(tree,**options)
            android=self.run_graph(tree,surfaceCompactGrid=True,**options)
            grid=android['surfaceGrid']
            decoded=[[[x,y,grid['z'][row][col]] if grid['z'][row][col] is not None else None for col,x in enumerate(grid['x'])] for row,y in enumerate(grid['y'])]
            self.assertEqual(web['surface'],decoded)
            self.assertEqual(web['surfaceSamples'],android['surfaceSamples'])
            self.assertEqual((web['zMin'],web['zMax']),(android['zMin'],android['zMax']))
            self.assertLess(len(json.dumps(android)),len(json.dumps(web))*.6)
        for count in (24,48):
            empty=self.run_graph(tree,parameters={'a':-1},surfaceSamples=count)
            self.assertEqual(1,sum(point is not None for row in empty['surface'] for point in row))

    def test_radial_sine_surface_extends_only_the_removable_center(self):
        radius_tree=add(*(binary('^',sym(axis),num(2)) for axis in 'xy'))
        argument=add(*(binary('*',sym('a'),binary('^',sym(axis),num(2))) for axis in 'xy'))
        tree=binary('/',call('sin',argument),radius_tree)
        for a in (1,2,-3,0,1e-12):
            result=self.run_graph(tree,parameters={'a':a},surfaceSamples=48)
            rings=result['surfaceRings']
            self.assertEqual(['a'],result['parameters'])
            self.assertEqual([0,a,0,1],rings[0])
            for radius,z,slope,count in rings:
                radius2=radius*radius
                self.assertAlmostEqual(a if radius2==0 else math.sin(a*radius2)/radius2,z,delta=1e-12)
                self.assertTrue(all(math.isfinite(v) for v in (radius,z,slope)))
        for a in (1,5,20,100,-20):
            result=self.run_graph(tree,parameters={'a':a},min=-10,max=10,surfaceYMin=-5,surfaceYMax=5,surfaceSamples=96)
            rings=result['surfaceRings']
            # The center is resolved at the oscillation scale, even far beyond
            # a uniform 96x96 grid, while response size stays bounded.
            self.assertLess(abs(a)*rings[1][0]**2,.4)
            self.assertLess(sum(r[3] for r in rings),8500)
            for p,q in zip(rings,rings[1:]):
                radius=(p[0]+q[0])/2
                expected=math.sin(a*radius*radius)/(radius*radius)
                self.assertLess(abs((p[1]+q[1])/2-expected)*200/(1.2173*abs(a)),1.5)
        # Direction-dependent limits and actual poles must remain undefined.
        for denominator in (radius_tree,binary('^',sym('x'),num(2))):
            result=self.run_graph(binary('/',call('sin',sym('x')),denominator))
            self.assertIsNone(result['surface'][10][10])

    def test_sphere_has_both_z_branches_and_a_closed_shared_vertex_mesh(self):
        squared=add(*(binary('^',sym(axis),num(2)) for axis in 'xyz'))
        tree=equation(squared,sym('a'))
        for a in (1,2):
            result=self.run_graph(tree,parameters={'a':a})
            vertices=result['surfaceVertices'];faces=result['surfaceTriangles']
            self.assertEqual(['a'],result['parameters']);self.assertTrue(faces)
            self.assertLess(min(p[2] for p in vertices),-.9*math.sqrt(a));self.assertGreater(max(p[2] for p in vertices),.9*math.sqrt(a))
            for point in vertices:self.assertAlmostEqual(a,sum(v*v for v in point),delta=1e-3)
            for point,normal in zip(vertices,result['surfaceNormals']):
                length=math.hypot(*point)
                self.assertAlmostEqual(1,math.hypot(*normal),delta=1e-12)
                self.assertGreater(sum(v*n/length for v,n in zip(point,normal)),1-1e-8)
            edges=collections.Counter(tuple(sorted((face[i],face[(i+1)%3]))) for face in faces for i in range(3))
            self.assertTrue(all(count==2 for count in edges.values()))
            self.assertLess(len(vertices),len(faces))

    def test_no_surface_and_undefined_cells_do_not_create_fake_faces(self):
        empty=self.run_graph(equation(sym('z'),binary('+',sym('z'),num(1))))
        self.assertEqual([],empty['surfaceTriangles'])
        tree=equation(add(binary('/',num(1),sym('x')),sym('y'),sym('z')),num(0))
        result=self.run_graph(tree)
        for face in result['surfaceTriangles']:
            xs=[result['surfaceVertices'][i][0] for i in face]
            self.assertFalse(min(xs)<0<max(xs))


if __name__=='__main__':unittest.main()
