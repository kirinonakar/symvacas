"""Brief result-reading guidance, shared by the Android and Web presentations."""

# Guidance explains how to read output; it does not infer a conclusion from a
# rounded p value or treat estimation/exploration as a significance test.
GROUPS = {
    'descriptive': 'stats mean median mode variance stdev skewness kurtosis sumdata quartiles covariance',
    'test': 'ttest ttest2 ttestpaired ztest ztest2 propztest propztest2',
    'categorical': 'chi2test chi2independence fisherexact mcnemar',
    'rank': 'wilcoxon mannwhitney kruskal friedman',
    'anova': 'anova welchanova repeatedanova yuen trimmedanova',
    'factorial': 'twowayanova ancova linearmodel',
    'multivariate': 'manova mancova',
    'posthoc': 'tukey gameshowell scheffe dunnett dunn conover',
    'normality': 'shapiro normaltest kstest',
    'variance': 'levene bartlett',
    'correlation': 'correlation pearson spearman kendall winsorcor',
    'effect': 'cohend eta2 cramerv phi',
    'reliability': 'cronbach omega icc cohenkappa',
    'agreement': 'blandaltman',
    'interval': 'tinterval zinterval bootstrapci',
    'equivalence': 'tost tost2 tostpaired',
    'adjustment': 'padjust',
    'regression': 'glm poissonreg nbreg zeroinflated tobit quantreg robustreg multinomial ordinal',
    'cluster': 'mixedmodel glmm gee',
    'comparison': 'modelcompare logisticcompare crossvalidate',
    'bayesian': 'bayesmean bayescompare bayesttest bayesanova bayesproportion bayesrate bayesbootstrap',
    'meta': 'metaanalysis metaregression metasubgroup',
    'exploratory': 'efa pca',
    'structural': 'cfa sem',
    'path': 'mediation moderation',
    'prediction': 'discriminantanalysis',
    'clustering': 'kmeans hcluster',
    'forecast': 'arima sarima',
    'survival': 'survivalanalysis kaplanmeier logrank cox',
    'aft': 'parametricsurvival',
    'power': 'testpower samplesize designpower designsize',
    'imputation': 'impute',
}

