import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {JSDOM} from 'jsdom';
import {advancedStatisticsSchema as schema} from '../advanced-statistics-schema.js';
import {advancedStatisticsExampleRows,guidedStatisticsCommand,createAdvancedStatistics} from '../advanced-statistics.js';
import {modelComparisonPlan} from '../model-comparison.js';
import {parse} from '../parser.js';
import {statisticsRequest} from '../statistics-request.js';
const definition=schema.find(item=>item.id==='modelcompare');
const defaults=Object.fromEntries(definition.controls.map(field=>[field.key,field.default]));

test('common row union, header-aligned validation and separate candidates retain original labels',()=>{
  const rows=[['1','2','0'],['3','','1'],['4','5','1']],opts={...defaults,candidates:'1',validation:'external',resamples:'0'};
  const plan=modelComparisonPlan(rows,opts,['age (x)','biomarker (y)','event (z)'],[['0','6','7'],['1','8','9']],['event (x)','biomarker (y)','age (z)']);
  assert.equal(plan.expression,'modelcompare([[1,2,0],[4,5,1]],1,linear,external,[[7,6,0],[9,8,1]],0.95,0,0,[[excludedrows,1],[excludedvalidation,0]],1)');
  assert.equal(plan.labels['candidate:1'],'biomarker (y)');assert.equal(plan.labels['model:A'],'age (x)');
  assert.throws(()=>modelComparisonPlan(rows,{...opts,addedPredictors:'0'},[],rows),/distinct baseline/);
});

test('all family examples generate numeric data and preserve a common measurement model',()=>{
  for(const family of Object.keys(definition.exampleRowsByFamily)){
    const opts={family,resamples:'0',validation:'apparent',basePredictors:family==='cox'?'2':['lmm','glmm','gee'].includes(family)?'1':'0',responsefamily:family==='gee'?'gaussian':'binomial'};
    const expression=guidedStatisticsCommand(definition,advancedStatisticsExampleRows(definition,opts),opts);
    const tree=statisticsRequest(expression).tree;assert.equal(tree.value,'modelcompare');assert.equal(tree.args[2].value,family);
  }
});

test('production form switches families, uses family examples, reserves roles and retains focused formulas',context=>{
  const dom=new JSDOM(readFileSync(new URL('../index.html',import.meta.url),'utf8'));
  const previous=globalThis.document;globalThis.document=dom.window.document;
  context.after(()=>{dom.window.close();globalThis.document=previous;});
  const state={fields:{'statistics-models-kind':'modelcompare','statistics-models-input':'example','statistics-form-modelcompare-resamples':'0'},datasets:{}};
  const tools=createAdvancedStatistics({state,persist:()=>{},data:()=>'',columnLimit:()=>3,section:'models'});
  assert.ok(!Array.from(document.getElementById('statistics-models-kind').options).some(option=>option.value==='logisticcompare'));
  for(const family of ['cox','lmm','cfa','mlclassification','linear']){
    const control=document.getElementById('statistics-form-modelcompare-family');control.value=family;control.onchange();
    assert.equal(statisticsRequest(tools.expression()).tree.args[2].value,family);
    if(family==='cox')assert.deepEqual(Array.from(document.querySelectorAll('#statistics-form-modelcompare-basePredictors ~ label input')).map(input=>input.dataset.column),['2','3']);
  }
  const control=document.getElementById('statistics-form-modelcompare-family');control.value='cfa';control.onchange();
  const residual=document.getElementById('statistics-form-modelcompare-addedresidual');residual.focus();residual.value='2,3;5,6';residual.oninput();
  assert.equal(document.getElementById(residual.id),residual);assert.equal(document.activeElement,residual);
  assert.ok(tools.expression().includes('[addedresidual,[[2,3],[5,6]]]'));
});
