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

def bundle(**definitions):return {'kind':'list','args':[equation(sym(name),body) for name,body in definitions.items()]}

def torus_tree():
    radius=add(num(2),binary('*',num(.35),call('sin',binary('-',binary('*',num(6),sym('u')),binary('*',num(3),sym('t'))))))
    return bundle(R=radius,x=binary('*',add(sym('R'),call('cos',sym('v'))),call('cos',sym('u'))),
                  y=binary('*',add(sym('R'),call('cos',sym('v'))),call('sin',sym('u'))),z=call('sin',sym('v')))

def waves_tree():
    r=lambda sign:call('sqrt',add(binary('^',binary(sign,sym('x'),num(2)),num(2)),binary('^',sym('y'),num(2))))
    wave=lambda name:binary('/',call('sin',binary('-',binary('*',num(4),sym(name)),binary('*',num(5),sym('t')))),add(num(1),binary('*',num(.2),sym(name))))
    return bundle(r1=r('-'),r2=r('+'),z=add(wave('r1'),wave('r2')))

def vortex_tree(frequency=5):
    r2=add(binary('^',sym('x'),num(2)),binary('^',sym('y'),num(2)))
    phase=binary('-',binary('-',binary('*',num(frequency),call('atan2',sym('y'),sym('x'))),binary('*',num(2),call('sqrt',r2))),binary('*',num(3),sym('t')))
    return equation(sym('z'),binary('*',call('exp',binary('*',num(-.08),r2)),call('sin',phase)))

class Graph3dTests(unittest.TestCase):

    def test_two_parameter_torus_with_local_radius_and_animation(self):
        for t in (0,.7,2):
            result=self.run_graph(torus_tree(),parameters={'t':t},surfaceUMin=0,surfaceUMax=2*math.pi,surfaceVMin=-math.pi,surfaceVMax=math.pi)
            self.assertEqual(['t'],result['parameters'])
            self.assertTrue(result['parametricSurface'])
            for j,row in enumerate(result['surface']):
                v=-math.pi+2*math.pi*j/20
                for i,(x,y,z) in enumerate(row):
                    u=2*math.pi*i/20;radius=2+.35*math.sin(6*u-3*t)+math.cos(v)
                    for expected,actual in zip((radius*math.cos(u),radius*math.sin(u),math.sin(v)),(x,y,z)):
                        self.assertAlmostEqual(expected,actual,delta=1e-12)
        stored={name:num(99) for name in ('u','v','x','y','R')}
        fresh=self.run_graph(torus_tree(),parameters={'t':.7})
        shadowed=self.run_graph(torus_tree(),parameters={'t':.7},variables=stored)
        self.assertEqual(fresh['surface'],shadowed['surface'])

    def test_local_distance_helpers_produce_two_animated_sources(self):
        for t in (0,.6):
            result=self.run_graph(waves_tree(),parameters={'t':t})
            self.assertEqual(['t'],result['parameters'])
            self.assertNotIn('implicitSurface',result)
            for row in result['surface']:
                for x,y,z in row:
                    expected=sum(math.sin(4*r-5*t)/(1+.2*r) for r in (math.hypot(x-2,y),math.hypot(x+2,y)))
                    self.assertAlmostEqual(expected,z,delta=1e-12)

    def test_surface_helpers_are_local_and_forward_references_resolve(self):
        tree=bundle(z=sym('b'),b=add(sym('a'),sym('x')),a=num(2))
        result=self.run_graph(tree,trees=[tree,equation(sym('z'),sym('a'))])
        self.assertEqual(['a'],result['parameters'])
        self.assertEqual([],result['surfaces'][0]['parameters'])
        self.assertTrue(all(z==1 for row in result['surfaces'][1]['surface'] for x,y,z in row))
        for tree in (bundle(a=sym('b'),b=sym('a'),z=sym('a')),bundle(x=sym('u'),z=sym('v')),bundle(u=num(2),z=sym('u'))):
            result=json.loads(dispatch(json.dumps({'action':'graph','graphKind':'surface','trees':[tree],'min':-2,'max':2})))
            self.assertFalse(result['ok'])

    def test_parametric_ranges_and_undefined_coordinate_samples(self):
        tree={'kind':'list','args':[sym('u'),sym('v'),binary('/',num(1),sym('u'))]}
        result=self.run_graph(tree,surfaceUMin=-1,surfaceUMax=1,surfaceVMin=2,surfaceVMax=3)
        self.assertEqual([],result['parameters'])
        self.assertTrue(all(row[10] is None for row in result['surface']))
        self.assertEqual([-1,2,-1],result['surface'][0][0])
        self.assertEqual([1,3,1],result['surface'][-1][-1])
        invalid=json.loads(dispatch(json.dumps({'action':'graph','graphKind':'surface','trees':[tree],'min':-2,'max':2,'surfaceUMin':1,'surfaceUMax':0})))
        self.assertFalse(invalid['ok'])
        wrapped=equation(call('S',sym('u'),sym('v')),{'kind':'tuple','args':[sym('u'),sym('v'),num(0)]})
        self.assertEqual([],self.run_graph(wrapped)['parameters'])

    def test_vortex_center_uses_fine_angular_rings_without_filling_the_singularity(self):
        for t in (0,.8):
            result=self.run_graph(vortex_tree(),parameters={'t':t},surfaceSamples=48)
            self.assertTrue(result['angularSurface'])
            self.assertEqual(['t'],result['parameters'])
            mesh=result['surface']
            self.assertLess(math.hypot(*mesh[1][0][:2]),.002)
            for row in mesh:
                for x,y,z in row:
                    r=math.hypot(x,y)
                    self.assertGreater(r,0)
                    self.assertAlmostEqual(math.exp(-.08*r*r)*math.sin(5*math.atan2(y,x)-2*r-3*t),z,delta=1e-12)
            # At the innermost ring, angular interpolation error is below 1.3%
            # of the unit amplitude, independent of the direction of approach.
            for a,b in zip(mesh[0],mesh[0][1:]):
                x,y=(a[0]+b[0])/2,(a[1]+b[1])/2;r=math.hypot(x,y)
                actual=math.exp(-.08*r*r)*math.sin(5*math.atan2(y,x)-2*r-3*t)
                self.assertLess(abs(actual-(a[2]+b[2])/2),.013)
        branch=self.run_graph(vortex_tree(.5),parameters={'t':0})['surface'][0]
        self.assertGreater(abs(branch[0][2]-branch[-1][2]),1.9)
        pole=add(vortex_tree()['args'][1],binary('/',num(1),sym('x')))
        holes=self.run_graph(pole,parameters={'t':0})['surface']
        self.assertTrue(all(sum(point is None for point in row)==2 for row in holes))

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
