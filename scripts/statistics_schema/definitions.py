"""Analysis presets and the shared Android/Web menu order."""
from statistics_social_schema import SPECS as SOCIAL_SPECS
from statistics_research_schema import SPECS as RESEARCH_SPECS
from statistics_comparison_schema import SPEC as COMPARISON_SPEC
from statistics_extensions_schema import SPECS as EXTENSION_SPECS
from .examples import GROUPS, COUNTS, CATEGORIES, CLUSTERS, GLMM, SURVIVAL, SERIES, LOGISTIC_COMPARE_ROWS
from .help import TIME_HELP, DATE_HELP

specs = [
    ('arima','ARIMA / time-series forecast','ARIMA / 시계열 예측','list',',[1,1,0],12,0.95,auto',SERIES,*TIME_HELP),
    ('sarima','SARIMA / seasonal forecast','SARIMA / 계절 시계열 예측','list',',[1,0,0],[0,1,1,4],8,0.95,auto',SERIES,TIME_HELP[0]+' Seasonal [P,D,Q,s] adds seasonal AR/differencing/MA and period s; at least two complete periods are required.',TIME_HELP[1]+' 계절 [P,D,Q,s]로 계절 AR·차분·MA·주기 s를 지정하며 최소 두 주기의 관측이 필요합니다.'),
    ('tinterval','t confidence interval','t 신뢰구간','list',',95','[1,2,3,4,5]','Mean confidence interval with unknown population SD: tinterval(level,data) or tinterval(level,mean,SD,n).','모집단 표준편차를 모르는 평균의 신뢰구간: tinterval(수준,자료) 또는 tinterval(수준,평균,표준편차,n).'),
    ('zinterval','z confidence interval','z 신뢰구간','list',',95,2','[1,2,3,4,5]','Mean confidence interval with known population SD: zinterval(level,sigma,data) or zinterval(level,sigma,mean,n).','모집단 표준편차를 아는 평균의 신뢰구간: zinterval(수준,모집단표준편차,자료) 또는 zinterval(수준,모집단표준편차,평균,n).'),
    ('propztest','One-sample proportion z test','단일 표본 비율 z 검정','table','','[[60,100]]',
     'propztest(p0,data) or propztest(p0,successes,trials); binary 0/1 data or [[successes,trials],...]. Optional both / left / right. Null-based standard error, no continuity correction; independent observations and adequate expected counts are required.',
     'propztest(p0,자료) 또는 propztest(p0,성공수,시행수); 0/1 자료 또는 [[성공수,시행수],...]. 선택적 both·left·right. 귀무가설의 표준오차, 연속성 보정 없음. 독립 관측·충분한 기대빈도가 필요합니다.'),
    ('propztest2','Two-sample proportion z test','두 표본 비율 z 검정','table','','[[60,100],[45,100]]',
     'propztest2(A,B) or propztest2(successesA,trialsA,successesB,trialsB). H0: pA=pB; pooled standard error, no continuity correction. Optional both / left / right for A−B. Independent binary samples; paired outcomes require McNemar.',
     'propztest2(A,B) 또는 propztest2(성공수A,시행수A,성공수B,시행수B). H0: pA=pB, 합동 표준오차, 연속성 보정 없음. A−B에 대한 both·left·right 선택. 독립 이항 표본용이며 대응 결과는 McNemar를 사용합니다.'),
    ('shapiro','Shapiro–Wilk','Shapiro–Wilk','list','','[1,2,3,4,5]','Normality test for 3 to 5000 observations; interpret with Q–Q plots.','관측값 3~5000개의 정규성 검정; Q–Q plot과 함께 해석합니다.'),
    ('tukey','Tukey–Kramer','Tukey–Kramer','groups','',GROUPS,'All pairwise mean comparisons for independent groups with equal variances.','등분산 독립 그룹의 모든 쌍별 평균 사후비교.'),
    ('gameshowell','Games–Howell','Games–Howell','groups','',GROUPS,'All pairwise mean comparisons for independent groups with unequal variances.','이분산 독립 그룹의 모든 쌍별 평균 사후비교.'),
    ('linearmodel','Factorial linear model / ANOVA','요인 선형회귀 / ANOVA','table',',[1,2],2,3,sum','[[1,1,2],[1,1,4],[1,2,5],[1,2,6],[2,1,4],[2,1,5],[2,2,8],[2,2,10]]','General OLS with numeric and categorical predictors. Categorical positions are one-based; interaction order, Type II/III, sum/treatment coding. Uses joint partial F tests for each term. Three-way and higher interactions require enough replicated observations and identifiable columns.','숫자·범주 설명변수를 포함한 일반 OLS. 범주 변수 번호는 1부터 시작하며 상호작용 차수·Type II/III·sum/treatment 코딩을 지정합니다. 항마다 여러 계수를 부분 F로 함께 검정합니다. 3요인 이상 상호작용에도 충분한 반복 관측·식별 가능한 열이 필요합니다.'),
    ('twowayanova','Two-way ANOVA','이요인 ANOVA','table',',1','[[1,1,2],[1,1,4],[1,2,5],[1,2,6],[2,1,4],[2,1,5],[2,2,8],[2,2,10]]','Independent observations, two categorical factors and a numeric response. Type III F tests with sum contrasts; interaction 1 (default) or additive 0. Normal errors and common residual variance; replication and a full-rank design are required.','독립 관측·두 범주 요인·숫자 반응. 합이 0인 대비의 Type III F 검정. 상호작용 1(기본) 또는 가법 0. 정규 오차·공통 잔차분산을 가정하며 반복 관측과 식별 가능한 설계가 필요합니다.'),
    ('friedman','Friedman test','Friedman 검정','table','','[[2,4,5],[3,4,7],[4,7,8],[2,3,6],[5,6,7]]','Rows are independent subjects; columns are at least three repeated conditions. Complete matched rows, midranks and tie correction. Chi-square approximation; small samples or few conditions can give inaccurate p values. Reports Kendall W.','행은 독립 대상, 열은 3개 이상 반복 조건입니다. 완전한 대응 행·평균순위·동점 보정. χ² 근사이므로 소표본·소수 조건에서 p값이 부정확할 수 있습니다. Kendall W를 제공합니다.'),
    ('ancova','ANCOVA','ANCOVA (공분산분석)','table',',0.95,1','[[1,1,3],[1,2,5],[1,3,4],[1,4,8],[2,2,6],[2,3,7],[2,4,9],[2,5,8],[3,1,5],[3,3,8],[3,4,10],[3,6,11]]','Rows: numeric group ID, one or more covariates, response; confidence level (default .95); slope homogeneity check 0/1 (default 1). One factor, common slopes, Type II F tests and adjusted means at pooled covariate means.','열: 숫자 그룹 ID, 하나 이상의 공변량, 종속변수; 신뢰수준(기본 .95), 기울기 동질성 검정 0/1(기본 1). 일요인·공통 기울기, Type II F 검정, 전체 공변량 평균에서의 조정 평균.'),
    ('glm','Generalized linear model (GLM)','GLM (일반화 선형모형)','table',',gaussian,auto,1','[[0,2],[1,4],[2,4],[3,7],[4,8],[5,9]]','Rows: predictors, response; family gaussian / binomial (0/1) / poisson / gamma / inversegaussian / nbinom; link auto or a supported link; NB2 alpha: positive fixed value (default 1) or estimate for joint ML; optional offset/exposure vector and mode. Default links: identity, logit, log, log, log, log. Model-based Wald z 95% intervals; Pearson dispersion for Gaussian/Gamma/inverse Gaussian. Use estimate as the fourth argument to estimate NB2 alpha jointly with coefficients; its uncertainty enters the observed-information covariance. Numeric alpha retains the fixed-alpha model.','열: 설명변수, 반응변수; 분포 gaussian·binomial(0/1)·poisson·gamma·inversegaussian·nbinom; 연결함수 auto 또는 지원 함수; NB2 alpha: 양수 고정값(기본 1) 또는 estimate(공동 ML 추정); 선택적 오프셋·노출량 목록과 유형. 기본 연결함수는 identity·logit·log·log·log·log. 모형 기반 Wald z 95% 구간; 정규·Gamma·역가우스는 Pearson 분산 추정. 넷째 인수를 estimate로 지정하면 NB2 alpha와 계수를 공동 ML 추정하며 관측 정보행렬에 alpha의 불확실성을 반영합니다. 숫자를 입력하면 alpha를 고정합니다.'),
    ('padjust','Multiple testing','다중검정 보정','list',',holm,0.05','[0.01,0.04,0.03,0.2]', 'p values; method bonferroni / holm / fdr (BH) / by; alpha.', 'p값 목록; 방법 bonferroni / holm / fdr (BH) / by; 유의수준.'),
    ('cohend',"Cohen’s d","Cohen의 d",'groups',',independent',GROUPS,'Two samples; independent (pooled d) or paired (dz).','두 표본; independent(합동 SD) 또는 paired(차이의 SD).'),
    ('eta2','η² effect size','η² 효과크기','groups','',GROUPS,'Independent groups as separate lists.','독립 그룹별 목록.'),
    ('levene','Levene / Brown–Forsythe','Levene / Brown–Forsythe','groups','',GROUPS,'Separate group lists; median-centered equal-variance test.','그룹별 목록; 중앙값 기준 등분산 검정.'),
    ('bartlett','Bartlett','Bartlett','groups','',GROUPS,'Separate group lists; normality assumption.','그룹별 목록; 정규성 가정.'),
    ('mcnemar','McNemar','McNemar','table',',exact','[[20,8],[2,15]]','Paired 2×2 count table; exact / corrected / asymptotic.','대응 2×2 빈도표; exact / corrected / asymptotic.'),
    ('bayesproportion','Bayesian proportion','베이지안 비율','list',',1,1,0.95,0.5','[1,1,0,1,0,1,1,1,0,1]','Binary 0/1 list or [[successes,trials],...]; Beta prior alpha, beta (default 1,1); credible level; threshold p0 in (0,1). Returns equal-tailed interval, P(p>p0), next-success probability and BF10 (Beta alternative / point null p=p0).','0/1 목록 또는 [[성공 수,시행 수],...]; Beta 사전 alpha,beta(기본 1,1), 구간 수준, 기준 p0(0~1 사이). 등꼬리 구간·P(p>p0)·다음 성공 확률·BF10(Beta 대립 / p=p0 점귀무).'),
    ('bayesmean','Bayesian mean','베이지안 평균','list',',0,1,2,1,0.95,0','[1,2,3,4,5]','Normal sample, unknown variance; prior mu0,kappa0,alpha0,beta0; credible level; threshold. Variance ~ InvGamma(alpha0,beta0), mean | variance ~ Normal(mu0,variance/kappa0). Defaults 0,1,2,1 are proper, scale-dependent priors. Returns Student-t mean interval and next-observation predictive interval.','분산 미지의 정규 표본; 사전 mu0,kappa0,alpha0,beta0, 구간 수준, 기준값. 분산 ~ InvGamma(alpha0,beta0), 평균|분산 ~ Normal(mu0,분산/kappa0). 기본 0,1,2,1은 자료 척도에 맞춰 조절할 적정 사전분포. 평균의 t 구간과 다음 관측 예측구간.'),
    ('bayescompare','Bayesian Two-Sample Comparison','베이지안 두 표본 비교','groups',',equal,0,0.01,2,1,0.95,20000,0','[10,11,9,10,12],[13,14,12,15,13]',
     'Two independent normal samples (at least 2 each); variance equal / unequal; mu0,kappa0,alpha0,beta0; credible level; IID posterior draws (2000-100000), seed. H1: independent Normal(mu0,variance/kappa0) means with shared (equal) or independent (unequal) InvGamma(alpha0,beta0) variances. H0: B-A=0 with nuisance prior conditioned from H1. BF10/BF01 use the Savage-Dickey density ratio. Reports B-A mean, equal-tailed credible interval, P(muB>muA), and posterior effect (B-A)/sqrt((varianceA+varianceB)/2). Equal-mode difference summaries and BF are analytic; unequal BF uses numerical t convolution, unequal intervals/probability and effect intervals use simulation. MCSE, draws and seed are reported. Defaults are proper but unit-dependent; choose priors before inspecting outcomes.',
     '독립 정규 표본 두 개(각 2개 이상); 분산 equal·unequal; mu0,kappa0,alpha0,beta0; 구간 수준; IID 사후 추출 수(2000~100000), 시드. H1: 평균|분산은 독립 Normal(mu0,분산/kappa0), 분산은 공통(등분산) 또는 독립(이분산) InvGamma(alpha0,beta0). H0: B-A=0이며 H1을 이 조건으로 제한한 방해모수 사전분포를 사용합니다. BF10/BF01은 Savage-Dickey 밀도비를 사용합니다. B-A 평균·등꼬리 신용구간·P(muB>muA)·사후 효과크기 (B-A)/sqrt((분산A+분산B)/2)를 출력합니다. 등분산 차이 요약·BF는 해석적, 이분산 BF는 t 합성곱 수치 적분, 이분산 구간·확률 및 효과크기 구간은 시뮬레이션입니다. MCSE·추출 수·시드 포함. 기본 사전분포는 적정하지만 단위에 의존하므로 결과를 보기 전에 척도에 맞게 지정하세요.'),
    ('bayesrate','Bayesian Poisson rate','베이지안 발생률','list',',1,1,0.95,1','[0,2,1,3,2]','Count list (one exposure unit each) or [[count,exposure],...]; Gamma prior shape, rate (inverse scale, default 1,1); credible level; nonnegative threshold. Equal-tailed rate interval and predictive count mean/SD for one exposure unit.','횟수 목록(관측당 노출 1) 또는 [[횟수,노출량],...]; Gamma 사전 shape,rate(척도의 역수, 기본 1,1), 구간 수준, 0 이상 기준값. 발생률 등꼬리 구간과 노출 1단위의 예측 횟수 평균·SD.'),
    ('kaplanmeier','Kaplan–Meier','Kaplan–Meier','table',',0.95',SURVIVAL,'Rows: time, event (1=event, 0=censored); confidence level.','열: 시간, 사건(1=발생, 0=중도절단); 신뢰수준.'),
    ('logrank','Log-rank','로그순위 검정','survivalgroups','','[[1,1],[3,1],[4,0],[6,1]],[[2,0],[4,1],[5,1],[7,0]]','Two time/event tables. Current data: time, event, group (exactly two groups).','두 시간/사건 표. 현재 데이터 열: 시간, 사건, 그룹(2개).'),
    ('survivalanalysis','Survival analysis','생존분석','table',',0,efron,-1,1','[[1,1,1],[2,1,2],[3,0,1],[4,1,2],[5,1,1],[6,0,2],[7,1,2],[8,1,1]]','Rows: time, event (0/1), group ID, optional Cox predictors; Cox 0=off, 1=on; then ties and the PH check.','열: 시간, 사건(0/1), 그룹 ID, 선택적 Cox 설명변수. Cox 0=끔, 1=켬; 이어서 동률 처리와 PH 검정.'),
    ('cox','Cox regression','Cox 회귀','table',',efron,-1,1','[[1,1,0],[2,1,1],[3,0,0],[4,1,1],[5,1,0],[6,0,1],[7,1,1],[8,1,0]]','Rows: time, event 0/1, predictors. Ties efron (default) or breslow; entry column for left truncation (-1 none); PH check 0/1.','열: 시간, 사건 0/1, 설명변수. 동률 efron(기본)/breslow, 좌측 절단 진입시간 열(-1 없음), PH 검정 0/1.'),
    ('repeatedanova','Repeated-measures ANOVA','반복측정 ANOVA','table',',1','[[2,4,5],[3,4,7],[4,7,8],[2,3,6],[5,6,7]]','Rows=subjects, columns=conditions. Second-factor levels: 1 = one-way, 2+ = two-way (first factor slowest); GG corrections.','행=대상, 열=조건. 둘째 요인 수준: 1=일요인, 2 이상=이요인(첫 요인 최외곽); GG 보정.'),
    ('mixedmodel','Mixed model','혼합모형','table',',0,reml',CLUSTERS,'Rows: subject ID, predictors, response. Gaussian random intercept with up to three random slopes (0 none, a predictor position, or [1,2]); third argument reml (default) or ml; up to 5000 rows. Includes subject BLUPs, slope correlations and singular-fit diagnostics; random-slope ICC is at x=0; asymptotic Wald z inference.','열: 대상 ID, 설명변수, 반응. Gaussian 랜덤 절편 + 최대 3개 랜덤 기울기(0 없음, 변수 위치, 또는 [1,2]); 셋째 인수 reml(기본)·ml; 최대 5000행. 대상별 BLUP·기울기 상관·singular 진단 포함; 기울기 ICC는 x=0 기준; 점근 Wald z 추론.'),
    ('glmm','Generalized mixed model (GLMM)','일반화 혼합모형 (GLMM)','table',',binomial,15',GLMM,'Rows: subject ID, predictors, response. Random intercept, optionally one correlated random slope (seventh argument: selected predictor position, 0 = none). Slopes use two-dimensional Laplace (third argument 1), use [],offset,likelihood before the slope position. Covariance and conditional modes are reported in original units. Random intercept: binomial (0/1, logit), poisson or nbinom (NB2, log). ML adaptive Gauss-Hermite quadrature: 15 points default, 1 = Laplace, otherwise 7-31. Optional fourth argument offset vector, fifth offset / exposure. Limit 1500 rows, 8 fixed coefficients. Subject-specific effects; joint marginal observed information by central differences; asymptotic Wald inference.','열: 대상 ID, 설명변수, 반응. 랜덤 절편 + 선택적 상관 랜덤 기울기 1개(일곱째 인수: 선택한 설명변수 번호, 0 없음). 기울기는 2차원 Laplace(셋째 인수 1), 번호 앞에 [],offset,likelihood를 지정합니다. 공분산·조건부 최빈값은 원래 단위로 표시합니다. 랜덤 절편: binomial(0/1, 로짓), poisson·nbinom(NB2, 로그). ML 적응형 Gauss-Hermite 적분: 기본 15점, 1=Laplace, 그 외 7~31점. 선택적 넷째 인수 오프셋 목록, 다섯째 offset·exposure. 최대 1500행·고정계수 8개. 대상별 조건부 효과, 중앙차분 관측 정보행렬·점근 Wald 추론.'),
    ('gee','GEE','GEE','table',',gaussian,independence',CLUSTERS,'Rows: cluster ID, predictors, response. gaussian / binomial / poisson; working correlation independence / exchangeable / ar1; fourth argument [i,j] interaction pairs; sandwich SE. Pearson dispersion-adjusted correlation; AR(1) uses row order and equal spacing. Few-cluster Wald inference may be unreliable.','열: 군집 ID, 설명변수, 반응. gaussian / binomial / poisson; 작업상관 independence / exchangeable / ar1; 넷째 인수 [i,j] 상호작용 쌍; 강건 SE. Pearson 분산 보정 상관; AR(1)은 행 순서·등간격 사용. 소수 군집의 Wald 추론은 부정확할 수 있습니다.'),
    ('multinomial','Multinomial logistic','다항 로지스틱','table','',CATEGORIES,'Rows: predictors, numeric category response. Smallest category is reference.','열: 설명변수, 숫자 범주 반응. 가장 작은 범주가 기준.'),
    ('ordinal','Ordinal logistic','순서형 로지스틱','table','',CATEGORIES,'Rows: predictors, ordered numeric response. Proportional-odds cumulative logit.','열: 설명변수, 순서가 있는 숫자 반응. 비례오즈 누적 로짓.'),
    ('poissonreg','Poisson regression','포아송 회귀','table','',COUNTS,'Rows: predictors, integer count response. Log link. Optional second argument row-aligned offset/exposure list; third argument offset (default) or exposure (positive, log transformed).','열: 설명변수, 정수 빈도 반응. 로그 연결함수. 선택적 둘째 인수 행별 오프셋·노출량 목록; 셋째 인수 offset(기본)·exposure(양수, 로그 변환).'),
    ('nbreg','Negative binomial regression','음이항 회귀','table','','[[0,0],[0,0],[0,1],[0,8],[1,0],[1,1],[1,3],[1,15],[2,0],[2,2],[2,5],[2,23],[3,1],[3,3],[3,10],[3,35]]','Rows: predictors, integer count response. NB2 with estimated dispersion. Optional offset/exposure list and offset (default) / exposure mode.','열: 설명변수, 정수 빈도 반응. NB2 과산포 모수 추정. 선택적 오프셋·노출량 목록과 offset(기본)·exposure 모드.'),
    ('bootstrapci','Bootstrap confidence interval','부트스트랩 신뢰구간','list',',mean,0.95,2000,0','[1,2,3,4,5,8]','Statistic mean / median / stdev, confidence level, resamples, seed. Percentile IID bootstrap.','통계량 mean / median / stdev, 신뢰수준, 재추출 수, 시드. IID 백분위 방식.'),
    ('bayesbootstrap','Bayesian Bootstrap','베이지안 부트스트랩','list',',mean,0.95,10000,0','[1,2,3,4,5,8]','Dirichlet(1,…,1) weights on IID observed values; mean / median / variance / stdev, credible level, draws, seed. Median estimate uses the ordinary sample median (average the two middle values for even n); posterior draws use the Lower weighted quantile (smallest value with weighted CDF >= 0.5); variance/SD use population weights. Equal-tailed simulated posterior interval and histogram. Two samples: bayesbootstrap(A,B,mean,0.95,10000,0,independent); paired uses shared row weights. Comparison is statistic(B) - statistic(A).','독립 관측값의 Dirichlet(1,…,1) 가중치; mean / median / variance / stdev, 베이지안 구간 수준·추출 수·시드. 중앙값 estimate는 일반 표본 중앙값(짝수 표본은 가운데 두 값의 평균)이고 사후추출은 Lower weighted quantile(가중 누적확률이 0.5 이상인 최소값), 분산·SD는 모집단 가중치 기준. 등꼬리 사후 구간·히스토그램. 두 표본: bayesbootstrap(A,B,mean,0.95,10000,0,independent); paired는 같은 행의 가중치를 공유합니다. 차이는 통계량(B) - 통계량(A)입니다.'),
    ('testpower','Power','검정력','none','', '0.5,64,0.05,independent','Cohen d, n per group/pairs, alpha, independent / paired / onesample, alternative two (default) / greater / less. Exact noncentral-t power.','Cohen d, 그룹별 n/쌍 수, 유의수준, independent / paired / onesample, 대립가설 two(기본) / greater / less. 정확 noncentral-t 검정력.'),
    ('samplesize','Sample size','표본수','none','','0.5,0.8,0.05,independent','Cohen d, target power, alpha, design, alternative. Exact noncentral-t power.','Cohen d, 목표 검정력, 유의수준, 설계, 대립가설. 정확 noncentral-t 검정력.'),
    ('kstest','Kolmogorov–Smirnov','Kolmogorov–Smirnov','groups','',GROUPS,'Two sample lists, or kstest(data,normal,mu,sigma) / kstest(data,uniform,lower,width). Continuous null; one-sample p is asymptotic.','두 표본 목록 또는 kstest(data,normal,평균,SD) / kstest(data,uniform,하한,폭). 연속분포 가정; 일표본 p는 근사.'),
    ('crossvalidate','Cross-validation','교차검증','table',',3,0','[[0,1],[1,3],[2,4],[3,7],[4,8],[5,11],[6,12],[7,15],[8,16]]','Rows: predictors, response; folds, seed; split random (default) / blocked / stratified; model linear (default) / ridge / lasso / elasticnet / logistic; penalty alpha or [alpha,l1 ratio].','열: 설명변수, 반응; 폴드 수, 시드; 분할 random(기본) / blocked / stratified; 모형 linear(기본) / ridge / lasso / elasticnet / logistic; 벌점 alpha 또는 [alpha,l1 비율].'),
    ('pca','PCA','주성분 분석','table',',2,1','[[1,2],[2,1],[3,4],[4,3],[5,7]]','Rows=observations, columns=features; components, standardize 1/0.','행=관측, 열=변수; 주성분 수, 표준화 1/0.'),
    ('kmeans','K-means clustering','K-means 군집','table',',2,0','[[1,1],[1,2],[2,1],[8,8],[8,9],[9,8]]','Numeric feature rows; k, seed. Euclidean distance, 10 restarts, raw feature scale.','숫자 변수 행; k, 시드. 유클리드 거리, 10회 초기화, 원래 변수 척도.'),
    ('impute','Missing-value imputation','결측치 대체','table',',mean','[[1,NA],[2,4],[NA,6],[4,8]]','NA for missing cells; mean / median / mode / regression / knn with neighbours (default 5). Single imputation.','결측값은 NA; mean / median / mode / regression / knn(이웃 수 기본 5). 단일 대체.'),
]
specs.append(('logisticcompare','Nested logistic model comparison','중첩 로지스틱 모형 비교','table',',1,crossvalidation,5,0.5,0.95,200,0,[48,0]',str(LOGISTIC_COMPARE_ROWS).replace(' ',''),'Select a binary response, Model A predictors and added Model B predictors. A selected validation dataset, stratified holdout or stratified cross-validation. Compare unpenalized MLE fit (LRT, AIC/BIC) and paired validation AUC, accuracy, log loss, Brier score and calibration. Differences are B minus A.','이항 반응·Model A 설명변수·Model B 추가 설명변수를 선택합니다. 선택한 데이터셋 검증·층화 홀드아웃·층화 교차검증을 지원합니다. 무벌점 MLE 적합도(LRT·AIC/BIC)와 대응 검증 AUC·정확도·Log loss·Brier score·보정 성능을 비교합니다. 차이는 B−A입니다.'))
specs.append(COMPARISON_SPEC)
CORRELATION_SPECS=[
    ('pearson','Pearson correlation','피어슨 상관','groups',',both','[1,2,3,4,5],[2,1,3,4,5]',
     'At least three paired finite observations with variation in both columns. Pearson r and t(n - 2) p value; both / left / right. Independent rows; the zero-correlation test assumes a bivariate normal population.',
     '양쪽 열에 변동이 있는 유한 관측값 3쌍 이상. 피어슨 r과 t(n - 2) p값; both / left / right. 행 간 독립이며 무상관 검정은 이변량 정규 모집단을 가정합니다.'),
    ('spearman','Spearman rank correlation','스피어만 순위상관','groups',',both','[1,2,2,4,5],[2,1,3,4,5]',
     'Paired finite observations; average ranks for ties. Both / left / right. Exact permutation p for n <= 8; otherwise approximate t p (small samples may need a permutation test).',
     '대응하는 유한 관측값; 동순위는 평균 순위. both / left / right. n <= 8은 정확 순열 p값, 그 외 t 근사 p값(작은 표본에는 순열 검정이 필요할 수 있음).'),
    ('kendall','Kendall tau-b correlation','켄달 tau-b 상관','groups',',both','[1,2,2,4,5],[2,1,3,4,5]',
     'Paired finite observations; tau-b adjusts for ties. Both / left / right. Exact p without ties for n <= 33; otherwise tie-corrected normal approximation.',
     '대응하는 유한 관측값; tau-b는 동순위를 보정. both / left / right. 동순위 없이 n <= 33이면 정확 p값, 그 외 동순위 보정 정규 근사.')]
