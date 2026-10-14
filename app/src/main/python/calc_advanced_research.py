"""Portable research synthesis, measurement agreement and equivalence tests.

Only mpmath is required at runtime (Android and Pyodide). Intervals and tests
use the chosen sampling model; no significance test is treated as equivalence.
"""
import math
from statistics import NormalDist
from calc_shared import require
from calc_advanced_common import number, vector, table, option, mean, variance
from calc_statistics import _t_sf, _f_sf, _chisq_sf, _normal_sf
from calc_effect_interpretation import icc_rating, ICC_GUIDE


def binary_studies(rows, measure, correction):
    """A/B event counts and totals -> log OR/RR and their sampling SEs."""
    require(len(rows[0]) == 4, 'Binary meta-analysis columns: events A, total A, events B, total B')
    require(correction >= 0, 'Continuity correction must be nonnegative')
    converted, details, excluded, indices = [], [], [], []
    for index, (a, n1, c, n2) in enumerate(rows):
        require(all(v.is_integer() for v in (a,n1,c,n2)) and n1>0 and n2>0 and 0<=a<=n1 and 0<=c<=n2,
                'Events and totals must be integers with 0 ≤ events ≤ positive total')
        if a==c==0 or measure=='or' and a==n1 and c==n2:
            excluded.append({'Study':index+1,'Reason':'No events in either arm' if a==c==0 else 'No non-events in either arm'})
            continue
        original=[a,n1,c,n2]; b,d=n1-a,n2-c
        corrected=min(a,b,c,d)==0
        if corrected:
            require(correction>0, 'Zero cells require a positive continuity correction')
            a,b,c,d=[value+correction for value in (a,b,c,d)];n1,n2=a+b,c+d
        log_or=math.log(a)+math.log(d)-math.log(b)-math.log(c)
        log_rr=math.log(a)-math.log(n1)-math.log(c)+math.log(n2)
        se_or=math.sqrt(1/a+1/b+1/c+1/d);se_rr=math.sqrt(max(0,1/a-1/n1+1/c-1/n2))
        require(se_rr>0, 'Risk-ratio sampling variance is zero')
        def ratio(value):return math.exp(value) if value<709 else math.inf
        converted.append([log_or if measure=='or' else log_rr,se_or if measure=='or' else se_rr]);indices.append(index+1)
        details.append({'Events A':int(original[0]),'Total A':int(original[1]),'Events B':int(original[2]),'Total B':int(original[3]),
                        'OR':ratio(log_or),'log(OR)':log_or,'SE log(OR)':se_or,'RR':ratio(log_rr),'log(RR)':log_rr,'SE log(RR)':se_rr,
                        'Continuity corrected':'yes' if corrected else 'no'})
    require(len(converted)>=2, 'At least two informative studies are required')
    return converted, details, excluded, indices


def continuous_studies(rows, measure):
    """Independent-arm summary statistics -> MD or bias-corrected Hedges g."""
    require(len(rows[0])==6,'Continuous meta-analysis columns: mean A, SD A, n A, mean B, SD B, n B')
    converted,details=[],[]
    for m1,s1,n1,m2,s2,n2 in rows:
        require(n1.is_integer() and n2.is_integer() and n1>=2 and n2>=2 and s1>=0 and s2>=0,
                'Each arm needs an integer n ≥ 2 and a nonnegative sample SD')
        delta=m1-m2;variance_md=s1*s1/n1+s2*s2/n2;total=n1+n2;df=total-2
        pooled=((n1-1)*s1*s1+(n2-1)*s2*s2)/df
        require(pooled>0 and math.isfinite(pooled) and variance_md>0 and math.isfinite(variance_md),
                'Continuous effects require positive finite sampling variance')
        # Conventional small-sample approximation used by statsmodels/Borenstein.
        correction=1-3/(4*df-1);g=correction*delta/math.sqrt(pooled)
        variance_g=total/(n1*n2)+g*g/(2*(total-3.94))
        require(math.isfinite(g) and math.isfinite(variance_g),'Standardized effect exceeds the numeric range')
        converted.append([delta if measure=='md' else g,math.sqrt(variance_md if measure=='md' else variance_g)])
        details.append({'Mean A':m1,'SD A':s1,'n A':int(n1),'Mean B':m2,'SD B':s2,'n B':int(n2),
                        'Mean difference':delta,'SE (MD)':math.sqrt(variance_md),"Hedges g":g,'SE (Hedges g)':math.sqrt(variance_g),'Bias correction J':correction})
    return converted,details


