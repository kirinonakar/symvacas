"""Spatial domains through the actual Kotlin parser and shared dispatcher."""
import json
import math
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app/src/main/python'))
from calc_engine import dispatch

TREES={case['source']:case['tree'] for case in json.loads((ROOT/'build/math-cases.json').read_text(encoding='utf-8'))}
SPACE='[(1-2*t)*cos(k*pi/2+a),(1-2*t)*sin(k*pi/2+a),k*pi/8]'


class SpaceCurveTests(unittest.TestCase):
    def graph(self,source,**options):
        request={'action':'graph','graphKind':'space','angle':'RAD','trees':[TREES[source]],'min':-1,'max':1,**options}
        return json.loads(dispatch(json.dumps(request)))

    def test_reported_curve_domain_and_six_member_animated_family(self):
        for suffix,ks,names in [(' {0<t<1}',[.3],['a','k']),(' {0<t<1, k=[0,0.1,0.2,0.3,0.4,0.5]}',[0,.1,.2,.3,.4,.5],['a']),(' {0<t<1} {k=[0,0.5]}',[0,.5],['a'])]:
            for a in (0,.7):
                result=self.graph(SPACE+suffix,parameters={'a':a,'k':.3,'t':.5},variables={'k':{'kind':'number','value':'99'}})
                self.assertTrue(result['ok'],result.get('error'))
                self.assertEqual(names,result['parameters'])
                self.assertEqual(len(ks),len(result['spaceCurves']))
                for k,curve,positions in zip(ks,result['spaceCurves'],result['curveParameters']):
                    self.assertGreater(len(curve),100)
                    self.assertEqual(len(curve),len(positions))
                    for (x,y,z),t in zip(curve,positions):
                        self.assertTrue(0<t<1,t)
                        self.assertAlmostEqual((1-2*t)*math.cos(k*math.pi/2+a),x)
                        self.assertAlmostEqual((1-2*t)*math.sin(k*math.pi/2+a),y)
                        self.assertAlmostEqual(k*math.pi/8,z)

    def test_named_curve_narrow_domain_is_sampled_directly(self):
        result=self.graph('C(t)=(t,k,a) {0.1234<t<0.1235, k=[0,1]}')
        self.assertTrue(result['ok'],result.get('error'))
        self.assertEqual(['a'],result['parameters'])
        for k,curve in enumerate(result['spaceCurves']):
            self.assertGreater(len(curve),100)
            self.assertTrue(all(.1234<t<.1235 and y==k and z==1 for t,y,z in curve))

    def test_closed_and_disjoint_domains_empty_families_and_row_local_parameters(self):
        result=self.graph('[t,k,a] {0<=t<=1,k=[0,1]} {t<k}')
        self.assertTrue(result['ok'],result.get('error'))
        self.assertEqual([],result['spaceCurves'][0])
        self.assertEqual(0,result['spaceCurves'][1][0][0])
        self.assertTrue(all(point[0]<1 for point in result['spaceCurves'][1]))
        result=self.graph('[t,k,a] {t^2>0.25,k=[0,1]}')
        self.assertTrue(result['ok'],result.get('error'))
        for curve in result['spaceCurves']:
            self.assertIn(None,curve)
            for first,last in zip(curve,curve[1:]):
                if first and last:self.assertGreater(first[0]*last[0],0)
        empty=self.graph('[t,k,a] {2<t<3,k=[0,1]}')
        self.assertEqual([[],[]],empty['spaceCurves'])
        cross=self.graph('[t,k,a] {0<t<1,k=[0,1],a=[2,3]}')
        self.assertEqual([],cross['parameters'])
        self.assertEqual([(0,2),(0,3),(1,2),(1,3)],[(curve[0][1],curve[0][2]) for curve in cross['spaceCurves']])
        mixed=self.graph(SPACE+' {0<t<1, k=[0,0.1,0.2,0.3,0.4,0.5]}',trees=[TREES[SPACE+' {0<t<1, k=[0,0.1,0.2,0.3,0.4,0.5]}'],TREES[SPACE+' {0<t<1}']])
        self.assertEqual(['a','k'],mixed['parameters'])
        self.assertEqual(7,len(mixed['spaceCurves']))

    def test_invalid_lists_fail_clearly(self):
        for suffix in ('k=[]','k=[t]','k=[oo]'):
            result=self.graph('[t,k,a] {0<t<1,'+suffix+'}')
            self.assertFalse(result['ok'])
            self.assertIn('Curve parameter lists',result['error'])


if __name__=='__main__':unittest.main()
