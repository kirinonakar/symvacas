"""Portable C-SVC and epsilon-SVR with deterministic pairwise dual optimization.

Predictors use population standard deviations. The response is never scaled, so
C and epsilon retain the usual summed-loss SVM meaning in response units.
Formulations: https://www.csie.ntu.edu.tw/~cjlin/papers/libsvm.pdf, section 2.
"""
import math
import random
from types import SimpleNamespace

import sympy as s

from calc_limits import within_limit
from calc_machine_learning import _data, _report, classification_metrics
from calc_shared import require


def _solve(kernel, target, lower, upper, epsilon, tolerance=1e-6, limit=100000):
    """Minimize .5*b'Kb - y'b + epsilon*|b|, sum(b)=0, with box bounds.

    Select the most violating feasible pair using one-sided L1 derivatives;
    minimize its piecewise quadratic exactly, including zero-curvature cases.
    """
    n = len(target)
    beta = [0.0]*n
    gradient = [-v for v in target]
    for iteration in range(limit+1):
        up = [(gradient[k]+(epsilon if beta[k] >= 0 else -epsilon), k)
              for k in range(n) if beta[k] < upper[k]]
        down = [(gradient[k]+(epsilon if beta[k] > 0 else -epsilon), k)
                for k in range(n) if beta[k] > lower[k]]
        low_score, i = min(up)
        high_score, j = max(down)
        violation = max(0.0, high_score-low_score)
        if violation <= tolerance:
            return beta, -(low_score+high_score)/2, iteration, violation
        require(iteration < limit, "SVM did not converge; adjust C or kernel parameters")
        lo = max(lower[i]-beta[i], beta[j]-upper[j])
        hi = min(upper[i]-beta[i], beta[j]-lower[j])
        curvature = max(0.0, kernel[i][i]+kernel[j][j]-2*kernel[i][j])
        slope = gradient[i]-gradient[j]
        knots = sorted(set([lo, hi]+[v for v in (-beta[i], beta[j]) if lo <= v <= hi]))
        candidates = list(knots)
        if curvature > 0:
            for left, right in zip(knots, knots[1:]):
                middle = (left+right)/2
                sign_i = 1 if beta[i]+middle >= 0 else -1
                sign_j = 1 if beta[j]-middle >= 0 else -1
                candidates.append(min(right, max(left, -(slope+epsilon*(sign_i-sign_j))/curvature)))
        def change(step):
            return slope*step+.5*curvature*step*step+epsilon*(
                abs(beta[i]+step)+abs(beta[j]-step)-abs(beta[i])-abs(beta[j]))
        step = min(candidates, key=change)
        require(step != 0 and math.isfinite(step),
                "SVM optimization stalled; adjust C or data scale")
        beta[i] += step
        beta[j] -= step
        # Snap exact breakpoints/bounds, avoiding tiny infeasible rounding drift.
        beta[i] = min(upper[i], max(lower[i], beta[i]))
        beta[j] = min(upper[j], max(lower[j], beta[j]))
        for k in range(n):
            gradient[k] += step*(kernel[k][i]-kernel[k][j])


def _cross_validation(rows, labels, options):
    """Stratified held-out predictions; preprocessing is refit within each fold."""
    groups = [[i for i, y in enumerate(labels) if y == label] for label in (0, 1)]
    folds = min(5, *(len(group) for group in groups))
    if folds < 2:
        return {"available": False, "reason": "Cross-validation requires at least two observations in each class."}
    rng = random.Random(0)
    assignment = [0]*len(rows)
    for group in groups:
        rng.shuffle(group)
        for i, index in enumerate(group):
            assignment[index] = i % folds
    predicted = [0]*len(rows)
    for fold in range(folds):
        training = [row for i, row in enumerate(rows) if assignment[i] != fold]
        model = SimpleNamespace()
        fit_svm(model, training, "svc", options, validation=False, diagnostics=False)
        for i, row in enumerate(rows):
            if assignment[i] == fold:
                predicted[i] = model.regression_predict(row[:-1])
    metrics = classification_metrics(labels, predicted)
    return {"available": True, "method": "Stratified cross-validation", "folds": folds, "seed": 0,
            "n": len(rows), "accuracy": metrics['accuracy'], "confusionMatrix": metrics['confusionMatrix'],
            "predictions": [{"row": i+1, "fold": assignment[i]+1, "observed": int(labels[i]),
                             "predicted": predicted[i]} for i in range(len(rows))]}