GUIDES = {
    'default': (
        'Read estimates in their original units and check which samples or reference categories are compared.\n\nUse intervals to assess estimation uncertainty and diagnostics to review the model fit.',
        '추정값의 단위와 비교한 표본·기준 범주를 먼저 확인하세요.\n\n구간으로 추정의 불확실성을, 진단 결과로 모형의 적합 상태를 확인합니다.'),
    'descriptive': (
        'Check valid n and missing values first. Mean/median describe location; SD, variance and quartiles describe spread.\n\nCompare averages, distributions and outliers to understand each sample.',
        '유효 표본 수 n과 결측값부터 확인하세요. 평균·중앙값은 중심, 표준편차·분산·사분위수는 퍼짐을 나타냅니다.\n\n평균·분포·이상값을 함께 비교해 각 표본의 특성을 파악합니다.'),
    'test': (
        'Check the estimated mean/proportion difference and its direction against the specified null value.\n\nA p value below the chosen significance level (for example .05) is evidence against that null. Use the interval and effect size to assess the magnitude and precision of the difference.',
        '평균·비율 차이의 추정값과 방향, 검정한 기준값을 확인하세요.\n\np값이 정한 유의수준(예: .05)보다 작으면 귀무가설에 반하는 증거입니다. 구간·효과크기로 차이의 크기와 추정 정밀도를 함께 봅니다.'),
    'categorical': (
        'Compare category counts, within-group percentages and any reported odds ratio or association effect size.\n\nThe p value tests the stated association or paired-proportion hypothesis. Check expected-count diagnostics and category order.',
        '범주별 빈도·그룹 내 비율과 제시된 오즈비·연관성 효과크기를 확인하세요.\n\np값은 지정한 연관성 또는 대응 비율 가설에 대한 검정입니다. 기대빈도 진단·범주 순서도 확인합니다.'),
    'rank': (
        'A small p value indicates evidence of a distribution/condition difference under this rank test.\n\nUse rank summaries and suitable post-hoc comparisons to locate differences. Under the relevant shape or symmetry assumptions, the result can be interpreted as a location shift.',
        '작은 p값은 이 순위 검정에서 분포·조건 차이에 대한 증거입니다.\n\n순위 요약·적절한 사후비교로 차이가 있는 그룹·조건을 확인하세요. 해당 방법의 분포 형태·대칭성 가정이 맞으면 위치 차이로 해석할 수 있습니다.'),
    'anova': (
        'A significant overall test indicates at least one group/condition differs in the tested mean or trimmed mean.\n\nLocate differences with adjusted post-hoc comparisons and inspect effect sizes. For repeated measures, review sphericity corrections and corrected p values when reported.',
        '전체 검정이 유의하면 적어도 한 그룹·조건의 평균 또는 절사평균이 다르다는 증거입니다.\n\n보정된 사후비교로 차이가 있는 쌍을 찾고 효과크기를 확인하세요. 반복측정은 제시된 구형성 보정·보정 p값도 확인합니다.'),
    'factorial': (
        'Read each factor/covariate test and any interaction separately. An interaction means an effect depends on another variable.\n\nInspect interactions before averaging main effects. Adjusted means depend on the covariate values and slope assumptions used by the model.',
        '요인·공변량 검정과 상호작용을 각각 읽으세요. 상호작용은 한 변수의 효과가 다른 변수에 따라 달라진다는 뜻입니다.\n\n주 효과를 평균적으로 해석하기 전에 상호작용을 확인하세요. 조정 평균은 사용한 공변량 값·기울기 가정에 의존합니다.'),
    'multivariate': (
        'Multivariate p values test the response means jointly.\n\nInspect individual-response follow-ups and adjusted means to identify which responses contribute to the joint result. Read follow-up p values with the chosen multiplicity adjustment and covariate model.',
        '다변량 p값은 여러 종속변수의 평균을 공동 검정합니다.\n\n변수별 후속 검정·조정 평균으로 어떤 반응이 공동 결과에 기여하는지 확인하세요. 후속 p값은 선택한 다중비교 보정·공변량 모형과 함께 읽습니다.'),
    'posthoc': (
        'Read the pair or treatment/control label before interpreting the sign of its difference.\n\nCompare adjusted p values with the chosen significance level. Use the reported interval to assess the direction, magnitude and precision of each difference.',
        '차이의 부호를 해석하기 전에 비교 쌍·처리군과 대조군의 순서를 확인하세요.\n\n보정 p값을 유의수준과 비교하고 제시된 구간으로 각 차이의 방향·크기·추정 정밀도를 확인합니다.'),
    'normality': (
        'A small p value is evidence against the normal/reference distribution, or equality of distributions for a two-sample KS test.\n\nReview Q–Q plots, sample size, tails and outliers to see where the observed distribution departs from the reference.',
        '작은 p값은 정규·기준분포 가설에 반하는 증거이며, 두 표본 KS 검정에서는 분포가 같다는 가설에 반하는 증거입니다.\n\nQ–Q plot·표본 수·꼬리·이상값을 함께 보며 관측분포가 기준분포와 어느 부분에서 다른지 확인하세요.'),
    'variance': (
        'A small p value is evidence that group variances differ.\n\nCompare group SDs and distributions. Bartlett compares variances under normality; median-centered Brown–Forsythe compares deviations from group medians.',
        '작은 p값은 그룹 분산이 다르다는 증거입니다.\n\n그룹별 표준편차·분포를 비교하세요. Bartlett은 정규성 가정 아래 분산을 비교하며 중앙값 기준 Brown–Forsythe는 그룹 중앙값에서의 편차를 비교합니다.'),
    'correlation': (
        'The coefficient sign indicates direction and its magnitude indicates strength on the chosen linear/rank scale.\n\nThe p value concerns zero association under the test assumptions. Use a scatterplot to examine the relationship, distribution and outliers.',
        '계수의 부호는 방향, 절댓값은 선택한 선형·순위 척도의 연관성 크기를 나타냅니다.\n\np값은 검정 가정에서 연관성이 0인지에 관한 값입니다. 산점도로 관계의 형태·분포·이상값을 확인하세요.'),
    'effect': (
        'Effect size describes the magnitude of a difference or association. Check the metric, comparison direction and any interval.\n\nLabels such as small/large are reference conventions. Assess practical importance using the field, units and study design.',
        '효과크기는 차이·연관성의 크기입니다. 사용한 척도·비교 방향·제시된 구간을 확인하세요.\n\n작음·큼 같은 평가는 참고 기준입니다. 실질적 중요성은 분야·단위·연구 설계를 함께 고려해 판단합니다.'),
    'reliability': (
        'Higher reliability/agreement usually indicates greater consistency. Read the interval and the selected rating/model definition.\n\nAlpha/omega summarize internal consistency; ICC measures numeric-rating reliability and kappa measures categorical agreement with chance adjustment.',
        '신뢰도·일치도가 높을수록 일반적으로 일관성이 높습니다. 구간과 선택한 평가·모형 정의를 함께 읽으세요.\n\nα·ω는 내적 일관성, ICC는 숫자 평가의 신뢰도, κ는 우연 일치를 보정한 범주 판정의 일치도를 나타냅니다.'),
    'agreement': (
        'Bias is the average A−B difference; limits of agreement describe the spread of individual differences. In log mode, read ratios.\n\nCompare the limits with a prespecified acceptable difference and inspect the proportional-bias trend.',
        '편향은 평균 A−B 차이, 일치한계는 개별 차이의 퍼짐입니다. 로그 방식에서는 비율로 읽으세요.\n\n미리 정한 허용 차이와 일치한계를 비교하고 비례 편향 추세를 확인합니다.'),
    'interval': (
        'Read the estimate and interval in the statistic’s units. A wider interval indicates greater estimation uncertainty.\n\nFor example, a 95% confidence procedure produces intervals containing the population parameter in 95% of repeated samples under its assumptions.',
        '추정값·구간을 해당 통계량의 단위로 읽으세요. 구간이 넓을수록 추정 불확실성이 큽니다.\n\n예를 들어 95% 신뢰구간은 가정이 맞을 때 같은 표집 절차를 반복해 얻은 구간 중 95%가 모집단 모수를 포함하도록 구성한 구간입니다.'),
    'equivalence': (
        'TOST establishes equivalence when both one-sided p values are below the chosen alpha.\n\nRead the result against the prespecified equivalence bounds; alpha=.05 corresponds to a 90% TOST interval.',
        'TOST는 두 단측 p값이 모두 선택한 alpha보다 작을 때 동등성을 인정합니다.\n\n미리 정한 동등성 경계와 비교하세요. alpha=.05의 TOST 구간은 90%입니다.'),
    'adjustment': (
        'Use adjusted p values or the reported rejection decisions for the entire selected family of hypotheses.\n\nHolm/Bonferroni address family-wise error; FDR methods address false discovery rate.',
        '선택한 가설 묶음 전체에 대해 보정 p값·제시된 기각 여부를 사용하세요.\n\nHolm·Bonferroni는 가족단위 오류율, FDR 방법은 거짓발견률을 다룹니다.'),
    'regression': (
        'Check coefficient direction, units and reference categories. Raw coefficients usually have null value 0; reported odds/rate ratios have null value 1.\n\nRead intervals and p values alongside fit and residual diagnostics. Effects depend on the family, link and modeled target, such as a mean, quantile or latent response.',
        '계수의 방향·단위·기준 범주를 확인하세요. 원래 계수의 귀무값은 보통 0, 제시된 오즈비·발생률비의 귀무값은 1입니다.\n\n구간·p값과 적합도·잔차 진단을 함께 봅니다. 효과의 의미는 분포·연결함수와 평균·분위수·잠재 반응 같은 모형화 대상에 따라 달라집니다.'),
    'logistic': (
        'Odds are the probability of an event p divided by the probability of no event: p/(1−p). For example, an 80% event probability gives odds of 0.8/0.2=4, an event-to-no-event ratio of 4:1.\n\nA coefficient expresses a change in log odds. An odds ratio compares two odds: above/below 1 indicates higher/lower odds relative to the reference. An odds ratio of 2 means twice the odds.\n\nRead intervals, calibration and validated discrimination together. AUC measures discrimination between events and nonevents; calibration measures agreement between predicted probabilities and observed event frequencies.',
        '오즈(odds)는 사건이 발생할 확률 p를 발생하지 않을 확률 1−p로 나눈 값 p/(1−p)입니다. 예를 들어 발생 확률이 80%이면 오즈는 0.8/0.2=4로, 발생과 미발생의 비가 4:1이라는 뜻입니다.\n\n계수는 로그 오즈의 변화를 나타냅니다. 오즈비는 두 오즈를 나눈 값으로, 1보다 크거나 작으면 기준보다 오즈가 높거나 낮음을 뜻합니다. 오즈비 2는 오즈가 2배라는 의미입니다.\n\n구간·보정 성능·검증된 판별력을 함께 확인하세요. AUC는 발생·미발생을 구분하는 판별력, 보정 성능은 예측 확률과 실제 발생 비율의 일치 정도를 나타냅니다.'),
    'cluster': (
        'Read fixed/predictor effects and their uncertainty together with cluster structure. Mixed models describe conditional effects; GEE describes population-average effects.\n\nRandom-effect variation describes differences across subjects/clusters. Review convergence, the selected correlation structure and the response distribution in the diagnostics.',
        '고정효과·설명변수 효과와 불확실성을 군집 구조와 함께 읽으세요. 혼합모형은 조건부 효과, GEE는 모집단 평균 효과입니다.\n\n랜덤효과 변동은 대상·군집 간 차이를 나타냅니다. 진단 결과에서 수렴 상태·선택한 상관 구조·반응 분포를 확인합니다.'),
    'comparison': (
        'Confirm that compared models use common observations and the intended validation design. Lower losses/AIC/BIC and higher validated discrimination indicate improvement on their respective scales.\n\nThe reported likelihood-ratio p value evaluates the stated model comparison. Cross-validation evaluates prediction on observations excluded from each training fold.',
        '비교 모형이 같은 관측값과 의도한 검증 설계를 사용했는지 확인하세요. 손실·AIC/BIC 감소와 검증 판별력 증가는 각 척도에서 개선을 나타냅니다.\n\n우도비 p값은 제시된 모형 비교를 평가합니다. 교차검증은 각 폴드의 학습에서 제외한 관측값으로 예측 성능을 평가합니다.'),
    'bayesian': (
        'Read the posterior estimate and credible interval using the chosen prior and model. Reported probabilities refer to the stated direction/event.\n\nWhen BF10 is reported, values above 1 favor H1 relative to H0; below 1 favor H0. Compare the Bayes factor with the posterior interval and the selected prior.',
        '선택한 사전분포·모형에 따라 사후 추정값·베이지안 구간을 읽으세요. 제시된 확률은 명시된 방향·사건에 대한 값입니다.\n\nBF10이 제시되면 1보다 클수록 H0 대비 H1, 작을수록 H0를 지지합니다. Bayes factor·사후 구간·선택한 사전분포를 함께 확인하세요.'),
    'meta': (
        'Read the pooled effect and interval on the selected effect scale; ratios use null value 1, while log ratios and differences use 0.\n\nStudy weights show each study’s contribution; heterogeneity summarizes between-study variation. Moderator/subgroup results describe how effects vary with study characteristics.',
        '선택한 효과 척도에서 통합 효과·구간을 읽으세요. 비율의 귀무값은 1, 로그 비율·차이의 귀무값은 0입니다.\n\n연구 가중치는 각 연구의 기여도, 이질성은 연구 간 효과의 변동을 나타냅니다. 조절변수·하위그룹 결과는 연구 특성에 따른 효과 차이를 설명합니다.'),
    'exploratory': (
        'Inspect explained variance, loadings and the selected number of components/factors. Loadings indicate how variables relate to each dimension.\n\nRead the dimensions using the selected scaling, extraction and rotation, and the variables with the largest loadings.',
        '설명분산·적재량·선택한 성분·요인 수를 확인하세요. 적재량은 각 변수와 차원의 관계를 나타냅니다.\n\n선택한 척도·추출법·회전과 적재량이 큰 변수들을 바탕으로 각 차원의 의미를 읽습니다.'),
    'structural': (
        'Read standardized loadings/paths, their intervals and the overall fit together. Review direct, indirect and total effects when reported.\n\nUse the fit indices to assess how closely the model reproduces the observed covariance structure, and the path estimates to read the direction and magnitude of relationships.',
        '표준화 적재량·경로·구간과 전체 적합도를 함께 읽으세요. 제시된 직접·간접·총 효과도 확인합니다.\n\n적합도 지수로 모형이 관측 공분산 구조를 얼마나 잘 재현하는지, 경로 추정값으로 관계의 방향·크기를 확인합니다.'),
    'path': (
        'For mediation, inspect the indirect effect and bootstrap interval. For moderation, inspect the interaction and conditional slopes.\n\nAn interval entirely above or below 0 indicates a positive or negative effect at that interval level. Conditional slopes show how the relationship changes across moderator values.',
        '매개분석은 간접효과·부트스트랩 구간, 조절분석은 상호작용·조건부 기울기를 확인하세요.\n\n구간 전체가 0보다 크거나 작으면 해당 구간 수준에서 효과가 양·음의 방향임을 나타냅니다. 조건부 기울기는 조절변수 값에 따라 관계가 어떻게 달라지는지 보여줍니다.'),
    'prediction': (
        'Use held-out, cross-validated or OOB metrics to judge prediction. Lower RMSE/MAE/loss is better on the same data and scale.\n\nFor classification, inspect accuracy/AUC, the confusion matrix, threshold and class balance. Feature importance summarizes each variable’s contribution to prediction.',
        '홀드아웃·교차검증·OOB 지표로 예측을 평가하세요. 같은 자료·척도에서는 RMSE·MAE·손실이 작을수록 좋습니다.\n\n분류는 정확도·AUC·혼동행렬·기준 확률·범주별 비율을 함께 확인합니다. 변수 중요도는 각 변수의 예측 기여도를 나타냅니다.'),
    'clustering': (
        'Read memberships, centers or the dendrogram as a summary of similarity under the selected distance and scaling.\n\nCluster numbers identify the groups. Compare their centers, sizes and variable profiles to describe each group.',
        '선택한 거리·척도에서의 유사성 요약으로 군집 소속·중심·덴드로그램을 읽으세요.\n\n군집 번호는 각 그룹을 식별하는 이름입니다. 중심·크기·변수별 특성을 비교해 그룹의 성격을 설명합니다.'),
    'forecast': (
        'Read the forecast with its prediction interval. A wider interval indicates a broader range of future values.\n\nInspect residual autocorrelation, fit status and seasonal patterns alongside forecasts at each horizon.',
        '예측값과 예측구간을 함께 읽으세요. 구간이 넓을수록 미래 값의 범위가 넓습니다.\n\n예측 시점별 결과와 함께 잔차 자기상관·적합 상태·계절 패턴을 확인합니다.'),
    'survival': (
        'Kaplan–Meier estimates remaining event-free probability; “not reached” means median survival was not observed. Log-rank p values compare survival functions.\n\nFor Cox results, HR above/below 1 means higher/lower instantaneous hazard relative to the reference. Read the HR interval, proportional-hazards diagnostics and censoring information together.',
        'Kaplan–Meier는 사건 없이 남아 있을 확률을 추정합니다. 중앙 생존시간 미도달은 관측 중 중앙값에 도달하지 않았다는 뜻이며 로그순위 p값은 생존함수를 비교합니다.\n\nCox의 HR이 1보다 크거나 작으면 기준보다 순간 위험이 높거나 낮음을 뜻합니다. HR 구간·비례위험 진단·중도절단 정보를 함께 읽으세요.'),
    'aft': (
        'A time ratio above 1 indicates longer event times; below 1 indicates shorter times, relative to the reference.\n\nRead its interval and predicted survival at the specified time using the selected event-time distribution.',
        '시간비가 1보다 크면 기준보다 사건 시간이 길고, 작으면 짧음을 뜻합니다.\n\n선택한 사건 시간 분포에서 시간비의 구간과 지정 시점의 생존확률을 함께 읽으세요.'),
    'power': (
        'Power is the detection probability for the assumed effect, design and alpha. Sample-size results target that power; check whether n is per group, total or pairs.\n\nCompare the assumed effect size, target power and planned sample size to choose the study scale.',
        '검정력은 가정한 효과·설계·alpha에서 효과를 탐지할 확률입니다. 표본 수는 이를 목표로 하므로 n이 그룹별·전체·대응 쌍 수인지 확인하세요.\n\n가정한 효과크기·목표 검정력·계획한 표본 수를 함께 비교해 연구 규모를 정합니다.'),
    'imputation': (
        'Check which missing cells were filled and the replacement values on the original scale.\n\nThe selected method supplies replacements from column summaries or relationships among observations. Compare the completed data with the original data before continuing the analysis.',
        '어떤 결측 셀이 채워졌는지와 대체값을 원래 척도에서 확인하세요.\n\n선택한 방법은 열의 요약값 또는 관측값 사이의 관계로 대체값을 구합니다. 채워진 자료와 원자료를 비교한 뒤 분석을 이어갑니다.'),
}


def build_interpretation():
    return {
        'analyses': {name: group for group, names in GROUPS.items() for name in names.split()},
        'guides': {key: dict(zip(('en', 'ko'), paragraphs)) for key, paragraphs in GUIDES.items()},
    }
