import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {bootstrapWork,executionTimeoutMillis} from '../execution-budget.js';

test('Android, Web and Python share workload budgets for literal and saved bootstrap counts',()=>{
  const cases=JSON.parse(readFileSync(new URL('../../tests/fixtures/execution_budget.json',import.meta.url),'utf8'));
  for(const item of cases){assert.equal(executionTimeoutMillis(item.request),item.timeoutMillis,item.name);assert.equal(bootstrapWork(item.request).samples,item.samples,item.name);}
  assert.equal(executionTimeoutMillis({...cases[2].request,removeComputationLimit:true}),Infinity);
});
