"""Public functions, summary reports and independent central-moment references."""
import unittest
from test_advanced_statistics import evaluate
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


if __name__=='__main__': unittest.main()
