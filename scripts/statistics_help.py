"""Bilingual test-selection guidance shared by the catalog-help generator."""
import re

GUIDES = [
'''What do you want to compare?
├─ Numeric values
│  ├─ One sample vs a target mean → One-sample t test
│  ├─ Two independent groups → Welch t test
│  ├─ Before/after on the same subjects → Paired t test
│  ├─ 3+ independent groups → Welch ANOVA → Games–Howell
│  │  └─ Equal-variance ANOVA selected → Tukey–Kramer
│  ├─ Same subjects in several conditions → Repeated-measures ANOVA / Friedman
│  ├─ Two independent factors → Two-way ANOVA
│  ├─ 3+ factors / numeric covariates → Factorial linear model
│  └─ Groups with covariates to adjust → ANCOVA
├─ Categories / counts
│  ├─ Independent categories → χ² independence
│  │  └─ Sparse 2×2 table → Fisher exact
│  ├─ One proportion vs a target / two independent proportions → Proportion z test
│  ├─ Paired binary outcomes → McNemar
│  └─ Counts vs expected frequencies → χ² goodness of fit
├─ Time until an event, with censoring → Survival analysis
└─ Predict a response from variables → Regression & models

Review shape, outliers and study design:
  Mean analysis → Shapiro–Wilk + Q–Q plot
  Equal-variance assumption → Brown–Forsythe / Levene
  Independent rank comparisons → Mann–Whitney (2), Kruskal–Wallis (3+)
  Symmetric paired differences → Wilcoxon signed-rank
''',
'''무엇을 비교하나요?
├─ 숫자 자료
│  ├─ 한 표본 평균 vs 기준값 → 단일 표본 t 검정
│  ├─ 독립된 두 그룹 → Welch t 검정
│  ├─ 같은 대상의 전·후 → 대응 t 검정
│  ├─ 독립된 3개 이상 그룹 → Welch ANOVA → Games–Howell
│  │  └─ 등분산 ANOVA 선택 → Tukey–Kramer
│  ├─ 같은 대상의 여러 조건 → 반복측정 ANOVA / Friedman
│  ├─ 독립 관측의 두 요인 → 이요인 ANOVA
│  ├─ 3개 이상 요인·숫자 공변량 → 요인 선형회귀
│  └─ 공변량을 보정한 그룹 비교 → ANCOVA
├─ 범주·빈도 자료
│  ├─ 독립된 범주 간 관계 → χ² 독립성 검정
│  │  └─ 기대빈도가 작은 2×2 표 → Fisher 정확 검정
│  ├─ 한 비율 vs 기준 / 독립된 두 비율 → 비율 z 검정
│  ├─ 대응된 이항 결과 → McNemar
│  └─ 빈도 vs 기대빈도 → χ² 적합도 검정
├─ 중도절단이 있는 사건 발생 시간 → 생존분석
└─ 변수로 반응값을 예측 → 회귀·모형

분포·이상값·연구 설계도 확인하세요:
  평균 분석 → Shapiro–Wilk + Q–Q plot
  등분산 가정 → Brown–Forsythe / Levene
  독립 표본의 순위 비교 → Mann–Whitney (2개), Kruskal–Wallis (3개 이상)
  대칭적인 대응 차이값 → Wilcoxon 부호순위
''']

