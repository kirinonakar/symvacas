"""Independent SciPy references for the D'Agostino-Pearson normality test."""
import json
from pathlib import Path
import scipy
from scipy import stats

samples = {
    'minimum_n': [2, 8, 0, 4, 1, 9, 9, 0],
    'ordinary': [2, 8, 0, 4, 1, 9, 9, 0, 3, 5, 6, 2, 7, 4, 1, 8, 3, 6, 5, 10, 4],
    'skewed': [0]*20 + [1]*10 + [2]*5 + [5, 10, 30],
    'negative_skew': [0]*20 + [-1]*10 + [-2]*5 + [-5, -10, -30],
    # Exercises the signed cube root in the kurtosis transform.
    'two_point': [0]*21 + [1]*20,
    'heavy_tail': [0]*100 + [1, -1, 2, -2, 500],
}
cases = []
for label, values in samples.items():
    result = stats.normaltest(values)
    cases.append(dict(label=label, values=values, K2=float(result.statistic),
                      p=float(result.pvalue), skew_z=float(stats.skewtest(values).statistic),
                      kurt_z=float(stats.kurtosistest(values).statistic)))
# The analytic skew transform is zero for exactly symmetric data. SciPy 1.18.1
# skewtest replaces an exact zero with 1, so use its kurtosis component alone.
values = list(range(21))
kurt_z = float(stats.kurtosistest(values).statistic)
cases.append(dict(label='symmetric', values=values, K2=kurt_z**2,
                  p=float(stats.chi2.sf(kurt_z**2, 2)), skew_z=0., kurt_z=kurt_z))
target = Path(__file__).resolve().parents[1]/'tests/fixtures/normaltest_reference.json'
target.write_text(json.dumps({'reference': 'SciPy '+scipy.__version__+
    ' normaltest/skewtest/kurtosistest; exact symmetric skew z = 0 analytically',
    'cases': cases}, indent=2)+'\n', encoding='utf-8')
