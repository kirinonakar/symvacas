import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {preparationTransform,preparationDataset} from '../statistics-preparation-data.js';
import {statisticsPreparationSchema} from '../statistics-preparation-schema.js';
import {statisticsDataRows,statisticsCsvHasHeader,csvRows} from '../workspace-commands.js';
import {statisticsHeaderKeys,restoreStatisticsHeaderKeys} from '../statistics-headers.js';
import {encodeData,decodeData,mergeData,resetSettingsState} from '../data-transfer.js';

const fixture=JSON.parse(readFileSync(new URL('../../tests/fixtures/statistics_preparation.json',import.meta.url),'utf8'));
test('row filters share Android numeric, text, missingness, AND/OR and original row preservation semantics',()=>{
  const fixture=JSON.parse(readFileSync(new URL('../../tests/fixtures/statistics_row_filter.json',import.meta.url),'utf8'));
  for(const item of fixture.cases){
    const source=fixture[item.source],kind=item.source==='multi'?'xyz':'xy',input=preparationDataset(source,kind);
    const result=preparationTransform(source,kind,'filter',{match:item.match,conditions:JSON.stringify(item.conditions)});
    assert.deepEqual(result.headers,input.headers);assert.deepEqual(result.rows,item.rows.map(i=>input.rows[i]));
    assert.equal(result.changed,input.rows.length-item.rows.length);assert.equal(result.omitted,0);
    if(result.rows.length)assert.deepEqual(preparationDataset(result.csv,result.kind),{headers:result.headers,rows:result.rows});
  }
  for(const item of fixture.invalid)assert.throws(()=>preparationTransform(fixture.numeric,'xy','filter',item),error=>error.message===item.error);
});
test('wide/long, recoding and row formulas share Android reference rows, labels, missingness and boundary semantics',()=>{
  for(const item of fixture.cases){
    const result=preparationTransform(item.source,item.kind,item.id,item.settings);
    assert.deepEqual(result.headers,item.headers);assert.equal(result.changed,item.changed);assert.equal(result.omitted,item.omitted);assert.equal(result.rows.length,item.rows.length);
    item.rows.forEach((row,i)=>row.forEach((cell,j)=>{
      if(item.numericColumns?.includes(j)&&cell!=='')assert.ok(Math.abs(Number(result.rows[i][j])-Number(cell))<=1e-12*Math.max(1,Math.abs(Number(cell))));
      else assert.equal(result.rows[i][j],cell);
    }));
    assert.deepEqual(preparationDataset(result.csv,result.kind).headers,item.headers);
    assert.deepEqual(preparationDataset(result.csv,result.kind).rows,result.rows);
  }
});
test('invalid roles, duplicate pairs, mappings and unsafe or undefined formulas fail before data can be replaced',()=>{
  for(const item of fixture.invalid)assert.throws(()=>preparationTransform(item.source,item.kind,item.id,item.settings),error=>error.message===item.error);
});
test('wide to long to wide roundtrip retains precision, quoted IDs and blank measurements',()=>{
  const original='ID,before,after\n"A,B",1.2000,\nC,2,4';
  const long=preparationTransform(original,'xyz','wideToLong'),wide=preparationTransform(long.csv,long.kind,'longToWide');
  assert.equal(wide.csv,original);
});
test('all-text recoded headers survive stored settings and editing rather than becoming observations',()=>{
  const result=preparationTransform('Gender\n1\n2','list','recode',{rules:'1, male\n2, female',output:'replace',header:'Sex'});
  const saved=statisticsHeaderKeys();restoreStatisticsHeaderKeys([]);
  assert.equal(statisticsCsvHasHeader(csvRows(result.csv,{skipHeader:false})),false);
  restoreStatisticsHeaderKeys(saved);
  assert.ok(saved.includes('4021414396:2881141766:3'),'header identity uses the same stable encoding on Android and Web');
  assert.deepEqual(statisticsDataRows(result.csv,'list'),[['male'],['female']]);
  const state={variables:{},functions:{},assumptions:{},datasets:{D1:result.csv},datasetKinds:{D1:'list'},fields:{}};
  const portable=decodeData(encodeData(state));restoreStatisticsHeaderKeys([]);
  mergeData(state,portable);assert.deepEqual(statisticsDataRows(result.csv,'list'),[['male'],['female']]);
  assert.ok(resetSettingsState(state).statisticsHeaderKeys.includes('4021414396:2881141766:3'));
});
