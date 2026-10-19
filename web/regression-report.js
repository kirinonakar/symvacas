import {element,control} from './app-ui.js';
import {t} from './i18n.js';
import {roundNumber} from './display-format.js';
import {regressionROC} from './regression-roc.js';
import {appendPlotExportButtons} from './svg-export.js';
import {svmDecisionPlot} from './svm-decision-plot.js';
import {svmDecisionEquation} from './svm-decision-equation.js';

export function regressionParameterLabels(mode,columns,responseColumn){
  const predictors=columns.filter((_,i)=>i!==responseColumn);if(!predictors.length)return {};
  if(['multiple','logistic','ridge','lasso','elasticnet','logisticridge','logisticlasso','logisticelasticnet','randomforest','randomforestclassifier','randomforestregressor','svm','svc','svr','bayeslinear','bayeslogistic'].includes(mode))return {b0:'Intercept',...Object.fromEntries(predictors.map((name,i)=>[`b${i+1}`,name]))};
  if(['linear','quadratic','polynomial'].includes(mode))return {b0:'Intercept',...Object.fromEntries(Array.from({length:10},(_,i)=>[`b${i+1}`,predictors[0]+(i?String(i+1).replace(/\d/g,digit=>'⁰¹²³⁴⁵⁶⁷⁸⁹'[Number(digit)]):'')]))};
  return {};
}
export function regressionParameterName(name,labels={}){return labels[name]==='Intercept'?t('Intercept'):labels[name]||name;}

