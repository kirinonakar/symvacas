"""Independent SciPy filter/least-squares and statsmodels impulse references.

Development only: neither dependency is shipped in the portable engine.
"""
import json
from pathlib import Path
import numpy as np
from scipy.signal import lfilter
from scipy.optimize import least_squares
from statsmodels.tsa.arima_process import arma_impulse_response
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
rng = np.random.default_rng(17)
cases = []
for seasonal, drift in ((False, False), (True, False), (False, True)):
    s = 4 if seasonal else 1
    ar = np.polynomial.polynomial.polymul([1, -.48], [1, 0, 0, 0, -.3] if seasonal else [1])
    ma = np.polynomial.polynomial.polymul([1, .35], [1, 0, 0, 0, .25] if seasonal else [1])
    z = lfilter(ma, ar, rng.normal(size=700))[500:]
    if drift: z += 3
    # Reference SARIMA includes both ordinary and seasonal integration.
    difference = np.polynomial.polynomial.polymul([1, -1], [1, 0, 0, 0, -1]) if seasonal else np.array([1., -1.]) if drift else np.array([1.])
    y = lfilter([1], difference, z)
    if seasonal:
        data = np.diff(y)[s:] - np.diff(y)[:-s]
    elif drift:
        data = np.diff(y)
    else:
        data = y
    burn = 5 if seasonal else 1

    def polynomials(beta):
        a = np.polynomial.polynomial.polymul([1, -beta[0]], [1, 0, 0, 0, -beta[2]] if seasonal else [1])
        b = np.polynomial.polynomial.polymul([1, beta[1]], [1, 0, 0, 0, beta[3]] if seasonal else [1])
        return a, b

    def residual(beta):
        a, b = polynomials(beta)
        drive = lfilter(a, [1], data)-(beta[-1] if drift else 0)
        drive[:burn] = 0
        return lfilter([1], b, drive)

    coefficient_count = 4 if seasonal else 2
    fits = [least_squares(lambda beta: residual(beta)[burn:], list(np.full(coefficient_count, initial))+([float(np.mean(data))*(1-initial)] if drift else []),
                          bounds=([- .98]*coefficient_count+([-np.inf] if drift else []),[.98]*coefficient_count+([np.inf] if drift else [])),
                          ftol=1e-12, xtol=1e-12, gtol=1e-12) for initial in (0, .2, -.2)]
    fit = min(fits, key=lambda item: item.cost)
    a, b = polynomials(fit.x)
    errors = residual(fit.x)
    n = len(data)-burn
    variance = float(np.mean(errors[burn:]**2))
    past, innovations = list(data), list(errors)
    for _ in range(8):
        t = len(past)
        past.append((fit.x[-1] if drift else 0)-sum(a[j]*past[t-j] for j in range(1, len(a))) + sum(b[j]*innovations[t-j] for j in range(1, len(b))))
        innovations.append(0.)
    forecast = past[len(data):]
    if seasonal:
        history = list(np.diff(y))
        for value in forecast:
            history.append(value+history[-s])
        differences = history[len(np.diff(y)):]
        history = list(y)
        for value in differences:
            history.append(value+history[-1])
        forecast = history[len(y):]
    elif drift:
        history = list(y)
        for value in forecast: history.append(value+history[-1])
        forecast = history[len(y):]
    psi = arma_impulse_response(np.polynomial.polynomial.polymul(a, difference), b, leads=8)
    k = len(fit.x)+1
    loglik = -.5*n*(np.log(2*np.pi)+1+np.log(variance))
    cases.append({'name': 'sarima' if seasonal else 'arima', 'data': y.tolist(),
                  'order': [1, 1 if seasonal or drift else 0, 1], 'seasonal': [1, 1, 1, s] if seasonal else None,
                  'trend': 'constant' if drift else 'none',
                  'coefficients': fit.x.tolist(), 'forecast': list(map(float, forecast)),
                  'standardError': np.sqrt(variance*np.cumsum(psi**2)).tolist(),
                  'variance': variance, 'aic': float(-2*loglik+2*k)})
    if drift:
        covariance = variance*np.linalg.inv(fit.jac.T@fit.jac)
        estimate = fit.x[-1]/(1-fit.x[0])
        gradient = np.array([estimate/(1-fit.x[0]),0,1/(1-fit.x[0])])
        se = float(np.sqrt(gradient@covariance@gradient))
        cases[-1]['driftInference'] = {'Estimate':float(estimate),'SE':se,'Lower 95% CI':float(estimate-norm.ppf(.975)*se),
                                     'Upper 95% CI':float(estimate+norm.ppf(.975)*se),'p value':float(2*norm.sf(abs(estimate)/se))}
(ROOT/'tests/fixtures/timeseries_reference.json').write_text(json.dumps(cases, indent=2)+'\n', encoding='utf-8')
