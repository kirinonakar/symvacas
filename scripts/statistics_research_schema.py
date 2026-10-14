"""Research analysis presets and bilingual help shared by Android/Web."""
SAMPLE = '[9.8,10.1,10.2,9.9,10,10.1,9.9,10.2]'
PAIR = SAMPLE+',[10,10.2,10.1,9.8,10.1,10,9.9,10.1]'
TOST_HELP = (
    'Prespecify lower/upper equivalence bounds in original units for A−B (one-sample: mean−reference). Both one-sided p values must be below alpha. Reports max p, equivalence decision and 1−2 alpha CI (90% at .05). A nonsignificant difference does not establish equivalence. Positive sampling variance and independent approximately normal observations/differences are required.',
    'A−B(단일 표본: 평균−기준평균)에 대한 원래 단위의 동등성 하한·상한을 미리 지정하세요. 두 단측 p값이 모두 alpha보다 작아야 합니다. 최대 p·동등성 판단·1−2 alpha 구간(.05이면 90%)을 제공합니다. 차이가 유의하지 않다는 것만으로 동등하지 않습니다. 양의 표본분산·독립 근사 정규 관측 또는 대응 차이가 필요합니다.')
SPECS = [
    ('metaanalysis','Meta-analysis','메타분석','table',',pm,0.95,z,1','[[0.2,0.1],[0.45,0.15],[-0.1,0.12],[0.6,0.2],[0.3,0.11]]',
     'Independent study rows: effect estimate, positive standard error (SE, not SD or variance). fixed / dl (DerSimonian–Laird) / pm (Paule–Mandel, default); confidence level 0–1; inference z / hksj (modified Hartung–Knapp for random effects); Egger 0/1. Returns pooled effect, weights, Q/p, I², τ², prediction interval, Forest/Funnel plots. Ratio effects require log effects and log-scale SE. Study and funnel limits use z. Egger OLS standardized effect on precision uses t(k−2); needs 3 studies with differing SE, has low power below 10, and asymmetry is not proof of publication bias. Random-effects prediction uses t(k−2) and omits tau estimation uncertainty.',
     '독립 연구별 행: 효과 추정값·양수 표준오차(SE, 표준편차·분산 아님). fixed·dl(DerSimonian–Laird)·pm(Paule–Mandel, 기본); 신뢰수준 0~1; 추론 z·hksj(랜덤효과의 수정 Hartung–Knapp); Egger 0/1. 통합 효과·가중치·Q/p·I²·τ²·예측구간·Forest/Funnel plot. 비율은 로그 효과·로그 척도 SE를 입력합니다. 연구·Funnel 경계는 z 근사. Egger는 표준화 효과 대 정밀도 OLS 절편의 t(k−2) 검정으로 연구 3개 이상·서로 다른 SE가 필요합니다. 10개 미만은 검정력이 낮고 비대칭이 출판편향을 증명하지 않습니다. 랜덤효과 예측은 t(k−2) 근사이며 tau 추정 불확실성을 제외합니다.'),
    ('icc','Intraclass correlation (ICC)','급내상관계수 (ICC)','table',',random,single,0.95','[[9,10,9],[6,7,6],[8,8,9],[5,6,5],[10,9,10],[7,7,8]]',
     'Complete subject × rater numeric matrix. oneway=ICC(1), random=two-way absolute agreement ICC(2), mixed=two-way consistency ICC(3). single / average (mean of all k raters); confidence level. F-based CIs; absolute agreement uses approximate Satterthwaite df. Negative estimates are retained. Independent subjects, normal ANOVA errors. Mixed consistency ignores systematic rater shifts; choose the model before analysis. Degenerate intervals are unavailable.',
     '완전한 숫자 대상×평가자 행렬. oneway=ICC(1), random=이원 랜덤 절대 일치 ICC(2), mixed=이원 혼합 일관성 ICC(3). single 단일·average k명 평균; 신뢰수준. F 기반 구간, 절대 일치는 Satterthwaite 근사 자유도. 음의 추정값 유지. 독립 대상·정규 ANOVA 오차 가정. 혼합 일관성은 평가자 간 체계적 차이를 무시하므로 분석 전 모형을 선택하세요. 퇴화 구간은 계산 불가로 표시합니다.'),
    ('blandaltman','Bland–Altman agreement','Bland–Altman 일치도','table',',0.95,difference','[[10,10.5],[12,11.8],[8,8.6],[15,14.7],[11,11.3],[9,9.1]]',
     'Two measurements per independent subject, complete rows A then B. difference A−B or log(A/B) (positive values). Reports bias, individual agreement limits, bias CI and approximate agreement-limit CIs at the chosen level; log mode also reports geometric mean ratio and ratio limits. Pair means versus differences plot. Assumes normal differences and constant variance; repeated observations per subject need another model. Agreement limits are not the mean-bias CI.',
     '독립 대상마다 두 측정값 A·B를 완전한 행으로 입력합니다. difference A−B·양수 자료의 log(A/B). 편향·개별 차이의 일치한계·편향 신뢰구간·일치한계의 근사 신뢰구간을 선택 수준으로 제공합니다. 로그 방식은 기하평균 비율·비율 한계도 제공합니다. 두 값의 평균 대 차이 그래프. 차이의 정규성·일정 분산 가정; 대상별 반복 관측에는 다른 모형이 필요합니다. 일치한계와 평균 편향의 신뢰구간은 구분해야 합니다.'),
    ('tost','One-sample equivalence (TOST)','단일 표본 동등성 (TOST)','list',',-0.5,0.5,10,0.05',SAMPLE,
     'tost(data,lower,upper,reference=0,alpha=.05). '+TOST_HELP[0], 'tost(자료,하한,상한,기준평균=0,alpha=.05). '+TOST_HELP[1]),
    ('tost2','Independent equivalence (TOST)','독립 두 표본 동등성 (TOST)','groups',',-0.5,0.5,welch,0.05',PAIR,
     'tost2(A,B,lower,upper,welch/student,alpha=.05). Welch permits unequal variances; Student assumes equal variances. Blank independent cells are omitted separately. '+TOST_HELP[0],
     'tost2(A,B,하한,상한,welch/student,alpha=.05). Welch는 이분산, Student는 등분산 가정. 독립 표본의 빈 셀은 각각 제외합니다. '+TOST_HELP[1]),
    ('tostpaired','Paired equivalence (TOST)','대응 두 표본 동등성 (TOST)','groups',',-0.5,0.5,0.05',PAIR,
     'tostpaired(A,B,lower,upper,alpha=.05). Complete pairs; subject-ID matching is available. '+TOST_HELP[0],
     'tostpaired(A,B,하한,상한,alpha=.05). 완전한 대응 쌍; 대상 ID 연결도 지원합니다. '+TOST_HELP[1]),
]


