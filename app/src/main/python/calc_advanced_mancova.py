"""Portable one-factor MANCOVA with common slopes and partial effect tests."""
import math
import mpmath as mp
from calc_shared import MathError, require
from calc_advanced_common import table, integer, number, mean, dot
from calc_advanced_linear import least_squares
from calc_advanced_manova import multivariate_tests
from calc_statistics import _f_sf, _quantile, _t_cdf


def calculate(engine, name, a):
    # Columns are group, c covariates, then two or more responses.
    rows = table(a[0], 4, 4)
    c = integer(a[1], 1, len(rows[0])-3) if len(a) > 1 else 1
    level = number(a[2]) if len(a) > 2 else .95
    check = integer(a[3], 0, 1) if len(a) > 3 else 1
    require(0 < level < 1, 'Confidence level must be between 0 and 1')
    groups = sorted(set(row[0] for row in rows))
    n, g, p = len(rows), len(groups), len(rows[0])-c-1
    require(g >= 2, 'Choose at least two groups')
    require(all(sum(row[0] == group for row in rows) >= 2 for group in groups),
            'At least two observations per group are required')
    centers = [mean(values) for values in zip(*(row[1:c+1] for row in rows))]
    scales = [math.sqrt(math.fsum((row[j+1]-center)**2 for row in rows)/n) for j, center in enumerate(centers)]
    require(all(v > 0 and math.isfinite(v) for v in scales), 'Covariates must vary with finite scale')
    z = [[(value-center)/scale for value, center, scale in zip(row[1:c+1], centers, scales)] for row in rows]
    design = [[1.]+[float(row[0] == group) for group in groups[1:]]+values for row, values in zip(rows, z)]
    responses = [row[c+1:] for row in rows]
    response_centers = [mean(values) for values in zip(*responses)]
    target = [[value-center for value, center in zip(row, response_centers)] for row in responses]

    def fit(x):
        fits = [least_squares(x, list(values)) for values in zip(*target)]
        beta = mp.matrix([item[0] for item in fits]).T
        residual = mp.matrix([[target[i][j]-fits[j][3][i] for j in range(p)] for i in range(n)])
        return beta, fits[0][1], residual.T*residual

    beta, covariance, e = fit(design)
    df = n-beta.rows
    # Congruent response scaling improves numerical conditioning without
    # changing any multivariate statistic or the original-unit output tables.
    require(all(e[j,j] > 0 for j in range(p)), 'Positive residual variation is required')
    scaling = mp.diag([1/mp.sqrt(e[j,j]) for j in range(p)])

    def hypothesis(b, cov, indices):
        contrast = mp.zeros(len(indices), b.rows)
        for i, j in enumerate(indices): contrast[i,j] = 1
        estimate = contrast*b
        return estimate.T*(contrast*cov*contrast.T)**-1*estimate

    def tests(error, h, q, residual_df):
        return multivariate_tests(scaling*error*scaling, scaling*h*scaling, q, residual_df)

    effects = [('Group', list(range(1, g)))]+[('x'+str(j+1), [g+j]) for j in range(c)]
    multivariate, univariate = [], []
    for term, indices in effects:
        h = hypothesis(beta, covariance, indices)
        multivariate.extend(dict(Term=term, **item) for item in tests(e, h, len(indices), df))
        for j in range(p):
            ss, error = max(0., float(h[j,j])), float(e[j,j])
            f = ss/len(indices)/(error/df)
            univariate.append({'Term':term, 'Response':'response:'+str(j+1), 'SS':ss,
                               'df':len(indices), 'F':f, 'p':float(_f_sf(f, len(indices), df)),
                               'partial eta2':ss/(ss+error)})
    with mp.workdps(max(25, engine.precision+10)):
        critical = float(_quantile(lambda t: _t_cdf(t, df), (1+level)/2, engine, 0, 4))
    adjusted = []
    for group in groups:
        at = [1.]+[float(group == other) for other in groups[1:]]+[0.]*c
        weight = float((mp.matrix([at])*covariance*mp.matrix(at))[0])
        sample = [row for row, original in zip(responses, rows) if original[0] == group]
        for j in range(p):
            estimate = response_centers[j]+dot(at, list(beta[:,j]))
            se = math.sqrt(max(0., weight*float(e[j,j])/df))
            adjusted.append({'group':'group:'+format(group, '.15g'), 'Response':'response:'+str(j+1),
                             'n':len(sample), 'raw mean':mean([row[j] for row in sample]),
                             'adjusted mean':estimate, 'SE':se, 'Lower CI':estimate-critical*se, 'Upper CI':estimate+critical*se})
    result = {'n':n, 'groups':g, 'covariates':c, 'responses':p, 'df residual':df, 'confidence level':level,
              'Multivariate tests':multivariate, 'Univariate follow-up tests':univariate, 'Adjusted means':adjusted,
              'Covariate reference values':[{'term':'x'+str(j+1), 'mean':v} for j,v in enumerate(centers)],
              'Error SSCP':e.tolist(),
              'Assumptions':'One categorical factor, independent complete rows, linear common covariate slopes, multivariate normal errors and equal group error covariance. Full-rank design and nonsingular residual covariance required. Partial tests adjust each effect for all others. Roy F is an upper bound. Univariate follow-up p values and adjusted-mean confidence intervals are unadjusted for multiplicity. A slope-test p value below the chosen significance level indicates that at least one covariate effect differs between groups. Examine group-specific covariate effects before interpreting common-slope adjusted means.'}
    if check:
        full = [row+[row[k]*row[g+j] for k in range(1, g) for j in range(c)] for row in design]
        try:
            full_beta, full_covariance, full_e = fit(full)
            indices = list(range(beta.rows, full_beta.rows))
            h = hypothesis(full_beta, full_covariance, indices)
            result['Slope homogeneity'] = tests(full_e, h, len(indices), n-full_beta.rows)
        except MathError as error:
            result['Slope homogeneity'] = {'status':'unavailable', 'reason':str(error)}
    engine.note += ' One-factor MANCOVA; partial multivariate tests and adjusted means at pooled covariate means. Follow-up p values and intervals are unadjusted for multiplicity.'
    return result
