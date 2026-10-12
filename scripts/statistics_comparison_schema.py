"""Shared model-comparison forms, bilingual operational help and family examples."""
import math
import random

ROWS=[[i/10,(i%7)/3,2+i/5+(i%7)/2+math.sin(i*1.7)] for i in range(48)]
HELP=('Select an analysis family, baseline predictors and added predictors. Both models use common complete rows. Linear: partial F, ΔR²/AIC; logistic, count and Cox: ML likelihood-ratio comparisons; LMM automatically uses ML; GLMM boundary/diagnostic failures suppress ordinary LRT. GEE has no likelihood-ratio test. Prediction families use shared holdout, selected validation data or folds and paired bootstrap differences. Training-data logistic comparisons show nominal DeLong/McNemar p values and fixed-prediction bootstrap intervals as descriptive reference results. Select individual candidates for separate additions with Holm-adjusted training tests. CFA/SEM keep the same indicators and add paths, cross-loadings or residual covariances; adjusted WLSMV chi-square values are not subtracted. Candidate selection remains exploratory; validate the chosen model separately.',
      '분석군·기존 설명변수·추가 설명변수를 선택하면 동일한 완전 행으로 두 모형을 적합합니다. 선형은 부분 F·ΔR²/AIC, 로지스틱·계수·Cox는 ML 우도비 비교를 제공합니다. LMM은 자동으로 ML을 사용하며 GLMM 분산 경계·적합 진단 실패 시 일반 LRT를 제외합니다. GEE에는 LRT를 적용하지 않습니다. 예측 모형은 동일한 홀드아웃·선택한 검증 자료·폴드와 대응 부트스트랩으로 차이를 비교합니다. 훈련 자료의 로지스틱 비교에는 명목상 DeLong·McNemar p값과 고정 예측의 부트스트랩 구간을 기술적 참고 결과로 표시합니다. 개별 후보 비교는 하나씩 추가하고 훈련 검정에 Holm 보정을 적용합니다. CFA/SEM은 동일한 지표를 유지하며 경로·교차적재·잔차 공분산을 추가합니다. 보정된 WLSMV χ²를 단순 차감하지 않습니다. 후보 선택은 탐색적이며 선택한 모형은 별도 자료에서 검증하세요.')
SPEC=('modelcompare','Model Comparison','모형 비교','table',',1,linear,crossvalidation,5,0.95,100,0,[[excludedrows,0]],0',str(ROWS).replace(' ',''),*HELP)
PREDICTIVE=['linear','logistic','poisson','nb','cox','mlclassification','mlregression']
REGRESSION=PREDICTIVE+['lmm','glmm','gee']


