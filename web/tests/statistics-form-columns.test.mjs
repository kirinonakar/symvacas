import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {JSDOM} from 'jsdom';
import {advancedStatisticsSchema as schema} from '../advanced-statistics-schema.js';
import {advancedStatisticsReservedColumns,createAdvancedStatistics} from '../advanced-statistics.js';
const definition=id=>schema.find(d=>d.id===id);

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
