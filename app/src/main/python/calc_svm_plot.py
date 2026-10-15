"""Shared SVC decision geometry in original predictor units."""
import math


def _domain(values):
    lo, hi = min(values), max(values)
    pad = (hi-lo)*.12 if hi > lo else max(1.0, abs(lo)*.05)
    return [lo-pad, hi+pad]


def regression_plots(xs, observed, fitted, support, predict, epsilon):
    """All-row SVR diagnostics; identity axes share limits and response units."""
    def points(xvalues, yvalues):
        return [{'row': i+1, 'x': x, 'y': y, 'support': i in support}
                for i, (x, y) in enumerate(zip(xvalues, yvalues))]
    limits = _domain(observed+fitted)
    comparison = {'kind': 'observedPredicted', 'xlim': limits, 'ylim': limits,
                  'points': points(observed, fitted), 'contours': [
                      {'level': 0, 'dashed': True, 'segments': [[[limits[0], limits[0]], [limits[1], limits[1]]]]}]}
    errors = [math.fsum([y, -f]) for y, f in zip(observed, fitted)]
    xlim = _domain(fitted)
    error = {'kind': 'predictionError', 'xlim': xlim, 'ylim': _domain(errors+[0]),
             'points': points(fitted, errors), 'contours': [
                 {'level': 0, 'segments': [[[xlim[0], 0], [xlim[1], 0]]]}]}
    plots = [comparison, error]
    if len(xs[0]) == 1:
        values = [row[0] for row in xs]
        xlim = _domain(values)
        curve = [[xlim[0]+(xlim[1]-xlim[0])*i/128, 0] for i in range(129)]
        for point in curve:
            point[1] = predict([point[0]])
        bounds = [[point[1]+direction*epsilon for point in curve] for direction in (-1, 1)]
        plots.append({'kind': 'regressionFit', 'xlim': xlim, 'ylim': _domain(observed+bounds[0]+bounds[1]),
                      'points': points(values, observed), 'curve': curve, 'epsilon': epsilon,
                      'contours': [{'level': direction, 'segments': [[
                          [curve[i][0], bound[i]], [curve[i+1][0], bound[i+1]]]
                          for i in range(len(curve)-1)]} for direction, bound in zip((-1, 1), bounds)]})
    return plots


def decision_plot(xs, labels, scores, support, decision):
    """One-dimensional score curve or a two-dimensional conditional slice.

    Use the same decision function as prediction. A fixed triangulation of each
    grid cell resolves saddle cells consistently for all three contour levels.
    """
    n, p = len(xs), len(xs[0])
    def domain(values):
        lo, hi = min(values), max(values)
        pad = (hi-lo)*.12 if hi > lo else max(1.0, abs(lo)*.05)
        return [lo-pad, hi+pad]
    xlim = domain([row[0] for row in xs])
    centers = [xs[0][j]+math.fsum((row[j]-xs[0][j])/n for row in xs) for j in range(p)]
    plot = {"kind": "score" if p == 1 else "boundary", "xlim": xlim,
            "features": list(range(min(p, 2))),
            "fixedFeatures": [{"index": j, "value": centers[j]} for j in range(2, p)],
            "points": [{"row": i+1, "x": row[0], "y": scores[i] if p == 1 else row[1],
                        "class": int(labels[i]), "support": i in support}
                       for i, row in enumerate(xs)], "contours": []}
    if p == 1:
        curve = [[xlim[0]+(xlim[1]-xlim[0])*i/128, 0] for i in range(129)]
        for point in curve:
            point[1] = decision([point[0]])
        plot["curve"] = curve
        plot["ylim"] = domain([-1, 1]+scores+[point[1] for point in curve])
        plot["contours"] = [{"level": level, "segments": [[[xlim[0], level], [xlim[1], level]]]}
                            for level in (-1, 0, 1)]
        return plot
    ylim = plot["ylim"] = domain([row[1] for row in xs])
    size = 49
    grid = []
    for j in range(size):
        line = []
        for i in range(size):
            x = xlim[0]+(xlim[1]-xlim[0])*i/(size-1)
            y = ylim[0]+(ylim[1]-ylim[0])*j/(size-1)
            line.append([x, y, decision([x, y]+centers[2:])])
        grid.append(line)
    for level in (-1, 0, 1):
        segments = []
        for j in range(size-1):
            for i in range(size-1):
                a, b, c, d = grid[j][i], grid[j][i+1], grid[j+1][i+1], grid[j+1][i]
                for triangle in ((a, b, c), (a, c, d)):
                    crossing = []
                    for start, end in zip(triangle, triangle[1:]+triangle[:1]):
                        if (start[2] < level) != (end[2] < level):
                            fraction = (level-start[2])/(end[2]-start[2])
                            crossing.append([start[k]+fraction*(end[k]-start[k]) for k in (0, 1)])
                    if len(crossing) == 2 and crossing[0] != crossing[1]:
                        segments.append(crossing)
        plot["contours"].append({"level": level, "segments": segments})
    return plot
