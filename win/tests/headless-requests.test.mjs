import test from 'node:test';
import assert from 'node:assert/strict';
import {statisticsInput,equationInput,datasetInput} from '../frontend/headless-requests.js';

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

test('saved CSV datasets use the web header and column conventions',()=>{
  const registeredDatasets={cohort:{source:'Value\n1\n2\n3',kind:'list'},trial:{source:'x,y\n1,3\n2,5\n3,7',kind:'xy'},unused:{source:'not data',kind:'list'}};
  const input=statisticsInput({expression:'mean(cohort)',registeredDatasets});
  assert.deepEqual(input.statisticsDatasets.cohort,['1','2','3']);
  assert.equal(input.statisticsDatasets.unused,undefined);
  const regression=statisticsInput({expression:'regression(trial,linear)',registeredDatasets});
  assert.deepEqual(regression.statisticsDatasets.trial,[['1','3'],['2','5'],['3','7']]);
  assert.deepEqual(statisticsInput({expression:'mean(cohort)',registeredDatasets,datasets:{cohort:[8,10]}}).statisticsDatasets.cohort,['8','10']);
});

test('equations preserve systems, numeric solver options and step flags',()=>{
  const system=equationInput({equations:['x+y=3','x-y=1'],variables:['x','y']});
  assert.equal(system.tree.value,'solve');assert.equal(system.tree.args[0].args.length,2);assert.equal(system.equationSteps,true);
  const numerical=equationInput({equations:'cos(x)=x',method:'nsolve',initialGuess:0.5,steps:false});
  assert.equal(numerical.tree.value,'nsolve');assert.equal(numerical.equationSteps,false);
  assert.equal(equationInput({equations:'diff(y,x)=y',variables:'y',method:'dsolve'}).tree.value,'dsolve');
  assert.throws(()=>equationInput({equations:'x=1',variables:'x,x'}),/distinct/);
  assert.throws(()=>equationInput({equations:'x=1',method:'bad'}),/Method/);
});

test('dataset import supports JSON tables, CSV headers and exact strings',()=>{
  assert.deepEqual(datasetInput({data:[1,'0.00000000000000000001',3]}),{source:'1\n0.00000000000000000001\n3',kind:'list'});
  assert.equal(datasetInput({csv:'x,y\n1,2\n3,4'}).kind,'xy');
  assert.equal(datasetInput({data:[[1,2,3,4],[5,6,7,8]]}).kind,'columns:4');
  assert.throws(()=>datasetInput({data:[[1,2],[3]]}),/equal/);
  assert.throws(()=>datasetInput({data:[1],csv:'1'}),/either/);
});