def critical(tail, df=None, denominator=None):
    """Invert survival probabilities directly, avoiding 1-CDF cancellation."""
    if df is None:
        return -NormalDist().inv_cdf(tail)
    sf = (lambda x: float(_f_sf(x, df, denominator))) if denominator else (lambda x: float(_t_sf(x, df)))
    lo, hi = 0.0, 1.0
    while sf(hi) > tail:
        hi *= 2
    for _ in range(75):
        mid = (lo+hi)/2
        if sf(mid) > tail: lo = mid
        else: hi = mid
    return (lo+hi)/2


def level_option(a, index, default=.95):
    level = number(a[index]) if len(a) > index else default
    require(0 < level < 1, 'Confidence level must be between 0 and 1')
    return level


def meta_analysis(engine, a):
    rows = table(a[0], 2, 2)
    requested=option(a,5,'generic').lower()
    measure={'oddsratio':'or','riskratio':'rr'}.get(requested,requested)
    require(measure in ('generic','or','rr','md','smd'),'Choose generic, oddsratio, riskratio, md or smd effects')
    binary,continuous,excluded=[],[],[];indices=list(range(1,len(rows)+1))
    correction=number(a[6]) if len(a)>6 else .5
    if measure in ('or','rr'):rows,binary,excluded,indices=binary_studies(rows,measure,correction)
    elif measure in ('md','smd'):rows,continuous=continuous_studies(rows,measure)
    else:require(len(rows[0]) == 2, 'Meta-analysis columns: effect estimate, standard error')
    method = option(a, 1, 'pm'); inference = option(a, 3, 'z')
    require(method in ('fixed', 'dl', 'pm'), 'Choose fixed, dl or pm meta-analysis')
    require(inference in ('z', 'hksj') and (method != 'fixed' or inference == 'z'),
            'Fixed effects use z; random effects use z or hksj')
    level = level_option(a, 2); egger = option(a, 4, '1')
    require(egger in ('0', '1'), 'Egger option must be 0 or 1')
    y = [r[0] for r in rows]; se = [r[1] for r in rows]; k = len(y)
    require(all(s > 0 and math.isfinite(s*s) and s*s > 0 for s in se), 'Standard errors must be positive and within the numeric range')
    # Normalize both variances and centered effects so inversion is unit invariant.
    origin = mean(y); scale = max(max(se), max(abs(v-origin) for v in y))
    v = [(s/scale)**2 for s in se]; effects = [(value-origin)/scale for value in y]
    require(all(value > 0 for value in v), 'Standard-error ratios exceed the numeric range')
    def fit(tau):
        w = [1/(value+tau) for value in v]; total = math.fsum(w)
        estimate = math.fsum(wi*yi for wi, yi in zip(w, effects))/total
        q = math.fsum(wi*(yi-estimate)**2 for wi, yi in zip(w, effects))
        return estimate, total, q, w
    fixed, total, q, w = fit(0); df = k-1; tau = 0.0
    if method == 'dl':
        denominator = total-math.fsum(wi*wi for wi in w)/total
        require(denominator > 0, 'Study weights exceed the numeric range')
        tau = max(0, (q-df)/denominator)
    elif method == 'pm' and q > df:
        lo, hi = 0.0, 1.0
        while fit(hi)[2] > df: hi *= 2
        for _ in range(80):
            mid = (lo+hi)/2
            if fit(mid)[2] > df: lo = mid
            else: hi = mid
        tau = (lo+hi)/2
    estimate, weight_sum, residual_q, weights = fit(tau)
    pooled = origin+scale*estimate; ordinary_se = scale/math.sqrt(weight_sum)
    # Modified HKSJ never narrows the variance below conventional inverse variance.
    pooled_se = ordinary_se*math.sqrt(max(1, residual_q/df)) if inference == 'hksj' else ordinary_se
    cutoff = critical((1-level)/2, df if inference == 'hksj' else None)
    bounds = [pooled-cutoff*pooled_se, pooled+cutoff*pooled_se]
    statistic = pooled/pooled_se
    probability = float(2*_t_sf(abs(statistic), df)) if inference == 'hksj' else float(2*_normal_sf(abs(statistic)))
    z = critical((1-level)/2)
    studies = [{'Study': indices[i], 'Estimate': yi, 'SE': si, 'Lower CI': yi-z*si,
                'Upper CI': yi+z*si, 'Weight (%)': 100*wi/weight_sum}
               for i, (yi, si, wi) in enumerate(zip(y, se, weights))]
    if binary or continuous:
        for study,converted in zip(studies,binary or continuous):study.update(converted)
    prediction = None
    if method != 'fixed' and k > 2:
        radius = critical((1-level)/2, k-2)*math.sqrt(tau*scale*scale+ordinary_se**2)
        prediction = [pooled-radius, pooled+radius]
    egger_result = {'Status': 'Disabled' if egger == '0' else 'Unavailable: at least three studies with differing standard errors are required'}
    if egger == '1' and k >= 3:
        precision = [scale/s for s in se]; standardized = [value/s for value, s in zip(y, se)]
        center = mean(precision); centered = [p-center for p in precision]; standardized_mean = mean(standardized)
        ss = math.fsum(p*p for p in centered)
        if ss > 1e-24*math.fsum(p*p for p in precision):
            slope = math.fsum(p*(value-standardized_mean) for p, value in zip(centered, standardized))/ss
            intercept = standardized_mean-slope*center
            mse = math.fsum((value-intercept-slope*p)**2 for p, value in zip(precision, standardized))/(k-2)
            intercept_se = math.sqrt(mse*(1/k+center*center/ss))
            test = intercept/intercept_se if intercept_se > 0 else None
            egger_result = {'Intercept': intercept, 'SE': intercept_se, 't': test, 'df': k-2,
                            'p': float(2*_t_sf(abs(test), k-2)) if test is not None else None,
                            'Note': 'OLS standardized effect on precision; asymmetry is not proof of publication bias. Tests have low power with fewer than 10 studies.'}
    labels = engine.request.get('statisticsTermLabels', {})
    forest = [[labels.get('study:'+str(r['Study']), str(r['Study'])), r['Estimate'], r['Lower CI'], r['Upper CI']] for r in studies]
    forest.append(['Pooled effect', pooled, *bounds])
    max_se = max(se)*1.08
    effect_label={'or':'Log odds ratio (A / B)','rr':'Log risk ratio (A / B)','md':'Mean difference (A − B)','smd':'Hedges g'}.get(measure,'Effect estimate')
    engine.statistics_plots = [
        {'kind': 'intervals', 'title': 'Forest plot', 'rows': forest, 'reference': 0,
         'summaryIndex': k, 'weights': [r['Weight (%)'] for r in studies], 'xlabel': effect_label,
         'caption': 'Study intervals use the normal approximation; the diamond shows the pooled confidence interval.'},
        {'kind': 'research-scatter', 'title': 'Funnel plot', 'points': [[yi, si] for yi, si in zip(y, se)],
         'xlabel': effect_label, 'ylabel': 'Standard error', 'invertY': True,
         'lines': [[[pooled, 0], [pooled-z*max_se, max_se]], [[pooled, 0], [pooled+z*max_se, max_se]], [[pooled, 0], [pooled, max_se]]],
         'caption': 'Dashed funnel limits are normal pseudo confidence limits around the pooled effect; asymmetry is not proof of publication bias.'}]
    engine.statistics_full_tables = {'Studies': studies}
    extra={}
    if measure in ('or','rr'):
        def ratio(value):return math.exp(value) if value<709 else math.inf
        extra={'Effect measure':'Odds ratio (A / B)' if measure=='or' else 'Risk ratio (A / B)',
               'Pooled ratio':ratio(pooled),'Ratio confidence interval':[ratio(value) for value in bounds],
               'Continuity correction':correction,'Excluded study count':len(excluded),'Excluded studies':excluded[:100],
               'Binary input note':'Pooling, Forest/Funnel plots and Egger use natural-log effects and SE(log effect). Ratios compare event odds/risk in A versus B; event meaning is user-defined. A zero cell adds the selected correction to all four cells of that study. Double-zero event studies are excluded; OR also excludes double-zero non-events. This is inverse-variance pooling, not Mantel–Haenszel or Peto.'}
    if continuous:
        extra={'Effect measure':'Mean difference (A − B)' if measure=='md' else 'Standardized mean difference (Hedges g)',
               'Continuous input note':'Independent A/B arms with sample means, sample SDs and n ≥ 2. MD = mean A−mean B; SE² = SD A²/n A + SD B²/n B, same measurement units across studies. SMD uses pooled within-study SD and approximate Hedges correction J=1−3/(4(n A+n B−2)−1); variance = (n A+n B)/(n A n B) + g²/(2(n A+n B−3.94)), matching statsmodels. SMD assumes comparable constructs and common within-study variance; align outcome direction before analysis. Paired arms require covariance. For independent-arm change outcomes, supply the means and SDs of the changes, not separate before/after summaries.'}
    if excluded:engine.statistics_full_tables['Excluded studies']=excluded
    return {**extra,'Studies (k)': k, 'Method': {'fixed': 'Fixed effect', 'dl': 'Random effects (DerSimonian–Laird)', 'pm': 'Random effects (Paule–Mandel)'}[method],
            'Inference': 'Modified Hartung–Knapp' if inference == 'hksj' else 'Normal approximation',
            'estimate': pooled, 'SE': pooled_se, 'confidence level': level, 'confidence interval': bounds, 'p': probability,
            'Q': q, 'Q df': df, 'Q p': float(_chisq_sf(q, df)), 'I² (%)': max(0, (q-df)/q)*100 if q else 0,
            'H²': q/df, 'τ²': tau*scale*scale, 'Prediction interval': prediction,
            'Egger test': egger_result, 'Studies': studies[:40 if binary or continuous else 100],
            'Assumptions': 'Independent studies; comparable effect estimates and known sampling standard errors. Enter log effects and log-scale SE for odds/risk/hazard ratios. Random-effects prediction intervals use t(k−2), omit tau estimation uncertainty, and require at least three studies. HKSJ uses max(1,Q residual/(k−1)); study CIs always use z. Small-study effects and heterogeneity do not establish publication bias.'}


