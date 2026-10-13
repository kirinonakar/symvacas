import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {statisticsSummaryPlan} from '../workspace-commands.js';
import {statisticsRequest} from '../statistics-request.js';

const {cases}=JSON.parse(readFileSync(new URL('../../tests/fixtures/statistics_summary.json',import.meta.url),'utf8'));
test('summary plans retain numeric summaries and encode literal categories with selected-column labels',()=>{
  for(const item of cases){
    const plan=statisticsSummaryPlan(item.source,item.kind,item.column);
    assert.deepEqual(plan,{source:item.command,termLabels:item.labels});
    assert.equal(statisticsRequest(plan.source).tree.value,'stats');
  }
  assert.throws(()=>statisticsSummaryPlan('""\n""','list'),/at least one/);
});