def fit_svm(engine, rows, mode, options=None, *, validation=True, diagnostics=True):
    xs, ys = _data(rows)
    n, p = len(xs), len(xs[0])
    require(within_limit(n, 500), "SVM supports at most 500 observations")
    classification = mode == "svc" or mode == "svm" and set(ys).issubset({0, 1})
    if classification:
        require(set(ys) == {0, 1}, "SVM classification requires both 0 and 1 in the response")
    options = [s.Symbol("rbf"), s.Integer(1), s.Symbol("auto"), s.Rational(1, 10)] if options is None else options
    require(isinstance(options, list) and len(options) == 4,
            "SVM options must be [kernel,C,gamma,epsilon]")
    kernel_name, cost, gamma, epsilon = options
    kernel_name = str(kernel_name)
    require(kernel_name in ("linear", "rbf"), "SVM kernel must be linear or rbf")
    def numeric(value, positive, label):
        require(getattr(value, "is_real", False) and value.is_finite,
                label+" must be a finite real number")
        result = float(value)
        require(math.isfinite(result) and (result > 0 if positive else result >= 0),
                label+(" must be positive" if positive else " must be nonnegative"))
        return result
    cost = numeric(cost, True, "SVM C")
    gamma = 1.0/p if str(gamma) == "auto" else numeric(gamma, True, "SVM gamma")
    epsilon = numeric(epsilon, False, "SVM epsilon")
    origins = xs[0]
    offsets = [[row[j]-origins[j] for j in range(p)] for row in xs]
    means = [math.fsum(row[j]/n for row in offsets) for j in range(p)]
    columns = [[row[j]-means[j] for row in offsets] for j in range(p)]
    peaks = [max(map(abs, col)) for col in columns]
    scales = [peak*math.sqrt(math.fsum((v/peak)**2/n for v in col)) if peak else 1.0
              for col, peak in zip(columns, peaks)]
    require(all(math.isfinite(v) for v in means+scales), "SVM data range is too large")
    def transform(row):
        require(len(row) == p and all(math.isfinite(float(v)) for v in row),
                "SVM prediction requires one finite value per predictor")
        return [(float(row[j])-origins[j]-means[j])/scales[j] for j in range(p)]
    normalized = [transform(row) for row in xs]
    def kernel(a, b):
        if kernel_name == "linear":
            return math.fsum(x*y for x, y in zip(a, b))
        return math.exp(-gamma*math.fsum((x-y)**2 for x, y in zip(a, b)))
    matrix = [[0.0]*n for _ in range(n)]
    for i in range(n):
        for j in range(i+1):
            matrix[i][j] = matrix[j][i] = kernel(normalized[i], normalized[j])
    # Center y to keep SVR optimization stable under response translations.
    origin = 0.0 if classification else ys[0]
    target = [2*y-1 for y in ys] if classification else [y-origin for y in ys]
    require(all(math.isfinite(v) for v in target), "SVM response range is too large")
    lower = [0.0 if y == 1 else -cost for y in ys] if classification else [-cost]*n
    upper = [cost if y == 1 else 0.0 for y in ys] if classification else [cost]*n
    beta, intercept, iterations, violation = _solve(matrix, target, lower, upper, 0.0 if classification else epsilon)
    support = [i for i, b in enumerate(beta) if b != 0]
    def decision(row):
        point = transform(row)
        value = origin+intercept+math.fsum(beta[i]*kernel(normalized[i], point) for i in support)
        require(math.isfinite(value), "SVM prediction exceeds numeric range")
        return value
    scores = [decision(row) for row in xs]
    fitted = [int(v >= 0) for v in scores] if classification else scores
    coefficients = []
    if kernel_name == "linear":
        weights = [math.fsum(beta[i]*normalized[i][j] for i in support)/scales[j] for j in range(p)]
        constant = math.fsum([origin, intercept]+[-w*(o+m) for w, o, m in zip(weights, origins, means)])
        require(all(math.isfinite(v) for v in [constant]+weights), "SVM coefficients exceed numeric range")
        coefficients = [constant]+weights
    report = _report(engine, ys, fitted, "svm", coefficients)
    report.update(task="classification" if classification else "regression", kernel=kernel_name,
                  C=cost, gamma=gamma if kernel_name == "rbf" else None,
                  epsilon=None if classification else epsilon, standardized=True,
                  supportVectors=len(support), iterations=iterations, kktViolation=violation,
                  converged=True, evaluation="training")
    if classification:
        for key in ("rSquared", "rmse", "sse"):
            report.pop(key, None)
        report.update(classification_metrics(ys, scores, threshold=0.0), scoreType="decision")
        for row, score in zip(report["residuals"], scores):
            row["decisionScore"] = str(score)
            row["supportVector"] = row["row"]-1 in support
        if diagnostics:
            from calc_svm_plot import decision_plot
            report["decisionPlot"] = decision_plot(xs, ys, scores, set(support), decision)
            names = ["x" if p == 1 else "x"+str(j+1) for j in range(p)]
            number = lambda v: format(v, '.17g')
            equation = {"variables": names, "intercept": coefficients[0] if kernel_name == 'linear' else intercept,
                        "scales": scales, "supportTerms": []}
            if kernel_name == 'linear':
                equation['expression'] = number(coefficients[0])+''.join(
                    '+('+number(w)+')*'+name for w, name in zip(coefficients[1:], names))
            else:
                equation['supportTerms'] = [{'row': i+1, 'coefficient': beta[i], 'coordinates': xs[i]} for i in support]
                equation['formula'] = 'f(x) = b + Σᵢ aᵢ exp(−γ Σⱼ ((xⱼ − vᵢⱼ)/sⱼ)²)'
                if len(support)*p <= 24:
                    equation['expression'] = number(intercept)+''.join(
                        '+('+number(beta[i])+')*exp(-('+number(gamma)+')*('+
                        '+'.join('(('+name+'-('+number(xs[i][j])+'))/('+number(scales[j])+'))^2'
                                 for j, name in enumerate(names))+'))' for i in support)
            report['decisionEquation'] = equation
        if validation:
            report['crossValidation'] = _cross_validation(rows, ys, options)
        report["warnings"].append("SVM decision scores are not probabilities; score >= 0 predicts class 1.")
    if kernel_name == 'linear':
        report["warnings"].append("SVM predictors are standardized; linear coefficients use original predictor units. Classification coefficients describe the decision score.")
    else:
        report["warnings"].append("SVM predictors are standardized.")
    report["warnings"].append("Training metrics do not estimate performance on unseen data.")
    engine.regression_predict = (lambda row: int(decision(row) >= 0)) if classification else decision
    return s.Symbol("SVC" if classification else "SVR")