def agreement(engine, name, a):
    rows = table(a[0], 3 if name == 'blandaltman' else 2, 2)
    n, k = len(rows), len(rows[0])
    if name == 'blandaltman':
        require(k == 2, 'Bland–Altman requires two measurement columns')
        level = level_option(a, 1); mode = option(a, 2, 'difference')
        require(mode in ('difference', 'log'), 'Choose difference or log measurements')
        require(mode != 'log' or all(value > 0 for row in rows for value in row), 'Log agreement requires positive measurements')
        data = [[math.log(value) for value in row] for row in rows] if mode == 'log' else rows
        differences = [r[0]-r[1] for r in data]; bias = mean(differences); sd = math.sqrt(variance(differences))
        z = critical((1-level)/2); t = critical((1-level)/2, n-1)
        limits = [bias-z*sd, bias+z*sd]; bias_radius = t*sd/math.sqrt(n)
        limit_radius = t*sd*math.sqrt(1/n+z*z/(2*(n-1)))
        result = {'n': n, 'Difference': 'log(A/B)' if mode == 'log' else 'A − B', 'Bias': bias, 'SD of differences': sd,
                  'confidence level': level, 'Bias CI': [bias-bias_radius, bias+bias_radius],
                  'Lower agreement limit': limits[0], 'Upper agreement limit': limits[1],
                  'Lower limit CI (approximate)': [limits[0]-limit_radius, limits[0]+limit_radius],
                  'Upper limit CI (approximate)': [limits[1]-limit_radius, limits[1]+limit_radius],
                  'Assumptions': 'Independent subjects with one pair each; approximately normal differences and constant difference variance. Agreement limits describe individual differences, not the confidence interval of mean bias. Limit CIs use a normal-theory delta approximation. Set acceptable agreement in advance; repeated measurements per subject require a different model.'}
        if mode == 'log':
            require(max(abs(v) for v in limits+[bias]) < 709, 'Ratio limits exceed the numeric range')
            result.update({'Geometric mean ratio A/B': math.exp(bias), 'Ratio agreement limits': [math.exp(v) for v in limits]})
        averages=[mean(row) for row in data];center=mean(averages);xs=[value-center for value in averages]
        sxx=math.fsum(value*value for value in xs);trend=[]
        proportional={'Status':'Unavailable: mean measurements must vary'}
        if sxx>0:
            slope=math.fsum(x*(d-bias) for x,d in zip(xs,differences))/sxx
            intercept=bias-slope*center;residual=math.fsum((d-bias-slope*x)**2 for x,d in zip(xs,differences))/(n-2)
            slope_se=math.sqrt(residual/sxx);available=residual>1e-24*max(sd*sd,1e-300)
            probability=float(2*_t_sf(abs(slope/slope_se),n-2)) if available else None
            radius=critical((1-level)/2,n-2)*slope_se
            proportional={'Slope':slope,'Intercept':intercept,'SE':slope_se,'t':slope/slope_se if available else None,'df':n-2,'p':probability,
                          'Slope CI':[slope-radius,slope+radius] if available else None,
                          'Proportional bias detected':'yes' if available and probability<1-level else 'not detected' if available else 'unavailable',
                          'Note':'OLS difference on pair mean tests slope=0 using t(n−2). A nonsignificant slope does not prove absence of proportional bias. Unequal measurement-error variances can induce a trend; interpret with study design and the plot. Log mode tests the trend on log measurements. Zero residual variance makes inference unavailable.'}
            trend=[[value,intercept+slope*value] for value in (min(averages),max(averages))]
        result['Proportional bias']=proportional
        engine.statistics_plots = [{'kind': 'research-scatter', 'title': 'Bland–Altman plot',
                                    'points': [[mean(row), d] for row, d in zip(data, differences)],
                                    'xlabel': 'Mean log measurement' if mode == 'log' else 'Mean measurement',
                                    'ylabel': 'log(A/B)' if mode == 'log' else 'Difference (A − B)',
                                    'horizontal': [bias, *limits], 'horizontalLabels': ['Bias', 'Lower agreement limit', 'Upper agreement limit'],
                                    'trend':trend,
                                    'caption': 'Solid lines: mean bias and OLS trend; dashed lines: limits of agreement for individual differences.' if trend else 'Solid line: mean bias; dashed lines: limits of agreement for individual differences.'}]
        return result
    model = option(a, 1, 'random'); unit = option(a, 2, 'single'); level = level_option(a, 3)
    require(model in ('oneway', 'random', 'mixed') and unit in ('single', 'average'), 'Choose ICC model oneway/random/mixed and unit single/average')
    # Center first to avoid subtracting large sums of squares.
    origin = rows[0][0]; centered = [[value-origin for value in row] for row in rows]
    grand = mean([value for row in centered for value in row])
    subjects = [mean(row) for row in centered]; raters = [mean(list(col)) for col in zip(*centered)]
    ssr = k*math.fsum((m-grand)**2 for m in subjects)
    ssc = n*math.fsum((m-grand)**2 for m in raters)
    sse = math.fsum((value-subjects[i]-raters[j]+grand)**2 for i, row in enumerate(centered) for j, value in enumerate(row))
    ssw = math.fsum((value-subjects[i])**2 for i, row in enumerate(centered) for value in row)
    msr = ssr/(n-1); msc = ssc/(k-1); mse = sse/((n-1)*(k-1)); msw = ssw/(n*(k-1))
    error = msw if model == 'oneway' else mse
    denominator = msr+(k-1)*error+(k*(msc-mse)/n if model == 'random' else 0)
    require(denominator > 0, 'ICC is undefined with no measurement variance')
    value = (msr-error)/denominator
    if unit == 'average':
        denominator = msr+((msc-mse)/n if model == 'random' else 0)
        require(denominator > 0, 'Average-measure ICC is undefined with no subject mean variance')
        value = (msr-error)/denominator
    df1, df2 = n-1, (n if model == 'oneway' else n-1)*(k-1)
    f = msr/error if error > 0 else math.inf; bounds = None
    tail = (1-level)/2
    if error > 0 and msr > 0:
        if model == 'random':
            rho = (msr-mse)/(msr+(k-1)*mse+k*(msc-mse)/n)
            fj = msc/mse
            b = n*(1+(k-1)*rho)-k*rho
            effective = (k-1)*(n-1)*(k*rho*fj+b)**2/((n-1)*k*k*rho*rho*fj*fj+b*b)
            if effective > 0:
                upper_f = critical(tail, n-1, effective); lower_f = critical(tail, effective, n-1)
                lower = n*(msr-upper_f*mse)/(upper_f*(k*msc+(k*n-k-n)*mse)+n*msr)
                upper = n*(lower_f*msr-mse)/(k*msc+(k*n-k-n)*mse+n*lower_f*msr)
                if unit == 'average':
                    denoms = [1+(k-1)*limit for limit in (lower, upper)]
                    if all(d > 0 for d in denoms): bounds = [k*lower/denoms[0], k*upper/denoms[1]]
                else: bounds = [lower, upper]
        else:
            fl = f/critical(tail, df1, df2); fu = f*critical(tail, df2, df1)
            bounds = [1-1/fl, 1-1/fu] if unit == 'average' else [(fl-1)/(fl+k-1), (fu-1)/(fu+k-1)]
    code = {'oneway': '1', 'random': '2', 'mixed': '3'}[model]+(',k' if unit == 'average' else ',1')
    return {'Subjects': n, 'Raters': k, 'Model': {'oneway': 'One-way random / absolute agreement', 'random': 'Two-way random / absolute agreement', 'mixed': 'Two-way mixed / consistency'}[model],
            'Reliability rating':icc_rating(value),'Koo & Li guide':ICC_GUIDE,
            'Lower CI rating':icc_rating(bounds[0]) if bounds else 'unavailable', 'Upper CI rating':icc_rating(bounds[1]) if bounds else 'unavailable',
            'Interpretation note':'Koo & Li (2016) recommend interpreting the ICC confidence interval, not just the point estimate. These are conventional reliability benchmarks; consider measurement purpose and clinical context. Negative estimates and CI endpoints are retained; the 0–1 graph clips the display only.',
            'Unit': unit, 'ICC type': 'ICC('+code+')', 'ICC': value, 'estimate': value, 'confidence level': level,
            'confidence interval': bounds, 'F': f, 'df1': df1, 'df2': df2, 'p': float(_f_sf(f, df1, df2)) if math.isfinite(f) else 0,
            'ANOVA': [{'Source': 'Subjects', 'SS': ssr, 'df': n-1, 'MS': msr}, {'Source': 'Raters', 'SS': ssc, 'df': k-1, 'MS': msc}, {'Source': 'Residual', 'SS': sse, 'df': (n-1)*(k-1), 'MS': mse}],
            'Assumptions': 'Complete balanced numeric subject × rater matrix; independent subjects and normal ANOVA errors. One-way treats raters as exchangeable within subjects; random generalizes absolute agreement to a rater population; mixed estimates consistency of these fixed raters and ignores systematic rater shifts. Average refers to the mean of all selected k raters. Negative ICC estimates are retained. F tests H0: ICC=0; two-way absolute CIs use approximate Satterthwaite degrees of freedom. Degenerate confidence intervals are unavailable.'}


