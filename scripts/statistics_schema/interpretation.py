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
        'Read estimates in their original units and check which samples or reference categories are compared.\n\nUse uncertainty intervals and diagnostics alongside the estimate. Unavailable values and warnings should be resolved before drawing conclusions.',
        '추정값의 단위와 비교한 표본·기준 범주를 먼저 확인하세요.\n\n추정값뿐 아니라 불확실성 구간·진단 결과를 함께 봅니다. unavailable 값과 경고를 확인한 뒤 결론을 내리세요.'),
    'descriptive': (
        'Check valid n and missing values first. Mean/median describe location; SD, variance and quartiles describe spread.\n\nCompare distributions and outliers as well as averages. Descriptive summaries alone do not establish group differences or causation.',
        '유효 표본 수 n과 결측값부터 확인하세요. 평균·중앙값은 중심, 표준편차·분산·사분위수는 퍼짐을 나타냅니다.\n\n평균뿐 아니라 분포·이상값도 함께 봅니다. 요약 통계만으로 그룹 차이의 유의성이나 인과성을 판단하지 않습니다.'),
    'test': (
        'Check the estimated mean/proportion difference and its direction against the specified null value.\n\nA p value below the chosen significance level (for example .05) is evidence against that null. A larger p value does not prove equality; also assess the interval and effect size.',
        '평균·비율 차이의 추정값과 방향, 검정한 기준값을 확인하세요.\n\np값이 정한 유의수준(예: .05)보다 작으면 귀무가설에 반하는 증거입니다. 크다고 동등함이 입증되는 것은 아니며 구간·효과크기도 함께 봅니다.'),
    'categorical': (
        'Compare category counts, within-group percentages and any reported odds ratio or association effect size.\n\nThe p value tests the stated association or paired-proportion hypothesis. Check expected-count diagnostics and category order; statistical association alone is not causation.',
        '범주별 빈도·그룹 내 비율과 제시된 오즈비·연관성 효과크기를 확인하세요.\n\np값은 지정한 연관성 또는 대응 비율 가설에 대한 검정입니다. 기대빈도 진단·범주 순서를 확인하며 통계적 연관성이 곧 인과성은 아닙니다.'),
    'rank': (
        'A small p value indicates evidence of a distribution/condition difference under this rank test. It does not by itself identify the differing pair.\n\nUse rank summaries and suitable post-hoc comparisons. Interpreting a difference as a median/location shift requires the method’s shape or symmetry assumptions.',
        '작은 p값은 이 순위 검정에서 분포·조건 차이에 대한 증거이며, 그 자체로 차이가 있는 쌍을 알려주지는 않습니다.\n\n순위 요약·적절한 사후비교를 함께 보세요. 중앙값·위치 차이로 해석하려면 해당 방법의 분포 형태·대칭성 가정이 필요합니다.'),
    'anova': (
        'A significant overall test indicates at least one group/condition differs in the tested mean or trimmed mean.\n\nLocate differences with adjusted post-hoc comparisons and inspect effect sizes. For repeated measures, review sphericity corrections and corrected p values when reported.',
        '전체 검정이 유의하면 적어도 한 그룹·조건의 평균 또는 절사평균이 다르다는 증거입니다.\n\n보정된 사후비교로 차이가 있는 쌍을 찾고 효과크기를 확인하세요. 반복측정은 제시된 구형성 보정·보정 p값도 확인합니다.'),
    'factorial': (
        'Read each factor/covariate test and any interaction separately. An interaction means an effect depends on another variable.\n\nInspect interactions before averaging main effects. Adjusted means depend on the covariate values and slope assumptions used by the model.',
        '요인·공변량 검정과 상호작용을 각각 읽으세요. 상호작용은 한 변수의 효과가 다른 변수에 따라 달라진다는 뜻입니다.\n\n주 효과를 평균적으로 해석하기 전에 상호작용을 확인하세요. 조정 평균은 사용한 공변량 값·기울기 가정에 의존합니다.'),
    'multivariate': (
        'Multivariate p values test the response means jointly; significance does not mean every response differs.\n\nInspect individual-response follow-ups, adjusted means and assumptions. Follow-up p values may need multiplicity adjustment; covariate-adjusted conclusions require an appropriate slope model.',
        '다변량 p값은 여러 종속변수의 평균을 공동 검정하며, 유의하다고 모든 변수에 차이가 있는 것은 아닙니다.\n\n변수별 후속 검정·조정 평균·가정을 확인하세요. 후속 p값은 다중비교 보정이 필요할 수 있으며 공변량 보정은 적절한 기울기 모형을 전제로 합니다.'),
    'posthoc': (
        'Read the pair or treatment/control label before interpreting the sign of its difference.\n\nCompare adjusted p values with the chosen significance level. Use the reported interval and adjustment method; a nonsignificant pair is not proof of equivalence.',
        '차이의 부호를 해석하기 전에 비교 쌍·처리군과 대조군의 순서를 확인하세요.\n\n보정 p값을 유의수준과 비교하고 제시된 구간·보정 방법을 함께 봅니다. 유의하지 않은 쌍이 동등함을 입증하는 것은 아닙니다.'),
    'normality': (
        'A small p value is evidence against the normal/reference distribution, or equality of distributions for a two-sample KS test.\n\nA large p value does not prove the distributional assumption. Review Q–Q plots, sample size, tails and outliers together.',
        '작은 p값은 정규·기준분포 가설에 반하는 증거이며, 두 표본 KS 검정에서는 분포가 같다는 가설에 반하는 증거입니다.\n\n큰 p값이 분포 가정을 증명하지는 않습니다. Q–Q plot·표본 수·꼬리·이상값을 함께 확인하세요.'),
    'variance': (
        'A small p value is evidence that group variances differ. A large value does not establish equal variances.\n\nInspect group SDs and distributions; Bartlett is sensitive to nonnormality. Use a comparison method compatible with the observed variance structure.',
        '작은 p값은 그룹 분산이 다르다는 증거이며 큰 값이 등분산을 입증하지는 않습니다.\n\n그룹별 표준편차·분포를 확인하세요. Bartlett은 비정규성에 민감하므로 관측된 분산 구조에 맞는 비교 방법을 사용합니다.'),
    'correlation': (
        'The coefficient sign indicates direction and its magnitude indicates strength on the chosen linear/rank scale.\n\nThe p value concerns zero association under the test assumptions. Check a scatterplot and outliers; correlation alone does not establish causation.',
        '계수의 부호는 방향, 절댓값은 선택한 선형·순위 척도의 연관성 크기를 나타냅니다.\n\np값은 검정 가정에서 연관성이 0인지에 관한 값입니다. 산점도·이상값을 확인하며 상관만으로 인과성을 판단하지 않습니다.'),
    'effect': (
        'Effect size describes the magnitude of a difference or association. Check the metric, comparison direction and any interval.\n\nLabels such as small/large are reference conventions. Practical importance depends on the field, units and study design, not only a threshold or p value.',
        '효과크기는 차이·연관성의 크기입니다. 사용한 척도·비교 방향·제시된 구간을 확인하세요.\n\n작음·큼 같은 평가는 참고 기준입니다. 실질적 중요성은 임계값·p값뿐 아니라 분야·단위·연구 설계에 따라 판단합니다.'),
    'reliability': (
        'Higher reliability/agreement usually indicates greater consistency, but compare intervals and the selected rating/model definition.\n\nAlpha/omega do not by themselves prove validity or unidimensionality. ICC and kappa depend on the agreement definition, categories and measurement setting.',
        '신뢰도·일치도가 높을수록 일반적으로 일관성이 높지만 구간과 선택한 평가·모형 정의도 확인하세요.\n\nα·ω만으로 타당도·단일차원성이 입증되지는 않습니다. ICC·κ는 일치도 정의·범주·측정 상황에 따라 해석합니다.'),
    'agreement': (
        'Bias is the average A−B difference; limits of agreement describe the spread of individual differences. In log mode, read ratios.\n\nCompare limits with a prespecified acceptable difference and inspect proportional bias. A nonsignificant bias test does not prove the methods are interchangeable.',
        '편향은 평균 A−B 차이, 일치한계는 개별 차이의 퍼짐입니다. 로그 방식에서는 비율로 읽으세요.\n\n미리 정한 허용 차이와 일치한계를 비교하고 비례 편향을 확인합니다. 편향 검정이 비유의하다고 두 방법을 대체할 수 있음이 입증되지는 않습니다.'),
    'interval': (
        'Read the estimate and interval in the statistic’s units. A wider interval indicates greater estimation uncertainty.\n\nA confidence interval describes a repeated-sampling procedure, not a posterior probability for this fixed parameter. Check the sampling and model assumptions.',
        '추정값·구간을 해당 통계량의 단위로 읽으세요. 구간이 넓을수록 추정 불확실성이 큽니다.\n\n신뢰구간은 반복 표집 절차의 성질이며 고정된 모수가 이 구간에 있을 사후확률을 뜻하지 않습니다. 표집·모형 가정을 확인하세요.'),
    'equivalence': (
        'TOST establishes equivalence only when both one-sided p values are below the chosen alpha.\n\nRead the result against the prespecified equivalence bounds. A nonsignificant ordinary difference test is insufficient; alpha=.05 corresponds to a 90% TOST interval.',
        'TOST는 두 단측 p값이 모두 선택한 alpha보다 작을 때 동등성을 인정합니다.\n\n미리 정한 동등성 경계와 비교하세요. 일반 차이 검정의 비유의 결과만으로는 충분하지 않으며 alpha=.05의 TOST 구간은 90%입니다.'),
    'adjustment': (
        'Use adjusted p values or the reported rejection decisions for the entire selected family of hypotheses.\n\nHolm/Bonferroni address family-wise error; FDR methods address false discovery rate. Adjustment does not change effect size or repair an unsuitable test.',
        '선택한 가설 묶음 전체에 대해 보정 p값·제시된 기각 여부를 사용하세요.\n\nHolm·Bonferroni는 가족단위 오류율, FDR 방법은 거짓발견률을 다룹니다. 보정이 효과크기를 바꾸거나 부적절한 검정을 바로잡지는 않습니다.'),
    'regression': (
        'Check coefficient direction, units and reference categories. Raw coefficients usually have null value 0; reported odds/rate ratios have null value 1.\n\nRead intervals and p values alongside fit and residual diagnostics. Effects depend on the family, link and modeled target, such as a mean, quantile or latent response.',
        '계수의 방향·단위·기준 범주를 확인하세요. 원래 계수의 귀무값은 보통 0, 제시된 오즈비·발생률비의 귀무값은 1입니다.\n\n구간·p값과 적합도·잔차 진단을 함께 봅니다. 효과의 의미는 분포·연결함수와 평균·분위수·잠재 반응 같은 모형화 대상에 따라 달라집니다.'),
    'logistic': (
        'Odds are the probability of an event p divided by the probability of no event: p/(1−p). For example, an 80% event probability gives odds of 0.8/0.2=4, an event-to-no-event ratio of 4:1.\n\nA coefficient is a change in log odds, not a direct change in probability. An odds ratio compares two odds: above/below 1 indicates higher/lower odds relative to the reference. An odds ratio of 2 means twice the odds, not twice the probability.\n\nCheck intervals, calibration and validated discrimination together. An odds ratio is not a risk ratio, and a high AUC alone does not guarantee accurate probabilities.',
        '오즈(odds)는 사건이 발생할 확률 p를 발생하지 않을 확률 1−p로 나눈 값 p/(1−p)입니다. 예를 들어 발생 확률이 80%이면 오즈는 0.8/0.2=4로, 발생과 미발생의 비가 4:1이라는 뜻입니다.\n\n계수는 확률의 직접 변화가 아닌 로그 오즈의 변화입니다. 오즈비는 두 오즈를 나눈 값으로, 1보다 크거나 작으면 기준보다 오즈가 높거나 낮음을 뜻합니다. 오즈비 2는 확률이 아닌 오즈가 2배라는 의미입니다.\n\n구간·보정 성능·검증된 판별력을 함께 확인하세요. 오즈비는 위험비와 다르며 AUC가 높다고 확률 예측이 정확함이 보장되지는 않습니다.'),
    'cluster': (
        'Read fixed/predictor effects and their uncertainty together with cluster structure. Mixed models describe conditional effects; GEE describes population-average effects.\n\nInspect random-effect variation, convergence and warnings. Few clusters, singular fits or unsuitable correlation/distribution assumptions can weaken inference.',
        '고정효과·설명변수 효과와 불확실성을 군집 구조와 함께 읽으세요. 혼합모형은 조건부 효과, GEE는 모집단 평균 효과입니다.\n\n랜덤효과 변동·수렴·경고를 확인합니다. 적은 군집·특이 적합·부적절한 상관·분포 가정은 추론을 약화시킬 수 있습니다.'),
    'comparison': (
        'Confirm that compared models use common observations and the intended validation design. Lower losses/AIC/BIC and higher validated discrimination may indicate improvement on their respective scales.\n\nUse a reported likelihood-ratio p value only for its stated model comparison. Cross-validation measures prediction; it does not by itself establish causal effects.',
        '비교 모형이 같은 관측값과 의도한 검증 설계를 사용했는지 확인하세요. 손실·AIC/BIC 감소와 검증 판별력 증가는 각 척도에서 개선을 시사합니다.\n\n우도비 p값은 제시된 모형 비교에 한해 해석합니다. 교차검증은 예측 평가이며 인과 효과를 입증하지는 않습니다.'),
    'bayesian': (
        'Read the posterior estimate and credible interval conditional on the chosen prior and model. Reported probabilities refer to the stated direction/event.\n\nWhen BF10 is reported, values above 1 favor H1 relative to H0; below 1 favor H0. Evidence depends on the priors, and this is not a frequentist p value.',
        '선택한 사전분포·모형을 전제로 사후 추정값·베이지안 구간을 읽으세요. 제시된 확률은 명시된 방향·사건에 대한 값입니다.\n\nBF10이 제시되면 1보다 클수록 H0 대비 H1, 작을수록 H0를 지지합니다. 증거는 사전분포에 의존하며 빈도주의 p값과 다릅니다.'),
    'meta': (
        'Read the pooled effect and interval on the selected effect scale; ratios use null value 1, while log ratios and differences use 0.\n\nInspect between-study heterogeneity and study weights. Moderator/subgroup findings are study-level associations; a pooled effect need not describe every study or setting.',
        '선택한 효과 척도에서 통합 효과·구간을 읽으세요. 비율의 귀무값은 1, 로그 비율·차이의 귀무값은 0입니다.\n\n연구 간 이질성·연구 가중치를 확인합니다. 조절변수·하위그룹 결과는 연구 수준의 연관성이며 통합 효과가 모든 연구·상황을 대표하지는 않습니다.'),
    'exploratory': (
        'Inspect explained variance, loadings and the selected number of components/factors. Loadings indicate how variables relate to each dimension.\n\nConsider scaling, extraction and rotation. A PCA component is not automatically a latent construct, and exploratory structure should be checked on appropriate data.',
        '설명분산·적재량·선택한 성분·요인 수를 확인하세요. 적재량은 각 변수와 차원의 관계를 나타냅니다.\n\n척도·추출법·회전을 고려합니다. PCA 성분이 곧 잠재 개념은 아니며 탐색한 구조는 적절한 자료로 확인하는 것이 좋습니다.'),
    'structural': (
        'Read standardized loadings/paths, their intervals and the overall fit together. Review direct, indirect and total effects when reported.\n\nFit indices have no single universal pass rule. Good fit does not prove a unique or causal model; inspect identification, estimation warnings and measurement assumptions.',
        '표준화 적재량·경로·구간과 전체 적합도를 함께 읽으세요. 제시된 직접·간접·총 효과도 확인합니다.\n\n적합도에 보편적인 단일 합격 기준은 없습니다. 좋은 적합도가 유일한 모형·인과성을 입증하지는 않으며 식별·추정 경고·측정 가정을 확인하세요.'),
    'path': (
        'For mediation, inspect the indirect effect and bootstrap interval. For moderation, inspect the interaction and conditional slopes.\n\nAn interval including 0 does not give clear evidence of a nonzero effect at that interval level. Causal interpretation requires assumptions beyond a fitted path or small p value.',
        '매개분석은 간접효과·부트스트랩 구간, 조절분석은 상호작용·조건부 기울기를 확인하세요.\n\n구간이 0을 포함하면 해당 구간 수준에서 0이 아닌 효과의 명확한 증거가 부족합니다. 인과 해석에는 적합 경로·작은 p값 외의 가정이 필요합니다.'),
    'prediction': (
        'Use held-out, cross-validated or OOB metrics to judge prediction; training performance can be optimistic. Lower RMSE/MAE/loss is better on the same data and scale.\n\nFor classification, inspect the confusion matrix, threshold and class balance alongside accuracy/AUC. Feature importance is predictive relevance, not a causal effect or a coefficient p value.',
        '홀드아웃·교차검증·OOB 지표로 예측을 평가하세요. 학습 성능은 낙관적일 수 있으며 같은 자료·척도에서는 RMSE·MAE·손실이 작을수록 좋습니다.\n\n분류는 정확도·AUC뿐 아니라 혼동행렬·기준 확률·범주 불균형도 확인합니다. 변수 중요도는 예측 기여이며 인과 효과·계수 p값이 아닙니다.'),
    'clustering': (
        'Read memberships, centers or the dendrogram as a summary of similarity under the selected distance and scaling.\n\nCluster labels have no inherent order or significance. Check stability and practical meaning; changing scale, distance or cluster count can change the groups.',
        '선택한 거리·척도에서의 유사성 요약으로 군집 소속·중심·덴드로그램을 읽으세요.\n\n군집 번호 자체에는 순서·유의성의 의미가 없습니다. 안정성·실질적 의미를 확인하며 척도·거리·군집 수를 바꾸면 결과도 달라질 수 있습니다.'),
    'forecast': (
        'Read the forecast with its prediction interval; uncertainty usually grows farther into the future.\n\nInspect residual autocorrelation, fit status and seasonal assumptions. A forecast is conditional on the fitted model and continuation of the data-generating pattern.',
        '예측값과 예측구간을 함께 읽으세요. 대체로 먼 미래일수록 불확실성이 커집니다.\n\n잔차 자기상관·적합 상태·계절 가정을 확인합니다. 예측은 적합 모형과 자료 생성 패턴이 이어진다는 조건에 의존합니다.'),
    'survival': (
        'Kaplan–Meier estimates remaining event-free probability; “not reached” means median survival was not observed. Log-rank p values compare survival functions.\n\nFor Cox results, HR above/below 1 means higher/lower instantaneous hazard, not a probability ratio. Review its interval, proportional hazards and censoring assumptions.',
        'Kaplan–Meier는 사건 없이 남아 있을 확률을 추정합니다. 중앙 생존시간 미도달은 관측 중 중앙값에 도달하지 않았다는 뜻이며 로그순위 p값은 생존함수를 비교합니다.\n\nCox의 HR이 1보다 크거나 작으면 순간 위험이 높거나 낮다는 뜻이며 확률의 비율은 아닙니다. 구간·비례위험·중도절단 가정을 확인하세요.'),
    'aft': (
        'A time ratio above 1 indicates longer event times; below 1 indicates shorter times, relative to the reference.\n\nRead its interval and predicted survival at the specified time. Results depend on the chosen event-time distribution, censoring and entry assumptions.',
        '시간비가 1보다 크면 기준보다 사건 시간이 길고, 작으면 짧음을 뜻합니다.\n\n시간비의 구간과 지정 시점의 생존확률을 함께 읽으세요. 결과는 선택한 사건 시간 분포·중도절단·진입시간 가정에 의존합니다.'),
    'power': (
        'Power is the detection probability for the assumed effect, design and alpha. Sample-size results target that power; check whether n is per group, total or pairs.\n\nRevisit plausible effect sizes and missing-data allowances. Achieved power from an assumed effect is not evidence that an observed result is true.',
        '검정력은 가정한 효과·설계·alpha에서 효과를 탐지할 확률입니다. 표본 수는 이를 목표로 하므로 n이 그룹별·전체·대응 쌍 수인지 확인하세요.\n\n타당한 효과크기와 결측 대비를 검토합니다. 가정한 효과의 검정력이 관측 결과가 참이라는 증거는 아닙니다.'),
    'imputation': (
        'Check which missing cells were filled and whether replacements are plausible in the original scale. Observed values should be retained.\n\nThis is data preparation, not a hypothesis test. Simple imputation can understate uncertainty; the missingness mechanism and downstream analysis still need review.',
        '어떤 결측 셀이 채워졌는지와 대체값이 원래 척도에서 타당한지 확인하세요. 관측값은 유지되어야 합니다.\n\n이는 가설 검정이 아닌 자료 준비입니다. 단순 대체는 불확실성을 과소평가할 수 있으므로 결측 원인·후속 분석도 검토합니다.'),
}


def build_interpretation():
    return {
        'analyses': {name: group for group, names in GROUPS.items() for name in names.split()},
        'guides': {key: dict(zip(('en', 'ko'), paragraphs)) for key, paragraphs in GUIDES.items()},
    }
