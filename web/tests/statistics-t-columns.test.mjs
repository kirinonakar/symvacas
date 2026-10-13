import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {statisticsGroupedTTestPlan,statisticsCommand,statisticsAnalysisData} from '../workspace-commands.js';
import {statisticsRequest} from '../statistics-request.js';

const {cases}=JSON.parse(readFileSync(new URL('../../tests/fixtures/statistics_t_columns.json',import.meta.url),'utf8'));
test('grouped multi-column t tests share labels, selected-column order, methods, tails and complete pairs',()=>{
  for(const item of cases){
    const plan=statisticsGroupedTTestPlan(item.source,item.settings);
    assert.deepEqual(plan,{source:item.command,termLabels:item.labels},item.name);
    assert.equal(statisticsCommand(item.source,{...item.settings,grouping:'groups'}),item.command);
    const data=statisticsAnalysisData(item.source,{...item.settings,grouping:'groups'});
    assert.equal(data.comparisons.length,item.expected.length);assert.deepEqual(data.termLabels,item.labels);
    const request=statisticsRequest(plan.source);assert.equal(request.tree.args[3].value,'batch');
  }
});
test('one selected value column preserves the detailed single-test path and excluded roles cannot be selected',()=>{
  const item=cases[0],settings={...item.settings,valueColumns:'1'};
  const request=statisticsRequest(statisticsGroupedTTestPlan(item.source,settings).source);
  assert.equal(request.tree.args.length,3);
  for(const valueColumns of ['', '0,1', '1,1','1,5'])assert.throws(()=>statisticsGroupedTTestPlan(item.source,{...settings,valueColumns}));
  const paired=cases[2];assert.throws(()=>statisticsGroupedTTestPlan(paired.source,{...paired.settings,valueColumns:'1,2'}));
});
