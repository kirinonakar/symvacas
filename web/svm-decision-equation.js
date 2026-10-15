import {element} from './app-ui.js';
import {t} from './i18n.js';
import {roundNumber} from './display-format.js';
import {expressionDisplay} from './expression-display.js';

export function svmDecisionEquation(report,digits=10,labels={}){
  const equation=report.decisionEquation;if(!equation)return null;
  const box=element('section');box.setAttribute('data-svm-decision-equation','true');
  const number=v=>roundNumber(String(v),digits,true);
  box.append(element('h4',t('Decision function')));
  const line=element('div','f(x) = ');line.style.overflowX='auto';
  if(equation.expression){try{line.append(expressionDisplay(equation.expression,{digits,roundNumbers:true,preserveSmallValues:true}));}catch{line.append(equation.expression);}}
  else line.textContent=equation.formula;
  box.append(line,element('p',t('f(x) >= 0: class 1; f(x) < 0: class 0.')));
  box.append(element('p',equation.variables.map((name,i)=>`${name} = ${labels[`b${i+1}`]||name}`).join(' · ')));
  if(report.kernel==='rbf'){
    box.append(element('p',`b=${number(equation.intercept)} · γ=${number(report.gamma)} · `+equation.scales.map((scale,i)=>`s${i+1}=${number(scale)}`).join(' · ')));
    box.append(element('p',t('aᵢ = αᵢyᵢ, αᵢ ≥ 0; yᵢ = −1 for class 0, +1 for class 1.')));
    const details=element('details'),table=element('table'),head=element('tr');
    details.append(element('summary',t('Support vector terms')));
    for(const label of ['Observation','Signed coefficient (αᵢyᵢ)',...equation.variables.map((_,i)=>`vᵢ${i+1}`)])head.append(element('th',t(label)));table.append(head);
    for(const term of equation.supportTerms.slice(0,100)){const row=element('tr');for(const value of [term.row,term.coefficient,...term.coordinates])row.append(element('td',number(value)));table.append(row);}
    const scroll=element('div');scroll.style.overflowX='auto';scroll.append(table);details.append(scroll);
    if(equation.supportTerms.length>100)details.append(element('p',t('Showing first 100 rows; export includes all rows.')));
    box.append(details);
  }
  return box;
}