ASSUMPTION_GUIDES = [
'''### Normal-model methods (parametric)
- One-sample t / t intervals: normal population for exact small-sample inference. Paired t: normally distributed within-pair differences. Inspect Q–Q plots, skewness and outliers.
- Welch t / Welch ANOVA / Games–Howell: independent group means with unequal variances. Student t / classic ANOVA / Tukey: equal variances.
- ANCOVA / factorial linear models: normal independent errors, common residual variance and a full-rank design. ANCOVA uses linear covariate effects and common slopes. Review interactions before main effects; Type II respects marginality and Type III uses sum contrasts.
- Repeated-measures ANOVA: complete within-subject measurements; review sphericity and Greenhouse–Geisser corrected p values.
- Gaussian mixed models: normal conditional errors and random effects. Bayesian mean / two-sample models: normal likelihood with the selected priors.
- Bartlett: normally distributed groups. For uncertain normality, use median-centered Levene / Brown–Forsythe.

### Distribution assumptions by model
- Mean z tests / z intervals: enter known population SDs; the mean sampling distribution is normal or adequately approximated.
- Logistic / multinomial / ordinal: categorical outcomes. Poisson / negative binomial: count outcomes. Check the family, link, dispersion and model diagnostics.
- GEE: cluster mean/variance model and working correlation. Review cluster count, mean specification and robust standard errors.
- GLMM: selected response family and random effects. Bayesian proportion / rate: binomial / Poisson likelihoods.

### Rank, distribution and resampling methods (nonparametric)
- Mann–Whitney / Kruskal–Wallis: independent distributions. Comparable distribution shapes are needed for location interpretations.
- Wilcoxon signed-rank: paired or one-sample differences; symmetry is needed for a location interpretation.
- Friedman: three or more repeated conditions; complete matched rows, ranks within subjects and tie correction.
- Kolmogorov–Smirnov: continuous distributions. Specify one-sample reference parameters independently of the tested sample.
- Kaplan–Meier / log-rank: censored event times. Review independent subjects and censoring; Cox uses proportional hazards.
- IID bootstrap: independent, representative observations. Match paired, clustered or time-dependent sampling to the data structure.

### Categorical tests
- χ²: independent counts and adequate expected frequencies. Fisher exact: independent 2×2 counts. McNemar: paired binary outcomes.

### Choosing a method
Choose the outcome and question first: means, distributions, association, prediction or survival. Then select independent groups, paired observations or clusters. Assess assumptions using Q–Q plots, p values, sample sizes and study design. For skewed or dependent data, review transformations and a model that matches the distribution and sampling structure.
''',
'''### 정규 모형 방법 (parametric)
- 일표본 t·t 구간: 정확한 소표본 추론은 모집단의 정규성을 가정합니다. 대응 t는 대상별 차이값의 정규성을 점검합니다. Q–Q plot·왜도·이상값을 함께 확인하세요.
- Welch t·Welch ANOVA·Games–Howell: 이분산 독립 그룹의 평균 비교. Student t·일반 ANOVA·Tukey: 등분산 가정.
- ANCOVA·요인 선형회귀: 정규·독립 오차, 잔차 등분산, 식별 가능한 설계. ANCOVA는 선형 공변량 효과·공통 기울기를 사용합니다. 주 효과보다 상호작용을 먼저 확인하며 Type II는 주변성 원리, Type III는 합 대비를 사용합니다.
- 반복측정 ANOVA: 완전한 대상 내 측정. 구형성과 Greenhouse–Geisser 보정 p값을 확인하세요.
- Gaussian 혼합모형: 조건부 오차·랜덤효과의 정규성. 베이지안 평균·두 표본 모형: 정규 우도와 선택한 사전분포.
- Bartlett: 정규 그룹의 분산 비교. 정규성이 불확실하면 중앙값 기준 Levene·Brown–Forsythe를 사용하세요.

### 모형별 분포 가정
- 평균 z 검정·z 구간: 알려진 모집단 표준편차를 입력합니다. 평균의 표집분포는 정규이거나 적절히 근사되어야 합니다.
- 로지스틱·다항·순서형: 범주 반응. 포아송·음이항: 빈도 반응. 분포족·연결함수·과산포·모형 진단을 확인하세요.
- GEE: 군집 평균·분산 모형과 작업상관. 군집 수·평균 모형·강건 표준오차를 확인하세요.
- GLMM: 선택한 반응 분포족·랜덤효과. 베이지안 비율·발생률: 이항·포아송 우도.

### 순위·분포·재표집 방법 (nonparametric)
- Mann–Whitney·Kruskal–Wallis: 독립 분포 비교. 위치 차이 해석에는 비슷한 분포 형태가 필요합니다.
- Wilcoxon 부호순위: 대응·일표본 차이값. 위치 차이 해석에는 대칭성이 필요합니다.
- Friedman: 3개 이상 반복 조건. 완전 대응 행·대상 내 순위·동점 보정을 사용합니다.
- Kolmogorov–Smirnov: 연속분포 비교. 일표본 기준분포의 모수는 검정할 표본과 독립적으로 지정하세요.
- Kaplan–Meier·로그순위: 중도절단 사건 시간. 대상 독립성·중도절단을 점검하며 Cox는 비례위험을 가정합니다.
- IID 부트스트랩: 독립적이고 대표성 있는 관측. 대응·군집·시계열은 자료 구조에 맞는 표집을 사용하세요.

### 범주형 검정
- χ²: 독립 빈도·충분한 기대빈도. Fisher 정확: 독립 2×2 빈도. McNemar: 대응 이항 결과.

### 방법 선택
평균·분포·연관성·예측·생존 중 분석 목적과 반응 척도를 정한 뒤 독립 그룹·대응 관측·군집을 구분하세요. Q–Q plot·p값·표본 수·연구 설계로 가정을 점검합니다. 왜도·의존성이 큰 자료는 변환과 분포·표집 구조에 맞는 모형을 검토하세요.
''']

