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


if __name__=='__main__': unittest.main()
