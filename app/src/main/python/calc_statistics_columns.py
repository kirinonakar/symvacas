"""Combined reports for grouped numeric and categorical column tests."""
from types import SimpleNamespace
import sympy as s
from calc_shared import MathError, require

BATCH_TESTS = {'ztest2', 'chi2independence', 'fisherexact', 'mannwhitney', 'wilcoxon', 'kruskal', 'anova', 'welchanova'}
ERRORS = (MathError, ValueError, TypeError, ZeroDivisionError, OverflowError)


def column_tests(engine, name, args, nodes, tail, marker):
    from calc_statistics import statistical_test, _shapiro_wilk
    from calc_advanced_inference import calculate
    categorical = name in ('chi2independence', 'fisherexact')
    prefix = args[:3] if name == 'ztest2' else []
    matrices = args[3:marker] if prefix else args[:marker]
    options = args[marker+1:]
    require(len(matrices) >= 2 and all(isinstance(matrix, (list, tuple)) for matrix in matrices), 'Select at least two groups')
    count = len(matrices[0])
    require(count > 0 and all(len(matrix) == count and all(isinstance(sample, (list, tuple)) for sample in matrix) for matrix in matrices),
            'Choose matching lists of columns for each group')
    require(not categorical or len(matrices) == 2, 'Categorical batches require group and category columns')
    require(name not in ('ztest2', 'mannwhitney', 'wilcoxon') or len(matrices) == 2, 'Select two groups')
    require(not options or name == 'chi2independence' and len(options) == 1 and options[0] in (0, 1), 'Invalid column-test option')
    labels = engine.request.get('statisticsTermLabels', {})
    groups = len(matrices) if not categorical else max(2, len([key for key in labels if key.startswith('sample:')]))
    if categorical:
        require(all(getattr(code,'is_Integer',False) and code>=0 for column in matrices[0] for code in column), 'Group codes must be nonnegative integers')
        groups=max(groups,max((int(code)+1 for column in matrices[0] for code in column),default=0))
    comparisons, checks, errors, warnings, tables, supplements = [], [], [], [], [], []
    for index in range(count):
        samples = [list(matrix[index]) for matrix in matrices]
        proxy = SimpleNamespace(precision=engine.precision, note='', request=engine.request)
        probability = s.nan
        test_args = prefix+samples+options
        test_nodes = [{'kind':'list'} for _ in test_args]
        if tail != 'both':
            test_args = test_args+[s.Symbol(tail)];test_nodes.append({'kind':'symbol', 'value':tail})
        try:
            outcome = statistical_test(proxy, name, test_args, test_nodes)
            probability = outcome['p value']
            if not categorical and name in ('anova', 'welchanova', 'kruskal'):
                from calc_statistics_report import statistics_report
                from calc_statistics_diagnostics import companion_report
                extra = statistics_report(name, outcome, engine.precision, labels)
                companion_report(extra, name, outcome, (name, test_args, test_nodes), engine.precision, labels)
                supplements.append({'Column':index, 'report':extra})
        except ERRORS as error:
            errors.append({'Column':s.Integer(index), 'Reason':str(error)})
        significant = 'unavailable' if probability is s.nan else 'yes' if probability < s.Rational(5,100) else 'no'
        if categorical:
            group_codes, values = samples
            require(len(group_codes) == len(values), 'Category and group columns must have equal lengths')
            present_groups = sorted(set(group_codes))
            groups = max(groups, len(present_groups), max((int(value)+1 for value in present_groups), default=0))
            categories = sorted(set(values))
            binary = labels.get('batch:binary:'+str(index), 'yes' if categories and all(value in (0,1) for value in categories) else 'no') == 'yes'
            shown = [s.Integer(1)] if binary else categories
            totals = [sum(group == at for group in group_codes) for at in range(groups)]
            counts = [[sum(group == at and value == category for group,value in zip(group_codes,values)) for category in categories] for at in range(groups)]
            expected = [[s.Rational(total*sum(row[col] for row in counts),len(values)) if values else s.nan for col in range(len(categories))] for total in totals]
            tables.append({'Column':s.Integer(index), 'Categories':categories, 'Observed':counts, 'Expected':expected})
            if name == 'chi2independence' and expected and all(row for row in expected):
                flat = [value for total,row in zip(totals,expected) if total for value in row if value is not s.nan]
                if flat:
                    below5, below1 = sum(bool(value < 5) for value in flat), sum(bool(value < 1) for value in flat)
                    checks.append({'Column':s.Integer(index), 'Minimum expected':min(flat), 'Cells below 5':s.Integer(below5), 'Cells below 1':s.Integer(below1), 'Cells':s.Integer(len(flat))})
                    if below5:
                        warnings.append({'Column':s.Integer(index), 'Text':'Some expected counts are below 5; the chi-square approximation may be inaccurate.'})
                        if len(present_groups) == 2 and len(categories) == 2:
                            warnings.append({'Column':s.Integer(index), 'Text':'Consider Fisher exact for this 2×2 table.'})
            for category in shown:
                counts_for_category = [sum(group == at and value == category for group,value in zip(group_codes,values)) for at in range(groups)]
                percentages = [s.Rational(100*amount,total) if total else s.nan for amount,total in zip(counts_for_category,totals)]
                row = {'Column':s.Integer(index), 'Category':category, 'Binary':binary,
                       'p-value':probability, 'n':s.Integer(len(values)), 'Significant':significant}
                for at,(amount,percent) in enumerate(zip(counts_for_category,percentages)):
                    row['count'+str(at+1)] = s.Integer(amount);row['percent'+str(at+1)] = percent
                    if at:
                        row['count diff'+str(at+1)] = s.Integer(counts_for_category[0]-amount)
                        row['percent diff'+str(at+1)] = percentages[0]-percent
                comparisons.append(row)
        else:
            paired = name == 'wilcoxon'
            require(not paired or len(samples[0]) == len(samples[1]), 'Paired columns require matching complete pairs')
            row = {'Column':s.Integer(index), 'p-value':probability, 'n':s.Integer(len(samples[0]) if paired else sum(map(len,samples))), 'Significant':significant,
                   'normality':'unavailable', 'equal var':'Not applicable' if paired else 'unavailable'}
            means = [s.Add(*sample)/len(sample) if sample and all(getattr(v,'is_real',False) is True and getattr(v,'is_finite',False) is True for v in sample) else s.nan for sample in samples]
            for at,mean in enumerate(means):
                row['mean'+str(at+1)] = mean
                if at: row['diff'+str(at+1)] = means[0]-mean
            statuses = []
            normal_samples = [[x-y for x,y in zip(*samples)]] if paired else samples
            for at,sample in enumerate(normal_samples):
                try:
                    _,p,_ = _shapiro_wilk(sample)
                    status = 'no' if p < .05 else 'yes'
                    checks.append({'Column':s.Integer(index), 'Check':'Shapiro–Wilk', 'Sample':'Differences' if paired else str(at+1), 'p-value':s.Float(str(p),15), 'Result':status})
                    statuses.append(status)
                except ERRORS as error:
                    checks.append({'Column':s.Integer(index), 'Check':'Shapiro–Wilk', 'Sample':'Differences' if paired else str(at+1), 'p-value':s.nan, 'Result':'unavailable'})
                    errors.append({'Column':s.Integer(index), 'Reason':str(error)})
                    statuses.append('unavailable')
            row['normality'] = 'no' if 'no' in statuses else 'yes' if all(status == 'yes' for status in statuses) else 'unavailable'
            if not paired:
                try:
                    variance = calculate(proxy,'levene',samples)
                    row['equal var'] = 'no' if variance['p'] < .05 else 'yes'
                    checks.append({'Column':s.Integer(index), 'Check':'Brown–Forsythe', 'Sample':'Across samples', 'p-value':variance['p'], 'Result':row['equal var']})
                except ERRORS as error:
                    checks.append({'Column':s.Integer(index), 'Check':'Brown–Forsythe', 'Sample':'Across samples', 'p-value':s.nan, 'Result':'unavailable'})
                    errors.append({'Column':s.Integer(index), 'Reason':str(error)})
            comparisons.append(row)
        if proxy.note: errors.append({'Column':s.Integer(index), 'Reason':proxy.note})
    engine.statistics_column_reports = supplements
    result = {'Column comparisons':comparisons, 'Group count':s.Integer(groups), 'Categorical':categorical,
              'Column checks':checks, 'Column details':errors, 'Column warnings':warnings, 'Contingency tables':tables}
    engine.statistics_full_tables = result
    preview = {key:value[:50] if isinstance(value,list) else value for key,value in result.items()}
    preview['Contingency tables']=[{**table,'Categories':table['Categories'][:50],
        'Observed':[row[:50] for row in table['Observed'][:50]], 'Expected':[row[:50] for row in table['Expected'][:50]]} for table in tables[:50]]
    if any(len(value)>50 for value in result.values() if isinstance(value,list)) or any(len(table['Categories'])>50 or len(table['Observed'])>50 for table in tables):
        preview['Output note'] = 'Plain Output previews up to 50 rows/columns per table; the formatted report and Copy include all data.'
    return preview
