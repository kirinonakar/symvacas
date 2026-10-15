"""Research-method extensions: canonical presets, forms and bilingual assumptions."""
import random
from statistics_research_schema import forms as research_forms

_rng=random.Random(71)
OMEGA=[]
for _ in range(48):
    _factor=_rng.gauss(0,1)
    OMEGA.append([round(3+loading*_factor+_rng.gauss(0,.7),5) for loading in (.7,.8,.9,.6)])
META=[[.1,.12,2012,1],[.25,.15,2014,1],[.18,.11,2016,1],[.5,.18,2018,2],[.4,.13,2020,2],[.7,.2,2022,2],[.55,.16,2024,2],[.31,.14,2019,1]]
GROUPS=[[1,2,2,3,4,5,6,7,8,25],[2,3,4,4,5,6,7,8,9,12],[4,5,6,6,7,8,9,10,11,15]]
SURVIVAL=[[1,1,0],[2,1,1],[3,0,0],[4,1,1],[5,1,0],[6,0,1],[7,1,0],[8,1,1],[10,0,0],[12,1,1],[14,1,0],[17,0,1]]

def compact(value):return str(value).replace(' ','')

SPECS=[
    ('omega','McDonald’s ω (single factor)','McDonald의 ω (단일요인)','table',',raw',compact(OMEGA),
     'Select at least three complete varying item columns. Single-factor congeneric normal ML, uncorrelated errors; raw sum or standardized sum. Reports omega, alpha, loadings, errors and model fit. Reverse-code deliberately before analysis. No automatic reversal, hierarchical omega or confidence interval; three items are just identified.',
     '변동이 있는 문항 열을 3개 이상 선택하고 완전한 행을 입력합니다. 단일요인 congeneric 정규 ML·오차 무상관 가정. 원점수 합·표준화 점수 합의 ω·α·적재량·오차·모형 적합도를 제공합니다. 역문항은 분석 전 직접 역코딩하세요. 자동 역코딩·계층적 ω·신뢰구간은 제공하지 않으며 3문항은 적합도를 검증할 자유도가 없습니다.'),
    ('bayesttest','Bayesian t test (JZS)','베이지안 t 검정 (JZS)','groups',',independent,0,0.7071067811865476,0.95,10000,0,1','[10,11,9,10,12],[13,14,12,15,13]',
     'Two-sided one-sample, paired or equal-variance independent t test. Cauchy(0,r) prior on standardized effect; BF10/BF01, H1 posterior effect/credible interval, MCSE and ordered-prefix evidence graph. A−B direction; one-sample uses A−null. One-sample expressions still supply [] as the second argument. Enter priors before examining outcomes; no unequal-variance or directional BF.',
     '양측 일표본·대응·등분산 독립표본 t 검정. 표준화 효과의 Cauchy(0,r) 사전분포; BF10/BF01·H1 조건부 사후 효과/신용구간·MCSE·입력 순서 누적 BF 그래프. 방향은 A−B, 일표본은 A−귀무평균입니다. 일표본 수식도 둘째 인수 []를 지정합니다. 사전분포는 결과를 보기 전에 선택하세요. 이분산·방향성 BF는 지원하지 않습니다.'),
    ('bayesanova','Bayesian one-way ANOVA','베이지안 일요인 ANOVA','table',',0.5,0.95,10000,0,1',compact(GROUPS),
     'Independent groups with common normal residual variance. Compare all means against one mean using g~InvGamma(1/2,r²/2), beta|sigma,g~N(0,n*g*sigma²*(XcᵀXc)^−1). BF10/BF01, conditional posterior design-weighted eta² and ordered-prefix BF graph. This design-dependent mixture-g prior is explicitly not JASP default factorial ANOVA; no repeated measures or interactions.',
     '공통 정규 잔차분산을 가정하는 독립 그룹. g~InvGamma(1/2,r²/2), beta|sigma,g~N(0,n*g*sigma²*(XcᵀXc)^−1)로 전체 그룹 평균과 공통 평균을 비교합니다. BF10/BF01·H1 조건부 설계 가중 사후 η²·순서별 누적 BF 그래프. 설계 의존 혼합 g 사전분포이며 JASP 기본 요인 ANOVA와 같지 않습니다. 반복측정·상호작용은 지원하지 않습니다.'),
    ('metaregression','Meta-regression','메타회귀','table',',pm,0.95,hksj',compact([r[:3] for r in META]),
     'Rows: effect, positive SE, one or more numeric study moderators. Fixed, generalized DL or PM residual heterogeneity; z or modified HKSJ t/F inference, joint moderator test and residual Q. Ratio effects and SE must be on the log scale. Prespecify moderators; study-level association is not an individual causal effect. Independent studies only; no automatic publication-bias correction.',
     '행: 효과·양수 SE·하나 이상의 숫자 연구 조절변수. 고정효과·일반화 DL·PM 잔여 이질성, z·수정 HKSJ t/F 추론·조절변수 공동 검정·잔여 Q. 비율 효과와 SE는 로그 척도입니다. 조절변수는 미리 지정하고 연구 수준 연관을 개인 수준 인과효과로 해석하지 마세요. 독립 연구 전용이며 자동 출판편향 보정은 없습니다.'),
    ('metasubgroup','Meta-analysis subgroups','메타분석 하위집단','table',',pm,0.95,hksj',compact([[r[0],r[1],r[3]] for r in META]),
     'Rows: effect, SE, group ID; UI accepts named groups. At least two studies per group. Common residual tau² across groups, pooled effects, forest plot and joint between-group test. Different within-group significance does not establish a group difference. Fixed/DL/PM and z/modified HKSJ; independent effects only.',
     '행: 효과·SE·그룹 ID. 폼에서는 이름 그룹도 허용합니다. 그룹마다 연구 2개 이상. 그룹 간 공통 잔여 τ²로 통합 효과·Forest plot·집단 차이 공동 검정을 제공합니다. 그룹별 유의 여부의 차이가 그룹 간 차이를 증명하지 않습니다. fixed/DL/PM·z/수정 HKSJ, 독립 효과 전용.'),
    ('designpower','Power: z / proportion / variance','검정력: z·비율·분산비','none','','z,0.5,64,0.05,two,0.5',
     'designpower(design,effect,n,alpha,tail,baseline). z uses known-SD standardized mean shift; proportion uses alternative p1 and null baseline p0; proportion2 uses pA,pB and equal n per arm; variance uses alternative variance ratio and equal n per normal arm. Proportions use normal approximations without continuity correction; variance uses exact F. Fixed-design only.',
     'designpower(설계,효과,n,alpha,방향,기준비율). z는 알려진 SD로 나눈 평균 이동, proportion은 대립 p1·귀무 기준 p0, proportion2는 pA·pB·그룹별 같은 n, variance는 대립 분산비·정규 그룹별 같은 n입니다. 비율은 연속성 보정 없는 정규근사, 분산비는 정확 F. 고정 표본 설계 전용.'),
    ('designsize','Sample size: z / proportion / variance','표본수: z·비율·분산비','none','','z,0.5,0.8,0.05,two,0.5',
     'Same design definitions as designpower; third argument is target power above alpha. Returns the smallest integer n (or n per arm), total n, attained power and power at n−1. Alternative must be in the chosen one-sided direction. Limit one million per arm. No group-sequential alpha spending.',
     'designpower와 같은 설계이며 셋째 인수는 alpha보다 큰 목표 검정력입니다. 최소 정수 n(또는 그룹별 n)·총 n·달성 검정력·n−1 검정력을 제공합니다. 단측 검정은 대립 방향이 일치해야 합니다. 그룹별 백만 명 한도이며 군순차 alpha spending은 지원하지 않습니다.'),
    ('yuen','Yuen trimmed-mean test','Yuen 절사평균 검정','groups',',0.2,0.95','[1,2,2,3,4,5,6,7,8,25],[2,3,4,4,5,6,7,8,9,12]',
     'Independent A/B samples, proportion trimmed per tail (default .20), confidence level. Yuen approximate t with Winsorized variance and Satterthwaite df; estimates trimmed mean A−B, not the ordinary mean. At least two retained observations and positive Winsorized variance in each group. No paired test.',
     '독립 A/B 표본·꼬리별 절사 비율(기본 .20)·신뢰수준. Winsorized 분산·Satterthwaite 자유도의 Yuen 근사 t 검정. 일반 평균이 아닌 절사평균 A−B를 추정합니다. 그룹마다 절사 후 2개 이상·양의 Winsorized 분산이 필요합니다. 대응 검정은 지원하지 않습니다.'),
    ('trimmedanova','Trimmed-mean ANOVA','절사평균 ANOVA','table',',0.2,0.95',compact(GROUPS),
     'Independent groups; Welch-type ANOVA of trimmed means with Winsorized sampling variances. Per-tail trimming in [0,.5), default .20; approximate F and df. Group intervals are individual, not simultaneous. No new Welch ordinary-mean analysis is needed; this targets trimmed means.',
     '독립 그룹, Winsorized 표본분산을 이용한 절사평균의 Welch형 ANOVA. 꼬리별 절사 비율 [0,.5), 기본 .20; 근사 F·자유도. 그룹별 구간은 동시 구간이 아닙니다. 기존 Welch 일반 평균 검정과 달리 절사평균을 대상으로 합니다.'),
    ('winsorcor','Winsorized correlation','Winsorized 상관','groups',',0.2','[1,2,3,4,5,6,7,8,9,30],[2,1,4,3,6,5,8,7,9,12]',
     'Complete paired columns; independently Winsorize both margins while retaining pairs. Correlation and approximate t p value with n−2 floor(n trim)−2 df (WRS2 convention). No confidence interval; normal Pearson intervals are not substituted.',
     '완전한 대응 열. 쌍을 유지하며 두 주변분포를 각각 Winsorize합니다. 상관·n−2 floor(n trim)−2 자유도의 근사 t p값(WRS2 관례). 신뢰구간을 제공하지 않으며 일반 Pearson 구간으로 대체하지 않습니다.'),
    ('robustreg','Huber robust regression (M)','Huber 강건 회귀 (M)','table',',1.345','[[0,1],[1,2.5],[2,5],[3,6.5],[4,9],[5,10.5],[6,13],[7,14.5],[8,17],[9,35],[10,21],[11,22.5]]',
     'Numeric predictors and response, intercept included. Huber M IRLS, iterated residual MAD scale, default tuning 1.345. Score-sandwich HC1 Wald intervals treat scale as fixed. Resistant to response outliers, not high leverage; this is not high-breakdown MM. Zero residual MAD or unidentified fits are rejected.',
     '숫자 설명변수·반응, 절편 포함. Huber M IRLS·반복 잔차 MAD 척도, 기본 조율값 1.345. 척도를 고정한 score-sandwich HC1 Wald 구간. 반응 이상치 영향을 줄이지만 고레버리지에는 취약하며 고붕괴점 MM이 아닙니다. 잔차 MAD=0·식별 불가 모형은 거부합니다.'),
    ('parametricsurvival','Parametric survival (AFT)','모수적 생존분석 (AFT)','table',',weibull,0.95,-1,6',compact(SURVIVAL),
     'Rows: positive time, event 0/1, optional numeric predictors. Weibull, exponential or lognormal AFT by censored maximum likelihood. Optional delayed entry column (zero-based index, −1 none) with 0≤entry<time. Time ratios, AIC/BIC, unconditional predicted median/mean/10%/90% event times and survival at a chosen time. Joint-information median CIs include shape/scale uncertainty; 10%/90% event quantiles are not CIs. No interval censoring or competing risks.',
     '행: 양수 시간·사건 0/1·선택적 숫자 설명변수. 검열 최대우도의 Weibull·지수·로그정규 AFT. 선택적 지연 진입시간 열(0부터 번호, −1 없음), 0≤진입<시간. 시간비·AIC/BIC·무조건부 예측 중앙/평균/10%/90% 사건시간·지정 시점 생존확률. 중앙시간의 공동 정보행렬 구간은 shape/scale 불확실성을 포함하며 10%/90% 사건 분위수는 신뢰구간이 아닙니다. 구간검열·경쟁위험은 지원하지 않습니다.'),
]


