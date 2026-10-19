"""Information criteria follow the model selected by marginal ML fitting."""
import math
import unittest
from test_advanced_statistics import run


class GlmmInformationCriteriaTests(unittest.TestCase):
    def assert_information_criteria(self,result,count,n):
        deviance=-2*float(result['log likelihood'])
        self.assertAlmostEqual(float(result['AIC']),deviance+2*count,places=8)
        self.assertAlmostEqual(float(result['BIC']),deviance+math.log(n)*count,places=8)

    def test_intercept_zero_variance_and_poisson_boundaries_match_glm(self):
        rows=[[g,t,v] for g in range(1,6) for t,v in enumerate([1,2,1,3,2])]
        glm=run('poissonreg',[[t,v] for _,t,v in rows])
        for family in ('poisson','nbinom'):
            for points in (1,15):
                with self.subTest(family=family,points=points):
                    result=run('glmm',rows,family,points)
                    self.assertEqual(float(result['random intercept variance']),0)
                    if family=='nbinom':
                        self.assertEqual(float(result['dispersion alpha (NB2)']),0)
                    self.assert_information_criteria(result,2,len(rows))
                    self.assertAlmostEqual(float(result['log likelihood']),float(glm['log likelihood']),places=8)
                    self.assertAlmostEqual(float(result['AIC']),float(glm['AIC']),places=8)

    def test_intercept_retains_only_selected_variance_and_dispersion_parameters(self):
        cases=[
            ('poisson boundary',[[g,t,v+10*(g%3)] for g in range(1,10) for t,v in enumerate([1,2,1,3,2])],True,False,3),
            ('zero variance NB2',[[g,t,v] for g in range(1,6) for t,v in enumerate([0,0,1,0,9,0,1,0,7])],False,True,3),
            ('interior NB2',[[g,t,v*(1 if g<4 else 5)] for g in range(1,7) for t,v in enumerate([1,2,1,3,2])],True,True,4),
        ]
        for label,rows,random,nb,count in cases:
            with self.subTest(model=label):
                result=run('glmm',rows,'nbinom',1)
                self.assertEqual(float(result['random intercept variance'])>0,random)
                self.assertEqual(float(result['dispersion alpha (NB2)'])>0,nb)
                self.assert_information_criteria(result,count,len(rows))

    def test_slope_poisson_boundary_excludes_nb2_dispersion_parameter(self):
        rows=[[g,t,round(math.exp(3+.5*(g%3-1)+.4*(g%4-1.5)*t))] for g in range(1,13) for t in range(-2,3)]
        result=run('glmm',rows,'nbinom',1,[],'offset','likelihood',1)
        self.assertEqual(float(result['dispersion alpha (NB2)']),0)
        self.assertEqual(int(result['singular fit']),0)
        self.assert_information_criteria(result,5,len(rows))


if __name__=='__main__': unittest.main()
