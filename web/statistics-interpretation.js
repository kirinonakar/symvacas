import {element} from './app-ui.js';
import {getLanguage} from './i18n.js';
import {statisticsInterpretationSchema as schema} from './statistics-interpretation-schema.js';

export function statisticsInterpretationKey(report,kind='statistics'){
  if(kind==='survival')return 'survival';
  if(kind==='regression'){
    if(report.bayesian)return 'bayesian';
    if(report.model)return 'prediction';
    return report.fitScale==='binomial'?'logistic':'regression';
  }
  return schema.analyses[report.analysis]||'default';
}

export function statisticsInterpretation(report,kind='statistics'){
  return schema.guides[statisticsInterpretationKey(report,kind)][getLanguage()==='ko'?'ko':'en'];
}

export function appendStatisticsInterpretation(container,report,kind='statistics'){
  const disclosure=element('details','','statistics-result-details statistics-interpretation-help');
  disclosure.append(element('summary',getLanguage()==='ko'?'해석 방법':'How to interpret'));
  for(const paragraph of statisticsInterpretation(report,kind).split('\n\n'))disclosure.append(element('p',paragraph,'hint'));
  container.append(disclosure);
}
