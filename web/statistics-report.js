import {advancedStatisticsSchema} from './advanced-statistics-schema.js';
import {element,control} from './app-ui.js';
import {t,setText} from './i18n.js';
import {resultDisplayTree,resultMathDisplay} from './result-display.js';
import {renderStatisticsVisualizations} from './statistics-visualization.js';
import {appendStatisticsModelWorkflow} from './statistics-model-workflow.js';
import {statisticsDetailText} from './statistics-report-details.js';

const basicAnalyses=new Set('mean median variance stdev mode skewness kurtosis sumdata quartiles stats covariance correlation ttest ttest2 ttestpaired ztest ztest2 chi2test chi2independence fisherexact anova welchanova tukey gameshowell shapiro normaltest wilcoxon mannwhitney kruskal tinterval zinterval'.split(' '));
export function statisticsReportTarget(result,source='',requested=''){
  if(!result?.statisticsReport)return '';
  if(['statistics-summary-result','statistics-analysis-result','statistics-advanced-result','statistics-tests-result','statistics-general-result','statistics-models-result','statistics-preparation-result'].includes(requested))return requested;
  const analysis=result.statisticsReport.analysis||source.split('(')[0].trim();
  const definition=advancedStatisticsSchema.find(item=>item.id===analysis);
  return !definition&&basicAnalyses.has(analysis)?'statistics-analysis-result':`statistics-${definition?.section||'advanced'}-result`;
}

export function renderStatisticsReport(container,report,{digits=10,onCopy,onClear,onModelWorkflow,isBusy,...options}={}){
  options.preserveSmallValues=true;
  container.replaceChildren();
  const panel=element('div','','statistics-result-report');
  const heading=element('div','','statistics-result-heading');heading.append(element('h3',t(report.title)));
  if(onCopy)heading.append(control('Copy',onCopy));
  if(onClear)heading.append(control('Clear',onClear));panel.append(heading);
  if(report.context){const context=element('p','','statistics-interpretation');context.textContent=report.context;context.setAttribute('translate','no');panel.append(context);}
  for(const warning of report.warnings||[]){const note=element('p','','statistics-warning');note.textContent=(warning.label?warning.label+': ':'')+t(warning.text||warning);note.setAttribute('role','status');panel.append(note);}
  appendStatisticsModelWorkflow(panel,report.modelWorkflow,onModelWorkflow,{isBusy});
  if(report.highlights?.length){
    const cards=element('div','','statistics-highlights');
    for(const item of report.highlights){const card=element('div','','statistics-highlight');card.append(element('span',t(item.label)),resultMathDisplay(resultDisplayTree(item.value,{decimal:true,mixed:false}),digits,true,options));cards.append(card);}
    panel.append(cards);
  }
  if(report.notes?.length){const notes=element('details','','statistics-result-details');notes.append(element('summary',t('Interpretation & assumptions')));for(const note of report.notes)notes.append(element('p',t(note),'statistics-interpretation'));panel.append(notes);}
  const variablesFirst=report.analysis==='stats'&&report.title!=='Overall';
  const primary=['Summary','ANOVA','Overall model','Overall ANOVA','Overall Welch ANOVA',report.title,...(report.title==='Overall'?['Numeric data','Categorical data']:[]),...(variablesFirst?['Analyzed variables']:[])];
  const prominent=section=>primary.includes(section.title)||['Model diagnostics','Indicator R²','Explained variance','Latent R²','Summary','Sample summaries','Condition summaries','Contrast summaries','Assumption checks','Effect size','Mean confidence interval (95%, two-sided)','Overall ANOVA','Expected-count diagnostics'].includes(section.title);
  const rank=section=>variablesFirst&&section.title==='Analyzed variables'?-1:Number(!primary.includes(section.title));
  const sections=[...report.sections.filter(prominent).sort((a,b)=>rank(a)-rank(b)),...report.sections.filter(section=>!prominent(section))];
  let plotsShown=false;
  const contingencyGroups=new Map();
  for(const section of sections){
    if(!prominent(section)&&!plotsShown){renderStatisticsVisualizations(panel,report.plots);plotsShown=true;}
    let target=panel;
    if(section.contingencyGroup){
      if(!contingencyGroups.has(section.contingencyGroup)){
        const group=element('details','','statistics-result-details statistics-contingency-group'),heading=element('summary');
        heading.textContent=(section.contingencyLabel?section.contingencyLabel+' · ':'')+t(section.contingencyTitle||'Contingency table');
        group.open=section.contingencyExpanded!==false;group.append(heading);panel.append(group);contingencyGroups.set(section.contingencyGroup,group);
      }
      target=contingencyGroups.get(section.contingencyGroup);
    }
    const collapsible=section.totalRows>12&&!prominent(section)&&!section.contingencyGroup,block=element(collapsible?'details':'section');
    if(collapsible){block.className='statistics-result-details';block.append(element('summary',`${t(section.title)} (${section.totalRows})`));}
    const scroll=element('div','','statistics-result-scroll');
    scroll.tabIndex=0;scroll.setAttribute('role','region');scroll.setAttribute('aria-label',t(section.title));
    const table=element('table');
    table.append(element('caption',t(section.title)));
    const head=element('thead'),header=element('tr');
    for(const label of section.columns){const th=element('th');if(section.literalColumns){th.textContent=label;th.setAttribute('translate','no');}else setText(th,label);th.scope='col';header.append(th);}
    head.append(header);table.append(head);
    const body=element('tbody');
    for(const [rowIndex,values] of section.rows.entries()){
      const row=element('tr');
      for(const [index,value] of values.entries()){
        const td=element('td');
        if(section.literalColumns)td.setAttribute('translate','no');
        if(value&&typeof value==='object')td.append(resultMathDisplay(resultDisplayTree(value,{decimal:true,mixed:false}),digits,true,options));
        else td.textContent=index===0&&rowIndex===section.totalRow||['Metric','Check','Interpretation','Sample','Role','R²','Kind','Effect','Intercept / drift','Status'].includes(section.columns[index])||section.columns[index]==='Parameter'&&['arima','sarima'].includes(report.analysis)||section.columns[index]==='Value'&&['Intercept / drift','Fit status'].includes(values[0])?t(String(value)):String(value);
        row.append(td);
      }
      body.append(row);
    }
    table.append(body);scroll.append(table);block.append(scroll);
    if(section.totalRows>section.rows.length)block.append(element('p',`${section.rows.length} / ${section.totalRows} · ${t('Copy result includes all rows.')}`,'hint'));
    target.append(block);
  }
  if(!plotsShown)renderStatisticsVisualizations(panel,report.plots);
  if(report.details?.length){
    const block=element('details','','statistics-result-details');
    block.append(element('summary',t('Model details')));
    for(const detail of report.details)block.append(element('p',statisticsDetailText(detail),'statistics-interpretation'));
    panel.append(block);
  }
  if(report.assumptions?.length){
    const block=element('details','','statistics-assumptions statistics-result-details');
    block.append(element('summary',t('Assumptions')));
    for(const assumption of report.assumptions)block.append(element('p',t(assumption),'statistics-interpretation'));
    panel.append(block);
  }
  container.append(panel);
}
