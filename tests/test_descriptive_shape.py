"""Public functions, summary reports and independent central-moment references."""
import json
import unittest
from test_advanced_statistics import evaluate, tree
from calc_engine import dispatch
import symvacas_catalog as calc


class DescriptiveShapeTests(unittest.TestCase):
    def test_corrected_and_moment_reference_values(self):
        # SciPy's published skew example; kurtosis from exact central moments:
        # mean=33/8, m2=887/64, m4=1049549/4096.
        values='[2,8,0,4,1,9,9,0]'
        references={'skewness':(0.3305821804079746,0.2650554122698573),
                    'kurtosis':(-8255576/3933845,-1310758/786769)}
        for function,(corrected,moment) in references.items():
            self.assertAlmostEqual(float(evaluate(f'{function}({values})')['decimal']),corrected,places=11)
            self.assertAlmostEqual(float(evaluate(f'{function}({values},0)')['decimal']),moment,places=11)
        self.assertEqual(calc.skewness([1,2,3,4,5]),0)
        self.assertEqual(str(calc.kurtosis([1,2,3,4,5])),'-6/5')

    def test_summary_retains_modes_and_undefined_shape_without_failing(self):
        self.assertEqual(evaluate('mode([1,1.0,2,2,3])')['exact'],'[1, 2]')
        self.assertEqual(evaluate('mode([3,1,2])')['exact'],'[1, 2, 3]')
        self.assertEqual(evaluate('mode([7])')['exact'],'[7]')
        result=evaluate('stats([1,1,2,2,3])')
        report=result['statisticsReport']
        titles=[section['title'] for section in report['sections']]
        self.assertIn('mode(s)',titles)
        rows=[row for section in report['sections'] for row in section['rows']]
        self.assertTrue(any(row[0]=='skewness (sample corrected)' for row in rows))
        for values in ('[1]','[1,2]','[5,5,5,5]'):
            self.assertIn('nan',evaluate(f'stats({values})')['exact'].lower())

    def test_shape_domains_and_extreme_units(self):
        for source in ('skewness([])','skewness([1,2])','kurtosis([1,2,3])',
                       'kurtosis([1,1,1,1])','skewness([1,2,3],2)',
                       'skewness([1,2,oo])','kurtosis([1,2,3,i])'):
            self.assertFalse(json.loads(dispatch(json.dumps({'tree':tree(source)})))['ok'],source)
        baseline=float(calc.skewness([2,8,0,4,1,9,9,0]))
        import sympy as s
        for scale in (s.Rational(1,10)**150,s.Integer(10)**150):
            self.assertAlmostEqual(float(calc.skewness([scale*v for v in [2,8,0,4,1,9,9,0]])),baseline,places=14)


if __name__=='__main__': unittest.main()