def equivalence(name, a):
    if name == 'tost':
        x = vector(a[0], 2); lower, upper = number(a[1]), number(a[2]); mu0 = number(a[3]) if len(a) > 3 else 0
        alpha = number(a[4]) if len(a) > 4 else .05
        estimate, se, df = mean(x)-mu0, math.sqrt(variance(x)/len(x)), len(x)-1
        sizes = {'n': len(x), 'Reference mean': mu0}; method = 'One-sample t'
    else:
        x, y = vector(a[0], 2), vector(a[1], 2); lower, upper = number(a[2]), number(a[3])
        alpha_index = 4 if name == 'tostpaired' else 5
        alpha = number(a[alpha_index]) if len(a) > alpha_index else .05
        estimate = mean(x)-mean(y); sizes = {'n A': len(x), 'n B': len(y)}
        if name == 'tostpaired':
            require(len(x) == len(y), 'Paired TOST requires equal-length matched lists')
            differences = [xi-yi for xi, yi in zip(x, y)]
            estimate, se, df = mean(differences), math.sqrt(variance(differences)/len(x)), len(x)-1
            method = 'Paired t (A − B)'
        else:
            mode = option(a, 4, 'welch'); require(mode in ('welch', 'student'), 'Choose welch or student TOST')
            vx, vy = variance(x), variance(y)
            if mode == 'student':
                df = len(x)+len(y)-2
                se = math.sqrt(((len(x)-1)*vx+(len(y)-1)*vy)/df*(1/len(x)+1/len(y)))
            else:
                v1, v2 = vx/len(x), vy/len(y); se = math.sqrt(v1+v2)
                df = (v1+v2)**2/(v1*v1/(len(x)-1)+v2*v2/(len(y)-1)) if se > 0 else 0
            method = ('Welch' if mode == 'welch' else 'Student')+' independent t (A − B)'
    require(lower < upper, 'Lower equivalence bound must be below upper bound')
    require(0 < alpha < .5, 'TOST alpha must be between 0 and 0.5')
    require(se > 0 and math.isfinite(se) and df > 0, 'TOST requires positive finite sampling variance')
    lower_t, upper_t = (estimate-lower)/se, (estimate-upper)/se
    lower_p, upper_p = float(_t_sf(lower_t, df)), float(_t_sf(-upper_t, df))
    p = max(lower_p, upper_p); cutoff = critical(alpha, df)
    return {**sizes, 'Method': method, 'estimate': estimate, 'SE': se, 'df': df, 'Lower equivalence bound': lower,
            'Upper equivalence bound': upper, 'alpha': alpha, 'Lower t': lower_t, 'Lower p': lower_p,
            'Upper t': upper_t, 'Upper p': upper_p, 'TOST p': p, 'Equivalent': 'yes' if p < alpha else 'not established',
            'confidence level': 1-2*alpha, 'confidence interval': [estimate-cutoff*se, estimate+cutoff*se],
            'Difference from zero p': float(2*_t_sf(abs(estimate/se), df)),
            'Assumptions': 'Bounds are prespecified in original measurement units for A−B (one-sample: mean−reference). Both one-sided p values must be below alpha; the corresponding CI has level 1−2 alpha (90% at alpha .05). Failure to detect a difference does not establish equivalence, and failure of TOST does not prove a meaningful difference. Independent normal samples (Student also assumes equal variances); paired tests assume independent subjects with approximately normal differences.'}


def calculate(engine, name, a):
    if name == 'metaanalysis': return meta_analysis(engine, a)
    if name in ('icc', 'blandaltman'): return agreement(engine, name, a)
    return equivalence(name, a)