def forms(field,col,multi):
    def when(item,families):return dict(item,when={'family':families})
    result = [field('family','Analysis family','분석군','choice','linear',[
        ('linear','Linear regression','선형회귀'),('logistic','Logistic regression','로지스틱 회귀'),('poisson','Poisson regression','Poisson 회귀'),('nb','Negative binomial regression','음이항 회귀'),('cox','Cox regression','Cox 회귀'),('lmm','Linear mixed model (ML)','선형혼합모형 (ML)'),('glmm','Generalized mixed model','일반화 혼합모형'),('gee','GEE (robust inference)','GEE (강건 추론)'),('cfa','CFA','CFA'),('sem','SEM','SEM'),('mlclassification','ML Classification','ML 분류'),('mlregression','ML Regression','ML 회귀')]),
        when(col('response','Response','반응 열',-1),[v for v in REGRESSION if v!='cox']),
        when(col('time','Time','시간 열',0),['cox']),when(col('event','Event (0/1)','사건 열 (0/1)',1),['cox']),
        when(col('subject','Subject / cluster','대상·군집 열',0),['lmm','glmm','gee']),
        when(field('basePredictors','Model A existing predictors','Model A 기존 설명변수','columns','0'),REGRESSION),
        when(multi('addedPredictors','Added Model B predictors','Model B 추가 설명변수'),REGRESSION),
        when(field('candidates','Compare additions','추가 변수 비교','choice','0',[('0','All added predictors together','추가 변수 모두 함께'),('1','Each candidate separately (Holm)','후보별 개별 추가 (Holm)')]),REGRESSION),
        when(field('validation','Validation method','검증 방식','choice','crossvalidation',[
            ('external','Validation dataset','검증 데이터셋'),('holdout','Shared holdout','동일 홀드아웃'),('crossvalidation','Shared K-fold cross-validation','동일 K-fold 교차검증'),('apparent','Training-data performance','훈련 데이터 성능')]),PREDICTIVE),
        dict(field('validationDataset','Validation dataset','검증 데이터셋','dataset',''),when={'family':PREDICTIVE,'validation':['external']}),
        dict(field('holdout','Holdout fraction','홀드아웃 비율','number','0.25'),when={'family':PREDICTIVE,'validation':['holdout']}),
        dict(field('folds','Folds','폴드 수','number','5'),when={'family':PREDICTIVE,'validation':['crossvalidation']}),
        when(field('resamples','Paired bootstrap resamples','대응 부트스트랩 수','number','100'),PREDICTIVE),
        field('level','Confidence level','신뢰수준','number','0.95'),field('seed','Seed','시드','number','0'),
        when(field('threshold','Classification threshold','분류 확률 기준','number','0.5'),['logistic','mlclassification']),
        when(field('ties','Cox ties','Cox 동률 처리','choice','efron',[('efron','Efron','Efron'),('breslow','Breslow','Breslow')]),['cox']),
        when(field('responsefamily','Response family','반응 분포','choice','binomial',[('binomial','Binomial','이항'),('poisson','Poisson','Poisson'),('nbinom','Negative binomial','음이항'),('gaussian','Gaussian','정규')]),['glmm','gee']),
        when(field('randomA','Model A random slope position (0 = intercept)','Model A 랜덤 기울기 위치 (0 = 절편)','text','0'),['lmm','glmm']),
        when(field('randomB','Model B random slope position (same = Model A)','Model B 랜덤 기울기 위치 (same = Model A)','text','same'),['lmm','glmm']),
        when(field('points','GLMM quadrature points','GLMM 구적점 수','number','15'),['glmm']),
        when(field('correlation','GEE working correlation','GEE 작업 상관','choice','independence',[('independence','Independence','독립'),('exchangeable','Exchangeable','교환가능'),('ar1','AR(1)','AR(1)')]),['gee']),
        when(field('algorithm','ML algorithm','ML 알고리즘','choice','ridge',[('ridge','Ridge / ridge logistic','Ridge / ridge 로지스틱'),('lasso','Lasso (regression)','Lasso (회귀)'),('elasticnet','Elastic net (regression)','Elastic net (회귀)'),('forest','Random forest','랜덤 포레스트')]),['mlclassification','mlregression']),
        when(field('alpha','Penalty alpha','벌점 alpha','number','0.1'),['mlclassification','mlregression']),when(field('ratio','Elastic net L1 ratio','Elastic net L1 비율','number','0.5'),['mlregression']),
        when(field('trees','Forest trees','포레스트 트리 수','number','50'),['mlclassification','mlregression']),when(field('depth','Forest max depth','포레스트 최대 깊이','number','6'),['mlclassification','mlregression']),
        when(multi('indicators','Common observed indicators','공통 관측 지표'),['cfa','sem']),
        when(field('factors','Factor ID per indicator','지표별 요인 ID','text','1,1,1,2,2,2'),['cfa','sem']),
        when(field('estimator','Estimator','추정법','choice','ml',[('ml','ML','ML'),('wlsmv','WLSMV','WLSMV')]),['cfa','sem']),
        when(field('basepaths','Existing latent paths (source,target; …)','기존 잠재 경로 (출발,도착; …)','text',''),['sem']),
        when(field('addedpaths','Added latent paths (source,target; …)','추가 잠재 경로 (출발,도착; …)','text',''),['sem']),
        when(field('basecross','Existing cross-loadings (indicator,factor; …)','기존 교차적재 (지표,요인; …)','text',''),['cfa','sem']),
        when(field('addedcross','Added cross-loadings (indicator,factor; …)','추가 교차적재 (지표,요인; …)','text',''),['cfa','sem']),
        when(field('baseresidual','Existing residual covariances (i,j; …)','기존 잔차 공분산 (i,j; …)','text',''),['cfa','sem']),
        when(field('addedresidual','Added residual covariances (i,j; …)','추가 잔차 공분산 (i,j; …)','text','2,5'),['cfa','sem'])]
    for item in result:
        if item['key']=='algorithm':
            for choice in item['choices']:
                if choice['id'] in ('lasso','elasticnet'):choice['when']={'family':['mlregression']}
        if item['key']=='responsefamily':
            for choice in item['choices']:
                choice['when']={'family':['gee']} if choice['id']=='gaussian' else {'family':['glmm']} if choice['id']=='nbinom' else {'family':['glmm','gee']}
    return result


def examples(schema,logistic):
    rng=random.Random(73);continuous=[]
    for i in range(150):
        f=rng.gauss(0,1);g=.4*f+rng.gauss(0,1)
        continuous.append([f+rng.gauss(0,1),.8*f+rng.gauss(0,1),1.2*f+rng.gauss(0,1),g+rng.gauss(0,1),.9*g+rng.gauss(0,1),1.1*g+rng.gauss(0,1)])
    count=[[r[0],r[1],int((i*7)%9+max(0,r[0]+r[1]))] for i,r in enumerate(ROWS)]
    nb=[]
    for row in ROWS:
        rate=rng.gammavariate(.7,math.exp(.1*row[0]+.2*row[1])/.7);limit=math.exp(-rate);product=1.;value=-1
        while product>limit:product*=rng.random();value+=1
        nb.append(row[:2]+[value])
    survival=[[1+(i*11)%43,int(i%4!=0),r[0],r[1]] for i,r in enumerate(ROWS)]
    clustered=[[i//4+1,r[0],r[1],r[-1]+(i//4)%5] for i,r in enumerate(ROWS)]
    binary=[[i//4+1,*row] for i,row in enumerate(logistic)]
    mapping={'linear':ROWS,'logistic':logistic,'poisson':count,'nb':nb,'cox':survival,'lmm':clustered,'glmm':binary,'gee':binary,'cfa':continuous,'sem':continuous,'mlclassification':logistic,'mlregression':ROWS}
    for item in schema:
        if item['id']=='modelcompare':
            item['exampleRowsByFamily']={key:[[str(v) for v in row] for row in values] for key,values in mapping.items()}
            item['validationExampleRows']=item['exampleRows']
        if item['id']=='logisticcompare':item['hidden']=True
