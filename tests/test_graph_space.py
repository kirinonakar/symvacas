"""Spatial domains through the actual Kotlin parser and shared dispatcher."""
import json
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

    def test_affine_singular_parameters_keep_undefined_samples(self):
        tree={'kind':'list','args':[{'kind':'binary','value':'/','args':[{'kind':'symbol','value':'t'},{'kind':'symbol','value':'a'}]},{'kind':'symbol','value':'t'},{'kind':'number','value':'0'}]}
        result=self.graph(SPACE+' {0<t<1}',trees=[tree],parameters={'a':0})
        self.assertTrue(result['ok'],result.get('error'))
        self.assertTrue(result['spaceCurves'][0])
        self.assertTrue(all(point is None for point in result['spaceCurves'][0]))


if __name__=='__main__':unittest.main()
