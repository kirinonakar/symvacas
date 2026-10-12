import test from 'node:test';
import assert from 'node:assert/strict';
import {parse} from '../parser.js';
import {statisticsRequest} from '../statistics-request.js';

test('large tables become small expressions with exact decimal dataset references',()=>{
  const source=`mixedmodel([${Array.from({length:5000},(_,i)=>`[${i%20},-1.25e-3,${i}]`).join(',')}],0)`;
  assert.throws(()=>parse(source),/8192/);
  const request=statisticsRequest(source),name=request.tree.args[0].value;
  assert.equal(request.tree.args[0].kind,'symbol');
  assert.equal(request.statisticsDatasets[name].length,5000);
  assert.deepEqual(request.statisticsDatasets[name][0],['0','-1.25e-3','0']);
  assert.ok(JSON.stringify(request.tree).length<500);
});

test('lists with formulas use normal parsing and references avoid existing names',()=>{
  const request=statisticsRequest('regression([[1,2],[3,4]],custom,SymvaStatisticsData0*x,x,[1])');
  assert.equal(request.tree.args[0].value,'SymvaStatisticsData0Data');
  assert.deepEqual(statisticsRequest('mean([1/2,2+3])').tree,parse('mean([1/2,2+3])'));
  assert.throws(()=>statisticsRequest('mean([1,,2])'));
  assert.throws(()=>statisticsRequest('mean([1,2]'));
});

test('large comparison data does not turn nested measurement parameter lists into datasets',()=>{
  const data=Array.from({length:1200},(_,i)=>`[${i},1.25,2.5]`).join(',');
  const request=statisticsRequest(`modelcompare([${data}],0,cfa,fit,0,0.95,0,0,[[factors,[1,1,1]],[addedresidual,[[2,3]]]],0)`);
  assert.equal(request.statisticsDatasets[request.tree.args[0].value].length,1200);
  assert.equal(request.tree.args[8].args[0].args[0].value,'factors');
  assert.equal(request.tree.args[8].args[0].args[1].args.length,3);
});

test('large mixed datasets isolate missing tokens and formula cells without lifting formula limits',()=>{
  const rows=Array.from({length:5000},(_,i)=>`[${i},${i===2?'NA':i===3?'sqrt(4)':'1/2'}]`),source=`impute([${rows.join(',')}],mean)`;
  const request=statisticsRequest(source),data=request.statisticsDatasets[request.tree.args[0].value];
  assert.equal(data.length,5000);assert.equal(data[2][1].kind,'symbol');assert.equal(data[2][1].value,'NA');
  assert.equal(data[3][1].kind,'call');assert.equal(data[0][1].value,'/');
  assert.ok(JSON.stringify(request.tree).length<600);
  assert.throws(()=>statisticsRequest(`mean([${'1+'.repeat(5000)}1])`),/8192/);
  assert.throws(()=>statisticsRequest(`impute([${rows.join(',')},[1,]],mean)`));
});
