import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {statisticsSummaryPlan,statisticsOverallPlan} from '../workspace-commands.js';
import {statisticsRequest} from '../statistics-request.js';

const {cases,overallCases}=JSON.parse(readFileSync(new URL('../../tests/fixtures/statistics_summary.json',import.meta.url),'utf8'));
test('summary plans retain numeric summaries and encode literal categories with selected-column labels',()=>{
  for(const item of cases){
    const plan=statisticsSummaryPlan(item.source,item.kind,item.column);
    assert.deepEqual(plan,{source:item.command,termLabels:item.labels});
    assert.equal(statisticsRequest(plan.source).tree.value,'stats');
  }
  assert.throws(()=>statisticsSummaryPlan('""\n""','list'),/at least one/);
});
test('Overall sends every column with independent valid values and literal category labels',()=>{
  for(const item of overallCases){
    const plan=statisticsOverallPlan(item.source,item.kind);
    assert.deepEqual(plan,{source:item.command,termLabels:item.labels});
    const request=statisticsRequest(plan.source);
    assert.equal(request.tree.value,'stats');
    assert.equal(request.tree.args[1].value,'overall');
  }
  assert.throws(()=>statisticsOverallPlan('""\n""','list'),/at least one/);
});
