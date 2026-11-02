"""Mantel–Haenszel association and Breslow–Day odds-ratio homogeneity.

Each row is [Group A events, Group A no events, Group B events, Group B no events].
No zero-cell pseudo-counts are added. RBG variance for the pooled log OR.
Reference: statsmodels.stats.contingency_tables.StratifiedTable.
"""
import mpmath as mp
from calc_shared import require
from calc_advanced_common import table, option
from calc_statistics import _chisq_sf


def calculate(engine, name, args):
    rows = table(args[0], 1, 4)
    require(all(len(row) == 4 for row in rows), 'Each stratum needs event and no-event counts for both groups')
    require(all(v >= 0 and v.is_integer() for row in rows for v in row), 'Enter nonnegative integer counts')
    mode = option(args, 1, 'uncorrected')
    allowed = ('uncorrected', 'corrected') if name == 'mantelhaenszel' else ('uncorrected', 'tarone')
    require(mode in allowed, 'Choose ' + ' / '.join(allowed))
    level = float(args[2]) if len(args) > 2 else .95
    require(0 < level < 1, 'Confidence level must lie in (0,1)')
    input_count=len(rows)
    input_n=sum(sum(row) for row in rows)
    included=[];excluded=[];indices=[]
    for i,(a,b,c,d) in enumerate(rows):
        if min(a+b,c+d,a+c,b+d)<=0:
            reason='One or both comparison groups have no observations' if min(a+b,c+d)<=0 else 'No outcome variation within this stratum'
            excluded.append({'Stratum':i+1,'n':int(a+b+c+d),'Reason':reason})
        else:
            included.append([a,b,c,d]);indices.append(i+1)
    require(included, 'No informative strata: each included stratum needs both groups and both outcomes')
    require(name != 'breslowday' or len(included) >= 2, 'Breslow–Day requires at least two informative strata with both groups and both outcomes')
    rows=included
    # Extra precision keeps fitted counts stable near OR=1 and at sparse margins.
    with mp.workdps(50):
        rows = [[mp.mpf(int(v)) for v in row] for row in rows]
        sizes = [sum(row) for row in rows]
        r = sum(a*d/n for (a,b,c,d),n in zip(rows,sizes))
        s = sum(b*c/n for (a,b,c,d),n in zip(rows,sizes))
        odds = r/s if s else mp.inf
        interval = None
        se = None
        if r > 0 and s > 0:
            variance = (sum((a+d)*a*d/n**2 for (a,b,c,d),n in zip(rows,sizes))/r**2
                        + sum(((a+d)*b*c+(b+c)*a*d)/n**2 for (a,b,c,d),n in zip(rows,sizes))/(r*s)
                        + sum((b+c)*b*c/n**2 for (a,b,c,d),n in zip(rows,sizes))/s**2)/2
            se = mp.sqrt(variance)
            z = mp.sqrt(2)*mp.erfinv(mp.mpf(str(level)))
            interval = [mp.exp(mp.log(odds)-z*se), mp.exp(mp.log(odds)+z*se)]
        strata = []
        residuals, variances = [], []
        if name == 'breslowday':
            require(r > 0 and s > 0, 'Breslow–Day requires a finite positive pooled odds ratio')
        for i, ((a,b,c,d),n) in enumerate(zip(rows,sizes)):
            row, col = a+b, a+c
            if name == 'mantelhaenszel':
                expected = row*col/n
                variance = row*(n-row)*col*(n-col)/(n*n*(n-1))
                fitted = [expected, row-expected, col-expected, n-row-col+expected]
            else:
                # Monotone fixed-margin odds equation: stable even when OR=1.
                lo, hi = max(mp.mpf(0), row+col-n), min(row,col)
                for _ in range(180):
                    x = (lo+hi)/2
                    if x*(n-row-col+x) < odds*(row-x)*(col-x): lo = x
                    else: hi = x
                expected = (lo+hi)/2
                fitted = [expected, row-expected, col-expected, n-row-col+expected]
                require(min(fitted) > 0, 'Fitted counts are outside the numerical range')
                variance = 1/sum(1/v for v in fitted)
            residuals.append(a-expected); variances.append(variance)
            strata.append({'Stratum':indices[i],'n':int(n),
                           'Group A: event count':a,'Group A: no-event count':b,
                           'Group B: event count':c,'Group B: no-event count':d,
                           'Expected Group A event count':expected,'Variance of Group A event count':variance,
                           'Minimum fitted count':min(fitted)})
        if name == 'mantelhaenszel':
            difference = abs(sum(residuals))
            if mode == 'corrected' and difference >= .5: difference -= mp.mpf('.5')
            statistic, df = difference**2/sum(variances), 1
        else:
            statistic = sum(e*e/v for e,v in zip(residuals,variances))
            if mode == 'tarone': statistic -= sum(residuals)**2/sum(variances)
            statistic, df = max(mp.mpf(0),statistic), len(rows)-1
        return {'χ²':statistic,'df':df,'p value':_chisq_sf(statistic,df),
                'Pooled odds ratio':odds,'confidence interval':interval,
                'Confidence level':level,'SE log(OR)':se,'Strata (k)':len(rows),
                'n':int(sum(sizes)),'Input observations':int(input_n),'Input strata':input_count,
                'Excluded strata count':len(excluded),'Excluded strata':excluded,
                'Method':mode,'Strata':strata,
                'Exclusion note':'Strata without both groups or outcome variation provide no information for these tests and are excluded. n counts included observations.',
                'Null hypothesis':'Common odds ratio = 1' if name == 'mantelhaenszel' else 'Equal odds ratios across strata',
                'Assumptions':'Independent observations within and between strata; consistent row/column coding. '
                    'Chi-square approximation; sparse fitted counts can give inaccurate p values. '
                    'Common OR and its RBG log-normal CI assume homogeneous odds ratios. '
                    'No zero-cell correction; strata with zero group or outcome totals are excluded.',
                'Sparse fitted counts':'yes' if any(row['Minimum fitted count'] < 5 for row in strata) else 'no'}
