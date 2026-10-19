import test from 'node:test';
import assert from 'node:assert/strict';
import {JSDOM} from 'jsdom';
import {statisticsModelDetails} from '../statistics-report-details.js';
import {renderStatisticsReport} from '../statistics-report.js';
import {statisticsResultMarkdown} from '../statistics-markdown.js';
import {readFileSync} from 'node:fs';
import {setLanguage} from '../i18n.js';
import {advancedStatisticsSchema} from '../advanced-statistics-schema.js';
import {statisticsInterpretationSchema} from '../statistics-interpretation-schema.js';
import {statisticsInterpretation,statisticsInterpretationKey} from '../statistics-interpretation.js';
import {renderRegressionReport} from '../regression-report.js';
import {renderSurvivalReport} from '../survival-report.js';

const report=()=>({title:'MANCOVA',analysis:'mancova',sections:[],plots:[],
  details:[{label:'Method',text:'Common slopes.'},{label:'Method',text:'Common slopes.'},
    {label:'Reason',text:'Unavailable.',context:[{label:'Sample',value:'A'}]},
    {label:'Reason',text:'Unavailable.',context:[{label:'Sample',value:'B'}]}],
  assumptions:['Common  slopes.','Independent subjects.','Independent subjects.'],
  notes:['Independent subjects.','Pointwise intervals.']});

test('model descriptions merge assumptions and notes without dropping contextual explanations',()=>{
  const input=report(),snapshot=JSON.stringify(input);
  const paragraphs=statisticsModelDetails(input,'Pointwise intervals.');
  assert.equal(paragraphs.length,5);
  assert.deepEqual(paragraphs,['Method: Common slopes.','Sample: A · Reason: Unavailable.','Sample: B · Reason: Unavailable.','Independent subjects.','Pointwise intervals.']);
  assert.equal(JSON.stringify(input),snapshot,'presentation leaves report data intact');
  const markdown=statisticsResultMarkdown({statisticsReport:input,note:'Pointwise intervals.'});
  assert.equal(markdown.split('### Model details').length-1,1);
  assert.equal(markdown.includes('### Assumptions'),false);
  assert.equal(markdown.split('Independent subjects.').length-1,1);
  assert.equal(markdown.split('Pointwise intervals.').length-1,1);
});

test('rendered report leaves model explanations under the model selector',context=>{
  const dom=new JSDOM('<main><div id="result"></div></main>');
  const previous=globalThis.document;globalThis.document=dom.window.document;
  context.after(()=>{dom.window.close();globalThis.document=previous;});
  const container=document.getElementById('result');
  renderStatisticsReport(container,report());
  const interpretation=container.querySelector('.statistics-interpretation-help');
  assert.equal(container.querySelectorAll('details').length,1);
  assert.equal(interpretation.open,false);
  assert.equal(container.firstElementChild.lastElementChild,interpretation,'interpretation follows every result section and plot');
  interpretation.open=true;
  renderStatisticsReport(container,{...report(),analysis:'ttest',title:'t test'});
  assert.equal(container.querySelector('.statistics-interpretation-help').open,false,'a new result starts collapsed');
  renderStatisticsReport(container,report());
  assert.equal(container.textContent.includes('Common slopes.'),false);
  assert.equal(container.textContent.includes('Independent subjects.'),false);
  assert.equal(container.querySelector('h3').textContent,'MANCOVA');
});

test('interpretation covers all analyses in both languages and distinguishes inference from prediction',()=>{
  assert.deepEqual(statisticsInterpretationSchema,JSON.parse(readFileSync(new URL('../../app/src/main/assets/statistics_interpretation.json',import.meta.url),'utf8')));
  for(const language of ['en','ko']){
    setLanguage(language);
    for(const definition of advancedStatisticsSchema){
      const report={analysis:definition.id};
      assert.notEqual(statisticsInterpretationKey(report),'default',definition.id);
      assert.ok(statisticsInterpretation(report).length>40,definition.id);
    }
  }
  setLanguage('en');
  assert.match(statisticsInterpretation({analysis:'ttest'}),/does not prove equality/);
  assert.match(statisticsInterpretation({analysis:'tost'}),/both one-sided p values/);
  assert.match(statisticsInterpretation({bayesian:true,model:'bayeslinear'},'regression'),/chosen prior/);
  assert.match(statisticsInterpretation({model:'svm'},'regression'),/Cross|cross-validated/);
  assert.equal(statisticsInterpretationKey({fitScale:'binomial'},'regression'),'logistic');
  assert.equal(statisticsInterpretationKey({analysis:'future-method'}),'default');
});

test('regression and survival also end with an initially collapsed interpretation',context=>{
  const dom=new JSDOM('<main><div id="result"></div></main>');
  const previous=globalThis.document;globalThis.document=dom.window.document;
  context.after(()=>{dom.window.close();globalThis.document=previous;setLanguage('en');});
  setLanguage('ko');
  const container=document.getElementById('result');
  const inputs=[
    [renderRegressionReport,{n:3,df:1,coefficients:[],residuals:[]}],
    [renderSurvivalReport,{groups:[{id:0,n:3,events:1,median:null,curve:[[1,3,1,0,2/3,.2,.9]]}]}],
  ];
  for(const [render,input] of inputs){
    const snapshot=JSON.stringify(input);render(container,input);
    const interpretation=container.lastElementChild;
    assert.ok(interpretation.classList.contains('statistics-interpretation-help'));
    assert.equal(interpretation.open,false);
    assert.equal(interpretation.querySelector('summary').textContent,'해석 방법');
    assert.equal(JSON.stringify(input),snapshot,'guidance does not modify computed values');
  }
});
