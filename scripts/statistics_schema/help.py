"""Concise operational help shared by Android and Web analysis forms."""
from .catalog import catalog_description

TIME_HELP = (
    'Choose a complete numeric series in time order with equal spacing. Set model orders, forecast horizon and prediction level. Review forecasts and residual diagnostics.',
    '시간순·등간격의 완전한 숫자 시계열을 선택합니다. 모형 차수·예측 길이·예측구간 수준을 설정하고 예측·잔차 진단을 확인하세요.')
DATE_HELP = (
    ' Optional dates: YYYY-MM-DD or integer years in a separate column.',
    ' 날짜는 별도 열에 YYYY-MM-DD 또는 정수 연도로 입력합니다.')

# Form help explains choices in the visible controls; expression help uses the
# compact function descriptions in catalog.py. Keep numerical contracts in forms
# and definitions rather than repeating their implementation in this text.
FORM_HELP = {
    'normaltest': (
        'Select one numeric sample column with at least 8 finite observations and variation. K² combines skewness and kurtosis z scores; its p value uses chi-square(2). For n ≤ 20 the kurtosis approximation may be inaccurate. Review the Q–Q plot; a large p value does not prove normality.',
        '유한 관측값 8개 이상이며 변동이 있는 숫자 표본 열을 선택하세요. K²는 왜도·첨도의 z값을 결합하며 p값은 자유도 2의 χ² 근사를 사용합니다. n ≤ 20에서는 첨도 근사가 부정확할 수 있습니다. Q–Q plot과 함께 해석하며 큰 p값이 정규성을 증명하지는 않습니다.'),
    'impute': (
        'Choose a replacement method and, for k-NN, neighbor count. Analyze first, then Apply to current data to fill missing cells while retaining observed values and headers. Reanalyze after editing data.',
        '대체 방법·k-NN 이웃 수를 선택합니다. 분석 후 현재 데이터에 적용하면 관측값·헤더를 유지하며 결측 셀을 채웁니다. 데이터 수정 후에는 다시 분석하세요.'),
    'propztest': (
        'Choose binary observations and a success value, or success/trial counts. Enter the null proportion p0 (0<p0<1) and alternative. For counts, rows belong to the same population.',
        '이항 자료·성공 값 또는 성공 수·시행 수를 선택합니다. 기준 비율 p0(0<p0<1)·대립가설을 지정하세요. 빈도의 각 행은 같은 모집단입니다.'),
    'propztest2': (
        'Choose two independent binary samples and a common success value, or two count rows ordered A then B. Alternatives refer to A−B; use McNemar for paired outcomes.',
        '독립 두 이항 표본·공통 성공 값 또는 A·B 순서의 빈도 두 행을 입력합니다. 대립가설은 A−B 기준; 대응 결과는 McNemar를 사용하세요.'),
    'mcnemar': (
        'Choose paired binary columns or a 2×2 count table. Select exact, continuity-corrected or asymptotic inference; results show discordant pairs and p value.',
        '대응 이항 열 또는 2×2 빈도표를 선택합니다. 정확·연속성 보정·점근 검정 중 선택하면 불일치 쌍 수·p값을 표시합니다.'),
    'icc': (
        'Select complete subject × rater data. Choose one-way, two-way random absolute agreement or two-way mixed consistency, then single/average rating and confidence level.',
        '완전한 대상×평가자 자료를 선택합니다. 일원·이원 랜덤 절대 일치·이원 혼합 일관성 중 모형을 정하고 단일/평균 평가·신뢰수준을 지정하세요.'),
    'cohenkappa': (
        'Choose two rater columns or a square count table with the same category order. Select unweighted, linear or quadratic weights; weighted categories must be ordered.',
        '두 평가자 열 또는 같은 범주 순서의 정방 빈도표를 선택합니다. 무가중·선형·제곱 가중치를 지정하며 가중 분석은 순서형 범주에 사용하세요.'),
    'blandaltman': (
        'Select two measurements per independent subject. Difference uses A−B; log mode requires positive values and reports ratios. Review bias, limits of agreement and the proportional-bias trend.',
        '독립 대상별 두 측정값을 선택합니다. 차이는 A−B, 로그 방식은 양수 자료의 비율입니다. 편향·일치한계·비례 편향 추세를 확인하세요.'),
    'kstest': (
        'Choose two numeric samples or a sample and reference distribution. Set reference parameters independently of the tested sample.',
        '두 숫자 표본 또는 표본·기준분포를 선택합니다. 기준 모수는 검정 표본과 독립적으로 지정하세요.'),
    'tukey': (
        'Select independent group columns or group/value columns. Tukey–Kramer compares all means under equal variances, with adjusted p values and simultaneous 95% intervals.',
        '독립 그룹 열 또는 그룹·값 열을 선택합니다. 등분산 가정의 Tukey–Kramer로 모든 평균 쌍·보정 p값·95% 동시 구간을 비교합니다.'),
    'gameshowell': (
        'Select independent group columns or group/value columns. Games–Howell allows unequal variances and reports adjusted p values and simultaneous 95% intervals.',
        '독립 그룹 열 또는 그룹·값 열을 선택합니다. 이분산을 허용하는 Games–Howell로 보정 p값·95% 동시 구간을 확인합니다.'),
    'ancova': (
        'Choose group, response and numeric covariates. Results include adjusted means and Type II tests; enable the slope-homogeneity check as needed.',
        '그룹·종속변수·숫자 공변량을 선택합니다. 조정 평균·Type II 검정을 제공하며 기울기 동질성 검정을 선택할 수 있습니다.'),
    'twowayanova': (
        'Choose two categorical factors and a numeric response from independent observations. Enable interaction to test joint factor effects; results include Type III tests and cell means.',
        '독립 관측의 두 범주 요인·숫자 반응을 선택합니다. 상호작용을 켜면 요인의 결합 효과를 검정합니다. Type III 검정·조합별 평균 제공.'),
    'manova': (
        'Select one-way, factorial or repeated design and multiple response columns. Repeated data use one complete row per subject and equal response blocks in time order. Review multivariate tests and response summaries.',
        '일요인·요인설계·반복측정 방식과 여러 종속변수 열을 선택합니다. 반복측정은 대상별 완전한 행에 시점 순서의 같은 크기 반응 블록을 입력하세요. 다변량 검정·변수별 요약 제공.'),
    'repeatedanova': (
        'Select complete condition columns with one subject per row. For two factors, set the second-factor level count. Review sphericity corrections and paired comparisons; Holm adjusts post-hoc p values.',
        '행=대상인 완전한 조건 열을 선택합니다. 이요인은 둘째 요인 수준 수를 지정하세요. 구형성 보정·대응 사후비교를 확인하며 사후 p값은 Holm 보정입니다.'),
    'friedman': (
        'Select at least three repeated-condition columns, with complete measurements for the same subject in each row. Reports a tie-corrected approximate χ² test and Kendall W.',
        '같은 대상의 완전한 측정값을 행에 놓고 반복 조건 열을 3개 이상 선택합니다. 동점 보정 χ² 근사 검정·Kendall W 제공.'),
    'tost': (
        'Choose a sample and target mean. Prespecify equivalence bounds in measurement units and alpha. Equivalence requires both one-sided p values below alpha; alpha=.05 gives a 90% interval.',
        '표본·기준평균을 선택하고 원래 단위의 동등성 하한·상한과 alpha를 미리 정합니다. 두 단측 p값 모두 alpha 미만이면 동등; alpha=.05의 구간은 90%입니다.'),
    'tost2': (
        'Choose independent groups A and B, Welch or Student, and prespecified bounds for A−B. Equivalence requires both one-sided p values below alpha.',
        '독립 그룹 A·B, Welch/Student, 미리 정한 A−B의 동등성 하한·상한을 선택합니다. 두 단측 p값 모두 alpha 미만이면 동등입니다.'),
    'tostpaired': (
        'Choose complete paired columns or match by subject ID. Prespecify bounds for A−B; equivalence requires both one-sided p values below alpha.',
        '완전한 대응 열 또는 대상 ID 연결을 선택하고 A−B의 동등성 하한·상한을 미리 정합니다. 두 단측 p값 모두 alpha 미만이면 동등입니다.'),
    'yuen': (
        'Select two independent samples and trimming per tail (default .20). Compares trimmed means A−B; each group needs at least two retained values and positive Winsorized variance.',
        '독립 두 표본·꼬리별 절사 비율(기본 .20)을 선택합니다. 절사평균 A−B 비교; 절사 후 그룹당 2개 이상·양의 Winsorized 분산이 필요합니다.'),
    'linearmodel': (
        'Choose response and predictors, marking categorical predictors. Interaction order 1 is additive, 2 includes all pairs. Select Type II/III and coding; Type III interactions use sum contrasts. Center numeric covariates when interpreting interactions.',
        '반응·설명변수를 선택하고 범주 변수를 표시합니다. 상호작용 차수 1은 가법, 2는 모든 쌍입니다. Type II/III·코딩을 선택하며 Type III 상호작용은 합 대비를 사용하세요. 숫자 상호작용 해석에는 중심화를 고려하세요.'),
    'glm': (
        'Choose response, predictors, family and link. Binomial uses 0/1, counts nonnegative integers, Gamma/inverse Gaussian positive values. Exposure uses a log link; NB2 alpha can be fixed or estimated.',
        '반응·설명변수·분포·연결함수를 선택합니다. 이항은 0/1, 빈도는 음이 아닌 정수, Gamma·역가우스는 양수입니다. 노출량은 로그 연결, NB2 alpha는 고정/추정을 선택하세요.'),
    'mixedmodel': (
        'Choose subject ID, continuous response and predictors. Select a random intercept and up to three slopes; REML is the default. Choose Wald, profile or bootstrap intervals. Compare models with different fixed effects using ML.',
        '대상 ID·연속 반응·설명변수를 선택합니다. 랜덤 절편·최대 3개 기울기, 기본 REML. Wald·프로파일·부트스트랩 구간을 선택하세요. 고정효과가 다른 모형 비교는 ML을 사용합니다.'),
    'glmm': (
        'Choose subject ID, predictors and binary/count response. Select family, integration points and optional offset/exposure. One correlated random slope uses Laplace; refit checks sensitivity to integration settings.',
        '대상 ID·설명변수·이항/빈도 반응을 선택합니다. 분포·적분점·오프셋/노출량을 지정하세요. 상관 랜덤 기울기 1개는 Laplace, refit은 적분 설정에 따른 변화를 확인합니다.'),
    'gee': (
        'Choose cluster ID, response, predictors and family. Select independence, exchangeable or AR(1) working correlation; AR(1) uses equally spaced row order. Add interactions and small-cluster correction as needed.',
        '군집 ID·반응·설명변수·분포를 선택합니다. 작업상관 independence/exchangeable/AR(1), 필요하면 상호작용·소수 군집 보정을 지정하세요. AR(1)은 등간격 행 순서 기준입니다.'),
    'crossvalidate': (
        'Choose response, predictors, model, split and fold count. Stratified binary folds need at least as many observations per class as folds. Review held-out prediction metrics.',
        '반응·설명변수·모형·분할·폴드 수를 선택합니다. 층화 이항 분할은 클래스별 표본 수가 폴드 수 이상이어야 합니다. 홀드아웃 예측 지표를 확인하세요.'),
    'modelcompare': (
        'Choose model family, baseline predictors and added predictors. Compare fit and prediction on common observations, using holdout, saved validation data or CV. For CFA/SEM, keep indicators and add paths, cross-loadings or residual covariances.',
        '분석군·기존/추가 설명변수를 선택합니다. 같은 관측값의 적합도와 홀드아웃·저장 검증자료·CV 성능을 비교하세요. CFA/SEM은 지표를 유지하며 경로·교차적재·잔차 공분산을 추가합니다.'),
    'logisticcompare': (
        'Select binary response, model A predictors and model B additions. Choose saved validation data, stratified holdout or CV. Compare AUC, accuracy, log loss and Brier score; differences are B−A, with lower losses better.',
        '이항 반응·모형 A 설명변수·B 추가 변수를 선택합니다. 저장 검증자료·층화 홀드아웃·CV로 AUC·정확도·Log loss·Brier score를 비교하세요. 차이는 B−A, 손실 감소가 개선입니다.'),
    'bayesmean': (
        'Select a numeric sample, prior parameters, credible level and target. Match the normal-inverse-gamma prior to data units; results include the mean posterior and next-observation prediction.',
        '숫자 표본·사전 모수·베이지안 구간 수준·기준값을 선택합니다. 정규-역감마 사전은 자료 단위에 맞추세요. 평균 사후분포·다음 관측 예측 제공.'),
    'bayescompare': (
        'Select two independent samples and equal/unequal variances. Set NIG priors in data units, credible level, draws and seed. Results compare B−A with posterior intervals and Bayes factors.',
        '독립 두 표본·등/이분산을 선택합니다. 자료 단위에 맞는 NIG 사전·구간 수준·추출 수·시드를 지정하세요. B−A 사후 구간·Bayes factor 제공.'),
    'bayesbootstrap': (
        'Choose one sample or a comparison and statistic. Paired data use complete rows and shared weights; the result is statistic(B)−statistic(A). Set credible level, draws and seed.',
        '단일 표본/비교 방식·통계량을 선택합니다. 대응 자료는 완전한 행에 공통 가중치를 적용하며 결과는 각 열의 통계량 차이 B−A입니다. 구간 수준·추출 수·시드를 지정하세요.'),
    'metaanalysis': (
        'Choose effect/SE, binary events/totals or continuous mean/SD/n input. Select effect measure, fixed/random model and z/HKSJ inference. SE is the study-effect standard error; align effect direction across studies.',
        '효과·SE, 이진 사건 수·전체 수, 연속형 평균·SD·n 중 입력 방식을 선택합니다. 효과 척도·고정/랜덤 모형·z/HKSJ 추론을 지정하세요. SE는 연구 효과의 표준오차이며 연구 간 효과 방향을 맞춥니다.'),
    'metaregression': (
        'Choose effect/SE or raw arm summaries and numeric study moderators. Set model and inference; ratio effects use the log scale. Review moderator tests and residual heterogeneity.',
        '효과·SE 또는 두 군 요약과 숫자 연구 조절변수를 선택합니다. 모형·추론을 정하고 비율 효과는 로그 척도를 사용하세요. 조절변수 검정·잔여 이질성 제공.'),
    'metasubgroup': (
        'Choose study effect/SE or arm summaries and a subgroup column, with at least two studies per subgroup. Compare pooled effects using the joint subgroup-difference test.',
        '연구 효과·SE 또는 두 군 요약·하위그룹 열을 선택합니다. 그룹당 연구 2개 이상이 필요하며 통합 효과·그룹 간 공동 검정으로 비교합니다.'),
    'efa': (
        'Select numeric items and factor count or parallel analysis. Choose PCA, principal-axis or ML extraction and rotation; oblimin/promax allow correlated factors. Review loadings before transferring to CFA.',
        '숫자 문항·요인 수 또는 평행분석을 선택합니다. PCA·주축요인·ML 추출과 회전을 지정하세요. oblimin/promax는 요인 상관을 허용합니다. 적재량을 확인한 뒤 CFA로 연결하세요.'),
    'cfa': (
        'Select indicators and their factor IDs; add cross-loadings as needed. Use ML for continuous or WLSMV for ordered indicators; ML supports FIML for missing data. Choose group/invariance options for multi-group analysis, then review loadings, fit and the diagram.',
        '지표·요인 번호를 지정하고 필요하면 교차적재를 추가합니다. 연속형은 ML, 순서형은 WLSMV; ML 결측은 FIML을 선택하세요. 다집단은 그룹·동일성 수준을 지정하고 적재량·적합도·경로도를 확인합니다.'),
    'sem': (
        'Assign indicator factor IDs and acyclic latent paths (source,target;…). Use ML for continuous or WLSMV for ordered indicators; ML supports FIML. Set group/invariance, cross-loadings, residual covariances or effect bootstrap as needed. Review standardized paths, direct/indirect/total effects and fit.',
        '지표별 요인 번호·비순환 잠재 경로(출발,도착;…)를 지정합니다. 연속형은 ML, 순서형은 WLSMV; ML 결측은 FIML 선택. 필요하면 집단 동일성·교차적재·잔차 공분산·효과 부트스트랩을 설정하세요. 표준화 경로·직접/간접/총 효과·적합도를 확인합니다.'),
    'pca': (
        'Select complete numeric feature columns, component count and standardization. Standardize when units differ. Review explained variance, scores and loadings.',
        '완전한 숫자 변수 열·주성분 수·표준화를 선택합니다. 단위가 다르면 표준화하세요. 설명분산·점수·로딩을 확인합니다.'),
    'arima': (
        'Select a complete, equally spaced numeric series, oldest first. Set [p,d,q], horizon and level; auto selects intercept/drift by AICc at those orders. Dates use a separate column. Review forecasts, conditional prediction intervals and residual checks.',
        '오래된 값부터 등간격의 완전한 숫자 열을 선택합니다. [p,d,q]·예측 길이·수준 지정; auto는 해당 차수에서 AICc로 절편/드리프트를 선택합니다. 날짜는 별도 열. 예측·조건부 예측구간·잔차 진단을 확인하세요.'),
    'sarima': (
        'Select a complete equally spaced series spanning at least two seasons. Set [p,d,q] and seasonal [P,D,Q,s], horizon and level; dates use a separate column. Review forecasts and residual checks.',
        '두 주기 이상의 등간격 완전 시계열을 선택합니다. [p,d,q]·계절 [P,D,Q,s]·예측 길이·수준을 지정하고 날짜는 별도 열에 입력하세요. 예측·잔차 진단을 확인합니다.'),
    'parametricsurvival': (
        'Choose positive time, event (1=event, 0=censored), optional predictors and Weibull/exponential/lognormal distribution. Optional entry time must satisfy 0≤entry<time. Set a prediction time; review time ratios and survival probabilities.',
        '양수 시간·사건(1=발생, 0=중도절단)·설명변수·Weibull/지수/로그정규 분포를 선택합니다. 진입시간은 0≤진입<시간. 예측 시점을 정하고 시간비·생존확률을 확인하세요.'),
    'designpower': (
        'Choose fixed-sample design and alpha. Effect: known-SD standardized mean shift for z, p1 for one proportion, pA with baseline pB for two proportions, or variance ratio. n is per group for two-group designs.',
        '고정 표본 설계·alpha를 선택합니다. 효과는 z의 알려진 SD 기준 평균 이동, 단일 비율의 p1, 두 비율의 pA·기준 pB, 또는 분산비입니다. 두 그룹 설계의 n은 그룹별 수입니다.'),
    'designsize': (
        'Choose design, effect, alpha and target power. Effects follow the same definitions as designpower; results show minimum n per group, total n and achieved power.',
        '설계·효과·alpha·목표 검정력을 선택합니다. 효과는 designpower와 같은 기준이며 최소 그룹별 n·총 n·달성 검정력을 표시합니다.'),
}


def build_form_help(definitions):
    """Keep each analysis self-contained while reusing concise function copy."""
    return {
        id_: FORM_HELP.get(id_, (catalog_description(item), catalog_description(item, True)))
        for id_, item in definitions.items()
    }