specs.extend(CORRELATION_SPECS)
specs.extend(SOCIAL_SPECS)
specs.extend(RESEARCH_SPECS)
specs.extend(EXTENSION_SPECS)
# Menu placement and order are shared by Android and Web; function IDs stay stable.
menus = [
    ('general', 'Correlation', '상관분석', ['pearson','spearman','kendall']),
    ('preparation', 'Data preparation', '데이터 준비', ['impute']),
    ('general', 'Categorical data', '범주형 자료', ['propztest','propztest2','mcnemar']),
    ('general', 'Reliability & agreement', '신뢰도·일치도', ['cronbach','omega','icc','cohenkappa','blandaltman']),
    ('tests', 'Distribution & variance', '분포·분산 검정', ['shapiro','kstest','levene','bartlett']),
    ('tests', 'Post-hoc comparisons', '사후비교', ['tukey','gameshowell','dunn']),
    ('tests', 'Group comparisons', '그룹 비교', ['twowayanova','ancova','manova','repeatedanova','friedman']),
    ('tests', 'Effect Size', 'Effect Size (효과크기)', ['cohend','eta2','cramerv','phi']),
    ('tests', 'Multiple testing', '다중검정 보정', ['padjust']),
    ('tests', 'Confidence intervals', '신뢰구간', ['tinterval','zinterval']),
    ('tests', 'Equivalence tests (TOST)', '동등성 검정 (TOST)', ['tost','tost2','tostpaired']),
    ('tests', 'Robust statistics', '강건 통계', ['yuen','trimmedanova','winsorcor']),
    ('models', 'Generalized regression', '일반화 회귀', ['linearmodel','glm','poissonreg','nbreg','zeroinflated','tobit','quantreg','robustreg','multinomial','ordinal']),
    ('models', 'Mediation & moderation', '매개·조절 분석', ['mediation','moderation']),
    ('models', 'Repeated & clustered data', '반복·군집 자료', ['mixedmodel','glmm','gee']),
    ('models', 'Model validation', '모형 검증', ['crossvalidate','modelcompare','logisticcompare']),
    ('advanced', 'Bayesian inference', '베이지안 추론', ['bayesmean','bayescompare','bayesttest','bayesanova','bayesproportion','bayesrate']),
    ('advanced', 'Resampling', '재표집', ['bootstrapci','bayesbootstrap']),
    ('advanced', 'Research synthesis', '연구 종합', ['metaanalysis','metaregression','metasubgroup']),
    ('advanced', 'Measurement & structural models', '측정·구조 모형', ['efa','cfa','sem']),
    ('advanced', 'Multivariate analysis', '다변량 분석', ['pca','discriminantanalysis','kmeans','hcluster']),
    ('advanced', 'Time series & forecasting', '시계열·예측', ['arima','sarima']),
    ('advanced', 'Survival analysis', '생존분석', ['survivalanalysis','kaplanmeier','logrank','cox','parametricsurvival']),
    ('advanced', 'Power & sample size', '검정력·표본수', ['testpower','samplesize','designpower','designsize']),
]


