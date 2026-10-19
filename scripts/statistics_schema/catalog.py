"""Concise bilingual catalog descriptions, separate from analysis-form instructions."""

# Each entry states the purpose, input shape and options needed to get started.
# Detailed control instructions stay with the analysis forms.
DESCRIPTIONS = {
    'pearson': (
        'Pearson linear correlation r and p value. Enter at least three variable numeric pairs; alternative: both / left / right.',
        '두 변수의 선형 상관계수 r과 p값. 변동이 있는 숫자 쌍 3개 이상; 대립가설 both / left / right.'),
    'spearman': (
        'Spearman rank correlation and p value for paired observations. Ties use average ranks; alternative: both / left / right.',
        '짝지은 관측값의 Spearman 순위 상관계수와 p값. 동순위는 평균 순위; 대립가설 both / left / right.'),
    'kendall': (
        'Kendall tau-b rank correlation and p value for paired observations, with tie correction. Alternative: both / left / right.',
        '짝지은 관측값의 Kendall tau-b 순위 상관계수와 p값. 동순위 보정; 대립가설 both / left / right.'),
    'impute': (
        'Fill missing numeric values (NA) by mean, median, mode, regression or knn. The default neighbor count is 5; preview before applying.',
        '결측 숫자(NA)를 mean·median·mode·regression·knn으로 대체합니다. 기본 이웃 수 5; 미리 보기 후 적용.'),
    'propztest': (
        'Compare a success proportion with p0. Input: 0/1 values or success/trial counts; alternative: both / left / right. Uses a normal approximation.',
        '성공 비율을 기준 p0와 비교합니다. 입력: 0/1 자료 또는 성공 수·시행 수; 대립가설 both / left / right. 정규근사 사용.'),
    'propztest2': (
        'Compare two independent success proportions. Input: two 0/1 lists or success/trial counts for A and B. Alternatives refer to A−B.',
        '독립 두 그룹의 성공 비율을 비교합니다. 입력: 두 0/1 목록 또는 A·B의 성공 수·시행 수. 대립가설은 A−B 기준.'),
    'mcnemar': (
        'Compare paired binary outcomes from a 2×2 count table. Method: exact / corrected / asymptotic.',
        '2×2 빈도표로 대응 이항 결과를 비교합니다. 방법: exact / corrected / asymptotic.'),
    'cronbach': (
        'Internal consistency using raw and standardized Cronbach α, item-total correlations and α after item deletion. Rows: subjects; columns: items. Reverse-code items first.',
        'Cronbach α로 내적 일관성을 평가합니다. 행=대상, 열=문항; 원점수·표준화 α, 문항-총점 상관, 문항 삭제 시 α. 역문항은 먼저 역코딩하세요.'),
    'omega': (
        'McDonald ω for a single-factor model. Enter complete rows for at least three variable items; reverse-code first. Reports ω, α, loadings and model fit.',
        '단일요인 모형의 McDonald ω. 변동이 있는 문항 3개 이상의 완전한 행을 입력하고 역문항은 먼저 역코딩하세요. ω·α·적재량·적합도 제공.'),
    'icc': (
        'Intraclass correlation from a subject × rater matrix. oneway=ICC(1), random=absolute-agreement ICC(2), mixed=consistency ICC(3); single or average ratings, with confidence intervals.',
        '대상×평가자 행렬의 급내상관계수. oneway=ICC(1), random=절대 일치 ICC(2), mixed=일관성 ICC(3). single 단일·average 평균 평가와 신뢰구간.'),
    'cohenkappa': (
        'Agreement between two raters from a square category-count table. Choose unweighted, linear or quadratic weights; weighted categories follow their specified order.',
        '두 평가자의 범주 일치도를 κ로 평가합니다. 입력: 같은 범주 순서의 정방 빈도표. 무가중·선형·제곱 가중치; 가중 분석은 순서형 범주에 사용.'),
    'blandaltman': (
        'Agreement of two measurements per independent subject: bias, limits of agreement and proportional-bias trend. Uses A−B; log mode accepts positive measurements and reports ratios.',
        '독립 대상별 두 측정값의 편향·일치한계·비례 편향 추세를 분석합니다. 차이는 A−B; 로그 방식은 양수 자료의 비율을 표시.'),
    'shapiro': (
        'Shapiro–Wilk normality test for 3–5000 observations. Read the p value alongside the Q–Q plot.',
        '관측값 3~5000개의 Shapiro–Wilk 정규성 검정. p값을 Q–Q plot과 함께 해석하세요.'),
    'normaltest': (
        'D’Agostino–Pearson normality test using skewness and kurtosis. At least 8 observations; reports K² and an approximate p value. For n ≤ 20 the approximation may be inaccurate; review the Q–Q plot.',
        '왜도·첨도를 결합한 D’Agostino–Pearson 정규성 검정. 관측값 8개 이상; K²·근사 p값을 제공합니다. n ≤ 20에서는 근사가 부정확할 수 있으므로 Q–Q plot과 함께 해석하세요.'),
    'kstest': (
        'Compare continuous distributions: two sample lists, or data with normal(mean,SD) / uniform(lower,width). Specify reference parameters independently of the sample.',
        '두 표본의 연속분포 또는 표본과 normal(평균,SD)·uniform(하한,폭)을 비교합니다. 기준 모수는 검정 표본과 독립적으로 지정하세요.'),
    'levene': (
        'Compare group variances using median-centered Brown–Forsythe. Input: one list per independent group.',
        '중앙값 기준 Brown–Forsythe로 그룹 분산을 비교합니다. 입력: 독립 그룹별 목록.'),
    'bartlett': (
        'Compare variances of normally distributed independent groups. Input: one list per group.',
        '정규분포를 가정하는 독립 그룹의 분산 비교. 입력: 그룹별 목록.'),
    'tukey': (
        'Tukey–Kramer comparisons of all independent group means under equal variances, with adjusted p values and simultaneous 95% intervals.',
        '등분산 독립 그룹의 모든 평균 쌍을 Tukey–Kramer로 비교합니다. 보정 p값·95% 동시 구간 제공.'),
    'gameshowell': (
        'Compare all independent group means allowing unequal variances, with adjusted p values and simultaneous 95% intervals.',
        '이분산 독립 그룹의 모든 평균 쌍을 비교합니다. 보정 p값·95% 동시 구간 제공.'),
    'scheffe': (
        'Pairwise mean comparisons with Scheffé protection for all linear contrasts. Input: independent group lists; assumes normality and equal variances.',
        '전체 선형 대비를 보호하는 Scheffé 쌍별 평균 비교. 입력: 독립 그룹 목록; 정규성·등분산 가정.'),
    'dunnett': (
        'Compare each treatment mean with a control under normality and equal variances. Input: group lists and control number (1-based, default 1). Difference: treatment−control.',
        '정규성·등분산 가정으로 각 처리군을 대조군과 비교합니다. 입력: 그룹 목록·대조군 번호(1부터, 기본 1). 차이=처리군−대조군.'),
    'dunn': (
        'Pairwise rank comparisons after Kruskal–Wallis. Input: independent group lists; adjustment: holm (default) / bonferroni / fdr / none.',
        'Kruskal–Wallis 이후 그룹 쌍별 순위 비교. 입력: 독립 그룹 목록; 보정 holm(기본) / bonferroni / fdr / none.'),
    'conover': (
        'Pairwise rank comparisons after a significant Kruskal–Wallis test. Input: independent group lists; adjustment: holm (default) / bonferroni / fdr / none.',
        '유의한 Kruskal–Wallis 이후 그룹 쌍별 순위 비교. 입력: 독립 그룹 목록; 보정 holm(기본) / bonferroni / fdr / none.'),
    'twowayanova': (
        'Test two categorical factors and their interaction in independent numeric observations. Type III tests; interaction 1 (default) or additive model 0.',
        '독립 숫자 관측에서 두 범주 요인과 상호작용을 검정합니다. Type III 검정; 상호작용 1(기본), 가법 모형 0.'),
    'ancova': (
        'Compare covariate-adjusted group means. Columns: group, covariates, response. Confidence level defaults to .95; slope-homogeneity check defaults to 1.',
        '공변량을 보정한 그룹 평균 비교. 열: 그룹·공변량·종속변수. 신뢰수준 기본 .95, 기울기 동질성 검정 기본 1.'),
    'mancova': (
        'Compare multiple responses jointly after adjusting for covariates. mancova(data,covariate count=1,confidence=.95,slope test=1); columns: group, covariates, then at least two responses. Reports four multivariate tests and adjusted means.',
        '공변량 보정 후 여러 종속변수를 함께 비교합니다. mancova(자료,공변량 수=1,신뢰수준=.95,기울기 검정=1); 열: 그룹·공변량·종속변수 2개 이상. 다변량 검정 4종·조정 평균 제공.'),
    'manova': (
        'Compare several responses jointly. Input: group then response columns; factorial mode adds factors, repeated mode uses subject rows with equal response blocks per time point. Reports Pillai, Wilks, Hotelling–Lawley and Roy.',
        '여러 종속변수를 함께 비교합니다. 기본은 그룹·종속변수 열; factorial은 요인설계, repeated는 대상별 시점 순서의 반응 블록. Pillai·Wilks·Hotelling–Lawley·Roy 제공.'),
    'repeatedanova': (
        'Compare repeated conditions in complete subject rows. Rows: subjects; columns: conditions. Supports one or two factors, sphericity corrections and paired post-hoc comparisons with Holm-adjusted p values.',
        '같은 대상의 반복 조건을 비교합니다. 행=대상, 열=조건인 완전자료. 일·이요인 설계, 구형성 보정, Holm p값 보정 대응 사후비교.'),
    'friedman': (
        'Rank comparison of three or more repeated conditions in complete subject rows. Uses a tie-corrected χ² approximation and reports Kendall W.',
        '3개 이상 반복 조건의 순위 비교. 행=대상, 열=조건인 완전자료. 동점 보정 χ² 근사·Kendall W 제공.'),
    'cohend': (
        'Standardized mean difference between two samples. independent uses pooled SD; paired uses the SD of within-pair differences.',
        '두 표본의 표준화 평균 차이. independent는 합동 SD, paired는 대응 차이의 SD 사용.'),
    'eta2': (
        'Proportion of total variation associated with group differences. Input: one list per independent group.',
        '전체 변동 중 그룹 차이가 차지하는 비율 η². 입력: 독립 그룹별 목록.'),
    'cramerv': (
        'Strength of categorical association from a count table. Reports Cramér’s V and, for 2×2 tables, signed phi.',
        '빈도표의 범주 연관성 크기를 평가합니다. Cramér의 V, 2×2 표의 부호 있는 phi 제공.'),
    'phi': (
        'Signed association for a 2×2 count table. Reversing one variable’s category order reverses the sign.',
        '2×2 빈도표의 부호 있는 연관성 계수. 한 변수의 범주 순서를 바꾸면 부호가 반전됩니다.'),
    'padjust': (
        'Adjust a family of p values for multiple testing. Method: bonferroni / holm / fdr (BH) / by; choose a significance level.',
        '여러 검정의 p값을 함께 보정합니다. 방법: bonferroni / holm / fdr(BH) / by; 유의수준 지정.'),
    'tinterval': (
        'Mean confidence interval using sample SD and Student t. Input: level and observations, or level, mean, SD and n.',
        '표본 SD와 Student t를 이용한 평균 신뢰구간. 입력: 수준·자료 또는 수준·평균·SD·n.'),
    'zinterval': (
        'Mean confidence interval using known population SD. Input: level, population SD and observations, or level, population SD, mean and n.',
        '알려진 모집단 SD를 이용한 평균 신뢰구간. 입력: 수준·모집단 SD·자료 또는 수준·모집단 SD·평균·n.'),
    'tost': (
        'Test whether mean−target is within prespecified equivalence bounds in the original units. Input: data, lower, upper, target (default 0), alpha (default .05). Both one-sided p values must be below alpha.',
        '평균−기준값이 미리 정한 동등성 범위 안인지 검정합니다. 입력: 자료·하한·상한·기준값(기본 0)·alpha(기본 .05). 두 단측 p값 모두 alpha 미만이면 동등.'),
    'tost2': (
        'Equivalence of two independent means, A−B. Input: A, B, bounds in original units, welch / student, alpha (default .05). Both one-sided p values must be below alpha.',
        '독립 두 평균 A−B의 동등성 검정. 입력: A·B·원래 단위의 하한·상한·welch/student·alpha(기본 .05). 두 단측 p값 모두 alpha 미만이면 동등.'),
    'tostpaired': (
        'Equivalence of paired mean differences, A−B. Input: complete pairs, bounds in original units and alpha (default .05). Both one-sided p values must be below alpha.',
        '대응 평균 차이 A−B의 동등성 검정. 입력: 완전한 쌍·원래 단위의 하한·상한·alpha(기본 .05). 두 단측 p값 모두 alpha 미만이면 동등.'),
    'yuen': (
        'Compare two independent trimmed means, A−B. Set trimming per tail (default .20) and confidence level; each group needs at least two retained values and positive Winsorized variance.',
        '독립 두 그룹의 절사평균 A−B를 비교합니다. 꼬리별 절사 비율 기본 .20, 신뢰수준 지정. 절사 후 그룹당 2개 이상·양의 Winsorized 분산 필요.'),
    'trimmedanova': (
        'Welch-type comparison of independent group trimmed means. Set trimming per tail in [0,.5), default .20.',
        '독립 그룹의 절사평균을 Welch형 ANOVA로 비교합니다. 꼬리별 절사 비율 [0,.5), 기본 .20.'),
    'winsorcor': (
        'Robust correlation of complete paired observations after Winsorizing each variable. Reports an approximate t-test p value.',
        '완전한 대응 자료의 각 변수를 Winsorize한 강건 상관계수. 근사 t 검정 p값 제공.'),
    'linearmodel': (
        'OLS with numeric and categorical predictors. Specify categorical predictor positions (1-based), interaction order, Type II/III tests and sum/treatment coding.',
        '숫자·범주 설명변수를 함께 쓰는 OLS. 범주 변수 번호(1부터)·상호작용 차수·Type II/III 검정·sum/treatment 코딩 지정.'),
    'glm': (
        'Generalized linear model. Columns: predictors, response. Family: gaussian / binomial (0/1) / poisson / gamma / inversegaussian / nbinom. Choose a link; NB2 alpha is fixed or estimate. Optional offset/exposure.',
        '일반화 선형모형. 열: 설명변수·반응. 분포: gaussian / binomial(0/1) / poisson / gamma / inversegaussian / nbinom. 연결함수·NB2 alpha 고정/estimate·오프셋/노출량 선택.'),
    'poissonreg': (
        'Poisson count regression with a log link. Columns: predictors, count response. Optional row-wise offset or positive exposure.',
        '로그 연결의 포아송 빈도 회귀. 열: 설명변수·빈도 반응. 행별 오프셋 또는 양수 노출량 선택.'),
    'nbreg': (
        'NB2 count regression with estimated overdispersion. Columns: predictors, count response. Optional offset or positive exposure.',
        '과산포를 추정하는 NB2 빈도 회귀. 열: 설명변수·빈도 반응. 오프셋 또는 양수 노출량 선택.'),
    'zeroinflated': (
        'Model counts with extra zeros using Poisson or NB2 and a logit zero component. Columns: predictors, count response; zero component: intercept or the same predictors.',
        '0이 많은 빈도 자료를 Poisson/NB2와 로짓 영과잉 성분으로 적합합니다. 열: 설명변수·빈도 반응. 영과잉 성분은 절편 또는 같은 설명변수.'),
    'tobit': (
        'Normal censored regression. Columns: predictors, observed response; lower bound defaults to 0, upper to none. Coefficients describe the latent response.',
        '정규 검열 회귀. 열: 설명변수·관측 반응; 하한 기본 0, 상한 기본 none. 계수는 잠재 반응 기준.'),
    'quantreg': (
        'Predict a response quantile. Columns: predictors, response; choose a quantile strictly between 0 and 1.',
        '반응값의 분위수를 예측합니다. 열: 설명변수·반응; 0과 1 사이의 분위수 지정.'),
    'robustreg': (
        'Huber regression reduces the influence of response outliers. Columns: numeric predictors, response. Tuning defaults to 1.345; inspect high-leverage observations.',
        '반응 이상값의 영향을 줄이는 Huber 회귀. 열: 숫자 설명변수·반응. 조율값 기본 1.345; 레버리지가 큰 관측값도 확인하세요.'),
    'multinomial': (
        'Predict unordered numeric categories. Columns: predictors, category response; the smallest category is the reference.',
        '순서 없는 숫자 범주를 예측합니다. 열: 설명변수·범주 반응; 가장 작은 범주가 기준.'),
    'ordinal': (
        'Proportional-odds regression for ordered numeric categories. Columns: predictors, response; category order follows numeric order.',
        '숫자순 범주의 비례오즈 회귀. 열: 설명변수·순서형 반응; 범주 순서는 숫자순.'),
    'mediation': (
        'Direct, indirect and total effects for one continuous mediator. Columns: X, M, optional covariates, Y. Reports bootstrap intervals and a Sobel approximation.',
        '연속형 매개변수 1개의 직접·간접·총 효과. 열: X·M·선택적 공변량·Y. 부트스트랩 구간·Sobel 근사 제공.'),
    'moderation': (
        'Test X×W interaction and conditional slopes at mean W ± SD. Columns: X, continuous W, optional covariates, Y; X and W are centered.',
        'X×W 상호작용과 W 평균±SD의 조건부 기울기. 열: X·연속형 W·선택적 공변량·Y. X·W는 중심화.'),
    'mixedmodel': (
        'Gaussian mixed model for repeated or clustered responses. Columns: subject ID, predictors, response. Random intercept plus up to three slopes; REML (default) / ML. Interval: Wald, profile or bootstrap.',
        '반복·군집 연속 반응의 Gaussian 혼합모형. 열: 대상 ID·설명변수·반응. 랜덤 절편·최대 3개 기울기; REML(기본)/ML. 구간: Wald·profile·bootstrap.'),
    'glmm': (
        'Mixed model for binomial or Poisson/NB2 counts. Columns: subject ID, predictors, response. Random intercept; one correlated random slope uses Laplace. Optional offset/exposure.',
        '이항·Poisson/NB2 빈도의 혼합모형. 열: 대상 ID·설명변수·반응. 랜덤 절편, 상관 기울기 1개는 Laplace 사용. 오프셋/노출량 선택.'),
    'gee': (
        'Population-average effects for clustered gaussian/binomial/poisson responses. Columns: cluster ID, predictors, response. Correlation: independence / exchangeable / ar1; small enables a small-cluster correction.',
        '군집 gaussian/binomial/poisson 반응의 모집단 평균 효과. 열: 군집 ID·설명변수·반응. 상관: independence / exchangeable / ar1; small은 소수 군집 보정.'),
    'crossvalidate': (
        'Evaluate held-out predictions. Columns: predictors, response. Set folds and seed; split: random / blocked / stratified; model: linear / ridge / lasso / elasticnet / logistic.',
        '홀드아웃 예측 성능을 평가합니다. 열: 설명변수·반응. 폴드 수·시드, 분할 random/blocked/stratified, 모형 linear/ridge/lasso/elasticnet/logistic 지정.'),
    'modelcompare': (
        'Compare baseline and expanded models on the same observations. Choose family, existing and added predictors; review fit tests and paired validation performance. CFA/SEM compares measurement/path additions.',
        '같은 관측값으로 기존·확장 모형을 비교합니다. 분석군·기존/추가 설명변수를 선택하고 적합도 검정·대응 검증 성능을 확인하세요. CFA/SEM은 측정·경로 추가 비교.'),
    'logisticcompare': (
        'Compare added predictors in binary logistic models A and B. Choose saved validation data, stratified holdout or CV; reports fit, AUC, accuracy, log loss and Brier score. Difference: B−A.',
        '이항 로지스틱 모형 A·B의 추가 설명변수를 비교합니다. 저장 검증자료·층화 홀드아웃·CV 선택. 적합도·AUC·정확도·Log loss·Brier score; 차이=B−A.'),
    'bayesmean': (
        'Bayesian normal mean and next-observation prediction. Input: sample, normal-inverse-gamma prior mu0,kappa0,alpha0,beta0, level and target. Set the prior in your data units.',
        '정규 평균의 베이지안 추정·다음 관측 예측. 입력: 표본·정규-역감마 사전 mu0,kappa0,alpha0,beta0·수준·기준값. 사전분포는 자료 단위에 맞추세요.'),
    'bayescompare': (
        'Compare two independent normal means, B−A. Choose equal/unequal variances, NIG prior, level, draws and seed. Reports posterior difference, credible interval and Bayes factors; set priors in data units.',
        '독립 정규 두 평균 B−A 비교. 등/이분산·NIG 사전·수준·추출 수·시드 선택. 사후 차이·베이지안 구간·Bayes factor; 사전은 자료 단위에 맞추세요.'),
    'bayesttest': (
        'Bayesian one-sample, paired or equal-variance independent t test. Cauchy prior on standardized effect; reports Bayes factors and posterior effect intervals. Direction: A−B or A−target.',
        '베이지안 일표본·대응·등분산 독립 t 검정. 표준화 효과의 Cauchy 사전; Bayes factor·사후 효과 구간. 방향: A−B 또는 A−기준값.'),
    'bayesanova': (
        'Bayesian comparison of independent normal group means with a common residual variance and a g prior. Reports Bayes factors and posterior group effects.',
        '공통 잔차분산·g 사전의 독립 정규 그룹 평균 비교. Bayes factor·사후 그룹 효과 제공.'),
    'bayesproportion': (
        'Estimate a success proportion with a Beta prior (default 1,1). Input: 0/1 values or success/trial rows; reports a credible interval, P(p>p0) and BF10.',
        'Beta 사전(기본 1,1)으로 성공 비율을 추정합니다. 입력: 0/1 자료 또는 성공 수·시행 수 행. 베이지안 구간·P(p>p0)·BF10 제공.'),
    'bayesrate': (
        'Estimate a Poisson rate with a Gamma shape/rate prior (default 1,1). Input: counts or count/exposure rows. Rate is the inverse scale; reports rate intervals and count prediction.',
        'Gamma shape/rate 사전(기본 1,1)으로 포아송 발생률 추정. 입력: 횟수 또는 횟수·노출량 행. rate는 척도의 역수; 발생률 구간·횟수 예측 제공.'),
    'bootstrapci': (
        'IID percentile-bootstrap interval for mean / median / stdev. Set confidence level, resamples and seed.',
        'mean/median/stdev의 IID 백분위 부트스트랩 구간. 신뢰수준·재표집 수·시드 지정.'),
    'bayesbootstrap': (
        'Bayesian bootstrap with Dirichlet weights for mean/median/variance/stdev. Analyze one sample or statistic(B)−statistic(A); choose independent/paired, level, draws and seed.',
        'Dirichlet 가중치의 베이지안 부트스트랩. mean/median/variance/stdev의 단일 표본 또는 통계량(B)−통계량(A); 독립/대응·수준·추출 수·시드 선택.'),
    'metaanalysis': (
        'Pool independent study effects. Input: effect and SE, binary arm events/totals for OR/RR, or arm mean/SD/n for MD/Hedges g. Choose fixed / dl / pm and z / hksj inference; reports forest plot and heterogeneity.',
        '독립 연구의 효과를 통합합니다. 입력: 효과·SE, 두 군 사건 수·전체 수(OR/RR), 두 군 평균·SD·n(MD/Hedges g). fixed/dl/pm·z/hksj 선택; Forest plot·이질성 제공.'),
    'metaregression': (
        'Relate independent study effects to numeric study moderators. Rows: effect, positive SE, moderators. Use log effects and SEs for ratios; reports moderator tests and residual heterogeneity.',
        '연구 효과와 숫자 조절변수의 관계를 분석합니다. 행: 효과·양수 SE·조절변수. 비율 효과·SE는 로그 척도; 조절변수 검정·잔여 이질성 제공.'),
    'metasubgroup': (
        'Compare study subgroups using a common residual heterogeneity. Rows: effect, SE, group; at least two studies per group. Reports pooled subgroup effects and a joint between-group test.',
        '공통 잔여 이질성을 사용해 연구 하위그룹을 비교합니다. 행: 효과·SE·그룹; 그룹당 연구 2개 이상. 그룹별 통합 효과·그룹 간 공동 검정 제공.'),
    'efa': (
        'Explore factors in numeric items. Extraction: pa / ml / pca; enter a factor count or parallel. Rotation: oblimin / varimax / promax. Reports loadings, communalities and factor correlations.',
        '숫자 문항의 요인 구조를 탐색합니다. 추출 pa/ml/pca, 요인 수 또는 parallel, 회전 oblimin/varimax/promax. 적재량·공통성·요인 상관 제공.'),
    'cfa': (
        'Fit a specified measurement model. Select indicator factors and cross-loadings; ML for continuous data, WLSMV for ordered categories. ML supports FIML. Includes group invariance, standardized loadings, fit indices and a path diagram.',
        '지정한 측정모형을 적합합니다. 지표별 요인·교차적재 선택; 연속형 ML, 순서형 WLSMV. ML은 FIML 지원. 집단 동일성·표준화 적재량·적합도·경로도 제공.'),
    'sem': (
        'Fit a measurement model with acyclic latent paths [from,to]. ML for continuous or WLSMV for ordered indicators. Reports standardized paths, direct/indirect/total effects, fit and diagrams; optional bootstrap intervals.',
        '측정모형에 비순환 잠재 경로 [출발,도착]를 지정합니다. 연속형 ML·순서형 WLSMV. 표준화 경로·직접/간접/총 효과·적합도·도표, 선택적 부트스트랩 구간 제공.'),
    'pca': (
        'Reduce numeric variables to principal components. Rows: observations; columns: variables. Set component count and standardization 1/0; reports variance, scores and loadings.',
        '숫자 변수를 주성분으로 요약합니다. 행=관측, 열=변수. 주성분 수·표준화 1/0; 설명분산·점수·로딩 제공.'),
    'discriminantanalysis': (
        'Classify using LDA pooled or QDA group-specific covariance. Columns: features, class; priors: empirical/equal. Optional fourth argument supplies new feature rows.',
        'LDA 합동·QDA 그룹별 공분산으로 분류합니다. 열: 변수·분류; 사전확률 empirical/equal. 선택적 넷째 인수로 새 변수 행 입력.'),
    'kmeans': (
        'Group observations by numeric-feature similarity. Input: feature rows, k and seed. Euclidean distance on original scales; standardize features as needed.',
        '숫자 변수의 유사성으로 군집화합니다. 입력: 변수 행·k·시드. 원래 척도의 유클리드 거리 사용; 필요하면 먼저 표준화하세요.'),
    'hcluster': (
        'Agglomerative hierarchical clustering. Set group count, single/complete/average/ward linkage and standardization 1/0. Reports a dendrogram and group assignments.',
        '응집형 계층 군집분석. 군집 수·single/complete/average/ward 연결·표준화 1/0 지정. 덴드로그램·군집 배정 제공.'),
    'arima': (
        'Forecast a complete, equally spaced series in time order. Set [p,d,q], horizon and level. auto selects intercept/drift by AICc at fixed orders. Optional dates; reports forecasts, conditional prediction intervals and residual checks.',
        '시간순·등간격·완전한 시계열을 예측합니다. [p,d,q]·예측 길이·수준 지정. auto는 고정 차수에서 AICc로 절편/드리프트 선택. 날짜 입력·예측표·조건부 예측구간·잔차 진단 제공.'),
    'sarima': (
        'Seasonal ARIMA forecast. Enter a complete, equally spaced series spanning at least two seasons; set [p,d,q], seasonal [P,D,Q,s], horizon and level. Optional dates; reports conditional prediction intervals and residual checks.',
        '계절 ARIMA 예측. 두 주기 이상의 등간격 완전 시계열에 [p,d,q]·계절 [P,D,Q,s]·예측 길이·수준 지정. 날짜 입력·조건부 예측구간·잔차 진단 제공.'),
    'survivalanalysis': (
        'Kaplan–Meier curves, log-rank and optional Cox regression. Columns: time, event (1=event, 0=censored), group, optional predictors; Cox 0/1.',
        'Kaplan–Meier 곡선·로그순위·선택적 Cox 회귀. 열: 시간·사건(1=발생, 0=중도절단)·그룹·선택적 설명변수; Cox 0/1.'),
    'kaplanmeier': (
        'Estimate survival with censoring. Columns: time, event (1=event, 0=censored); set confidence level.',
        '중도절단을 반영한 생존확률 추정. 열: 시간·사건(1=발생, 0=중도절단); 신뢰수준 지정.'),
    'logrank': (
        'Compare survival between two groups. Input: two time/event tables, or current-data columns time, event, group.',
        '두 그룹의 생존 비교. 입력: 두 시간·사건 표 또는 현재 데이터의 시간·사건·그룹 열.'),
    'cox': (
        'Relate predictors to event hazard under proportional hazards. Columns: time, event 0/1, predictors. Ties: efron / breslow; optional entry-time column and PH check.',
        '비례위험 가정으로 설명변수와 사건 위험의 관계를 분석합니다. 열: 시간·사건 0/1·설명변수. 동률 efron/breslow; 진입시간 열·PH 검정 선택.'),
    'parametricsurvival': (
        'Weibull, exponential or lognormal AFT survival model. Rows: positive time, event 0/1, optional predictors and delayed entry. Reports time ratios, event-time quantiles and survival probabilities.',
        'Weibull·지수·로그정규 AFT 생존모형. 행: 양수 시간·사건 0/1·선택적 설명변수·지연 진입. 시간비·사건시간 분위수·생존확률 제공.'),
    'testpower': (
        'Power for a t-test design. Input: Cohen d, n, alpha, independent / paired / onesample and two / greater / less. n is per group or the number of pairs.',
        't 검정의 검정력. 입력: Cohen d·n·alpha·independent/paired/onesample·two/greater/less. n은 그룹별 수 또는 대응 쌍 수.'),
    'samplesize': (
        'Sample size for a target t-test power. Input: Cohen d, target power, alpha, design and alternative. Returns n per group or the number of pairs.',
        '목표 t 검정력을 위한 표본 수. 입력: Cohen d·목표 검정력·alpha·설계·대립가설. 그룹별 n 또는 대응 쌍 수 반환.'),
    'designpower': (
        'Power for fixed-sample z, proportion, two-proportion or variance-ratio designs. Set design, effect, n, alpha, direction and reference proportion; two-group n is per group.',
        '고정 표본 z·단일 비율·두 비율·분산비 설계의 검정력. 설계·효과·n·alpha·방향·기준비율 지정; 두 그룹의 n은 그룹별 수.'),
    'designsize': (
        'Sample size for the same designs as designpower. Replace n with target power; reports minimum n, total n and achieved power.',
        'designpower와 같은 설계의 표본 수. n 대신 목표 검정력을 지정하면 최소 n·총 n·달성 검정력을 제공합니다.'),
}


def catalog_description(item, korean=False):
    """Use dedicated catalog copy, with schema help as a fallback for new analyses."""
    descriptions = DESCRIPTIONS.get(item['id'])
    if descriptions:
        return descriptions[int(bool(korean))]
    return item['helpKo'] if korean else item['help']
