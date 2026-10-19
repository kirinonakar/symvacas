import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {JSDOM} from 'jsdom';
import {advancedStatisticsSchema as schema} from '../advanced-statistics-schema.js';
import {advancedStatisticsReservedColumns,createAdvancedStatistics} from '../advanced-statistics.js';
import {socialStatisticsPlan} from '../statistics-social-forms.js';
const definition=id=>schema.find(d=>d.id===id);

test('MANCOVA preserves selected covariate/response order and encodes text groups',()=>{
  const rows=[['A','2','9','7','3'],['B','4','8','6','5'],['A','6','7','5','8']];
  const opts={group:'0',covariates:'4,1',responses:'3,2',level:'0.9',slopes:'test'};
  const plan=socialStatisticsPlan('mancova',rows,opts,['Treatment','Age','Speed','Score','Baseline']);
  assert.equal(plan.expression,'mancova([[1,3,2,7,9],[2,5,4,6,8],[1,8,6,5,7]],2,0.9,1)');
  assert.deepEqual(plan.labels,{Group:'Treatment','group:1':'A','group:2':'B',x1:'Baseline',x2:'Age','response:1':'Score','response:2':'Speed'});
  assert.throws(()=>socialStatisticsPlan('mancova',rows,{...opts,responses:'1,2'}),/distinct/);
  assert.throws(()=>socialStatisticsPlan('mancova',rows,{...opts,responses:'2'}),/two responses/);
  assert.throws(()=>socialStatisticsPlan('mancova',[['A','','9','7','3']],opts),/Complete/);
  const d=definition('mancova');assert.equal(d.section,'tests');
  assert.deepEqual(advancedStatisticsReservedColumns(d,{},'responses',4),[0,1]);
  assert.deepEqual(advancedStatisticsReservedColumns(d,opts,'responses',5),[0,4,1]);
  assert.deepEqual(advancedStatisticsReservedColumns(d,{},'covariates',4),[0]);
});

test('MANCOVA production form excludes covariates from response checkboxes',context=>{
  const dom=new JSDOM(readFileSync(new URL('../index.html',import.meta.url),'utf8'));
  const previous=globalThis.document;globalThis.document=dom.window.document;
  context.after(()=>{dom.window.close();globalThis.document=previous;});
  const state={fields:{'statistics-tests-kind':'mancova'},datasets:{}};
  const api=createAdvancedStatistics({state,persist:()=>{},data:()=> 'A,1,3,7\nA,2,5,6\nB,3,6,9\nB,4,8,7',columnLimit:()=>4,section:'tests'});
  assert.ok(api);
  const response=document.getElementById('statistics-form-mancova-responses');
  assert.ok(response);
  assert.deepEqual([...response.parentElement.querySelectorAll('input[type="checkbox"]')].map(input=>input.dataset.column),['2','3']);
});

test('post-hoc forms preserve unequal sample sizes, control identity and group labels',()=>{
  const rows=[['1','3','6'],['2','4','8'],['','5','9']];
  const base={grouping:'columns',columns:'2,0,1',control:'2',adjustment:'holm'};
  const nested='[[6,8,9],[1,2],[3,4,5]]';
  for(const id of ['scheffe','dunnett','conover']){
    const d=definition(id);assert.equal(d.section,'tests');
    const plan=socialStatisticsPlan(id,rows,base,['Placebo','Low','High']);
    assert.equal(plan.expression,`${id}(${nested}${id==='dunnett'?',2':id==='conover'?',holm':''})`);
    assert.deepEqual(plan.labels,{'sample:1':'High','sample:2':'Placebo','sample:3':'Low'});
  }
  const long=[['Placebo','1'],['High','6'],['Placebo','2'],['High','8']];
  assert.equal(socialStatisticsPlan('dunnett',long,{grouping:'groups',group:'0',value:'1',control:'2'}).expression,'dunnett([[1,2],[6,8]],2)');
  assert.throws(()=>socialStatisticsPlan('dunnett',rows,{...base,control:'4'}),/control/);
});

test('Huber, moderator and AFT checkbox roles match the analysis input contract',()=>{
  const reserved=(id,settings,count)=>advancedStatisticsReservedColumns(definition(id),settings,'predictors',count);
  assert.deepEqual(reserved('robustreg',{},3),[2]);
  assert.deepEqual(reserved('robustreg',{response:'0'},3),[0]);
  assert.deepEqual(reserved('metaregression',{},3),[0,1]);
  assert.deepEqual(reserved('metaregression',{layout:'binary'},5),[0,1,2,3]);
  assert.deepEqual(reserved('metaregression',{layout:'continuous'},7),[0,1,2,3,4,5]);
  for(const id of ['parametricsurvival','cox']){
    assert.deepEqual(reserved(id,{},4),[0,1]);
    assert.deepEqual(reserved(id,{truncation:'entry',entry:'2'},4),[0,1,2]);
  }
});

test('opening the production Huber form shows only eligible predictor checkboxes',context=>{
  const dom=new JSDOM(readFileSync(new URL('../index.html',import.meta.url),'utf8'));
  const previous=globalThis.document;globalThis.document=dom.window.document;
  context.after(()=>{dom.window.close();globalThis.document=previous;});
  const state={fields:{'statistics-models-kind':'robustreg'},datasets:{}};
  createAdvancedStatistics({state,persist:()=>{},data:()=> '1,2,3\n2,3,4\n3,4,5',columnLimit:()=>3,section:'models'});
  const columns=()=>[...document.querySelectorAll('#statistics-models-controls input[type="checkbox"]')].map(input=>input.dataset.column);
  assert.deepEqual(columns(),['0','1']);
  const response=document.getElementById('statistics-form-robustreg-response');response.value='0';response.dispatchEvent(new dom.window.Event('change'));
  assert.deepEqual(columns(),['1','2']);
});
