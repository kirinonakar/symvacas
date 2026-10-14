"""Input controls, choices, defaults and conditional visibility."""
from statistics_social_schema import forms as social_forms
from statistics_research_schema import forms as research_forms
from statistics_comparison_schema import forms as comparison_forms
from .common import field, col, multi
from .definitions import CORRELATION_SPECS


def build_forms():
    """Construct fresh controls on each build; no caller shares mutable defaults."""
    credible_fields=[field('level','Credible level','베이지안 구간 수준','number','0.95')]
    bayesian_prior=[field('alpha','Prior α','사전 α','number','1'),field('beta','Prior β','사전 β','number','1')]
    grouping=field('grouping','Grouping','그룹 구성','choice','columns',[('columns','Columns','열별 그룹'),('groups','Group / value columns','그룹·값 열')])
    group_fields=[grouping,dict(multi('columns','Group columns','그룹 열'),when={'grouping':['columns']}),dict(col('group','Group column','그룹 열',0),when={'grouping':['groups']}),dict(col('value','Value column','값 열',1),when={'grouping':['groups']})]
    survival_fields=[col('time','Time','시간 열',0),col('event','Event','사건 열',1),field('eventValue','Event value','사건 발생 값','number','1')]
    cluster_fields=[col('subject','Subject / cluster','대상·군집 열',0),col('response','Response','반응 열',-1),multi('predictors','Predictors','설명변수 열')]
    offset_fields=[field('adjustment','Offset / exposure','오프셋·노출량','choice','none',[('none','None','없음'),('offset','Log offset','로그 오프셋'),('exposure','Exposure','노출량')]),dict(col('offset','Offset / exposure column','오프셋·노출량 열',0),when={'adjustment':['offset','exposure']})]
    count_fields=[col('response','Response','반응 열',-1),multi('predictors','Predictors','설명변수 열')]+offset_fields
    forms={
        'shapiro':[col('column','Sample column','표본 열',0)],
        'tukey':group_fields,'gameshowell':group_fields,
        'pca':[multi('columns','Feature columns','변수 열'),field('components','Components','주성분 수','number','2'),field('standardize','Scaling','척도','choice','1',[('1','Standardize (sample SD)','표준화 (표본 표준편차)'),('0','Center only','중심화만')])],
        'bayesbootstrap':[field('layout','Data layout','자료 구성','choice','single',[('single','Single sample','단일 표본'),('columns','Two columns','두 컬럼'),('groups','Group / value columns','그룹·값 컬럼')]),
            dict(col('column','Sample column','표본 열',0),when={'layout':['single']}),
            dict(col('first','Group A column','A 그룹 열',0),when={'layout':['columns']}),dict(col('second','Group B column','B 그룹 열',1),when={'layout':['columns']}),
            dict(field('comparison','Comparison','비교 방식','choice','independent',[('independent','Independent samples','독립 표본'),('paired','Paired rows','대응 행')]),when={'layout':['columns']}),
            dict(col('group','Group column','그룹 열',0),when={'layout':['groups']}),dict(col('value','Value column','값 열',1),when={'layout':['groups']}),
            dict(field('order','Group A','A 그룹','choice','first',[('first','First observed group','먼저 나온 그룹'),('reverse','Second observed group','둘째로 나온 그룹')]),when={'layout':['groups']}),
            field('statistic','Statistic','통계량','choice','mean',[('mean','Mean','평균'),('median','Median (sample estimate / weighted posterior)','중앙값 (표본 추정치 / 가중 사후추출)'),('variance','Population variance','모분산'),('stdev','Population SD','모표준편차')])]+credible_fields+[field('samples','Posterior draws','사후 추출 수','number','10000'),field('seed','Seed','시드','number','0')],
        'ancova':[col('group','Group column','그룹 열',0),col('response','Response','종속변수 열',-1),multi('predictors','Covariates','공변량 열'),field('level','Confidence level','신뢰수준','number','0.95'),field('slopes','Slope homogeneity','회귀 기울기 동질성','choice','test',[('test','Test','검정'),('none','Skip','생략')])],
        'glm':[col('response','Response','반응변수 열',-1),multi('predictors','Predictors','설명변수 열'),field('family','Family','분포','choice','gaussian',[('gaussian','Gaussian','정규'),('binomial','Binomial (0/1)','이항 (0/1)'),('poisson','Poisson','포아송'),('gamma','Gamma','Gamma'),('inversegaussian','Inverse Gaussian','역가우스'),('nbinom','Negative binomial (NB2)','음이항 (NB2)')]),
            field('link','Link function','연결함수','choice','auto',[('auto','Default for family','분포별 기본값'),('identity','Identity','항등'),('log','Log','로그'),('logit','Logit','로짓'),('probit','Probit','프로빗'),('cloglog','Complementary log-log','상보 로그로그'),('inverse','Inverse','역수'),('inverse_squared','Inverse squared','역수 제곱')]),
            dict(field('dispersionMode','NB2 dispersion','NB2 과산포','choice','fixed',[('fixed','Fixed alpha','alpha 고정'),('estimate','Estimate by ML','ML 추정')]),when={'family':['nbinom']}),
            dict(field('alpha','NB2 alpha (fixed)','NB2 alpha (고정)','number','1'),when={'family':['nbinom'],'dispersionMode':['fixed']})]+offset_fields,
        'bayesproportion':[field('layout','Data','자료 형태','choice','binary',[('binary','Binary observations (0/1)','0/1 관측값'),('counts','Successes / trials','성공 수·시행 수')]),
            dict(col('column','Observation column','관측값 열',0),when={'layout':['binary']}),
            dict(col('successes','Successes','성공 수 열',0),when={'layout':['counts']}),dict(col('trials','Trials','시행 수 열',1),when={'layout':['counts']})]+bayesian_prior+credible_fields+[field('threshold','Threshold p0','기준 비율 p0','number','0.5')],
        'bayesmean':[col('column','Sample column','표본 열',0),field('mu','Prior mean μ0','사전 평균 μ0','number','0'),field('kappa','Prior strength κ0','사전 강도 κ0','number','1'),field('alpha','Variance prior α0','분산 사전 α0','number','2'),field('beta','Variance prior β0','분산 사전 β0','number','1')]+credible_fields+[field('threshold','Threshold mean','기준 평균','number','0')],
        'bayescompare':[col('first','Group A column','A 집단 열',0),col('second','Group B column','B 집단 열',1),
            field('variance','Variance model','분산 모형','choice','equal',[('equal','Equal variance','등분산'),('unequal','Unequal variance','이분산')]),
            field('mu','Prior mean μ0 (both groups)','사전 평균 μ0 (두 집단)','number','0'),field('kappa','Prior strength κ0','사전 강도 κ0','number','0.01'),
            field('alpha','Variance prior α0','분산 사전 α0','number','2'),field('beta','Variance prior β0','분산 사전 β0','number','1')]+credible_fields+[
            field('samples','Posterior draws','사후 추출 수','number','20000'),field('seed','Simulation seed','시뮬레이션 시드','number','0')],
        'bayesrate':[field('layout','Data','자료 형태','choice','counts',[('counts','Counts (exposure = 1)','횟수 (노출량 = 1)'),('exposure','Counts / exposure','횟수·노출량')]),
            col('column','Count column','횟수 열',0),dict(col('exposure','Exposure','노출량 열',1),when={'layout':['exposure']}),field('alpha','Prior shape α','사전 shape α','number','1'),field('beta','Prior rate β','사전 rate β','number','1')]+credible_fields+[field('threshold','Threshold rate','기준 발생률','number','1')],
        'padjust':[col('column','p-value column','p값 열',0),field('method','Correction','보정 방법','choice','holm',[('bonferroni','Bonferroni','Bonferroni'),('holm','Holm','Holm'),('fdr','FDR (BH)','FDR (BH)')]),field('alpha','Significance α','유의수준 α','number','0.05')],
        'levene':group_fields,'bartlett':group_fields,
        'mcnemar':[field('layout','Data','자료 형태','choice','counts',[('counts','2×2 counts','2×2 빈도표'),('pairs','Paired observations','대응 관측값')]),col('first','Before / first','이전·첫째 열',0),col('second','After / second','이후·둘째 열',1),field('method','Method','검정 방법','choice','exact',[('asymptotic','McNemar','McNemar'),('exact','Exact McNemar','Exact McNemar'),('corrected','Continuity correction','연속성 보정')])],
        'kaplanmeier':survival_fields+[field('level','Confidence level','신뢰수준','number','0.95')],
        'logrank':survival_fields+[col('group','Group','그룹 열',2)],
        'survivalanalysis':survival_fields+[field('grouping','Groups','그룹','choice','groups',[('groups','Group column','그룹 열'),('all','All subjects','전체 대상')]),
            dict(col('group','Group column','그룹 열',2),when={'grouping':['groups']}),
            field('cox','Cox model','Cox 모형','choice','0',[('0','Off','끔'),('1','On','켬')]),
            dict(multi('predictors','Cox predictors','Cox 설명변수 열'),when={'cox':['1']}),
            field('ties','Tie handling','동률 처리','choice','efron',[('efron','Efron','Efron'),('breslow','Breslow','Breslow')]),
            dict(field('ph','Proportional-hazards check','비례위험 검정','choice','test',[('test','Schoenfeld test','Schoenfeld 검정'),('none','Skip','생략')]),when={'cox':['1']})],
        'cox':survival_fields+[multi('predictors','Predictors','설명변수 열'),
            field('ties','Tie handling','동률 처리','choice','efron',[('efron','Efron','Efron'),('breslow','Breslow','Breslow')]),
            field('truncation','Left truncation','좌측 절단','choice','none',[('none','None','없음'),('entry','Entry-time column','진입시간 열')]),
            dict(col('entry','Entry time','진입시간 열',2),when={'truncation':['entry']}),
            field('ph','Proportional-hazards check','비례위험 검정','choice','test',[('test','Schoenfeld test','Schoenfeld 검정'),('none','Skip','생략')])],
        'repeatedanova':[multi('columns','Condition columns','조건 열'),field('factor2','Second-factor levels','둘째 요인 수준','number','1')],
        'mixedmodel':cluster_fields+[field('slope','Random-slope predictors','랜덤 기울기 변수','number','0'),field('method','Estimation','추정 방법','choice','reml',[('reml','REML','REML'),('ml','ML','ML')]),field('ci','Fixed-effect 95% CI','고정효과 95% 신뢰구간','choice','wald',[('wald','Wald','Wald'),('profile','ML profile likelihood','ML 프로파일 우도'),('bootstrap','Parametric bootstrap','모수적 부트스트랩')]),dict(field('ciSamples','Bootstrap refits','부트스트랩 재적합 수','number','200'),when={'ci':['bootstrap']}),dict(field('ciSeed','Bootstrap seed','부트스트랩 시드','number','0'),when={'ci':['bootstrap']})],
        'glmm':cluster_fields+[field('slope','Random slope position (0 = none, Laplace)','랜덤 기울기 번호 (0 = 없음, Laplace)','number','0'),field('family','Family','분포','choice','binomial',[('binomial','Binomial (0/1)','이항 (0/1)'),('poisson','Poisson','포아송'),('nbinom','Negative binomial (NB2)','음이항 (NB2)')]),dict(field('points','Quadrature points (1 = Laplace)','적분 점 수 (1 = Laplace)','number','15'),when={'slope':['0']}),dict(field('sensitivity','Quadrature sensitivity','적분 민감도 확인','choice','likelihood',[('likelihood','Compare likelihood','우도 비교'),('refit','Refit and compare coefficients','재적합·계수 비교')]),when={'slope':['0']})]+[dict(f,when={**f.get('when',{}),'family':['poisson','nbinom']}) for f in offset_fields],
        'poissonreg':count_fields,'nbreg':count_fields,
        'gee':cluster_fields+[field('family','Family','분포','choice','gaussian',[('gaussian','Gaussian','Gaussian'),('binomial','Binomial (0/1)','이항 (0/1)'),('poisson','Poisson','포아송')]),field('corr','Working correlation','작업상관','choice','independence',[('independence','Independent','독립'),('exchangeable','Exchangeable','교환가능'),('ar1','AR(1)','AR(1)')]),field('correction','Covariance correction','공분산 보정','choice','robust',[('robust','Asymptotic sandwich','점근 샌드위치'),('small','Mancl-DeRouen + t','Mancl-DeRouen + t')]),field('interactions','Interactions (columns or names)','상호작용 (열·이름)','number','')],
        'kstest':[field('mode','Samples / distribution','표본·분포','choice','two',[('two','Two samples','두 표본'),('normal','Normal','정규분포'),('uniform','Uniform','균등분포')]),col('first','Sample column','표본 열',0),dict(col('second','Second sample','둘째 표본 열',1),when={'mode':['two']}),dict(field('location','Mean / lower bound','평균·하한','number','0'),when={'mode':['normal','uniform']}),dict(field('scale','SD / width','표준편차·폭','number','1'),when={'mode':['normal','uniform']})],
        'impute':[field('method','Method','대체 방법','choice','mean',[('mean','Mean','평균'),('median','Median','중앙값'),('mode','Mode','최빈값'),('regression','Regression','회귀'),('knn','k-NN','k-NN')]),dict(field('k','Neighbours','이웃 수','number','5'),when={'method':['knn']})],
        'crossvalidate':[field('folds','Folds','폴드 수','number','3'),field('seed','Seed','시드','number','0'),
            field('split','Split','분할','choice','random',[('random','Random','무작위'),('blocked','Blocked','블록'),('stratified','Stratified','층화')]),
            field('model','Model','모형','choice','linear',[('linear','Linear (OLS)','선형 (OLS)'),('ridge','Ridge','Ridge'),('lasso','Lasso','Lasso'),('elasticnet','Elastic net','Elastic net'),('logistic','Logistic (0/1)','로지스틱 (0/1)')]),
            dict(field('alpha','Penalty α','벌점 α','number','0.1'),when={'model':['ridge','lasso','elasticnet','logistic']}),
            dict(field('ratio','L1 ratio','L1 비율','number','0.5'),when={'model':['elasticnet']})]
    }
    design_field=field('design','Study design','연구 설계','choice','independent',[('independent','Independent groups','독립 두 그룹'),('paired','Paired observations','대응 표본'),('onesample','One sample','단일 표본')])
    tail_field=field('tail','Alternative hypothesis','대립가설','choice','two',[('two','Two-sided','양측'),('greater','Greater','우측'),('less','Less','좌측')])
    forms.update({
        'twowayanova':[field('layout','Data layout','자료 구조','choice','groups',[('groups','Factor columns + response','요인 열 + 반응 열'),('columns','One column per factor cell','요인 조합별 열')]),dict(col('factorA','Factor A','요인 A 열',0),when={'layout':['groups']}),dict(col('factorB','Factor B','요인 B 열',1),when={'layout':['groups']}),dict(col('response','Response','반응 열',2),when={'layout':['groups']}),dict(multi('columns','Cell columns (A slowest)','조합별 열 (A 최외곽)'),when={'layout':['columns']}),dict(field('levelsB','Factor B levels','요인 B 수준 수','number','2'),when={'layout':['columns']}),field('interaction','Model','모형','choice','1',[('1','Main effects + interaction','주효과 + 상호작용'),('0','Additive main effects','가법 주효과')])],
        'friedman':[multi('columns','Condition columns','반복 조건 열')],
        'cohend':[col('first','Group A','그룹 A 열',0),col('second','Group B','그룹 B 열',1),field('design','Comparison','비교 방식','choice','independent',[('independent','Independent groups','독립 표본'),('paired','Paired observations','대응 표본')])],
        'eta2':group_fields,
        'bootstrapci':[col('column','Data column','자료 열',0),field('statistic','Statistic','통계량','choice','mean',[(v,en,ko) for v,en,ko in [('mean','Mean','평균'),('median','Median','중앙값'),('stdev','Standard deviation','표준편차')]]),field('level','Confidence level','신뢰수준','number','0.95'),field('samples','Resamples','재표집 수','number','2000'),field('seed','Seed','시드','number','0')],
        'kmeans':[multi('columns','Feature columns','변수 열'),field('clusters','Clusters','군집 수','number','2'),field('seed','Seed','시드','number','0')],
        'multinomial':[col('response','Category response','범주 반응 열',-1),multi('predictors','Predictors','설명변수 열')],
        'ordinal':[col('response','Ordered category response','순서형 반응 열',-1),multi('predictors','Predictors','설명변수 열')],
        'testpower':[design_field,field('effect','Cohen’s d','Cohen의 d','number','0.5'),field('n','Sample size per group / pairs','그룹별 표본수·쌍 수','number','64'),field('alpha','Significance level α','유의수준 α','number','0.05'),tail_field],
        'samplesize':[design_field,field('effect','Cohen’s d','Cohen의 d','number','0.5'),field('power','Target power','목표 검정력','number','0.8'),field('alpha','Significance level α','유의수준 α','number','0.05'),tail_field],
    })
    forms['modelcompare']=comparison_forms(field,col,multi)
    forms['logisticcompare']=[col('response','Response (0/1)','반응 열 (0/1)',-1),field('basePredictors','Model A predictors','Model A 설명변수','columns','0'),multi('addedPredictors','Added Model B predictors','Model B 추가 설명변수'),field('validation','Validation method','검증 방식','choice','crossvalidation',[('external','Validation dataset','검증 데이터셋'),('holdout','Stratified holdout','층화 홀드아웃'),('crossvalidation','Stratified K-fold cross-validation','층화 K-fold 교차검증')]),field('validationDataset','Validation dataset','검증 데이터셋','dataset','',when={'validation':['external']}),field('holdout','Holdout fraction','홀드아웃 비율','number','0.25',when={'validation':['holdout']}),field('folds','Folds','폴드 수','number','5',when={'validation':['crossvalidation']}),field('threshold','Classification threshold','분류 확률 기준','number','0.5'),field('level','Confidence level','신뢰수준','number','0.95'),field('resamples','Paired bootstrap resamples (CV refits)','대응 부트스트랩 수 (CV 재적합)','number','200'),field('seed','Seed','시드','number','0')]
    forms['linearmodel']=[col('response','Response','반응 열',-1),multi('predictors','Predictors','설명변수 열'),multi('categorical','Categorical predictors','범주 설명변수 열'),field('order','Interaction order (1 = additive)','상호작용 차수 (1 = 가법)','number','2'),field('ssType','Sums of squares','제곱합','choice','3',[('3','Type III','Type III'),('2','Type II','Type II')]),field('coding','Categorical coding','범주 코딩','choice','sum',[('sum','Sum-to-zero contrasts','합이 0인 대비'),('treatment','Treatment / dummy coding','처리 / 더미 코딩')])]
    forms['crossvalidate']=[col('response','Response','반응 열',-1),multi('predictors','Predictors','설명변수 열')]+forms['crossvalidate']
    two_fields=[grouping,dict(col('first','Group A column','A 그룹 열',0),when={'grouping':['columns']}),dict(col('second','Group B column','B 그룹 열',1),when={'grouping':['columns']}),dict(col('group','Group column','그룹 열',0),when={'grouping':['groups']}),dict(col('value','Value column','값 열',1),when={'grouping':['groups']}),field('firstGroup','Group A value','A 그룹 값','group','',when={'grouping':['groups']}),field('secondGroup','Group B value','B 그룹 값','group','',when={'grouping':['groups']})]
    matching_fields=[field('matching','Pair matching','대응 연결','choice','order',[('order','Within-group row order','그룹 안의 행 순서'),('subject','Subject ID','대상 ID')],when={'grouping':['groups']}),dict(col('subject','Subject ID','대상 ID 열',0),when={'grouping':['groups'],'matching':['subject']})]
    forms['cohend']=two_fields+forms['cohend'][2:]+matching_fields
    forms['bayescompare']=two_fields+forms['bayescompare'][2:]
    for id_ in ('friedman','repeatedanova'): forms[id_]=group_fields+matching_fields+forms[id_][1:]
    # KS one-sample keeps its own data column; two-sample enables arbitrary long roles.
    forms['kstest']+= [dict(f,when={**f.get('when',{}),'mode':['two']}) for f in two_fields if f['key'] not in ('first','second')]
    forms['bayesbootstrap']=[dict(f,when={'layout':['columns','groups']}) if f['key']=='comparison' else f for f in forms['bayesbootstrap']]
    forms['bayesbootstrap'] += [dict(f,when={**{k:v for k,v in f.get('when',{}).items() if k!='grouping'},'layout':['groups']}) for f in two_fields+matching_fields if f['key'] in ('firstGroup','secondGroup','matching','subject')]
    next(f for f in forms['mcnemar'] if f['key']=='layout')['choices'].append(dict(id='groups',label='Group / value columns',ko='그룹·값 열'))
    forms['mcnemar'] += [dict(f,when={**{k:v for k,v in f.get('when',{}).items() if k!='grouping'},'layout':['groups']}) for f in two_fields+matching_fields if f['key'] in ('group','value','firstGroup','secondGroup','matching','subject')]
    proportion_tail=field('tail','Alternative','대립가설','choice','both',[('both','Two-sided','양측'),('left','Less than','작다 (좌측)'),('right','Greater than','크다 (우측)')])
    forms['tinterval']=[col('column','Sample column','표본 열',0),field('level','Confidence level (%)','신뢰수준 (%)','number','95')]
    forms['zinterval']=forms['tinterval']+[field('sigma','Known population SD σ','알려진 모집단 표준편차 σ','number','2')]
    proportion_layout=field('layout','Data layout','자료 구성','choice','counts',[('counts','Successes / trials','성공 수·시행 수'),('binary','Binary observations','이항 관측값')])
    proportion_counts=[dict(col('successes','Successes column','성공 수 열',0),when={'layout':['counts']}),dict(col('trials','Trials column','시행 수 열',1),when={'layout':['counts']})]
    forms['propztest']=[proportion_layout]+proportion_counts+[dict(col('column','Sample column','표본 열',0),when={'layout':['binary']}),dict(field('successValue','Success value','성공 값','text','1'),when={'layout':['binary']}),field('p0','Null proportion p0','귀무가설 비율 p0','number','0.5'),proportion_tail]
    forms['propztest2']=[proportion_layout]+proportion_counts+[dict(f,when={**f.get('when',{}),'layout':['binary']}) for f in two_fields]+[dict(field('successValue','Success value','성공 값','text','1'),when={'layout':['binary']}),proportion_tail]
    forms.update(social_forms(field,col,multi,group_fields))
    time_fields = [col('column','Series column','시계열 값 열',-1),field('dateMode','Time labels','시간 표시','choice','auto',[('auto','Detect date column','날짜 열 자동 인식'),('index','Observation index','관측 순서'),('dates','Date / year column','날짜·연도 열')]),dict(col('dateColumn','Date / year column','날짜·연도 열',0),when={'dateMode':['auto','dates']}),field('p','AR order p','AR 차수 p','number','1'),field('d','Differencing d','차분 차수 d','number','1'),field('q','MA order q','MA 차수 q','number','0')]
    forecast_fields = [field('horizon','Forecast horizon','예측 길이','number','12'),field('level','Prediction level','예측구간 수준','number','0.95'),field('trend','Intercept / drift','절편·드리프트','choice','auto',[('auto','Auto (AICc)','자동 (AICc)'),('none','None','없음'),('constant','Constant / drift','상수·드리프트')])]
    forms['arima'] = time_fields + forecast_fields
    forms['sarima'] = [dict(f,default='0') if f['key']=='d' else f for f in time_fields] + [field('P','Seasonal AR order P','계절 AR 차수 P','number','0'),field('D','Seasonal differencing D','계절 차분 차수 D','number','1'),field('Q','Seasonal MA order Q','계절 MA 차수 Q','number','1'),field('period','Seasonal period s','계절 주기 s','number','4')] + [dict(f,default='8') if f['key']=='horizon' else f for f in forecast_fields]
    forms.update(research_forms(field,col,multi,two_fields,matching_fields))
    for spec in CORRELATION_SPECS:
        forms[spec[0]]=[col('first','First column','첫째 열',0),col('second','Second column','둘째 열',1),field('tail','Alternative','대립가설','choice','both',[('both','Two-sided','양측'),('left','Negative association','음의 상관'),('right','Positive association','양의 상관')])]
    (next(field for field in forms['cohenkappa'] if field['key']=='layout'))['default']='pairs'
    links={'identity':['gaussian'],'log':['gaussian','poisson','gamma','inversegaussian','nbinom'],'logit':['binomial'],'probit':['binomial'],'cloglog':['binomial'],'inverse':['gamma'],'inverse_squared':['inversegaussian']}
    for choice in next(f for f in forms['glm'] if f['key']=='link')['choices']:
        if choice['id']!='auto': choice['when']={'family':links[choice['id']]}
    return forms
