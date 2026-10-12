"""Portable multiplicative ARIMA/SARIMA with conditional Gaussian estimation.

Initial innovations are zero; the first max(AR lag, MA lag) differenced
observations are conditioned on. Forecast variance uses the integrated
impulse response, conditional on estimated parameters and initial history.
"""
import math
import mpmath as mp
from calc_shared import MathError, require
from calc_advanced_common import vector, integer, number, option
from calc_advanced_optimize import minimize
from calc_timeseries_calendar import time_calendar
from calc_timeseries_inference import drift_inference


def multiply(a, b):
    result = [0.] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            result[i+j] += x*y
    return result


def coefficients(raw):
    """Partial autocorrelations map unconstrained coordinates to stable AR."""
    values = []
    for x in raw:
        reflection = .999999 * math.tanh(x)
        values = [v-reflection*values[-1-i] for i, v in enumerate(values)] + [reflection]
    return values


def polynomial(values, spacing=1, sign=-1):
    result = [1.] + [0.] * (len(values)*spacing)
    for i, value in enumerate(values):
        result[(i+1)*spacing] = sign*value
    return result


def impulse(ar, ma, length):
    values = []
    for i in range(length):
        values.append((ma[i] if i < len(ma) else 0.) -
                      sum(ar[j]*values[i-j] for j in range(1, min(i+1, len(ar)))))
    return values