def forms(field,col,multi,group_fields,two_fields,matching_fields):
    level=[field('level','Confidence level','신뢰수준','number','0.95')]
    credible=[field('r','Prior scale r','사전 척도 r','number','0.7071067811865476'),field('level','Credible level','신용구간 수준','number','0.95'),field('samples','Posterior IID draws','사후 IID 추출 수','number','10000'),field('seed','Seed','시드','number','0'),field('sequential','Sequential evidence graph','누적 BF 그래프','choice','1',[('1','On','켬'),('0','Off','끔')])]
    trim=[field('trim','Trim proportion per tail','꼬리별 절사 비율','number','0.2')]
    meta=[field('method','Residual heterogeneity','잔여 이질성','choice','pm',[('fixed','Fixed effect','고정효과'),('pm','Paule–Mandel','Paule–Mandel'),('dl','DerSimonian–Laird','DerSimonian–Laird')])]+level+[field('inference','Inference','추론','choice','hksj',[('hksj','Modified HKSJ t / F','수정 HKSJ t / F'),('z','Normal / χ²','정규 / χ²')],when={'method':['pm','dl']})]
    raw_meta=research_forms(field,col,multi,two_fields,matching_fields)['metaanalysis']
    effects=raw_meta[:next(i for i,f in enumerate(raw_meta) if f['key']=='studyLabels')]
    result={
        'omega':[multi('columns','Item columns','문항 열'),field('mode','Score sum','점수 합','choice','raw',[('raw','Raw items','원점수'),('standardized','Standardized items','표준화 점수')])],
        'bayesttest':[field('design','Design','설계','choice','independent',[('independent','Independent (equal variance)','독립 (등분산)'),('paired','Paired','대응'),('onesample','One sample','일표본')]),dict(col('column','Sample column','표본 열',0),when={'design':['onesample']})]+[dict(f,when={**f.get('when',{}),'design':['independent','paired']}) for f in two_fields]+[dict(f,when={**f.get('when',{}),'design':['paired']}) for f in matching_fields]+[field('null','Null mean / difference','귀무 평균·차이','number','0')]+credible,
        'bayesanova':group_fields+[dict(f,default='0.5') if f['key']=='r' else f for f in credible],
        'metaregression':effects+[multi('predictors','Numeric moderator columns','숫자 조절변수 열')]+meta,
        'metasubgroup':effects+[col('group','Subgroup column','하위집단 열',-1)]+meta,
        'yuen':two_fields+trim+level,
        'trimmedanova':group_fields+trim+level,
        'winsorcor':[col('first','Column A','A 열',0),col('second','Column B','B 열',1)]+trim,
        'robustreg':[col('response','Response','반응 열',-1),multi('predictors','Predictors','설명변수 열'),field('tuning','Huber tuning constant','Huber 조율 상수','number','1.345')],
        'parametricsurvival':[col('time','Time','시간 열',0),col('event','Event','사건 열',1),field('eventValue','Event value','사건 발생 값','text','1'),field('covariates','Predictors','설명변수','choice','selected',[('none','Intercept only','절편만'),('selected','Selected predictors','설명변수 선택')]),dict(multi('predictors','Predictor columns','설명변수 열'),default='2',when={'covariates':['selected']}),field('family','Distribution','분포','choice','weibull',[('weibull','Weibull','Weibull'),('exponential','Exponential','지수'),('lognormal','Lognormal','로그정규')])]+level+[field('truncation','Delayed entry','지연 진입','choice','none',[('none','None','없음'),('entry','Entry column','진입시간 열')]),dict(col('entry','Entry time','진입시간 열',2),when={'truncation':['entry']}),field('horizon','Prediction time','예측 시점','number','6')],
    }
    for id_ in ('designpower','designsize'):
        result[id_]=[field('design','Fixed design','고정 표본 설계','choice','z',[('z','Known-SD mean z','알려진 SD 평균 z'),('proportion','One proportion z','단일 비율 z'),('proportion2','Two proportions z (equal n)','두 비율 z (같은 n)'),('variance','Variance-ratio F (equal n)','분산비 F (같은 n)')]),field('effect','Standardized shift / p1 / variance ratio','표준화 이동 / p1 / 분산비','number','0.5'),dict(field('baseline','Null p0 / second proportion pB','귀무 p0 / 둘째 비율 pB','number','0.5'),when={'design':['proportion','proportion2']}),field('size','n / n per arm' if id_=='designpower' else 'Target power','n / 그룹별 n' if id_=='designpower' else '목표 검정력','number','64' if id_=='designpower' else '0.8'),field('alpha','Significance level α','유의수준 α','number','0.05'),field('tail','Alternative','대립가설','choice','two',[('two','Two-sided','양측'),('greater','Greater','크다'),('less','Less','작다')])]
    return result


RAW_META_HELP=(
    ' Forms also accept independent-arm binary events/totals (log OR/RR, selected zero-cell correction) or continuous mean/sample SD/n (MD/Hedges g), followed by moderators/group. Expressions add measure as argument 5 and binary correction as argument 6. Double-zero exclusions retain moderator alignment and original study IDs. Switching layout requires selecting the matching summary and moderator columns; missing selected cells are rejected.',
    ' 폼에서 독립 두 군의 이진 사건 수·전체 수(log OR/RR·선택한 0 셀 보정) 또는 연속형 평균·표본 SD·n(MD/Hedges g)과 조절변수·하위집단을 바로 선택할 수 있습니다. 수식은 다섯째 인수 효과 유형·여섯째 이진 보정값을 지정합니다. 양쪽 사건 0 연구 제외 후에도 조절변수·원래 연구 번호를 유지합니다. 입력 유형을 바꾸면 요약 통계와 조절변수 열을 각각 선택하세요. 선택 열의 결측은 거부합니다.')
SPECS=[(*spec[:6],spec[6]+RAW_META_HELP[0],spec[7]+RAW_META_HELP[1]) if spec[0] in ('metaregression','metasubgroup') else spec for spec in SPECS]
