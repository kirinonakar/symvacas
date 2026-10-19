"""Purpose and use cases, before the existing bilingual parameter instructions."""
from .catalog import catalog_description

# These clarify the inferential target where the compact catalog name alone is
# insufficient. Estimation and exploratory methods retain their actual purpose.
PURPOSES = {
    'pearson': ('Measures linear association and tests whether population correlation is zero.', '선형 연관성을 측정하고 모집단 상관계수가 0인지 검정합니다.'),
    'spearman': ('Measures monotonic rank association and tests for zero rank correlation.', '단조 관계의 순위 상관을 측정하고 순위 상관이 0인지 검정합니다.'),
    'kendall': ('Measures concordance of ranks with tie correction and tests for zero association.', '동순위를 보정한 순위 일치도를 측정하고 연관성이 0인지 검정합니다.'),
    'shapiro': ('Tests the null hypothesis that a numeric sample comes from a normal distribution.', '숫자 표본이 정규분포에서 나왔다는 귀무가설을 검정합니다.'),
    'normaltest': ('Tests normality by combining departures in skewness and kurtosis.', '왜도·첨도의 이탈을 결합해 정규분포라는 귀무가설을 검정합니다.'),
    'kstest': ('Tests whether two continuous distributions, or a sample and a specified reference distribution, agree.', '두 연속분포 또는 표본과 지정한 기준분포가 같은지 검정합니다.'),
    'levene': ('Tests whether independent groups have equal variances using median-centered Brown–Forsythe.', '중앙값 기준 Brown–Forsythe로 독립 그룹의 분산이 같은지 검정합니다.'),
    'bartlett': ('Tests equality of variances across independent normal populations.', '독립된 정규 모집단들의 분산이 같은지 검정합니다.'),
    'mcnemar': ('Tests whether paired binary outcomes have equal marginal success proportions.', '대응된 이항 결과의 주변 성공 비율이 같은지 검정합니다.'),
    'twowayanova': ('Tests mean effects of two categorical factors and whether their effects interact.', '두 범주 요인의 평균 효과와 두 요인 간 상호작용을 검정합니다.'),
    'manova': ('Tests group or condition effects on several response means jointly.', '여러 종속변수의 평균을 함께 고려해 그룹·조건 효과를 검정합니다.'),
    'mancova': ('Tests group differences in multiple response means jointly after adjusting for covariates.', '공변량을 보정한 뒤 여러 종속변수의 평균에 그룹 차이가 있는지 공동 검정합니다.'),
    'repeatedanova': ('Tests mean differences between conditions measured on the same subjects.', '같은 대상에서 반복 측정한 조건들의 평균이 같은지 검정합니다.'),
    'friedman': ('Tests repeated-condition differences using within-subject ranks.', '대상 내 순위를 이용해 반복 조건 간 차이가 있는지 검정합니다.'),
    'linearmodel': ('Estimates numeric and categorical predictor effects and tests main effects and interactions on a continuous response.', '연속형 반응에 대한 숫자·범주 설명변수의 효과를 추정하고 주 효과·상호작용을 검정합니다.'),
    'glm': ('Models the response mean with a chosen distribution and link, and tests predictor coefficients.', '선택한 분포·연결함수로 반응의 평균을 모형화하고 설명변수 계수를 검정합니다.'),
    'mixedmodel': ('Estimates fixed effects and subject/cluster variation for a continuous response, accounting for dependent observations.', '관측값의 의존성을 반영해 연속형 반응의 고정효과와 대상·군집 간 변동을 추정합니다.'),
    'glmm': ('Estimates subject-specific predictor effects for binary or count responses with random effects.', '랜덤효과를 반영해 이항·빈도 반응에 대한 대상별 조건부 설명변수 효과를 추정합니다.'),
    'gee': ('Estimates population-average predictor effects while accounting for correlation within clusters.', '군집 내 상관을 반영해 모집단 평균 기준의 설명변수 효과를 추정합니다.'),
    'mediation': ('Estimates direct and indirect effects through a mediator, with uncertainty for the indirect effect.', '매개변수를 거치는 간접효과와 직접효과를 추정하고 간접효과의 불확실성을 평가합니다.'),
    'moderation': ('Tests whether the relationship between X and the response changes with moderator W through an X×W interaction.', 'X×W 상호작용으로 조절변수 W에 따라 X와 반응의 관계가 달라지는지 검정합니다.'),
    'cfa': ('Evaluates how well a prespecified latent-factor measurement model explains indicator covariances.', '미리 정한 잠재요인 측정모형이 관측 지표들의 공분산을 얼마나 잘 설명하는지 평가합니다.'),
    'sem': ('Estimates a specified latent-variable path model and evaluates path effects and overall fit.', '지정한 잠재변수 경로모형을 추정하고 경로 효과와 전체 적합도를 평가합니다.'),
    'logrank': ('Tests whether survival functions differ between independent groups with censored event times.', '중도절단을 포함한 사건 시간에서 독립 그룹의 생존함수가 같은지 검정합니다.'),
    'cox': ('Estimates predictor effects on event hazard under proportional hazards and tests their coefficients.', '비례위험 가정에서 설명변수의 사건 위험 효과를 추정하고 계수를 검정합니다.'),
}

