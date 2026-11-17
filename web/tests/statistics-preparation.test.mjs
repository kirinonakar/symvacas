import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {preparationTransform,preparationDataset} from '../statistics-preparation-data.js';

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
const tableFixture=JSON.parse(readFileSync(new URL('../../tests/fixtures/statistics_table_preparation.json',import.meta.url),'utf8'));
function transformTable(item){
  const source=tableFixture.sources[item.source],other=tableFixture.sources[item.other];
  return preparationTransform(source.csv,source.kind,item.id,item.settings,other);
}
test('deletion and row/column alignment match Android, including ragged and quoted CSV data',()=>{
  for(const item of tableFixture.cases){
    const result=transformTable(item);
    assert.deepEqual(result.headers,item.headers);
    assert.deepEqual(result.rows,item.rows);
    assert.equal(result.changed,item.changed);
    assert.deepEqual(preparationDataset(result.csv,result.kind),{headers:result.headers,rows:result.rows});
  }
});