def forms(field, col, multi, two_fields, matching_fields):
    bounds=[field('lower','Lower equivalence bound','동등성 하한','number','-0.5'),field('upper','Upper equivalence bound','동등성 상한','number','0.5')]
    alpha=[field('alpha','Significance level α','유의수준 α','number','0.05')]
    level=[field('level','Confidence level','신뢰수준','number','0.95')]
    return {
        'metaanalysis':[field('layout','Input data','입력 자료','choice','effects',[('effects','Effect estimate / SE','효과 추정값 / SE'),('binary','Binary events / patients','이진 사건 수 / 환자 수'),('continuous','Continuous mean / SD / n','연속형 평균 / SD / n')]),
                        dict(col('effect','Effect estimate column','효과 추정값 열',0),when={'layout':['effects']}),dict(col('se','Standard error column (SE)','표준오차 열 (SE)',1),when={'layout':['effects']}),
                        dict(col('eventsA','Events A','A 사건 수 열',0),when={'layout':['binary']}),dict(col('totalA','Total patients A','A 전체 환자 수 열',1),when={'layout':['binary']}),
                        dict(col('eventsB','Events B','B 사건 수 열',2),when={'layout':['binary']}),dict(col('totalB','Total patients B','B 전체 환자 수 열',3),when={'layout':['binary']}),
                        dict(col('meanA','Mean A','A 평균 열',0),when={'layout':['continuous']}),dict(col('sdA','Sample SD A','A 표본 표준편차 열',1),when={'layout':['continuous']}),dict(col('nA','Sample size A','A 표본수 열',2),when={'layout':['continuous']}),
                        dict(col('meanB','Mean B','B 평균 열',3),when={'layout':['continuous']}),dict(col('sdB','Sample SD B','B 표본 표준편차 열',4),when={'layout':['continuous']}),dict(col('nB','Sample size B','B 표본수 열',5),when={'layout':['continuous']}),
                        field('continuousMeasure','Continuous effect','연속형 효과','choice','md',[('md','Mean difference (MD)','평균차 (MD)'),('smd','Standardized mean difference (Hedges g)','표준화 평균차 (Hedges g)')],when={'layout':['continuous']}),
                        field('measure','Ratio measure (A / B)','비율 효과 (A / B)','choice','oddsratio',[('oddsratio','Odds ratio (OR)','오즈비 (OR)'),('riskratio','Risk ratio (RR)','위험비 (RR)')],when={'layout':['binary']}),
                        field('correction','Zero-cell continuity correction','0 셀 연속성 보정','choice','0.5',[('0.5','Add 0.5 when a cell is zero','0 셀이 있으면 0.5 추가'),('0','None (zero cells rejected)','없음 (0 셀은 오류)')],when={'layout':['binary']}),
                        field('studyLabels','Study labels','연구 이름','choice','index',[('index','Row numbers','행 번호'),('column','Study name column','연구 이름 열')]),
                        dict(col('study','Study name column','연구 이름 열',2),when={'studyLabels':['column']}),
                        field('method','Effect model / τ² estimator','효과 모형 / τ² 추정','choice','pm',[('fixed','Fixed effect','고정효과'),('pm','Random: Paule–Mandel','랜덤: Paule–Mandel'),('dl','Random: DerSimonian–Laird','랜덤: DerSimonian–Laird')])]+level+[
                        field('inference','Pooled inference','통합 효과 추론','choice','z',[('z','Normal approximation','정규 근사'),('hksj','Modified Hartung–Knapp','수정 Hartung–Knapp')],when={'method':['pm','dl']}),
                        field('egger','Egger asymmetry test','Egger 비대칭 검정','choice','1',[('1','On','켬'),('0','Off','끔')])],
        'icc':[multi('columns','Rater columns','평가자 열'),field('model','ICC model','ICC 모형','choice','random',[('oneway','ICC(1): one-way agreement','ICC(1): 일원 일치'),('random','ICC(2): two-way random agreement','ICC(2): 이원 랜덤 일치'),('mixed','ICC(3): two-way mixed consistency','ICC(3): 이원 혼합 일관성')]),
               field('unit','Measurement unit','측정 단위','choice','single',[('single','Single measurement','단일 측정'),('average','Average of selected raters','선택 평가자의 평균')])]+level,
        'blandaltman':[col('first','Measurement A','측정 A 열',0),col('second','Measurement B','측정 B 열',1)]+level+[field('mode','Agreement scale','일치도 척도','choice','difference',[('difference','Difference A − B','차이 A − B'),('log','Log ratio log(A/B)','로그 비율 log(A/B)')])],
        'tost':[col('column','Sample column','표본 열',0)]+bounds+[field('reference','Reference mean','기준평균','number','10')]+alpha,
        'tost2':two_fields+bounds+[field('method','Variance assumption','분산 가정','choice','welch',[('welch','Welch (unequal variances)','Welch (이분산)'),('student','Student (equal variances)','Student (등분산)')])]+alpha,
        'tostpaired':two_fields+matching_fields+bounds+alpha,
    }
