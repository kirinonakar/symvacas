import test from 'node:test';
import assert from 'node:assert/strict';
import {createAppState,restoreFields,createPersistence} from '../app-state.js';
import {readState} from '../storage.js';
import {readFileSync} from 'node:fs';

test('legacy statistics records never restore into calculator history, even with large datasets',()=>{
  const source=`regression([${'1,2,'.repeat(40000)}1,2],linear)`;
  const mathematical={source:'2+2',exact:'4',mode:'scientific'};
  const explicitlyTyped={source:'mean([1,2])',mode:'scientific'};
  const legacyMath={source:'sin(pi/2)',exact:'1'};
  const saved={fields:{expression:'2+2'},history:[
    {source,mode:'statistics'},...Array.from({length:501},()=>({source})),
    {source:'ttest(0,[1,2,3])',star:true},mathematical,explicitlyTyped,legacyMath
  ]};
  const state=createAppState(saved);
  assert.deepEqual(state.history,[mathematical,explicitlyTyped,legacyMath]);
  assert.equal(state.fields.expression,'2+2');
  assert.equal(saved.history.length,506,'migration does not mutate the supplied snapshot');
});


test('saved state rejects malformed collections and bounds preferences and retained entries',()=>{
  const state=createAppState({variables:[],functions:null,datasets:'invalid',datasetKinds:[],fields:[],matrixCells:null,rates:[],assumptions:'invalid',history:'invalid',favorites:{},recent:null,precision:999,digits:999,inputFont:1,outputFont:999,theme:'invalid',resultDisplayMode:'invalid'},'ko-KR');
  for(const key of ['variables','functions','datasets','datasetKinds','fields','matrixCells','rates','assumptions'])assert.deepEqual(state[key],{});
  for(const key of ['history','favorites','recent'])assert.deepEqual(state[key],[]);
  assert.equal(state.precision,200);assert.equal(state.digits,200);
  assert.equal(state.inputFont,10);assert.equal(state.outputFont,48);
  assert.equal(state.theme,'system');assert.equal(state.resultDisplayMode,'off');
  assert.equal(state.language,'ko');assert.equal(state.autoCloseBrackets,true);
  const saved={precision:8,digits:20,history:Array.from({length:501},(_,time)=>({time})),displayShortcuts:Array.from({length:13},(_,label)=>({label}))};
  const bounded=createAppState(saved);
  assert.equal(bounded.digits,8);assert.equal(bounded.history.length,500);assert.equal(bounded.displayShortcuts.length,6);
  assert.equal(saved.history.length,501,'normalization does not truncate the source backup');
});