def calculate(engine, name, args):
    y = vector(args[0], 4)
    order = vector(args[1], 3) if len(args) > 1 else [1, 1, 0]
    require(len(order) == 3, 'ARIMA order must be [p,d,q]')
    p, d, q = [integer(v, 0, cap, capacity=True) for v, cap in zip(order, (5, 2, 5))]
    seasonal = name == 'sarima'
    season = vector(args[2], 4) if seasonal and len(args) > 2 else [0, 1, 1, 12] if seasonal else [0, 0, 0, 1]
    require(len(season) == 4, 'Seasonal order must be [P,D,Q,s]')
    P, D, Q = [integer(v, 0, cap, capacity=True) for v, cap in zip(season[:3], (3, 2, 3))]
    period = integer(season[3], 2 if seasonal else 1, 365, capacity=True)
    at = 3 if seasonal else 2
    horizon = integer(args[at], 1, 500, capacity=True) if len(args) > at else 12
    level = number(args[at+1]) if len(args) > at+1 else .95
    require(0 < level < 1, 'Prediction level must be between 0 and 1')
    trend = option(args, at+2, 'auto')
    dates = time_calendar(args[at+3], len(y), horizon) if len(args) > at+3 else None
    require(trend in ('auto', 'none', 'constant'), 'Choose auto, none or constant')
    require(trend != 'constant' or d+D <= 1, 'Constant/drift requires total differencing at most 1')
    include_constant = trend == 'constant'
    diff = [1.]
    stages = []
    z = y[:]
    for lag in [1]*d + [period]*D:
        require(len(z) > lag, 'Not enough observations for differencing')
        stages.append((lag, z[:]))
        z = [z[i]-z[i-lag] for i in range(lag, len(z))]
        diff = multiply(diff, [1.] + [0.]*(lag-1) + [-1.])
    burn = max(p+P*period, q+Q*period)
    count = len(z)-burn
    ar_ma_parameters = p+q+P+Q
    require(count > ar_ma_parameters+int(include_constant)+2, 'Not enough observations after differencing and model lags')
    require(not (P or D or Q) or len(y) >= 2*period, 'Seasonal models need at least two complete periods')
    scale = max(abs(v) for v in z)
    require(scale > 0, 'Differenced series has no innovation variance')
    values = [v/scale for v in z]
    center = sum(values)/len(values)
    require(sum((v-center)**2 for v in values) > 1e-20,
            'Differenced series has no innovation variance')

    def unpack(raw):
        ar = multiply(polynomial(coefficients(raw[:p])),
                      polynomial(coefficients(raw[p+q:p+q+P]), period))
        # Negating stable AR coefficients gives an invertible MA polynomial.
        ma = multiply(polynomial(coefficients(raw[p:p+q]), sign=-1),
                      polynomial(coefficients(raw[p+q+P:p+q+P+Q]), period, -1))
        return ar, ma, raw[-1] if include_constant else 0.

    def residuals_for(ar, ma, constant):
        residuals = [0.]*len(values)
        for t in range(burn, len(values)):
            fitted = constant - sum(ar[j]*values[t-j] for j in range(1, len(ar))) + \
                     sum(ma[j]*residuals[t-j] for j in range(1, len(ma)))
            residuals[t] = values[t]-fitted
        return residuals

    def innovations(raw):
        return residuals_for(*unpack(raw))

    def natural_innovations(beta):
        ar = multiply(polynomial(beta[:p]), polynomial(beta[p+q:p+q+P], period))
        ma = multiply(polynomial(beta[p:p+q], sign=1), polynomial(beta[p+q+P:p+q+P+Q], period, 1))
        return residuals_for(ar, ma, beta[-1])

    def loss(raw):
        require(all(math.isfinite(v) for v in raw), 'Time-series optimization exceeds the numeric range')
        errors = innovations(raw)[burn:]
        mse = sum(v*v for v in errors)/count
        return math.log(max(mse, 1e-300))

    def objective(raw):
        value = loss(raw)
        gradient = []
        for i, v in enumerate(raw):
            step = 1e-5*max(1., abs(v))
            left, right = raw[:], raw[:]
            left[i] -= step
            right[i] += step
            gradient.append((loss(right)-loss(left))/(2*step))
        return value, gradient

    choices = [False, True] if trend == 'auto' and d+D <= 1 else [include_constant]
    models = []
    selection_rows = []
    for include_constant in choices:
        parameters = ar_ma_parameters+int(include_constant)
        if count <= parameters+2:
            continue
        candidates = []
        if not ar_ma_parameters:
            raw = [center] if include_constant else []
            candidates.append((raw, loss(raw), 0))
        elif q == Q == 0 and (p == 1 and P == 0 or p == 0 and P == 1):
            # Conditional AR(1) is constrained least squares, including the
            # intercept. Solve it directly rather than saturating BFGS/tanh.
            lag = 1 if p else period
            x, response_values = values[burn-lag:-lag], values[burn:]
            mx = sum(x)/count if include_constant else 0.
            my = sum(response_values)/count if include_constant else 0.
            denominator = sum((v-mx)**2 for v in x)
            if denominator > 1e-20:
                phi = sum((a-mx)*(b-my) for a, b in zip(x, response_values))/denominator
                reflection = max(-1+1e-9, min(1-1e-9, phi/.999999))
                raw = [math.atanh(reflection)]
                if include_constant:
                    raw.append(my-.999999*reflection*mx)
                candidates.append((raw, loss(raw), 0))
        else:
            # Multiple starts matter especially for multiplicative ARMA fits.
            for shift in (0., .25, -.25):
                initial = [shift]*ar_ma_parameters + ([center] if include_constant else [])
                if include_constant:
                    initial[-1] = center*sum(unpack(initial)[0])
                try:
                    candidates.append(minimize(initial, objective, tolerance=2e-6, maximum=300))
                except MathError:
                    pass
        label = 'Drift' if include_constant and d+D == 1 else 'Constant' if include_constant else 'None'
        if not candidates:
            selection_rows.append({'Intercept / drift': label, 'Status': 'Fit did not converge'})
            continue
        raw, score, iterations = min(candidates, key=lambda item: item[1])
        k = parameters+1
        # Same differencing/burn-in for both candidates, so the omitted
        # likelihood constant (including scale) cancels in their comparison.
        criterion = count*score+2*k+2*k*(k+1)/(count-k-1)
        candidate_aicc = criterion+count*(math.log(2*math.pi)+1+2*math.log(scale))
        models.append((criterion, raw, iterations, include_constant, parameters))
        selection_rows.append({'Intercept / drift': label, 'Conditional AICc': candidate_aicc, 'Status': 'Converged'})
    require(models, 'Time-series fit did not converge; simplify the orders or check the data')
    _, raw, iterations, include_constant, parameters = min(models, key=lambda item: item[0])
    max_reflection = max((abs(.999999*math.tanh(v)) for v in raw[:ar_ma_parameters]), default=0.)
    near_boundary = max_reflection >= .999
    ar, ma, constant = unpack(raw)
    residuals = [v*scale for v in innovations(raw)]
    sigma2 = sum(v*v for v in residuals[burn:])/count
    require(sigma2 > 0 and math.isfinite(sigma2), 'Innovation variance is undefined')
    constant *= scale
    future_z = z[:]
    future_errors = residuals[:]
    for _ in range(horizon):
        t = len(future_z)
        prediction = constant - sum(ar[j]*future_z[t-j] for j in range(1, len(ar))) + \
                     sum(ma[j]*future_errors[t-j] for j in range(1, len(ma)))
        future_z.append(prediction)
        future_errors.append(0.)
    forecasts = future_z[len(z):]
    for lag, history in reversed(stages):
        restored = history[:]
        for value in forecasts:
            restored.append(value+restored[-lag])
        forecasts = restored[len(history):]
    response = impulse(multiply(ar, diff), ma, horizon)
    critical = float(mp.sqrt(2)*mp.erfinv(level))
    variance = 0.
    forecast_rows = []
    for h, (estimate, weight) in enumerate(zip(forecasts, response), 1):
        variance += sigma2*weight*weight
        se = math.sqrt(variance)
        forecast_rows.append({'Time': len(y)+h, 'Horizon': h, 'Forecast': estimate,
                              'Standard error': se, 'Lower PI': estimate-critical*se,
                              'Upper PI': estimate+critical*se})
    require(all(math.isfinite(v) for row in forecast_rows for v in row.values()),
            'Forecast exceeds the numeric range; shorten the horizon or simplify the model')
    offset = len(y)-len(z)
    fitted_rows = [{'Time': offset+t+1, 'Observed': y[offset+t],
                    'Fitted': y[offset+t]-residuals[t], 'Residual': residuals[t]}
                   for t in range(burn, len(z))]
    errors = residuals[burn:]
    error_mean = sum(errors)/count
    denominator = sum((v-error_mean)**2 for v in errors)
    lags = min(count-1, max(10, 2*period if seasonal else 20))
    acf = [sum((errors[t]-error_mean)*(errors[t-lag]-error_mean) for t in range(lag, count))/denominator
           if denominator else 0. for lag in range(1, lags+1)]
    diagnostic_lag = min(lags, max(1, count//5), 2*period if seasonal else 10)
    lb = count*(count+2)*sum(acf[lag-1]**2/(count-lag) for lag in range(1, diagnostic_lag+1))
    df = diagnostic_lag-(p+q+P+Q)
    lb_p = float(mp.gammainc(df/2, lb/2, mp.inf, regularized=True)) if df > 0 else None
    loglik = -.5*count*(math.log(2*math.pi)+1+math.log(sigma2))
    k = parameters+1
    aic = -2*loglik+2*k
    coefficients_rows = []
    blocks = [('AR', raw[:p]), ('MA', raw[p:p+q]), ('Seasonal AR', raw[p+q:p+q+P]),
              ('Seasonal MA', raw[p+q+P:p+q+P+Q])]
    for title, block in blocks:
        for i, value in enumerate(coefficients(block), 1):
            coefficients_rows.append({'Parameter': title+' '+str(i),
                                      'Estimate': -value if 'MA' in title else value})
    if include_constant:
        coefficients_rows.append({'Parameter': 'Differenced intercept' if d+D else 'ARMA intercept',
                                  'Estimate': constant})
        if d+D == 1:
            beta = [row['Estimate'] for row in coefficients_rows[:-1]] + [raw[-1]]
            try:
                mean_change = constant/(sum(ar)*(1 if d == 1 else period))
            except (ZeroDivisionError, OverflowError):
                mean_change = None
            try:
                intercept_inference, mean_inference = drift_inference(beta, natural_innovations, burn, scale, p, q, P, near_boundary, 1 if d == 1 else period)
            except (MathError, ValueError, OverflowError, ZeroDivisionError):
                intercept_inference = {'SE': None, 'Lower 95% CI': None, 'Upper 95% CI': None, 'p value': None,
                                       'Inference': 'Joint coefficient covariance is singular or exceeds the numeric range; drift inference is unavailable.'}
                mean_inference = {'Estimate': mean_change, **intercept_inference}
            coefficients_rows[-1].update(intercept_inference)
            if p+P:
                coefficients_rows.append({'Parameter': 'Drift', **mean_inference})
            else:
                coefficients_rows[-1]['Parameter'] = 'Drift'
            coefficients_rows[-1]['Convention'] = 'Mean change per observation; distinct from the differenced ARMA intercept. Seasonal-only differencing divides the mean seasonal change by the seasonal period.'
    model = f'ARIMA({p},{d},{q})' + (f'({P},{D},{Q})[{period}]' if seasonal else '')
    engine.statistics_plots = [
        {'kind': 'timeseries', 'title': 'Time-series forecast', 'level': level,
         'observed': [[i+1, value] for i, value in enumerate(y)],
         'fitted': [[row['Time'], row['Fitted']] for row in fitted_rows],
         'forecast': [[len(y), y[-1]]] + [[row['Time'], row['Forecast']] for row in forecast_rows],
         'interval': [[row['Time'], row['Lower PI'], row['Upper PI']] for row in forecast_rows],
         'boundary': len(y), 'caption': 'Observed · fitted · forecast · shaded prediction interval'},
        {'kind': 'timeseries', 'title': 'Time-series residuals', 'boundary': None,
         'observed': [[row['Time'], row['Residual']] for row in fitted_rows],
         'fitted': [], 'forecast': [], 'interval': [], 'reference': 0.},
        {'kind': 'acf', 'title': 'Residual autocorrelation', 'values': acf,
         'bound': 1.96/math.sqrt(count), 'caption': 'Dashed bounds: approximate 95% white-noise limits'}]
    calendar_summary = {}
    if dates:
        labels = dates['labels']
        forecast_rows = [{'Date': labels[row['Time']-1], **row} for row in forecast_rows]
        fitted_rows = [{'Date': labels[row['Time']-1], **row} for row in fitted_rows]
        for plot in engine.statistics_plots[:2]:
            plot['timeLabels'] = labels
            plot['timeTickLabels'] = dates['ticks']
        calendar_summary = {'Calendar frequency': dates['frequency'], 'Calendar step': dates['step'],
                            'First date': labels[0], 'Last date': labels[len(y)-1]}
    engine.note = 'Conditional Gaussian fit; prediction intervals condition on estimated parameters.'
    selected_trend = 'Drift' if include_constant and d+D == 1 else 'Constant' if include_constant else 'None'
    for row in selection_rows:
        row['Selected'] = int(row['Intercept / drift'] == selected_trend)
    warnings = []
    if near_boundary:
        warnings.append('The stationary/invertible fit is close to a boundary. Forecasts are available, but coefficients and long-range intervals can be sensitive; inspect residuals and the differencing order.')
    # Plain Output has a strict display-size ceiling. The report and Copy retain
    # all rows, and the plots retain every observation and forecast coordinate.
    engine.statistics_full_tables = {'Forecasts': forecast_rows, 'Fitted values': fitted_rows}
    return {'Model': model, **calendar_summary, 'Estimation': 'Conditional Gaussian (zero initial innovations)',
            'Intercept / drift': selected_trend,
            'Fit status': 'Near boundary (forecasts available)' if near_boundary else 'Converged',
            **({'Automatic intercept / drift selection': selection_rows} if trend == 'auto' else {}),
            'Maximum absolute reflection coefficient': max_reflection,
            **({'Warnings': warnings} if warnings else {}),
            'Observations': len(y), 'Effective observations': count, 'Prediction level': level,
            'Forecast horizon': horizon, 'Innovation variance': sigma2, 'RMSE': math.sqrt(sigma2),
            'MAE': sum(abs(v) for v in errors)/count, 'Conditional log likelihood': loglik,
            'Conditional AIC': aic, 'Conditional AICc': aic+2*k*(k+1)/(count-k-1) if count>k+1 else None,
            'Conditional BIC': -2*loglik+k*math.log(count), 'Iterations': iterations,
            'Coefficients': coefficients_rows, 'Forecasts': forecast_rows[:50], 'Fitted values': fitted_rows[:50],
            'Output note': 'Plain Output previews up to 50 fitted/forecast rows; the formatted report and Copy include all rows.',
            'Residual diagnostics': [{'Lags': diagnostic_lag, 'Ljung–Box Q': lb,
                                      'df': df if df > 0 else None, 'p value': lb_p}],
            'Assumptions': ['Rows are equally spaced, ordered from oldest to newest; missing periods must be resolved before fitting.',
                            'After differencing, the series is stationary and innovations are uncorrelated with constant variance. Gaussian prediction intervals exclude parameter uncertainty.',
                            'Auto compares no intercept against an intercept (no differencing) or drift (one difference) using conditional AICc. Two or more differences exclude drift. Initial model lags are conditioned on, so fitted values start later.',
                            'Compare conditional information criteria only with the same differencing and effective observations. Residual ACF bounds are approximate; Ljung–Box uses lag count minus fitted AR/MA orders.']}
