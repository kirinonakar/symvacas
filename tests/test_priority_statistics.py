"""Independent numerical references and contracts for the six research extensions."""
import json
import math
import unittest
from test_advanced_statistics import ROOT, run, evaluate
from calc_shared import MathError

IDS=set('omega bayesttest bayesanova metaregression metasubgroup designpower designsize yuen trimmedanova winsorcor robustreg parametricsurvival'.split())


class PriorityStatisticsTests(unittest.TestCase):
    def test_independent_numerical_references(self):
        fixture=json.loads((ROOT/'tests/fixtures/priority_statistics_reference.json').read_text(encoding='utf8'))
        for case in fixture['cases']:
            with self.subTest(function=case['function'],options=case['arguments'][1:]):
                result=run(case['function'],*case['arguments'])
                for path,expected in case['expected']:
                    actual=result
                    for key in path:actual=actual[key]
                    self.assertAlmostEqual(float(actual),expected,delta=case['tolerance']*max(1,abs(expected)),msg=str(path))

    def test_public_examples_produce_report_plots_and_full_copy_rows(self):
        schema=json.loads((ROOT/'app/src/main/assets/advanced_statistics.json').read_text(encoding='utf8'))
        for definition in schema:
            if definition['id'] not in IDS:continue
            with self.subTest(analysis=definition['id']):
                result=evaluate(definition['example']);report=result['statisticsReport']
                self.assertEqual(report['analysis'],definition['id']);self.assertTrue(report['sections']);self.assertTrue(report['plots']);self.assertTrue(report['assumptions'])
                self.assertNotEqual(report['title'],definition['id'])
        # Predict every selected subject; the visible preview must not truncate copying.
        rows=[[i+1,0 if i%4==0 else 1] for i in range(110)]
        report=evaluate('parametricsurvival('+str(rows)+',exponential)')['statisticsReport']
        section=next(s for s in report['sections'] if s['title']=='Predicted survival times')
        self.assertEqual(len(section['rows']),100);self.assertEqual(len(section['copyRows']),110)

    def test_bayesian_direction_scaling_pairing_and_ordered_prefix(self):
        a=[1.,2,4,5,8,9];b=[3.,5,4,7,9,12]
        args=['independent',0,math.sqrt(.5),.95,6000,3,1]
        first=run('bayesttest',a,b,*args);repeat=run('bayesttest',a,b,*args);reverse=run('bayesttest',b,a,*args)
        self.assertEqual(first,repeat);self.assertAlmostEqual(float(first['BF10'])*float(first['BF01']),1,places=12)
        self.assertAlmostEqual(float(first['BF10']),float(reverse['BF10']),places=12)
        self.assertAlmostEqual(float(first['BF10']),float(run('bayesttest',[v*10+100 for v in a],[v*10+100 for v in b],*args)['BF10']),places=10)
        self.assertAlmostEqual(float(first['BF10']),float(first['Sequential evidence'][-1]['BF10']),places=10)
        paired=run('bayesttest',a,b,'paired',0,1,.95,4000,0,0)
        differences=run('bayesttest',[x-y for x,y in zip(a,b)],[],'onesample',0,1,.95,4000,0,0)
        self.assertAlmostEqual(float(paired['BF10']),float(differences['BF10']),places=12)
        key=next(k for k in first if k.startswith('Posterior standardized'))
        self.assertLess(float(first[key]['posterior mean']),0);self.assertGreater(float(reverse[key]['posterior mean']),0)
        with self.assertRaises(MathError):run('bayesttest',a,b[:-1],'paired')

    def test_subgroup_contrasts_are_joint_and_common_tau(self):
        rows=[[.1,.1,1],[.3,.1,1],[.2,.15,1],[.8,.1,2],[1.1,.15,2],[.9,.1,2]]
        result=run('metasubgroup',rows,'pm',.95,'hksj')
        self.assertEqual(len(result['Subgroups']),2);self.assertLess(float(result['Moderator test']['p']),.01)
        self.assertLess(float(result['Subgroups'][0]['estimate']),float(result['Subgroups'][1]['estimate']))
        scaled=run('metasubgroup',[[r[0]*10,r[1]*10,r[2]] for r in rows],'pm',.95,'hksj')
        self.assertAlmostEqual(float(result['Moderator test']['p']),float(scaled['Moderator test']['p']),places=12)
        with self.assertRaises(MathError):run('metaregression',[[r[0],r[1],1.] for r in rows])

    def test_raw_meta_summaries_preserve_moderators_after_exclusions(self):
        binary=[[0,20,0,20,2000],[12,100,20,100,2010],[8,80,15,90,2012],[25,150,40,160,2014],[4,60,10,65,2016]]
        generic=[]
        for a,na,b,nb,x in binary[1:]:
            generic.append([math.log(a/(na-a)/(b/(nb-b))),math.sqrt(1/a+1/(na-a)+1/b+1/(nb-b)),x])
        raw=run('metaregression',binary,'pm',.95,'hksj','oddsratio',.5);converted=run('metaregression',generic,'pm',.95,'hksj')
        self.assertEqual(int(raw['Excluded study count']),1);self.assertEqual([int(s['Study']) for s in raw['Studies']],[2,3,4,5])
        self.assertAlmostEqual(float(raw['coefficients'][1]['estimate']),float(converted['coefficients'][1]['estimate']),places=10)
        continuous=[[12,3,50,10,2.5,48,1],[15,4,60,12,3.5,55,1],[9,2,40,8,2.2,42,2],[11,3.2,65,9.5,3,62,2]]
        generic=[[m1-m2,math.sqrt(s1*s1/n1+s2*s2/n2),g] for m1,s1,n1,m2,s2,n2,g in continuous]
        raw=run('metasubgroup',continuous,'pm',.95,'hksj','md');converted=run('metasubgroup',generic,'pm',.95,'hksj')
        self.assertAlmostEqual(float(raw['Moderator test']['p']),float(converted['Moderator test']['p']),places=12)

    def test_yuen_reduces_to_welch_and_winsorization_retains_pairs(self):
        a=[1,2,3,4,5,7];b=[2,5,4,7,8,11]
        first=run('yuen',a,b,0);reverse=run('yuen',b,a,0)
        self.assertAlmostEqual(float(first['estimate']),-float(reverse['estimate']),places=12)
        self.assertAlmostEqual(float(first['p']),float(reverse['p']),places=12)
        positive=run('winsorcor',a,b,.2);negative=run('winsorcor',a,[-v for v in b],.2)
        self.assertAlmostEqual(float(positive['Winsorized correlation']),-float(negative['Winsorized correlation']),places=12)
        with self.assertRaises(MathError):run('yuen',a,b,.5)
        with self.assertRaises(MathError):run('winsorcor',[1,1,1,1],[1,2,3,4],.2)

    def test_minimal_sample_sizes_direction_and_null_power(self):
        for design,effect,baseline in [('z',.4,.5),('proportion',.65,.5),('proportion2',.65,.4),('variance',2.,.5)]:
            with self.subTest(design=design):
                result=run('designsize',design,effect,.8,.05,'two',baseline)
                self.assertGreaterEqual(float(result['power']),.8);self.assertLess(float(result['Power at n−1']),.8)
        for design,effect in [('z',0),('proportion',.5),('proportion2',.5),('variance',1)]:
            self.assertAlmostEqual(float(run('designpower',design,effect,60,.05,'two',.5)['power']),.05,places=10)
        with self.assertRaises(MathError):run('designsize','z',-.4,.8,.05,'greater')

    def test_survival_predictions_units_censoring_and_entry_validation(self):
        data=[[1,1],[2,0],[3,1],[4,1],[6,0],[7,1]]
        first=run('parametricsurvival',data,'exponential',.95,-1,5)
        # Intercept-only exponential ML rate = events / total exposure.
        expected=sum(row[0] for row in data)/sum(row[1] for row in data)
        self.assertAlmostEqual(float(first['Predicted survival times'][0]['Predicted mean time']),expected,places=8)
        scaled=run('parametricsurvival',[[t*10,e] for t,e in data],'exponential',.95,-1,50)
        self.assertAlmostEqual(float(first['Predicted survival times'][0]['Survival at prediction time']),float(scaled['Predicted survival times'][0]['Survival at prediction time']),places=9)
        for invalid in ([[0,1],[2,1],[3,1],[4,1]],[[1,0],[2,0],[3,0],[4,0]],[[1,1,1],[2,1,2],[3,1,3],[4,1,4]]):
            with self.assertRaises(MathError):run('parametricsurvival',invalid,'weibull',.95,2 if len(invalid[0])==3 else -1)


if __name__=='__main__':unittest.main()
