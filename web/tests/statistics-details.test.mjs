import test from 'node:test';
import assert from 'node:assert/strict';
import {JSDOM} from 'jsdom';
import {statisticsModelDetails} from '../statistics-report-details.js';
import {renderStatisticsReport} from '../statistics-report.js';
import {statisticsResultMarkdown} from '../statistics-markdown.js';

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
  assert.equal(container.querySelectorAll('details').length,0);
  assert.equal(container.textContent.includes('Common slopes.'),false);
  assert.equal(container.textContent.includes('Independent subjects.'),false);
  assert.equal(container.querySelector('h3').textContent,'MANCOVA');
});