COMPARISON_TABLES = [
'''### Independent and paired samples at a glance

| Data structure | Parametric comparison | Nonparametric comparison |
| --- | --- | --- |
| Two independent groups | Student / Welch t-test | Mann–Whitney U |
| Two paired groups | Paired t-test | Wilcoxon signed-rank |
| 3+ independent groups | ANOVA / Welch ANOVA | Kruskal–Wallis |
| 3+ repeated conditions | Repeated-measures ANOVA | Friedman test |

Select by the data structure and target quantity. Rank-based location comparisons require appropriate distribution shapes or symmetry. Repeated conditions are measurements of the same subjects.
''',
'''### 독립표본·대응표본에 따른 검정 비교

| 데이터 구조 | 모수 검정 | 비모수 검정 |
| --- | --- | --- |
| 독립된 두 집단 | Student / Welch t-test | Mann–Whitney U |
| 대응된 두 집단 | Paired t-test | Wilcoxon signed-rank |
| 독립된 3집단 이상 | ANOVA / Welch ANOVA | Kruskal–Wallis |
| 반복측정 3조건 이상 | Repeated-measures ANOVA | Friedman test |

자료 구조와 비교할 통계량에 맞춰 선택하세요. 순위 기반 위치 비교는 분포 형태·대칭성 가정을 확인합니다. 반복 조건은 같은 대상의 측정입니다.
''']

POSTHOC_GUIDES = [
'''### Choosing a post-hoc test

```text
Compare differences between groups
├─ Parametric tests
│  ├─ All pairs of groups → Tukey
│  ├─ Each treatment vs a control → Dunnett
│  ├─ Complex mean contrasts → Scheffé
│  └─ Unequal variances → Games–Howell
├─ Nonparametric tests
│  └─ After Kruskal–Wallis → Dunn / Conover
│     ├─ Conservative approach → Dunn + Holm
│     └─ Emphasis on power → Conover + Holm
└─ Repeated-measures data
   └─ After Friedman → Separate paired post-hoc tests
```

Tukey, Dunnett and Scheffé assume equal variances across independent groups. Interpret Conover after a significant Kruskal–Wallis test. Scheffé protects all linear contrasts; this app reports pairwise mean differences. After Friedman, this app provides paired Wilcoxon comparisons with Holm adjustment.
''',
'''### 사후검정 선택 흐름

```text
집단 간 차이를 비교
├─ 모수 검정
│  ├─ 모든 집단 쌍 비교 → Tukey
│  ├─ 대조군과 비교 → Dunnett
│  ├─ 복잡한 평균 대비 → Scheffé
│  └─ 등분산 불충족 → Games–Howell
├─ 비모수 검정
│  └─ Kruskal–Wallis 이후 → Dunn / Conover
│     ├─ 보수적인 접근 → Dunn + Holm
│     └─ 검정력 중시 → Conover + Holm
└─ 반복측정 자료
   └─ Friedman 이후 → 별도 대응 사후검정
```

Tukey·Dunnett·Scheffé는 독립 집단의 등분산을 가정합니다. Conover는 유의한 Kruskal–Wallis 검정 이후 해석합니다. Scheffé는 모든 선형 대비를 보호하며 이 앱은 쌍별 평균 차이를 출력합니다. Friedman 이후에는 대응 Wilcoxon + Holm 사후비교를 제공합니다.
''']