USE_CASES = {
    'pearson': ('Use for the linear relationship between two numeric variables.', '두 숫자 변수의 선형 관계를 확인할 때 사용합니다.'),
    'spearman': ('Use for ordered data or monotonic relationships that need not be linear.', '순서형 자료 또는 선형이 아닌 단조 관계를 확인할 때 사용합니다.'),
    'kendall': ('Use to compare rankings, including data with tied ranks.', '동순위가 있는 자료를 포함해 두 순위의 연관성을 확인할 때 사용합니다.'),
    'impute': ('Use to prepare incomplete numeric data before analysis; review the preview and missingness mechanism.', '분석 전에 불완전한 숫자 자료를 준비할 때 사용하며 미리 보기와 결측 발생 원인을 확인합니다.'),
    'propztest': ('Use to compare a binary success rate with a target when normal approximation is adequate.', '정규근사가 가능한 이항 성공률을 목표 비율과 비교할 때 사용합니다.'),
    'propztest2': ('Use to compare success rates in two independent groups when normal approximation is adequate.', '정규근사가 가능한 독립 두 그룹의 성공률을 비교할 때 사용합니다.'),
    'mcnemar': ('Use for before/after binary outcomes or matched binary pairs.', '전·후 이항 결과 또는 짝지은 이항 결과를 비교할 때 사용합니다.'),
    'cronbach': ('Use to assess internal consistency of items intended to measure the same construct.', '같은 개념을 측정하는 문항의 내적 일관성을 평가할 때 사용합니다.'),
    'omega': ('Use for reliability of a scale when a single-factor measurement model is appropriate.', '단일요인 측정모형이 적절한 척도의 신뢰도를 평가할 때 사용합니다.'),
    'icc': ('Use to assess repeatability or agreement of numeric ratings across raters or repeated measurements.', '평가자 간 또는 반복 측정한 숫자 점수의 재현성·일치도를 평가할 때 사용합니다.'),
    'cohenkappa': ('Use for chance-adjusted agreement between two categorical raters.', '두 평가자의 범주 판정에서 우연 일치를 보정한 일치도를 평가할 때 사용합니다.'),
    'blandaltman': ('Use to assess whether two measurement methods agree closely enough in the original units.', '두 측정 방법의 차이가 원래 단위에서 허용 가능한지 평가할 때 사용합니다.'),
    'shapiro': ('Use to check a normal-model assumption alongside a Q–Q plot.', 'Q–Q plot과 함께 정규성 가정을 점검할 때 사용합니다.'),
    'normaltest': ('Use to check normality through skewness and tail shape in a sufficiently large numeric sample.', '충분한 크기의 숫자 표본에서 왜도·꼬리 형태를 통해 정규성을 점검할 때 사용합니다.'),
    'kstest': ('Use to compare entire continuous distributions, including shape and location.', '위치·형태를 포함한 연속분포 전체의 차이를 비교할 때 사용합니다.'),
    'levene': ('Use to check equal variances before a group comparison, especially when normality is uncertain.', '그룹 비교 전에 등분산을 점검할 때, 특히 정규성이 불확실할 때 사용합니다.'),
    'bartlett': ('Use to compare variances when normality is credible; nonnormality can affect the test.', '정규성 가정이 타당한 그룹의 분산을 비교할 때 사용하며 비정규성에 민감합니다.'),
    'tukey': ('Use after equal-variance ANOVA to identify which independent group means differ.', '등분산 ANOVA 이후 어느 독립 그룹의 평균이 다른지 확인할 때 사용합니다.'),
    'gameshowell': ('Use for pairwise mean comparisons with unequal variances or unequal group sizes.', '그룹 분산·표본 수가 다를 수 있는 평균 쌍별 비교에 사용합니다.'),
    'scheffe': ('Use after equal-variance ANOVA when protection for a broader family of mean contrasts is needed.', '등분산 ANOVA 이후 폭넓은 평균 대비에 대한 다중비교 보호가 필요할 때 사용합니다.'),
    'dunnett': ('Use when each treatment group is compared with the same control group.', '여러 처리군을 하나의 공통 대조군과 비교할 때 사용합니다.'),
    'dunn': ('Use after Kruskal–Wallis to locate independent group differences with multiplicity adjustment.', 'Kruskal–Wallis 이후 다중비교를 보정해 차이가 있는 독립 그룹 쌍을 찾을 때 사용합니다.'),
    'conover': ('Use after a significant Kruskal–Wallis result for pairwise rank comparisons.', 'Kruskal–Wallis가 유의한 뒤 순위의 쌍별 사후비교에 사용합니다.'),
    'twowayanova': ('Use for independent numeric outcomes classified by two factors, such as treatment and group.', '처리·그룹 등 두 요인으로 분류한 독립 숫자 반응을 분석할 때 사용합니다.'),
    'ancova': ('Use to compare groups while adjusting for numeric covariates such as baseline measurements.', '기초 측정값 등 숫자 공변량을 보정하면서 그룹 평균을 비교할 때 사용합니다.'),
    'manova': ('Use when several related outcomes should be compared jointly across groups or repeated conditions.', '서로 관련된 여러 결과를 그룹·반복 조건 간에 함께 비교할 때 사용합니다.'),
    'mancova': ('Use to compare several related outcomes across groups while adjusting for covariates.', '공변량을 보정하면서 서로 관련된 여러 결과의 그룹 차이를 함께 비교할 때 사용합니다.'),
    'repeatedanova': ('Use for continuous measurements collected from the same subjects in several conditions or times.', '같은 대상을 여러 조건·시점에서 반복 측정한 연속형 자료에 사용합니다.'),
    'friedman': ('Use for three or more matched conditions when a within-subject rank comparison is appropriate.', '대응된 3개 이상 조건에서 대상 내 순위 비교가 적절할 때 사용합니다.'),
    'cohend': ('Use to express the size of a mean difference in SD units alongside its uncertainty.', '평균 차이의 크기를 표준편차 단위로 표현하고 불확실성과 함께 해석할 때 사용합니다.'),
    'eta2': ('Use to summarize how much outcome variation is associated with group differences.', '결과의 변동 중 그룹 차이가 차지하는 크기를 요약할 때 사용합니다.'),
    'cramerv': ('Use to quantify the strength of association in a categorical contingency table.', '범주형 분할표에서 연관성의 크기를 평가할 때 사용합니다.'),
    'phi': ('Use for the strength and direction of association in a binary 2×2 table.', '이항 2×2 표에서 연관성의 크기·방향을 평가할 때 사용합니다.'),
    'padjust': ('Use when interpreting a family of hypotheses to control family-wise error or false discovery rate.', '여러 가설을 함께 해석하면서 가족단위 오류율·거짓발견률을 제어할 때 사용합니다.'),
    'tinterval': ('Use to estimate a population mean when population SD is unknown and t-model assumptions are reasonable.', '모집단 표준편차를 모르며 t 모형 가정이 적절할 때 모집단 평균을 추정하는 데 사용합니다.'),
    'zinterval': ('Use to estimate a population mean when population SD is known and a normal approximation is appropriate.', '모집단 표준편차를 알고 정규근사가 적절할 때 모집단 평균을 추정하는 데 사용합니다.'),
    'tost': ('Use to show that a mean is practically close to a target within prespecified bounds.', '미리 정한 허용 범위에서 평균이 기준값과 실질적으로 동등한지 확인할 때 사용합니다.'),
    'tost2': ('Use to assess practical equivalence of two independent means within prespecified bounds.', '미리 정한 허용 범위에서 독립 두 평균의 실질적 동등성을 확인할 때 사용합니다.'),
    'tostpaired': ('Use to assess practical equivalence of paired measurements within prespecified bounds.', '짝지은 측정값이 미리 정한 허용 범위에서 동등한지 확인할 때 사용합니다.'),
    'yuen': ('Use for independent-group location comparisons when outliers or heavy tails motivate trimmed means.', '이상값·두꺼운 꼬리 때문에 절사평균으로 독립 두 그룹의 위치를 비교할 때 사용합니다.'),
    'trimmedanova': ('Use for robust comparison of several independent groups through trimmed means.', '절사평균으로 여러 독립 그룹을 강건하게 비교할 때 사용합니다.'),
    'winsorcor': ('Use to reduce extreme-value influence when assessing association between numeric variables.', '숫자 변수의 연관성을 평가하면서 극단값의 영향을 줄이고 싶을 때 사용합니다.'),
    'linearmodel': ('Use for continuous outcomes with multiple factors, covariates or interactions.', '여러 요인·공변량·상호작용으로 연속형 결과를 분석할 때 사용합니다.'),
    'glm': ('Use when the response distribution calls for a binary, count or positive-response model.', '이항·빈도·양수 반응 등 결과 분포에 맞춘 모형이 필요할 때 사용합니다.'),
    'poissonreg': ('Use for event counts whose conditional variance is reasonably close to their conditional mean.', '조건부 분산이 조건부 평균과 비슷한 사건 횟수를 분석할 때 사용합니다.'),
    'nbreg': ('Use for counts with overdispersion beyond a Poisson model.', '포아송 모형보다 분산이 큰 과산포 빈도 자료에 사용합니다.'),
    'zeroinflated': ('Use when a separate structural-zero process is plausible in addition to ordinary count variation.', '일반 빈도 변동 외에 별도의 구조적 0 발생 과정이 타당할 때 사용합니다.'),
    'tobit': ('Use for continuous outcomes recorded at a detection or censoring limit.', '검출한계·검열 경계 때문에 연속형 반응이 경계값으로 기록될 때 사용합니다.'),
    'quantreg': ('Use to study a median or another conditional quantile rather than only the mean.', '평균뿐 아니라 조건부 중앙값·다른 분위수의 관계를 분석할 때 사용합니다.'),
    'robustreg': ('Use for a continuous response when response outliers would strongly affect ordinary least squares.', '반응 이상값이 최소제곱 회귀에 큰 영향을 줄 때 연속형 반응 분석에 사용합니다.'),
    'multinomial': ('Use to predict unordered categories, such as choices among several alternatives.', '여러 선택지처럼 순서가 없는 범주형 결과를 예측할 때 사용합니다.'),
    'ordinal': ('Use for ordered outcomes such as rating levels when proportional odds is reasonable.', '평가 등급처럼 순서가 있는 결과에서 비례오즈 가정이 적절할 때 사용합니다.'),
    'mediation': ('Use to examine a proposed indirect pathway through a mediator.', '매개변수를 거치는 간접 경로를 살펴볼 때 사용합니다.'),
    'moderation': ('Use when a predictor effect may depend on another variable.', '설명변수의 효과가 다른 변수의 수준에 따라 달라질 수 있을 때 사용합니다.'),
    'mixedmodel': ('Use for repeated or clustered continuous measurements with subject-specific variation.', '대상별 차이가 있는 반복·군집 연속형 측정에 사용합니다.'),
    'glmm': ('Use for repeated or clustered binary/count outcomes when subject-specific effects are of interest.', '반복·군집 이항·빈도 결과에서 대상별 조건부 효과가 관심일 때 사용합니다.'),
    'gee': ('Use for repeated or clustered outcomes when population-average effects are of interest.', '반복·군집 결과에서 모집단 평균 효과가 관심일 때 사용합니다.'),
    'crossvalidate': ('Use to estimate performance on unseen observations and compare predictive choices.', '새 관측값에 대한 예측 성능을 추정하고 모형 선택을 비교할 때 사용합니다.'),
    'modelcompare': ('Use to assess whether added predictors or paths improve a baseline model on common data.', '같은 자료에서 설명변수·경로 추가가 기존 모형을 개선하는지 평가할 때 사용합니다.'),
    'logisticcompare': ('Use to assess whether added predictors improve binary model fit and validated prediction.', '설명변수 추가가 이항 모형의 적합도와 검증 예측 성능을 개선하는지 평가할 때 사용합니다.'),
    'bayesmean': ('Use to combine prior knowledge with numeric observations to estimate a mean and predict a new value.', '사전 지식과 숫자 관측값을 결합해 평균을 추정하고 새 관측값을 예측할 때 사용합니다.'),
    'bayescompare': ('Use to quantify uncertainty and evidence about two independent normal means using specified priors.', '지정한 사전분포로 독립 정규 두 평균 차이의 불확실성과 증거를 평가할 때 사용합니다.'),
    'bayesttest': ('Use to compare zero-effect and nonzero-effect hypotheses with Bayes factors in t-test designs.', 't 검정 설계에서 효과 없음·있음 가설의 증거를 Bayes factor로 비교할 때 사용합니다.'),
    'bayesanova': ('Use to compare equal-mean and group-effect hypotheses for independent normal groups.', '독립 정규 그룹에서 평균 동일 가설과 그룹 효과 가설의 증거를 비교할 때 사용합니다.'),
    'bayesproportion': ('Use to update uncertainty about a binary success probability with prior information.', '사전 정보를 반영해 이항 성공 확률의 불확실성을 갱신할 때 사용합니다.'),
    'bayesrate': ('Use to update an event rate from counts and observation exposure with prior information.', '횟수·관측 노출량과 사전 정보로 사건 발생률을 갱신할 때 사용합니다.'),
    'bootstrapci': ('Use to estimate uncertainty of a statistic by resampling independent representative observations.', '독립적이고 대표성 있는 관측값을 재표집해 통계량의 불확실성을 추정할 때 사용합니다.'),
    'bayesbootstrap': ('Use for weighted posterior uncertainty in a statistic or a two-sample statistic difference.', '통계량 또는 두 표본 통계량 차이의 가중 사후 불확실성을 평가할 때 사용합니다.'),
    'metaanalysis': ('Use to synthesize comparable effect estimates from independent studies.', '독립 연구에서 얻은 비교 가능한 효과 추정치를 통합할 때 사용합니다.'),
    'metaregression': ('Use to examine whether study-level characteristics explain variation in study effects.', '연구 수준 특성이 연구 간 효과 차이를 설명하는지 살펴볼 때 사용합니다.'),
    'metasubgroup': ('Use to compare pooled effects across predefined categories of studies.', '미리 정한 연구 범주 사이의 통합 효과를 비교할 때 사용합니다.'),
    'efa': ('Use to explore an unknown latent structure among related items before specifying a measurement model.', '측정모형을 지정하기 전에 관련 문항의 알려지지 않은 잠재 구조를 탐색할 때 사용합니다.'),
    'cfa': ('Use to evaluate a theory-based factor structure or measurement invariance across groups.', '이론에 근거한 요인 구조 또는 집단 간 측정동일성을 평가할 때 사용합니다.'),
    'sem': ('Use to assess hypothesized relationships between latent constructs and their indicators.', '잠재 개념·지표 간 가정한 관계를 평가할 때 사용합니다.'),
    'pca': ('Use to reduce correlated numeric variables to a smaller set of variance-preserving components.', '상관된 숫자 변수를 변동을 요약하는 적은 수의 성분으로 축약할 때 사용합니다.'),
    'discriminantanalysis': ('Use for supervised classification into known groups using numeric predictors.', '숫자 설명변수로 관측값을 미리 알려진 그룹으로 분류할 때 사용합니다.'),
    'kmeans': ('Use to explore compact groups in numeric data without predefined class labels.', '미리 정한 정답 범주 없이 숫자 자료의 밀집 그룹을 탐색할 때 사용합니다.'),
    'hcluster': ('Use to explore nested similarity groups and inspect a dendrogram.', '자료의 계층적 유사 그룹을 탐색하고 덴드로그램을 확인할 때 사용합니다.'),
    'arima': ('Use to model serial dependence and forecast an equally spaced time series.', '등간격 시계열의 시간 의존성을 모형화하고 미래 값을 예측할 때 사용합니다.'),
    'sarima': ('Use to forecast an equally spaced series with a recurring seasonal pattern.', '반복되는 계절 패턴이 있는 등간격 시계열을 예측할 때 사용합니다.'),
    'survivalanalysis': ('Use for time-to-event data with censoring, from group comparisons to predictor-adjusted hazards.', '중도절단이 있는 사건 시간에서 그룹 비교·설명변수 보정 위험 분석에 사용합니다.'),
    'kaplanmeier': ('Use to estimate survival probabilities over time without specifying an event-time distribution.', '사건 시간 분포를 지정하지 않고 시간에 따른 생존확률을 추정할 때 사용합니다.'),
    'logrank': ('Use to compare independent survival groups; power is often best when hazards are proportional.', '독립 그룹의 생존을 비교할 때 사용하며 비례위험에서 검정력이 좋은 경우가 많습니다.'),
    'cox': ('Use to assess predictor-adjusted event hazards while leaving the baseline hazard unspecified.', '기저 위험함수를 지정하지 않고 설명변수를 보정한 사건 위험을 분석할 때 사용합니다.'),
    'parametricsurvival': ('Use to model censored event times with a chosen distribution and interpret effects as time ratios.', '선택한 분포로 중도절단 사건 시간을 모형화하고 효과를 시간비로 해석할 때 사용합니다.'),
    'testpower': ('Use before a t-test study to assess detection probability for an assumed effect and sample size.', 't 검정 연구 전에 가정한 효과·표본 수에서 효과를 탐지할 확률을 평가할 때 사용합니다.'),
    'samplesize': ('Use to plan a t-test study with a prespecified effect, significance level and target power.', '가정한 효과·유의수준·목표 검정력으로 t 검정 연구의 표본 수를 계획할 때 사용합니다.'),
    'designpower': ('Use to plan detection probability for mean, proportion or variance comparisons at a fixed sample size.', '고정 표본 수에서 평균·비율·분산 비교의 효과 탐지 확률을 계획할 때 사용합니다.'),
    'designsize': ('Use to plan sample size for mean, proportion or variance comparisons at a target power.', '목표 검정력에서 평균·비율·분산 비교에 필요한 표본 수를 계획할 때 사용합니다.'),
}


