import test from 'node:test';
import assert from 'node:assert/strict';
import {statisticsInput,datasetInput} from '../frontend/headless-requests.js';

test('statistics keeps large and exact datasets separate from expression AST',()=>{
  const values=Array.from({length:3000},(_,i)=>String(i+1));
  const large=statisticsInput({expression:`mean([${values.join(',')}])`});
  assert.equal(large.tree.value,'mean');
  assert.equal(Object.values(large.statisticsDatasets)[0].length,3000);
  const data=statisticsInput({expression:'ttest2(0,a,b)',datasets:{a:['0.10000000000000000001','1/3'],b:[2,3]}});
  assert.equal(data.statisticsDatasets.a[0],'0.10000000000000000001');
  assert.equal(data.statisticsDatasets.a[1].kind,'binary');
  assert.deepEqual(data.statisticsDatasets.b,['2','3']);
  assert.throws(()=>statisticsInput({expression:'mean(a)',datasets:{a:[{}]}}),/Dataset/);
});

test('dataset import supports JSON tables, CSV headers and exact strings',()=>{
  assert.deepEqual(datasetInput({data:[1,'0.00000000000000000001',3]}),{source:'1\n0.00000000000000000001\n3',kind:'list'});
  assert.equal(datasetInput({csv:'x,y\n1,2\n3,4'}).kind,'xy');
  assert.equal(datasetInput({data:[[1,2,3,4],[5,6,7,8]]}).kind,'columns:4');
  assert.throws(()=>datasetInput({data:[[1,2],[3]]}),/equal/);
  assert.throws(()=>datasetInput({data:[1],csv:'1'}),/either/);
});
