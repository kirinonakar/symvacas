export const statisticsAnalysisHelp = {
  "ttest": {
    "help": "Model\nTests whether a population mean equals a target.\n\nWhen to use\nUse for one numeric sample with unknown population SD; review normality and outliers.\n\nParameters\nChoose sample column, null mean and alternative. Blank cells are omitted.",
    "helpKo": "모델 설명\n모집단 평균이 기준값과 같은지 검정합니다.\n\n사용 시점\n모집단 표준편차를 모르는 숫자 표본 하나에 사용하며 정규성·이상값을 확인합니다.\n\n파라미터 설명\n표본 열·귀무가설 평균·대립가설을 선택합니다. 빈 셀은 제외합니다."
  },
  "ttest2": {
    "help": "Model\nTests a specified difference between two independent population means.\n\nWhen to use\nUse for independent groups such as treatment and control. Welch allows unequal variances; Student assumes equal variances.\n\nParameters\nChoose groups A/B or two columns, Welch/Student, null difference and alternative. Difference is A−B.",
    "helpKo": "모델 설명\n독립 두 모집단 평균의 차이가 기준 차이와 같은지 검정합니다.\n\n사용 시점\n처리군·대조군처럼 독립인 그룹에 사용합니다. Welch는 이분산을 허용하며 Student는 등분산을 가정합니다.\n\n파라미터 설명\n그룹 A·B 또는 열 두 개, Welch/Student, 기준 차이·대립가설을 선택합니다. 차이는 A−B입니다."
  },
  "ttestpaired": {
    "help": "Model\nTests whether the mean within-pair difference equals a target.\n\nWhen to use\nUse for before/after measurements on the same subjects or matched pairs; check normality of differences.\n\nParameters\nChoose paired columns or group/value columns, matching method, null difference and alternative. Use complete pairs; difference is A−B.",
    "helpKo": "모델 설명\n대응 쌍 차이의 모집단 평균이 기준값과 같은지 검정합니다.\n\n사용 시점\n같은 대상의 전·후 측정 또는 짝지은 표본에 사용하며 차이값의 정규성을 확인합니다.\n\n파라미터 설명\n대응 열 또는 그룹·값 열, 연결 방식·기준 차이·대립가설을 선택합니다. 완전한 쌍을 사용하며 차이는 A−B입니다."
  },
  "ztest": {
    "help": "Model\nTests whether a population mean equals a target using a known population SD.\n\nWhen to use\nUse when population SD is known and the mean sampling distribution is normal or adequately approximated.\n\nParameters\nChoose sample column, null mean, known population SD σ and alternative.",
    "helpKo": "모델 설명\n알려진 모집단 표준편차로 모집단 평균이 기준값과 같은지 검정합니다.\n\n사용 시점\n모집단 표준편차를 알고 평균의 표집분포가 정규이거나 정규근사가 적절할 때 사용합니다.\n\n파라미터 설명\n표본 열·귀무가설 평균·알려진 모집단 표준편차 σ·대립가설을 선택합니다."
  },
  "ztest2": {
    "help": "Model\nTests a specified difference between independent means using known population SDs.\n\nWhen to use\nUse when both population SDs are known and normal approximation is adequate.\n\nParameters\nChoose groups A/B, null difference, population SDs σx/σy and alternative. Difference is A−B.",
    "helpKo": "모델 설명\n알려진 모집단 표준편차로 독립 두 모집단 평균의 기준 차이를 검정합니다.\n\n사용 시점\n두 모집단 표준편차를 알고 정규근사가 적절한 독립 두 표본에 사용합니다.\n\n파라미터 설명\n그룹 A·B, 기준 차이·모집단 표준편차 σx/σy·대립가설을 선택합니다. 차이는 A−B입니다."
  },
  "anova": {
    "help": "Model\nTests whether all independent group population means are equal.\n\nWhen to use\nUse for several independent numeric groups. A significant result indicates at least one different mean; post-hoc tests locate the differences.\n\nParameters\nChoose group columns or group/value columns. Welch uses Games–Howell with unequal variances; Classic assumes equal variances and uses Tukey–Kramer.",
    "helpKo": "모델 설명\n독립 그룹들의 모집단 평균이 모두 같은지 검정합니다.\n\n사용 시점\n여러 독립 숫자 그룹에 사용합니다. 유의하면 적어도 한 평균이 다르며 사후비교로 어느 그룹인지 확인합니다.\n\n파라미터 설명\n그룹별 열 또는 그룹·값 열을 선택합니다. Welch는 이분산·Games–Howell, Classic은 등분산·Tukey–Kramer를 사용합니다."
  },
  "wilcoxon": {
    "help": "Model\nTests whether a sample or paired-difference distribution is symmetric about the null target.\n\nWhen to use\nUse for signed-rank comparisons of one sample or matched measurements. Location interpretation requires symmetric differences.\n\nParameters\nChoose one sample or complete paired columns and alternative. Grouped pairs use subject ID or row order.",
    "helpKo": "모델 설명\n표본 또는 대응 차이의 분포가 귀무가설 기준값을 중심으로 대칭인지 검정합니다.\n\n사용 시점\n일표본·짝지은 측정값의 부호순위 비교에 사용하며 위치 차이 해석에는 차이 분포의 대칭성이 필요합니다.\n\n파라미터 설명\n일표본 또는 완전한 대응 열과 대립가설을 선택합니다. 그룹 자료는 대상 ID·행 순서로 대응시킵니다."
  },
  "mannwhitney": {
    "help": "Model\nCompares two independent distributions using ranks under the null of equal distributions.\n\nWhen to use\nUse for independent ordinal or numeric groups. A location interpretation requires similar distribution shapes.\n\nParameters\nChoose groups A/B or two columns and alternative; observations must be independent between groups.",
    "helpKo": "모델 설명\n분포가 같다는 귀무가설에서 순위를 이용해 독립 두 분포를 비교합니다.\n\n사용 시점\n독립된 순서형·숫자 그룹에 사용하며 위치 차이로 해석하려면 분포 형태가 비슷해야 합니다.\n\n파라미터 설명\n그룹 A·B 또는 열 두 개와 대립가설을 선택합니다. 그룹 간 관측값은 독립이어야 합니다."
  },
  "kruskal": {
    "help": "Model\nTests whether independent groups have the same distribution using pooled ranks.\n\nWhen to use\nUse for several independent ordinal or numeric groups. A location interpretation requires comparable distribution shapes.\n\nParameters\nChoose group columns or group/value columns. Use rank post-hoc comparisons to locate differences after a significant result.",
    "helpKo": "모델 설명\n통합 순위를 이용해 독립 그룹들의 분포가 같은지 검정합니다.\n\n사용 시점\n여러 독립 순서형·숫자 그룹에 사용하며 위치 차이 해석에는 비슷한 분포 형태가 필요합니다.\n\n파라미터 설명\n그룹별 열 또는 그룹·값 열을 선택합니다. 유의한 뒤 차이가 있는 쌍은 순위 사후비교로 확인합니다."
  },
  "chi2independence": {
    "help": "Model\nTests whether two categorical variables are statistically independent.\n\nWhen to use\nUse for independent categorical observations with adequate expected counts; consider Fisher exact for sparse 2×2 tables.\n\nParameters\nChoose two category columns with complete rows and at least two categories per column. Yates correction applies only to 2×2 tables.",
    "helpKo": "모델 설명\n두 범주형 변수가 통계적으로 독립인지 검정합니다.\n\n사용 시점\n기대빈도가 충분한 독립 범주 관측값에 사용하며 작은 빈도의 2×2 표는 Fisher 정확 검정을 고려합니다.\n\n파라미터 설명\n완전한 행이 있는 두 범주 열을 선택하며 각 열에 범주 2개 이상이 필요합니다. Yates 보정은 2×2 표에만 적용합니다."
  },
  "fisherexact": {
    "help": "Model\nTests association in a 2×2 table conditional on its margins, under a null odds ratio of one.\n\nWhen to use\nUse for independent binary categories, especially when counts are too small for a chi-square approximation.\n\nParameters\nChoose two binary category columns and alternative. Uses complete rows; paired binary outcomes require McNemar.",
    "helpKo": "모델 설명\n주변합을 고정한 2×2 표에서 오즈비가 1이라는 귀무가설로 연관성을 검정합니다.\n\n사용 시점\n독립 이항 범주, 특히 빈도가 작아 χ² 근사가 부적절할 때 사용합니다.\n\n파라미터 설명\n두 이항 범주 열과 대립가설을 선택합니다. 완전한 행을 사용하며 대응 이항 결과는 McNemar를 사용합니다."
  },
  "regression-linear": {
    "help": "Model\nFits a straight-line relationship and estimates the slope and intercept.\n\nWhen to use\nUse to predict a continuous response from one numeric predictor and assess its linear relationship.\n\nParameters\nUse x/y observations. Optional ridge, lasso or elastic net controls coefficient shrinkage; α is penalty strength and L1 ratio mixes lasso/ridge.",
    "helpKo": "모델 설명\n직선 관계를 적합하고 기울기·절편을 추정합니다.\n\n사용 시점\n숫자 설명변수 하나로 연속형 반응을 예측하고 선형 관계를 평가할 때 사용합니다.\n\n파라미터 설명\nx·y 관측값을 사용합니다. 선택적 ridge·lasso·elastic net은 계수를 축소하며 α는 벌점 강도, L1 비율은 lasso·ridge 혼합 비율입니다."
  },
  "regression-multiple": {
    "help": "Model\nEstimates the linear relationship of several predictors with a continuous response.\n\nWhen to use\nUse to assess a predictor while accounting for other measured predictors, or to predict numeric outcomes.\n\nParameters\nChoose the response column; other columns are predictors. Optional ridge/lasso/elastic net uses α for strength and L1 ratio for mixing.",
    "helpKo": "모델 설명\n여러 설명변수와 연속형 반응의 선형 관계를 추정합니다.\n\n사용 시점\n다른 측정 변수를 보정한 관계를 평가하거나 숫자 결과를 예측할 때 사용합니다.\n\n파라미터 설명\n반응 열을 선택하며 나머지 열은 설명변수입니다. 선택적 ridge·lasso·elastic net의 α는 벌점 강도, L1 비율은 혼합 비율입니다."
  },
  "regression-quadratic": {
    "help": "Model\nFits a second-degree polynomial response curve.\n\nWhen to use\nUse when a continuous response has a curved relationship with one predictor.\n\nParameters\nUse x/y observations; the model includes x and x² terms.",
    "helpKo": "모델 설명\n2차 다항식 반응 곡선을 적합합니다.\n\n사용 시점\n설명변수 하나와 연속형 반응의 관계가 곡선일 때 사용합니다.\n\n파라미터 설명\nx·y 관측값을 사용하며 x·x² 항을 포함합니다."
  },
  "regression-polynomial": {
    "help": "Model\nFits a polynomial relationship of the selected degree.\n\nWhen to use\nUse for a smooth curved relationship; higher degrees need more data and can overfit.\n\nParameters\nChoose response column and polynomial degree. Check the fitted curve and residuals.",
    "helpKo": "모델 설명\n선택한 차수의 다항식 관계를 적합합니다.\n\n사용 시점\n매끄러운 곡선 관계에 사용하며 높은 차수는 더 많은 자료가 필요하고 과적합될 수 있습니다.\n\n파라미터 설명\n반응 열·다항식 차수를 선택하고 적합 곡선·잔차를 확인합니다."
  },
  "regression-logarithmic": {
    "help": "Model\nFits a response linear in log(x).\n\nWhen to use\nUse when response changes with a diminishing slope over positive x values.\n\nParameters\nUse x/y observations with x>0.",
    "helpKo": "모델 설명\nlog(x)에 선형인 반응 관계를 적합합니다.\n\n사용 시점\n양수 x에서 x가 커질수록 반응의 변화 폭이 줄어드는 관계에 사용합니다.\n\n파라미터 설명\nx>0인 x·y 관측값을 사용합니다."
  },
  "regression-exponential": {
    "help": "Model\nFits an exponential growth or decay curve.\n\nWhen to use\nUse for positive responses whose change is approximately proportional to their current size.\n\nParameters\nUse x/y observations with y>0; the fit uses a log-transformed response.",
    "helpKo": "모델 설명\n지수 증가·감소 곡선을 적합합니다.\n\n사용 시점\n현재 크기에 비례해 변하는 양수 반응의 증가·감소를 분석할 때 사용합니다.\n\n파라미터 설명\ny>0인 x·y 관측값을 사용하며 로그 변환한 반응으로 적합합니다."
  },
  "regression-power": {
    "help": "Model\nFits a power-law relationship y=a·x^b.\n\nWhen to use\nUse for positive variables related through multiplicative scaling.\n\nParameters\nUse x/y observations with x>0 and y>0; fitting uses log-transformed values.",
    "helpKo": "모델 설명\n거듭제곱 관계 y=a·x^b를 적합합니다.\n\n사용 시점\n양수 변수 사이의 곱셈적 크기 관계를 분석할 때 사용합니다.\n\n파라미터 설명\nx>0·y>0인 관측값을 사용하며 로그 변환값으로 적합합니다."
  },
  "regression-logistic": {
    "help": "Model\nModels binary-event probability and predictor effects on log odds.\n\nWhen to use\nUse for a 0/1 response such as event/no event; coefficient inference concerns log odds.\n\nParameters\nChoose a binary response column; others are predictors. Firth handles separation. Optional regularization uses α and, for elastic net, L1 ratio.",
    "helpKo": "모델 설명\n이항 사건의 발생 확률과 로그 오즈에 대한 설명변수 효과를 추정합니다.\n\n사용 시점\n발생·미발생 같은 0/1 반응에 사용하며 계수 추론은 로그 오즈 기준입니다.\n\n파라미터 설명\n이항 반응 열을 선택하며 나머지는 설명변수입니다. Firth는 분리에 대응합니다. 선택적 벌점은 α, elastic net은 L1 비율도 사용합니다."
  },
  "regression-randomforest": {
    "help": "Model\nCombines many decision trees to predict a category or numeric response.\n\nWhen to use\nUse for nonlinear prediction with interactions; assess prediction with validation metrics.\n\nParameters\nChoose response, classification/regression task, tree count, maximum depth and seed.",
    "helpKo": "모델 설명\n여러 결정트리를 결합해 범주·숫자 반응을 예측합니다.\n\n사용 시점\n상호작용이 있는 비선형 예측에 사용하며 검증 지표로 예측 성능을 평가합니다.\n\n파라미터 설명\n반응 열·분류/회귀 방식·트리 수·최대 깊이·시드를 선택합니다."
  },
  "regression-svm": {
    "help": "Model\nUses a support-vector boundary or function for classification or regression.\n\nWhen to use\nUse for nonlinear prediction through a selected kernel.\n\nParameters\nChoose response, task and kernel. Predictors are standardized; use C > 0, gamma > 0 or auto, and regression epsilon >= 0 in response units. Binary classification uses 0/1. Training metrics use training data; cross-validation metrics are reported separately.",
    "helpKo": "모델 설명\n서포트 벡터의 경계·함수로 분류·회귀를 수행합니다.\n\n사용 시점\n커널을 이용한 비선형 예측에 사용합니다.\n\n파라미터 설명\n반응 열·SVM 유형·커널을 선택합니다. 설명변수는 표준화되며 C > 0, 감마 > 0 또는 auto, 회귀 엡실론 >= 0(종속변수 단위)를 사용합니다. 분류는 0/1 자료를 사용합니다. 학습 지표는 학습 데이터 기준이며 교차검증 지표는 별도로 표시합니다."
  },
  "regression-bayeslinear": {
    "help": "Model\nEstimates linear coefficients and predictive uncertainty using a prior and a normal response model.\n\nWhen to use\nUse to combine prior information with data for continuous-response prediction.\n\nParameters\nChoose response, prior SD, credible level and variance-prior shape/scale. For NUTS set draws, warmup and chains; review R-hat, ESS and divergences.",
    "helpKo": "모델 설명\n사전분포·정규 반응 모형으로 선형 계수와 예측 불확실성을 추정합니다.\n\n사용 시점\n사전 정보와 자료를 결합해 연속형 반응을 예측할 때 사용합니다.\n\n파라미터 설명\n반응 열·사전 SD·구간 수준·분산 사전 shape/scale을 지정합니다. NUTS는 추출 수·워밍업·체인 수를 설정하고 R-hat·ESS·발산 수를 확인합니다."
  },
  "regression-bayeslogistic": {
    "help": "Model\nEstimates binary-event probabilities and coefficient posterior uncertainty.\n\nWhen to use\nUse to combine prior information with binary observations for probability prediction.\n\nParameters\nChoose 0/1 response, prior SD, credible level and inference method. For NUTS set draws, warmup and chains; review R-hat, ESS and divergences.",
    "helpKo": "모델 설명\n이항 사건 확률과 계수의 사후 불확실성을 추정합니다.\n\n사용 시점\n사전 정보와 이항 관측값을 결합해 사건 확률을 예측할 때 사용합니다.\n\n파라미터 설명\n0/1 반응 열·사전 SD·구간 수준·추론 방식을 지정합니다. NUTS는 추출 수·워밍업·체인 수를 설정하고 R-hat·ESS·발산 수를 확인합니다."
  },
  "regression-custom": {
    "help": "Model\nFits the parameters of a user-specified response function.\n\nWhen to use\nUse when a scientific or practical model specifies the curve to fit.\n\nParameters\nSet formula and independent variable. Initial values/bounds use [[parameter,initial,lower,upper],…]; upper bounds are optional.",
    "helpKo": "모델 설명\n사용자가 지정한 반응 함수의 파라미터를 적합합니다.\n\n사용 시점\n과학적·실무적 모형으로 적합할 곡선의 식이 정해져 있을 때 사용합니다.\n\n파라미터 설명\n수식·독립변수를 지정합니다. 시작값·경계는 [[파라미터,시작값,하한,상한],…]이며 상한은 생략할 수 있습니다."
  }
};