def enrich_help(text, korean=False):
    index=int(bool(korean))
    # Keep the choosing guide before the first descriptive-statistics entry.
    # Remove its earlier generated placement before rebuilding it below.
    for old_heading in ('## Stats — choosing a test','## 통계 — 검정 선택'):
        old_start=text.find(old_heading)
        old_end=text.find('\n## ',old_start+3) if old_start>=0 else -1
        if old_end>=0 and text[old_end+1:].startswith('## Data & units'):
            text=text[:old_start]+text[old_end+1:]
    start=text.find('## Statistical tests')
    if start<0: start=text.find('## Stats — choosing a test')
    if start<0: start=text.find('## 통계 — 검정 선택')
    if start>=0:
        first=text.index('`ttest(',start)
        heading='통계 — 검정 선택' if korean else 'Stats — choosing a test'
        suite=('원자료 평균 분석은 표본 요약·Q–Q plot·분포를 제공합니다. t 검정은 효과크기·구간, ANOVA는 사후비교를 함께 표시합니다. 대응 t는 차이값, ANCOVA·요인 모형은 잔차의 정규성을 점검합니다.\n\n그룹·값 형식에서는 여러 값 열을 한 번에 분석할 수 있습니다. mean은 그룹 평균, diff는 첫 그룹−비교 그룹, n은 유효 표본 수(대응 분석은 쌍 수)입니다. Significant는 p<.05, normality의 yes는 두 그룹 모두 Shapiro p≥.05, equal var의 yes는 Brown–Forsythe p≥.05를 뜻합니다. 컬럼별 p값은 개별 검정 기준이며, 여러 가설을 함께 해석할 때는 padjust로 보정하세요. 범주형 표는 개수·그룹 내 비율·퍼센트포인트 차이와 관측/기대빈도를 제공합니다. 작은 기대빈도의 2×2 표에는 Fisher 정확 검정을 사용하세요.' if korean else 'Raw-data mean analyses include summaries, Q–Q plots and distributions. t tests add effect sizes and intervals; ANOVA adds post-hoc comparisons. Paired t tests check differences; ANCOVA and factorial models check residuals.\n\nGroup/value layouts can analyze several value columns at once. mean is the group mean, diff is the first group minus the comparison group, and n counts valid observations (pairs for paired data). Significant means p<.05; normality is yes when both groups have Shapiro p≥.05; equal var is yes when Brown–Forsythe p≥.05. Column p values are individual tests; use padjust for a family of hypotheses. Categorical tables report counts, within-group percentages, percentage-point differences and observed/expected counts. Use Fisher exact for sparse 2×2 tables.')
        text=text[:start]+'## '+heading+'\n\n```text\n'+GUIDES[index].rstrip()+'\n```\n\n'+COMPARISON_TABLES[index]+'\n'+POSTHOC_GUIDES[index]+'\n'+suite+'\n\n'+ASSUMPTION_GUIDES[index]+'\n'+text[first:]
    if '`welchanova(' not in text:
        pos=text.find('`tukey(')
        if pos>=0:
            basic=('`ttest2(delta, A, B, student)` — 독립 두 그룹의 합동분산 Student t. 기본 3인수는 Welch입니다.\n\n`welchanova(A, B, ...)` — 이분산 일요인 ANOVA + Games–Howell 자동 세트.\n\n`gameshowell(A, B, ...)` — 이분산 쌍별 사후비교·95% 동시 구간.\n\n' if korean else '`ttest2(delta, A, B, student)` — Pooled Student t; the three-argument default remains Welch.\n\n`welchanova(A, B, ...)` — Unequal-variance one-way ANOVA with automatic Games–Howell.\n\n`gameshowell(A, B, ...)` — Pairwise unequal-variance comparisons and simultaneous 95% intervals.\n\n')
            text=text[:pos]+basic+text[pos:]
    guide_start=text.find('## '+('통계 — 검정 선택' if korean else 'Stats — choosing a test'))
    data_start=text.find('## Data & units')
    if 0<=data_start<guide_start:
        entries=text.index('`ttest(',guide_start)
        guide=text[guide_start:entries]
        text=text[:guide_start]+'## Statistical tests\n\n'+text[entries:]
        text=text[:data_start]+guide+text[data_start:]
    def entry(match):
        signature,description=match.group(1),match.group(2)
        name=signature.split('(')[0]
        if name=='discriminant':
            description=('x에 대한 다항식의 판별식.' if korean else 'Discriminant of a polynomial in x.')
            return '`'+signature+'` — '+description
        return match.group(0)
    return re.sub(r'^`([^`]+)`\s*[—–-]\s*(.*)$',entry,text,flags=re.MULTILINE)
