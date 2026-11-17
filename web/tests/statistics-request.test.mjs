import test from 'node:test';
import assert from 'node:assert/strict';
import {parse} from '../parser.js';
import {statisticsRequest} from '../statistics-request.js';
import {savedStatisticsDatasets} from '../statistics-bindings.js';

test('saved dataset references keep exact cells, table shapes and updated values',()=>{
  const state={datasets:{D1:'value\n0.1\n\n0.2\n1/2',D2:'x,y\n1,2\n3,4',Unused:'bad('},datasetKinds:{D1:'list',D2:'xy'}};
  const bindings=source=>savedStatisticsDatasets(parse(source),state);
  const data=bindings('sumdata(D1)').D1;
  assert.equal(data[0].value,'0.1');assert.equal(data[2].value,'/');
  assert.deepEqual(bindings('regression(D2,linear)'),{D2:[['1','2'],['3','4']]});
  state.datasets.D1=Array.from({length:5000},(_,i)=>String(i+1)).join('\n');
  assert.equal(bindings('mean(D1)').D1.length,5000);
  assert.deepEqual(bindings('2+3'),{});
  state.variables={A:parse('mean(D1)')};
  state.functions={f:{parameters:['x'],body:parse('sumdata(D2)+x')}};
  assert.deepEqual(Object.keys(bindings('A+f(1)')).sort(),['D1','D2']);
  state.functions.f={parameters:['D2'],body:parse('sumdata(D2)')};
  assert.deepEqual(bindings('f([1,2,3])'),{});
});

test('large tables become small expressions with exact decimal dataset references',()=>{
  const source=`mixedmodel([${Array.from({length:5000},(_,i)=>`[${i%20},-1.25e-3,${i}]`).join(',')}],0)`;
  assert.throws(()=>parse(source),/8192/);
  const request=statisticsRequest(source),name=request.tree.args[0].value;
  assert.equal(request.tree.args[0].kind,'symbol');
  assert.equal(request.statisticsDatasets[name].length,5000);
  assert.deepEqual(request.statisticsDatasets[name][0],['0','-1.25e-3','0']);
  assert.ok(JSON.stringify(request.tree).length<500);
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
