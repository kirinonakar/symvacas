import test from 'node:test';
import assert from 'node:assert/strict';
import {createAppState} from '../app-state.js';

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
