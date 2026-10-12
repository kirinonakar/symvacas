"""Approximate Gaussian CSS Wald inference in natural coefficient coordinates."""
import math
import mpmath as mp
from calc_shared import MathError, require
from calc_advanced_common import normal_p


def drift_inference(beta, residuals, burn, scale, p, q, P, near_boundary, drift_period=1):
    """Use the joint residual Jacobian, including AR and MA uncertainty.

    Normalized CSS covariance is sigma² (J'J)^-1. Differencing intercept c
    and mean change c / ((1-sum(phi)) (1-sum(Phi))) are separate quantities.
    Wald intervals use the delta method and are approximate near boundaries.
    """
    errors = residuals(beta)[burn:]
    n, k = len(errors), len(beta)
    sigma2 = math.fsum(v*v for v in errors)/n
    derivatives = []
    for i, value in enumerate(beta):
        step = 1e-5*max(1., abs(value))
        left, right = beta[:], beta[:]
        left[i] -= step
        right[i] += step
        low, high = residuals(left)[burn:], residuals(right)[burn:]
        derivatives.append([(b-a)/(2*step) for a, b in zip(low, high)])
    norms = [math.sqrt(math.fsum(v*v for v in column)) for column in derivatives]
    require(all(v > 0 and math.isfinite(v) for v in norms), 'Drift inference is not identifiable')
    normalized = [[v/norm for v in column] for column, norm in zip(derivatives, norms)]
    information = mp.matrix([[math.fsum(a*b for a, b in zip(left, right))
                              for right in normalized] for left in normalized])
    require(min(mp.eigsy(information, eigvals_only=True)) > 1e-10,
            'Drift inference is not identifiable')
    inverse = information**-1
    covariance = mp.matrix([[sigma2*inverse[i,j]/(norms[i]*norms[j]) for j in range(k)] for i in range(k)])
    ordinary = 1-math.fsum(beta[:p])
    seasonal = 1-math.fsum(beta[p+q:p+q+P])
    require(ordinary*seasonal > 0, 'Drift inference is not identifiable')
    drift = scale*beta[-1]/(ordinary*seasonal*drift_period)
    gradient = [0.]*k
    for i in range(p): gradient[i] = drift/ordinary
    for i in range(p+q, p+q+P): gradient[i] = drift/seasonal
    gradient[-1] = scale/(ordinary*seasonal*drift_period)
    vector = mp.matrix(gradient)
    drift_variance = float((vector.T*covariance*vector)[0])
    intercept_variance = float(covariance[k-1,k-1])*scale*scale
    require(all(v > 0 and math.isfinite(v) for v in (drift_variance, intercept_variance)),
            'Drift inference is not identifiable')
    critical = float(mp.sqrt(2)*mp.erfinv(mp.mpf('.95')))
    note = 'Approximate Gaussian Wald inference with joint AR/MA/intercept covariance; near-boundary intervals and p values may be unreliable.' if near_boundary else 'Approximate Gaussian Wald inference with joint AR/MA/intercept covariance.'

    def row(estimate, variance):
        se = math.sqrt(variance)
        values = {'Estimate': estimate, 'SE': se, 'Lower 95% CI': estimate-critical*se,
                  'Upper 95% CI': estimate+critical*se, 'p value': normal_p(estimate/se), 'Inference': note}
        require(all(math.isfinite(v) for v in values.values() if isinstance(v, (int, float))),
                'Drift inference exceeds the numeric range')
        return values

    return row(scale*beta[-1], intercept_variance), row(drift, drift_variance)