def analysis_help(item, parameters, korean=False):
    index = int(bool(korean))
    purpose = PURPOSES.get(item['id'])
    description = purpose[index] if purpose else catalog_description(item, korean).split('. ', 1)[0].rstrip('.') + '.'
    usage = USE_CASES[item['id']][index]
    headings = ('모델 설명', '사용 시점', '파라미터 설명') if korean else ('Model', 'When to use', 'Parameters')
    return '\n\n'.join(f'{heading}\n{body}' for heading, body in zip(headings, (description, usage, parameters)))


# Dedicated basic-analysis controls share this copy across Android and Web.
GENERAL_HELP = {
    'ttest': (
        ('Tests whether a population mean equals a target.', 'Use for one numeric sample with unknown population SD; review normality and outliers.', 'Choose sample column, null mean and alternative. Blank cells are omitted.'),
        ('모집단 평균이 기준값과 같은지 검정합니다.', '모집단 표준편차를 모르는 숫자 표본 하나에 사용하며 정규성·이상값을 확인합니다.', '표본 열·귀무가설 평균·대립가설을 선택합니다. 빈 셀은 제외합니다.')),
    'ttest2': (
        ('Tests a specified difference between two independent population means.', 'Use for independent groups such as treatment and control. Welch allows unequal variances; Student assumes equal variances.', 'Choose groups A/B or two columns, Welch/Student, null difference and alternative. Difference is A−B.'),
        ('독립 두 모집단 평균의 차이가 기준 차이와 같은지 검정합니다.', '처리군·대조군처럼 독립인 그룹에 사용합니다. Welch는 이분산을 허용하며 Student는 등분산을 가정합니다.', '그룹 A·B 또는 열 두 개, Welch/Student, 기준 차이·대립가설을 선택합니다. 차이는 A−B입니다.')),
    'ttestpaired': (
        ('Tests whether the mean within-pair difference equals a target.', 'Use for before/after measurements on the same subjects or matched pairs; check normality of differences.', 'Choose paired columns or group/value columns, matching method, null difference and alternative. Use complete pairs; difference is A−B.'),
        ('대응 쌍 차이의 모집단 평균이 기준값과 같은지 검정합니다.', '같은 대상의 전·후 측정 또는 짝지은 표본에 사용하며 차이값의 정규성을 확인합니다.', '대응 열 또는 그룹·값 열, 연결 방식·기준 차이·대립가설을 선택합니다. 완전한 쌍을 사용하며 차이는 A−B입니다.')),
    'ztest': (
        ('Tests whether a population mean equals a target using a known population SD.', 'Use when population SD is known and the mean sampling distribution is normal or adequately approximated.', 'Choose sample column, null mean, known population SD σ and alternative.'),
        ('알려진 모집단 표준편차로 모집단 평균이 기준값과 같은지 검정합니다.', '모집단 표준편차를 알고 평균의 표집분포가 정규이거나 정규근사가 적절할 때 사용합니다.', '표본 열·귀무가설 평균·알려진 모집단 표준편차 σ·대립가설을 선택합니다.')),
    'ztest2': (
        ('Tests a specified difference between independent means using known population SDs.', 'Use when both population SDs are known and normal approximation is adequate.', 'Choose groups A/B, null difference, population SDs σx/σy and alternative. Difference is A−B.'),
        ('알려진 모집단 표준편차로 독립 두 모집단 평균의 기준 차이를 검정합니다.', '두 모집단 표준편차를 알고 정규근사가 적절한 독립 두 표본에 사용합니다.', '그룹 A·B, 기준 차이·모집단 표준편차 σx/σy·대립가설을 선택합니다. 차이는 A−B입니다.')),
    'anova': (
        ('Tests whether all independent group population means are equal.', 'Use for several independent numeric groups. A significant result indicates at least one different mean; post-hoc tests locate the differences.', 'Choose group columns or group/value columns. Welch uses Games–Howell with unequal variances; Classic assumes equal variances and uses Tukey–Kramer.'),
        ('독립 그룹들의 모집단 평균이 모두 같은지 검정합니다.', '여러 독립 숫자 그룹에 사용합니다. 유의하면 적어도 한 평균이 다르며 사후비교로 어느 그룹인지 확인합니다.', '그룹별 열 또는 그룹·값 열을 선택합니다. Welch는 이분산·Games–Howell, Classic은 등분산·Tukey–Kramer를 사용합니다.')),
    'wilcoxon': (
        ('Tests whether a sample or paired-difference distribution is symmetric about the null target.', 'Use for signed-rank comparisons of one sample or matched measurements. Location interpretation requires symmetric differences.', 'Choose one sample or complete paired columns and alternative. Grouped pairs use subject ID or row order.'),
        ('표본 또는 대응 차이의 분포가 귀무가설 기준값을 중심으로 대칭인지 검정합니다.', '일표본·짝지은 측정값의 부호순위 비교에 사용하며 위치 차이 해석에는 차이 분포의 대칭성이 필요합니다.', '일표본 또는 완전한 대응 열과 대립가설을 선택합니다. 그룹 자료는 대상 ID·행 순서로 대응시킵니다.')),
    'mannwhitney': (
        ('Compares two independent distributions using ranks under the null of equal distributions.', 'Use for independent ordinal or numeric groups. A location interpretation requires similar distribution shapes.', 'Choose groups A/B or two columns and alternative; observations must be independent between groups.'),
        ('분포가 같다는 귀무가설에서 순위를 이용해 독립 두 분포를 비교합니다.', '독립된 순서형·숫자 그룹에 사용하며 위치 차이로 해석하려면 분포 형태가 비슷해야 합니다.', '그룹 A·B 또는 열 두 개와 대립가설을 선택합니다. 그룹 간 관측값은 독립이어야 합니다.')),
    'kruskal': (
        ('Tests whether independent groups have the same distribution using pooled ranks.', 'Use for several independent ordinal or numeric groups. A location interpretation requires comparable distribution shapes.', 'Choose group columns or group/value columns. Use rank post-hoc comparisons to locate differences after a significant result.'),
        ('통합 순위를 이용해 독립 그룹들의 분포가 같은지 검정합니다.', '여러 독립 순서형·숫자 그룹에 사용하며 위치 차이 해석에는 비슷한 분포 형태가 필요합니다.', '그룹별 열 또는 그룹·값 열을 선택합니다. 유의한 뒤 차이가 있는 쌍은 순위 사후비교로 확인합니다.')),
    'chi2independence': (
        ('Tests whether two categorical variables are statistically independent.', 'Use for independent categorical observations with adequate expected counts; consider Fisher exact for sparse 2×2 tables.', 'Choose two category columns with complete rows and at least two categories per column. Yates correction applies only to 2×2 tables.'),
        ('두 범주형 변수가 통계적으로 독립인지 검정합니다.', '기대빈도가 충분한 독립 범주 관측값에 사용하며 작은 빈도의 2×2 표는 Fisher 정확 검정을 고려합니다.', '완전한 행이 있는 두 범주 열을 선택하며 각 열에 범주 2개 이상이 필요합니다. Yates 보정은 2×2 표에만 적용합니다.')),
    'fisherexact': (
        ('Tests association in a 2×2 table conditional on its margins, under a null odds ratio of one.', 'Use for independent binary categories, especially when counts are too small for a chi-square approximation.', 'Choose two binary category columns and alternative. Uses complete rows; paired binary outcomes require McNemar.'),
        ('주변합을 고정한 2×2 표에서 오즈비가 1이라는 귀무가설로 연관성을 검정합니다.', '독립 이항 범주, 특히 빈도가 작아 χ² 근사가 부적절할 때 사용합니다.', '두 이항 범주 열과 대립가설을 선택합니다. 완전한 행을 사용하며 대응 이항 결과는 McNemar를 사용합니다.')),
}


