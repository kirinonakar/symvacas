import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {csvRows,statisticsImportRows,statisticsPasteText,statisticsDatasetSource,statisticsAddColumn} from '../workspace-commands.js';

const cases=JSON.parse(readFileSync(new URL('../../tests/fixtures/statistics_number_import.json',import.meta.url),'utf8'));
test('adding columns preserves headers, values, missing cells and empty drafts on both platforms',()=>{
  const {cases}=JSON.parse(readFileSync(new URL('../../tests/fixtures/statistics_column_addition.json',import.meta.url),'utf8'));
  for(const item of cases)assert.deepEqual(statisticsAddColumn(item.source,item.columns),{csv:item.csv,kind:item.kind});
  assert.equal(statisticsAddColumn('',99).kind,'columns:100');
  assert.throws(()=>statisticsAddColumn('',100),/Column count/);
});
test('CSV and worksheet rows remove thousands separators while retaining columns, labels and missing cells',()=>{
  for(const item of cases.imports){
    const raw=csvRows(item.source,{skipHeader:false});
    const rows=statisticsImportRows(raw);
    assert.deepEqual(rows,item.expected);
    assert.deepEqual(statisticsImportRows(rows),rows);
    assert.deepEqual(csvRows(item.csv,{skipHeader:false}),rows);
  }
  assert.equal(statisticsDatasetSource('"1,234"\n"5,678"','list'),'[1234,5678]');
});
test('pastes normalize grouped numbers in CSV, Excel TSV, List and Markdown without merging CSV columns',()=>{
  for(const item of cases.pastes)assert.equal(statisticsPasteText(item.source,{singleColumn:item.singleColumn}),item.expected,item.source);
});
