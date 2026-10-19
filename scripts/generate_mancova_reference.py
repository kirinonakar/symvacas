"""Independent statsmodels MANCOVA references; not a runtime dependency."""
import json
from pathlib import Path
import numpy as np
from scipy.stats import t
from statsmodels.multivariate.manova import MANOVA
from statsmodels.api import OLS


def main():
    rng = np.random.default_rng(71019)
    cases = []
    for sizes, c, p in [([9, 11, 8], 1, 2), ([13, 10, 15], 2, 3), ([10, 14], 2, 2)]:
        groups = np.repeat(np.arange(len(sizes)), sizes)
        n, g = len(groups), len(sizes)
        covariates = rng.normal(size=(n, c))+groups[:, None]*.4
        responses = covariates@rng.normal(size=(c, p))+groups[:, None]*np.linspace(.5, 1.5, p)+rng.normal(size=(n, p))
        rows = np.column_stack([groups+1, covariates, responses]).tolist()
        design = np.column_stack([np.ones(n), *[(groups == i).astype(float) for i in range(1, g)], covariates])
        terms = [('Group', list(range(1, g)))]+[('x'+str(i+1), [g+i]) for i in range(c)]
        contrasts = [(name, np.eye(design.shape[1])[indices]) for name, indices in terms]
        mv = MANOVA(responses, design).mv_test(contrasts)
        expected = []
        for term_index, (name, _) in enumerate(terms):
            for i, values in enumerate(mv.results[name]['stat'].to_numpy()[[1,0,2,3]]):
                for key, value in zip(['Statistic','df1','df2','F','p'], values):
                    expected.append([['Multivariate tests', term_index*4+i, key], float(value)])
        full = np.column_stack([design, *[design[:, k]*covariates[:, j] for k in range(1, g) for j in range(c)]])
        slope = MANOVA(responses, full).mv_test([('Slope', np.eye(full.shape[1])[design.shape[1]:])])
        for i, values in enumerate(slope.results['Slope']['stat'].to_numpy()[[1,0,2,3]]):
            for key, value in zip(['Statistic','df1','df2','F','p'], values):
                expected.append([['Slope homogeneity', i, key], float(value)])
        for j in range(p):
            fit = OLS(responses[:, j], design).fit()
            for ti, (_, indices) in enumerate(terms):
                f = fit.f_test(np.eye(design.shape[1])[indices])
                expected.extend([[['Univariate follow-up tests', ti*p+j, 'F'], float(f.fvalue)],
                                 [['Univariate follow-up tests', ti*p+j, 'p'], float(f.pvalue)]])
            for group in range(g):
                at = np.r_[1., [float(group == k) for k in range(1, g)], covariates.mean(axis=0)]
                estimate = float(at@fit.params)
                se = float(np.sqrt(at@fit.cov_params()@at))
                critical = t.ppf(.975, fit.df_resid)
                for key, value in [('adjusted mean', estimate), ('SE', se), ('Lower CI', estimate-critical*se), ('Upper CI', estimate+critical*se)]:
                    expected.append([['Adjusted means', group*p+j, key], float(value)])
        cases.append(dict(name=f'{g} groups {c} covariates {p} responses', arguments=[rows, c, .95, 1], expected=expected, tolerance=2e-7))
    path = Path(__file__).resolve().parents[1]/'tests/fixtures/mancova_reference.json'
    path.write_text(json.dumps({'source':'statsmodels MANOVA.mv_test and OLS, NumPy seed 71019', 'cases':cases}, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