REGRESSION_HELP = {
    'linear': (
        ('Fits a straight-line relationship and estimates the slope and intercept.', 'Use to predict a continuous response from one numeric predictor and assess its linear relationship.', 'Use x/y observations. Optional ridge, lasso or elastic net controls coefficient shrinkage; α is penalty strength and L1 ratio mixes lasso/ridge.'),
        ('직선 관계를 적합하고 기울기·절편을 추정합니다.', '숫자 설명변수 하나로 연속형 반응을 예측하고 선형 관계를 평가할 때 사용합니다.', 'x·y 관측값을 사용합니다. 선택적 ridge·lasso·elastic net은 계수를 축소하며 α는 벌점 강도, L1 비율은 lasso·ridge 혼합 비율입니다.')),
    'multiple': (
        ('Estimates the linear relationship of several predictors with a continuous response.', 'Use to assess a predictor while accounting for other measured predictors, or to predict numeric outcomes.', 'Choose the response column; other columns are predictors. Optional ridge/lasso/elastic net uses α for strength and L1 ratio for mixing.'),
        ('여러 설명변수와 연속형 반응의 선형 관계를 추정합니다.', '다른 측정 변수를 보정한 관계를 평가하거나 숫자 결과를 예측할 때 사용합니다.', '반응 열을 선택하며 나머지 열은 설명변수입니다. 선택적 ridge·lasso·elastic net의 α는 벌점 강도, L1 비율은 혼합 비율입니다.')),
    'quadratic': (
        ('Fits a second-degree polynomial response curve.', 'Use when a continuous response has a curved relationship with one predictor.', 'Use x/y observations; the model includes x and x² terms.'),
        ('2차 다항식 반응 곡선을 적합합니다.', '설명변수 하나와 연속형 반응의 관계가 곡선일 때 사용합니다.', 'x·y 관측값을 사용하며 x·x² 항을 포함합니다.')),
    'polynomial': (
        ('Fits a polynomial relationship of the selected degree.', 'Use for a smooth curved relationship; higher degrees need more data and can overfit.', 'Choose response column and polynomial degree. Check the fitted curve and residuals.'),
        ('선택한 차수의 다항식 관계를 적합합니다.', '매끄러운 곡선 관계에 사용하며 높은 차수는 더 많은 자료가 필요하고 과적합될 수 있습니다.', '반응 열·다항식 차수를 선택하고 적합 곡선·잔차를 확인합니다.')),
    'logarithmic': (
        ('Fits a response linear in log(x).', 'Use when response changes with a diminishing slope over positive x values.', 'Use x/y observations with x>0.'),
        ('log(x)에 선형인 반응 관계를 적합합니다.', '양수 x에서 x가 커질수록 반응의 변화 폭이 줄어드는 관계에 사용합니다.', 'x>0인 x·y 관측값을 사용합니다.')),
    'exponential': (
        ('Fits an exponential growth or decay curve.', 'Use for positive responses whose change is approximately proportional to their current size.', 'Use x/y observations with y>0; the fit uses a log-transformed response.'),
        ('지수 증가·감소 곡선을 적합합니다.', '현재 크기에 비례해 변하는 양수 반응의 증가·감소를 분석할 때 사용합니다.', 'y>0인 x·y 관측값을 사용하며 로그 변환한 반응으로 적합합니다.')),
    'power': (
        ('Fits a power-law relationship y=a·x^b.', 'Use for positive variables related through multiplicative scaling.', 'Use x/y observations with x>0 and y>0; fitting uses log-transformed values.'),
        ('거듭제곱 관계 y=a·x^b를 적합합니다.', '양수 변수 사이의 곱셈적 크기 관계를 분석할 때 사용합니다.', 'x>0·y>0인 관측값을 사용하며 로그 변환값으로 적합합니다.')),
    'logistic': (
        ('Models binary-event probability and predictor effects on log odds.', 'Use for a 0/1 response such as event/no event; coefficient inference concerns log odds.', 'Choose a binary response column; others are predictors. Firth handles separation. Optional regularization uses α and, for elastic net, L1 ratio.'),
        ('이항 사건의 발생 확률과 로그 오즈에 대한 설명변수 효과를 추정합니다.', '발생·미발생 같은 0/1 반응에 사용하며 계수 추론은 로그 오즈 기준입니다.', '이항 반응 열을 선택하며 나머지는 설명변수입니다. Firth는 분리에 대응합니다. 선택적 벌점은 α, elastic net은 L1 비율도 사용합니다.')),
    'randomforest': (
        ('Combines many decision trees to predict a category or numeric response.', 'Use for nonlinear prediction with interactions; assess prediction with validation metrics.', 'Choose response, classification/regression task, tree count, maximum depth and seed.'),
        ('여러 결정트리를 결합해 범주·숫자 반응을 예측합니다.', '상호작용이 있는 비선형 예측에 사용하며 검증 지표로 예측 성능을 평가합니다.', '반응 열·분류/회귀 방식·트리 수·최대 깊이·시드를 선택합니다.')),
    'svm': (
        ('Uses a support-vector boundary or function for classification or regression.', 'Use for nonlinear prediction through a selected kernel.', 'Choose response, task and kernel. Predictors are standardized; use C > 0, gamma > 0 or auto, and regression epsilon >= 0 in response units. Binary classification uses 0/1. Training metrics use training data; cross-validation metrics are reported separately.'),
        ('서포트 벡터의 경계·함수로 분류·회귀를 수행합니다.', '커널을 이용한 비선형 예측에 사용합니다.', '반응 열·SVM 유형·커널을 선택합니다. 설명변수는 표준화되며 C > 0, 감마 > 0 또는 auto, 회귀 엡실론 >= 0(종속변수 단위)를 사용합니다. 분류는 0/1 자료를 사용합니다. 학습 지표는 학습 데이터 기준이며 교차검증 지표는 별도로 표시합니다.')),
    'bayeslinear': (
        ('Estimates linear coefficients and predictive uncertainty using a prior and a normal response model.', 'Use to combine prior information with data for continuous-response prediction.', 'Choose response, prior SD, credible level and variance-prior shape/scale. For NUTS set draws, warmup and chains; review R-hat, ESS and divergences.'),
        ('사전분포·정규 반응 모형으로 선형 계수와 예측 불확실성을 추정합니다.', '사전 정보와 자료를 결합해 연속형 반응을 예측할 때 사용합니다.', '반응 열·사전 SD·구간 수준·분산 사전 shape/scale을 지정합니다. NUTS는 추출 수·워밍업·체인 수를 설정하고 R-hat·ESS·발산 수를 확인합니다.')),
    'bayeslogistic': (
        ('Estimates binary-event probabilities and coefficient posterior uncertainty.', 'Use to combine prior information with binary observations for probability prediction.', 'Choose 0/1 response, prior SD, credible level and inference method. For NUTS set draws, warmup and chains; review R-hat, ESS and divergences.'),
        ('이항 사건 확률과 계수의 사후 불확실성을 추정합니다.', '사전 정보와 이항 관측값을 결합해 사건 확률을 예측할 때 사용합니다.', '0/1 반응 열·사전 SD·구간 수준·추론 방식을 지정합니다. NUTS는 추출 수·워밍업·체인 수를 설정하고 R-hat·ESS·발산 수를 확인합니다.')),
    'custom': (
        ('Fits the parameters of a user-specified response function.', 'Use when a scientific or practical model specifies the curve to fit.', 'Set formula and independent variable. Initial values/bounds use [[parameter,initial,lower,upper],…]; upper bounds are optional.'),
        ('사용자가 지정한 반응 함수의 파라미터를 적합합니다.', '과학적·실무적 모형으로 적합할 곡선의 식이 정해져 있을 때 사용합니다.', '수식·독립변수를 지정합니다. 시작값·경계는 [[파라미터,시작값,하한,상한],…]이며 상한은 생략할 수 있습니다.')),
}


def build_general_help():
    headings = (('Model', 'When to use', 'Parameters'), ('모델 설명', '사용 시점', '파라미터 설명'))
    return {id_: {key: '\n\n'.join(f'{heading}\n{body}' for heading, body in zip(headings[index], blocks[index]))
                  for index, key in enumerate(('help', 'helpKo'))}
            for id_, blocks in {**GENERAL_HELP, **{'regression-' + key: value for key, value in REGRESSION_HELP.items()}}.items()}
