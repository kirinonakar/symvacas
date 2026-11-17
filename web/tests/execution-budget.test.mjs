import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {bootstrapWork,executionTimeoutMillis} from '../execution-budget.js';

const cases=JSON.parse(readFileSync(new URL('../../tests/fixtures/execution_budget.json',import.meta.url),'utf8'));
test('execution budgets match the shared Android and Python cases',()=>{
  for(const entry of cases){
    assert.deepEqual(bootstrapWork(entry.request),{samples:entry.samples,seconds:entry.seconds},entry.name);
    assert.equal(executionTimeoutMillis(entry.request),entry.timeoutMillis,entry.name);
    assert.equal(executionTimeoutMillis({...entry.request,removeComputationLimit:true}),Infinity,entry.name);
  }
});
