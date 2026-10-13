"""Column-wise t comparisons using the existing test and assumption estimators."""
import sympy as s
from calc_shared import MathError, require


def column_t_tests(engine, name, args, tail):
    from calc_statistics import statistical_test, _shapiro_wilk
    from calc_advanced_inference import calculate
    require(len(args) == 4 or name == 'ttest2' and len(args) == 5,
            'Column t tests expect a null difference, two column lists, batch and optional method')
    left, right = args[1:3]
    require(isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)) and left and
            len(left) == len(right) and all(isinstance(sample, (list, tuple)) for sample in list(left)+list(right)),
            'Choose matching lists of columns for both groups')
    method = str(args[4]) if len(args) == 5 else 'welch'
    require(method in ('welch', 'student'), 'Choose welch or student for the independent t test')
    comparisons, checks, errors = [], [], []
    paired = name == 'ttestpaired'
    require(not paired or all(len(xs) == len(ys) for xs,ys in zip(left,right)), 'Paired columns require matching complete pairs')
    def decision(p): return 'yes' if p >= s.Rational(5, 100) else 'no'
    for index, (xs, ys) in enumerate(zip(left, right)):
        row = {'Column': s.Integer(index), 'mean1': s.nan, 'mean2': s.nan, 'diff': s.nan, 'p-value': s.nan,
               'n': s.Integer(len(xs) if paired else len(xs)+len(ys)), 'Significant': 'unavailable',
               'normality': 'unavailable', 'equal var': 'Not applicable' if paired else 'unavailable'}
        try:
            require(all(getattr(v, 'is_real', False) is True and getattr(v, 'is_finite', False) is True for v in list(xs)+list(ys)),
                    'The selected value column requires finite real numbers')
            row['mean1'] = s.Add(*xs)/len(xs) if xs else s.nan
            row['mean2'] = s.Add(*ys)/len(ys) if ys else s.nan
            row['diff'] = row['mean1']-row['mean2']
            sample_args = [args[0], xs, ys]+([s.Symbol(method)] if not paired else [])
            sample_nodes = [{'kind': 'number'}, {'kind': 'list'}, {'kind': 'list'}]+([{'kind': 'symbol', 'value': method}] if not paired else [])
            if tail != 'both':
                sample_args.append(s.Symbol(tail));sample_nodes.append({'kind': 'symbol', 'value': tail})
            result = statistical_test(engine, name, sample_args, sample_nodes)
            row['p-value'] = result['p value']
            row['Significant'] = 'yes' if result['p value'] < s.Rational(5, 100) else 'no'
        except (MathError, ValueError, TypeError, ZeroDivisionError, OverflowError) as error:
            errors.append({'Column': s.Integer(index), 'Reason': str(error)})
        normal_samples = [('Differences', [x-y for x,y in zip(xs,ys)])] if paired and len(xs) == len(ys) else [('1',xs),('2',ys)]
        normal_results = []
        for label, sample in normal_samples:
            try:
                _, p, _ = _shapiro_wilk(sample)
                status = decision(p)
                checks.append({'Column': s.Integer(index), 'Check': 'Shapiro–Wilk', 'Sample': label,
                               'p-value': s.Float(str(p), min(engine.precision, 15)), 'Result': status})
                normal_results.append(status)
            except (MathError, ValueError, TypeError, ZeroDivisionError, OverflowError) as error:
                checks.append({'Column': s.Integer(index), 'Check': 'Shapiro–Wilk', 'Sample': label,
                               'p-value': s.nan, 'Result': 'unavailable', 'Reason': str(error)})
                normal_results.append('unavailable')
        row['normality'] = 'no' if 'no' in normal_results else 'yes' if all(v == 'yes' for v in normal_results) else 'unavailable'
        if not paired:
            try:
                variance = calculate(engine, 'levene', [xs, ys])
                row['equal var'] = decision(variance['p'])
                checks.append({'Column': s.Integer(index), 'Check': 'Brown–Forsythe', 'Sample': 'Across samples',
                               'p-value': variance['p'], 'Result': row['equal var']})
            except (MathError, ValueError, TypeError, ZeroDivisionError, OverflowError) as error:
                checks.append({'Column': s.Integer(index), 'Check': 'Brown–Forsythe', 'Sample': 'Across samples',
                               'p-value': s.nan, 'Result': 'unavailable', 'Reason': str(error)})
        comparisons.append(row)
    result = {'Comparisons': comparisons, 'Assumption checks': checks, 'Unavailable comparisons': errors,
              'Method': 'paired' if paired else method}
    engine.statistics_full_tables = result
    preview = {key: value[:50] if isinstance(value, list) else value for key,value in result.items()}
    if any(len(value) > 50 for value in result.values() if isinstance(value, list)):
        preview['Output note'] = 'Plain Output previews up to 50 rows per table; the formatted report and Copy include all rows.'
    return preview
