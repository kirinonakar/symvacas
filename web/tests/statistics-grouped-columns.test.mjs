import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {statisticsGroupedTestPlan,statisticsCommand,statisticsAnalysisData} from '../workspace-commands.js';
import {statisticsRequest} from '../statistics-request.js';

const {cases}=JSON.parse(readFileSync(new URL('../../tests/fixtures/statistics_grouped_columns.json',import.meta.url),'utf8'));
test('categorical, rank, ANOVA and z grouped column plans share Android data and labels',()=>{
  for(const item of cases){
    const plan=statisticsGroupedTestPlan(item.source,item.settings);
    assert.deepEqual(plan,{source:item.command,termLabels:item.labels},item.name);
    assert.equal(statisticsCommand(item.source,{...item.settings,grouping:'groups'}),item.command);
    assert.deepEqual(statisticsAnalysisData(item.source,{...item.settings,grouping:'groups'}).termLabels,item.labels);
    assert.ok(statisticsRequest(plan.source).tree.args.some(node=>node.value==='batch'));
  }
});