def build_definitions():
    """Return fresh definitions in menu order, retaining public IDs and examples."""
    schema = [{'id':id_,'label':label,'ko':ko,'input':layout,'suffix':suffix,'example':f'{id_}({data}{suffix})','help':help_,'helpKo':helpko} for id_,label,ko,layout,suffix,data,help_,helpko in specs]
    definitions = {item['id']: item for item in schema}
    schema = []
    for section, group, group_ko, ids in menus:
        for id_ in ids:
            schema.append(dict(definitions[id_], section=section, group=group, groupKo=group_ko))
    assert len(schema) == len(definitions) and len({item['id'] for item in schema}) == len(definitions)
    definitions = {item['id']: item for item in schema}
    definitions['tinterval']['example']='tinterval(95,[1,2,3,4,5])'
    definitions['zinterval']['example']='zinterval(95,2,[1,2,3,4,5])'
    definitions['propztest']['example']='propztest(0.5,[[60,100]])'
    definitions['propztest2']['example']='propztest2(60,100,45,100)'
    for id_ in ('arima','sarima'):
        definitions[id_]['help'] += DATE_HELP[0]
        definitions[id_]['helpKo'] += DATE_HELP[1]
    definitions['cramerv'].update(label='Phi / Cramér’s V',ko='Phi / Cramér의 V')
    definitions['phi']['hidden']=True
    return schema