export function renderRegressionReport(container,report,digits=10,parameterLabels={}, {onCopy,onClear}={}) {
  container.replaceChildren();
  if(!report)return;
  const svm=report.model==='svm',svmClassification=svm&&report.task==='classification';
  if(onCopy||onClear||svm){const heading=element('div','','statistics-result-heading');heading.append(element('h3',t(svm?(svmClassification?'SVM classification':'SVM regression'):'Regression')));if(onCopy)heading.append(control('Copy',onCopy));if(onClear)heading.append(control('Clear',onClear));container.append(heading);}
  const number=value=>value===null||value===undefined?'—':roundNumber(String(value),digits,true);
  const bayesian=!!report.bayesian;
  const machineLearning=!!report.model&&!bayesian;
  const credibleLabel=`${number(Number(report.credibleLevel)*100)}% ${t("Credible interval")}`;
  const forest=report.model==='randomforest';
  const summary=element('p');
  const metrics=[['R²','rSquared'],['Adjusted R²','adjustedRSquared'],['RMSE','rmse'],['MAE','mae'],['Log loss','logLoss'],['Accuracy','accuracy'],['Sensitivity','sensitivity'],['Specificity','specificity'],['OOB C-statistic (AUC)','oobAuc'],['OOB sensitivity','oobSensitivity'],['OOB specificity','oobSpecificity'],['OOB accuracy','oobAccuracy'],['OOB R²','oobRSquared'],['OOB RMSE','oobRMSE'],['Residual SE','residualSE'],['C-statistic (AUC)','auc'],['McFadden R²','pseudoRSquared'],['Deviance','deviance'],['AIC','aic'],['LR p','likelihoodP'],['Durbin–Watson','durbinWatson'],['Residual Shapiro p','shapiroP']];
  summary.textContent=`n=${report.n} · ${report.df==null?'':`df=${report.df} · `}`+metrics.filter(([,key])=>report[key]!=null||['rSquared','adjustedRSquared'].includes(key)&&key in report).map(([name,key])=>`${t(svmClassification&&key==='accuracy'?'Training accuracy':name)}=${number(report[key])}`).join(' · ');
  container.append(summary);
  if(bayesian){container.append(element("p",`${t("Prior SD")}=${number(report.priorSD)} · ${t("Credible level (0–1)")}=${number(report.credibleLevel)}`));if(report.varianceShape)container.append(element("p",`${t("Variance prior shape")}=${number(report.varianceShape)} · ${t("Variance prior scale")}=${number(report.varianceScale)} · ${t("Posterior variance mean")}=${number(report.posteriorVarianceMean)}`));}
  if(machineLearning)container.append(element('p',svm?`${t('Model')}: ${svmClassification?'SVC':'SVR'} · ${t('Kernel')}: ${report.kernel} · C=${number(report.C)}${report.kernel==='rbf'&&report.gamma!=null?' · γ='+number(report.gamma):''}${!svmClassification&&report.epsilon!=null?' · ε='+number(report.epsilon):''} · ${t('Support vectors')}: ${report.supportVectors} · ${t('Iterations')}: ${report.iterations}`:forest?`${t('Random Forest')} · ${t(report.task==='classification'?'Binary classification':'Regression')} · ${t('Trees')}: ${report.trees} · ${t('Max depth')}: ${report.maxDepth} · ${t('Random seed')}: ${report.seed} · OOB n=${report.oobN}/${report.n}`:`${t(report.model.replace('logistic',''))} · α=${number(report.alpha)} · ${t('Selected predictors')}: ${report.selectedPredictors} · L1=${number(report.l1Ratio)}`));
  if(svm)container.append(element('p',t('Training data evaluation'),'statistics-training-evaluation'));
  if(svm){const equation=svmDecisionEquation(report,digits,parameterLabels);if(equation)container.append(equation);}
  if(svm){
    const cv=report.crossValidation;
    if(cv){
      const metrics=svmClassification?`${t('Cross-validated accuracy')}=${number(cv.accuracy)}`:`${t('Cross-validated R²')}=${number(cv.rSquared)} · ${t('Cross-validated RMSE')}=${number(cv.rmse)} · ${t('Cross-validated MAE')}=${number(cv.mae)}`;
      container.append(element('p',cv.available?`${metrics} · ${t(cv.method)} · ${t('Folds')}=${cv.folds} · n=${cv.n}`:t(cv.reason),'statistics-cross-validation'));
    }
  }
  if(report.nuts){
    const h=report.nuts;
    container.append(element('p',`NUTS · ${t('Samples per chain')}=${h.samples} · ${t('Warmup')}=${h.warmup} · ${t('Max tree depth')}=${h.maxTreeDepth} · ${t('Chains')}=${h.chains} · ${t('Random seed')}=${h.seed} · ${t('Mean acceptance probability')}=${number(h.meanAcceptanceProbability)} · ${t('Divergences')}=${h.divergences} · ${t('Max tree depth hits')}=${h.maxTreeDepthHits} · ${t('Mean tree depth')}=${number(h.meanTreeDepth)} · ${t('Mean leapfrog steps')}=${number(h.meanLeapfrogSteps)}`));
    for(const c of h.chainDiagnostics||[])container.append(element('p',`${t('Chain')} ${c.chain} · ${t('Mean acceptance probability')}=${number(c.meanAcceptanceProbability)} · ${t('Step size')}=${number(c.stepSize)} · ${t('Divergences')}=${c.divergences}`));
  }
  for(const warning of report.warnings||[])container.append(element('p',t(warning)));
  const wrapper=element('div');wrapper.style.overflowX='auto';
  const table=element('table');table.setAttribute('aria-label',t(forest?'Feature importance':machineLearning?'Fitted parameters':'Coefficient inference'));
  const hasVif=(report.coefficients||[]).some(c=>c.vif!=null);
  const hasOdds=report.fitScale==='binomial'||(report.coefficients||[]).some(c=>c.oddsRatio!=null);
  const hasOddsCI=report.fitScale==='binomial';
  const head=element('tr');for(const label of [...(bayesian?['Parameter','Posterior estimate','Posterior SD',credibleLabel,'P(β > 0)']:machineLearning?['Parameter',forest?'Feature importance':'Estimate']:['Parameter','Estimate','SE','95% CI','p']),...(report.nuts?['Rank-normalized R-hat','Bulk ESS','Tail ESS','MCSE']:[]),...(hasVif?['VIF']:[]),...(hasOdds?['Odds ratio']:[]),...(hasOddsCI?[bayesian?'OR credible interval':'OR 95% CI']:[])])head.append(element('th',label===credibleLabel?label:t(label)));
  const thead=element('thead');thead.append(head);table.append(thead);
  const body=element('tbody');
  for(const c of (forest?report.featureImportance:report.coefficients)||[]){const row=element('tr');for(const label of [regressionParameterName(c.name,parameterLabels),number(c.estimate),...(bayesian?[number(c.posteriorSD),`${number(c.low)} … ${number(c.high)}`,number(c.probabilityPositive)]:machineLearning?[]:[number(c.se),`${number(c.low)} … ${number(c.high)}`,number(c.p)]),...(report.nuts?[number(c.rHat),number(c.bulkEss),number(c.tailEss),number(c.mcse)]:[]),...(hasVif?[number(c.vif)]:[]),...(hasOdds?[number(c.oddsRatio)]:[]),...(hasOddsCI?[`${number(c.oddsLow)} … ${number(c.oddsHigh)}`]:[])])row.append(element('td',label));body.append(row);}
  table.append(body);wrapper.append(table);if(!svm||(report.coefficients||[]).length)container.append(wrapper);
  if(forest&&report.permutationImportance){const info=element('p',`${t(report.permutationMetric==='auc'?'Permutation importance (OOB ΔAUC)':'Permutation importance (OOB ΔR²)')} · n=${report.permutationN} · ${t('Repeats')}: ${report.permutationRepeats}`);container.append(info);const table=element('table'),head=element('tr');for(const label of ['Parameter',report.permutationMetric==='auc'?'Permutation importance (OOB ΔAUC)':'Permutation importance (OOB ΔR²)'])head.append(element('th',label===credibleLabel?label:t(label)));table.append(head);for(const c of report.permutationImportance){const row=element('tr');row.append(element('td',regressionParameterName(c.name,parameterLabels)),element('td',number(c.estimate)));table.append(row);}const scroll=element('div');scroll.style.overflowX='auto';scroll.append(table);container.append(scroll);}
  if(svmClassification){const plot=svmDecisionPlot(report.decisionPlot,digits,parameterLabels);if(plot)container.append(plot);}
  if(report.roc){const roc=regressionROC(report,digits);if(roc)container.append(roc);}
  if(report.confusionMatrix){
    for(const [label,classification] of [['Training classification',report],['OOB classification',report.oobClassification]]){
      if(!classification?.confusionMatrix)continue;
      container.append(element('p',`${t(label)} · n=${classification.n} · ${t('Decision threshold')}=${number(classification.threshold)} · ${t('Positive class')}=1`));
      const table=element('table'),head=element('tr');table.setAttribute('aria-label',`${t(label)} · ${t('Confusion matrix')}`);
      for(const text of ['Confusion matrix','Predicted 0','Predicted 1'])head.append(element('th',t(text)));table.append(head);
      for(const [i,counts] of classification.confusionMatrix.entries()){const row=element('tr');row.append(element('th',t(i?'Observed 1':'Observed 0')));for(const count of counts)row.append(element('td',String(count)));table.append(row);}const scroll=element('div');scroll.style.overflowX='auto';scroll.append(table);container.append(scroll);
    }
    const oob=report.oobClassification&&regressionROC(report.oobClassification,digits,{oob:true});if(oob)container.append(oob);
  }
  if(svm){
    if(!svmClassification)for(const item of report.predictionPlots||[]){const plot=svmDecisionPlot(item,digits,parameterLabels);if(plot)container.append(plot);}
    const details=element('details'),table=element('table'),head=element('tr'),rows=report.residuals||[];
    details.append(element('summary',t(svmClassification?'Classification predictions':'Regression predictions')));
    if(!svmClassification)container.append(element('p',t('Prediction error = observed − predicted; MAE is mean absolute prediction error.')));
    const support=rows.some(row=>typeof row.supportVector==='boolean');
    for(const label of [...(svmClassification?['Observation','Observed class','Predicted class','Decision score']:['Observation','Observed value','Predicted value','Prediction error','Absolute error']),...(support?['Support vector']:[])])head.append(element('th',t(label)));
    table.append(head);
    for(const row of rows.slice(0,100)){const tr=element('tr');for(const value of [number(row.row),number(row.observed),number(row.fitted),...(svmClassification?[number(row.decisionScore)]:[number(row.predictionError??row.residual),number(row.absoluteError??Math.abs(Number(row.residual)))]),...(support?[t(row.supportVector?'Yes':'No')]:[])])tr.append(element('td',value));table.append(tr);}
    const scroll=element('div');scroll.style.overflowX='auto';scroll.append(table);details.append(scroll);
    if(rows.length>100)details.append(element('p',t('Showing first 100 rows; export includes all rows.')));
    container.append(details);return;
  }
  const details=element('details'),label=element('summary',t('Residual diagnostics'));details.append(label);
  details.append(element('p',t(report.fitScale==='binomial'||report.model?.startsWith('logistic')?'Deviance residual vs fitted probability.':machineLearning?'Residual vs fitted':'Residual vs fitted; Durbin–Watson uses input row order.')));
  const binomial=report.fitScale==='binomial'||report.model?.startsWith('logistic');
  if(binomial)details.append(element('p',t("Logistic leverage and Cook's D use a one-step GLM approximation.")));
  const rows=report.residuals||[],points=rows.map(r=>[Number(r.fitted),Number(binomial?r.deviance:r.residual),r]).filter(p=>p.slice(0,2).every(Number.isFinite));
  if(points.length){
    const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox','0 0 600 200');svg.setAttribute('role','img');svg.setAttribute('aria-label',t('Residual vs fitted'));svg.style.width='100%';
    const min=Math.min(...points.map(p=>p[0])),max=Math.max(...points.map(p=>p[0])),range=Math.max(...points.map(p=>Math.abs(p[1])))||1;
    const zero=document.createElementNS(ns,'line');for(const [key,v] of Object.entries({x1:30,x2:580,y1:90,y2:90,stroke:'currentColor'}))zero.setAttribute(key,String(v));svg.append(zero);
    for(const [x,y,r] of points){const dot=document.createElementNS(ns,'circle');for(const [key,v] of Object.entries({cx:30+550*(x-min)/(max-min||1),cy:90-75*y/range,r:2.5,fill:Math.abs(Number(r.standardized))>3?'#da5545':'currentColor'}))dot.setAttribute(key,String(v));const title=document.createElementNS(ns,'title');title.textContent=`${r.row}: ${number(binomial?r.deviance:r.residual)}`;dot.append(title);svg.append(dot);}
    const axis=document.createElementNS(ns,'text');axis.setAttribute('x','300');axis.setAttribute('y','195');axis.setAttribute('text-anchor','middle');axis.setAttribute('fill','currentColor');axis.textContent=t('Fitted value');svg.append(axis);details.append(svg);
    appendPlotExportButtons(svg,'symvacas-residuals');
  }
  const residualWrapper=element('div');residualWrapper.style.overflowX='auto';
  const predictive=bayesian&&!binomial;
  const labels=binomial?['Observation','Observed','Fitted value','Residual','Pearson residual','Deviance residual','Leverage',"Cook's D"]:bayesian||machineLearning?['Observation','Observed','Fitted value','Residual']:['Observation','Observed','Fitted value','Residual','Standardized','Leverage',"Cook's D"];
  if(svmClassification)labels.push('Decision score');
  if(predictive)labels.push('Predictive lower','Predictive upper');
  const residualTable=element('table'),residualHead=element('tr');for(const label of labels)residualHead.append(element('th',label===credibleLabel?label:t(label)));residualTable.append(residualHead);
  for(const r of rows.slice(0,100)){const row=element('tr');for(const v of [r.row,r.observed,r.fitted,r.residual,...(binomial?[r.standardized,r.deviance,r.leverage,r.cook]:bayesian||machineLearning?[]:[r.standardized,r.leverage,r.cook]),...(svmClassification?[r.decisionScore]:[]),...(predictive?[r.predictiveLow,r.predictiveHigh]:[])])row.append(element('td',number(v)));residualTable.append(row);}
  residualWrapper.append(residualTable);details.append(residualWrapper);
  if(rows.length>100)details.append(element('p',t('Showing first 100 rows; export includes all rows.')));
  container.append(details);
}

export function regressionResidualCSV(report){
  if(report?.model==='svm'&&report.task==='classification')return ['row,observedClass,predictedClass,decisionScore,supportVector',...(report.residuals||[]).map(row=>[row.row,row.observed,row.fitted,row.decisionScore,row.supportVector??''].join(','))].join('\n');
  if(report?.model==='svm'&&report.task==='regression')return ['row,observed,predicted,predictionError,absoluteError,supportVector',...(report.residuals||[]).map(row=>[row.row,row.observed,row.fitted,row.predictionError??row.residual,row.absoluteError??Math.abs(Number(row.residual)),row.supportVector??''].join(','))].join('\n');
  const keys=['row','observed','fitted','residual','standardized','leverage','cook','deviance',...(report?.scoreType==='decision'?['decisionScore']:[]),...(report?.bayesian&&report.fitScale!=='binomial'?['predictiveLow','predictiveHigh']:[])];
  return [keys.join(','),...(report?.residuals||[]).map(row=>keys.map(key=>row[key]??'').join(','))].join('\n');
}
