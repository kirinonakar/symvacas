import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {bootstrapWork,executionTimeoutMillis} from '../execution-budget.js';

const cases=JSON.parse(readFileSync(new URL('../../tests/fixtures/execution_budget.json',import.meta.url),'utf8'));
for(const entry of cases)test(`shared execution budget: ${entry.name}`,()=>{
  assert.deepEqual(bootstrapWork(entry.request),{samples:entry.samples,seconds:entry.seconds});
  assert.equal(executionTimeoutMillis(entry.request),entry.timeoutMillis);
  assert.equal(executionTimeoutMillis({...entry.request,removeComputationLimit:true}),Infinity);
});
