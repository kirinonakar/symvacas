import test from 'node:test';
import assert from 'node:assert/strict';
import {fork} from 'node:child_process';
import {readFileSync} from 'node:fs';
import {advancedStatisticsSchema} from '../advanced-statistics-schema.js';
import {guidedStatisticsCommand,advancedStatisticsTermLabels} from '../advanced-statistics.js';
import {statisticsRequest} from '../statistics-request.js';

test('D’Agostino–Pearson form uses the chosen sample and rejects fewer than 8 observations',()=>{
  const definition=advancedStatisticsSchema.find(d=>d.id==='normaltest');
  const rows=Array.from({length:8},(_,i)=>['99',String(i)]).concat([['100','']]);
  assert.equal(definition.section,'tests');
  assert.equal(definition.group,'Distribution & variance');
  assert.equal(guidedStatisticsCommand(definition,rows,{column:'1'}),'normaltest([0,1,2,3,4,5,6,7])');
  assert.deepEqual(advancedStatisticsTermLabels(definition,rows,{column:'1'},['ID','Outcome']),{'sample:1':'Outcome'});
  assert.throws(()=>guidedStatisticsCommand(definition,rows.slice(0,7),{column:'1'}),/at least 8/);
  assert.equal(guidedStatisticsCommand(definition,definition.exampleRows),definition.example);
});

test('production WASM normaltest matches independent references and produces full diagnostics',{timeout:60000},async context=>{
  const worker=fork(new URL('./worker-bridge.mjs',import.meta.url),[],{execArgv:['--experimental-wasm-jspi']});
  context.after(()=>worker.kill());
  const receive=predicate=>new Promise((resolve,reject)=>{
    const timeout=setTimeout(()=>finish(new Error('Normaltest worker timed out')),30000);
    const listener=data=>{if(data.type==='fatal')finish(new Error(data.error));else if(predicate(data))finish(null,data);};
    function finish(error,data){clearTimeout(timeout);worker.off('message',listener);worker.off('error',finish);error?reject(error):resolve(data);}
    worker.on('message',listener);worker.on('error',finish);
  });
  await receive(data=>data.type==='ready');
  let id=0;
  const run=async expression=>{
    const current=++id,pending=receive(data=>data.type==='result'&&data.id===current);
    worker.send({id:current,request:{...statisticsRequest(expression),precision:15,statisticsTermLabels:{'sample:1':'Outcome'}}});
    return (await pending).result;
  };
  const fixture=JSON.parse(readFileSync(new URL('../../tests/fixtures/normaltest_reference.json',import.meta.url),'utf8'));
  for(const entry of fixture.cases){
    const result=await run(`normaltest(${JSON.stringify(entry.values)})`);
    assert.equal(result.ok,true,result.error);
    const report=result.statisticsReport;
    assert.equal(report.analysis,'normaltest');
    const summary=report.sections.find(s=>s.title==='Summary');
    const cells=Object.fromEntries(summary.rows.map(row=>[row[0],Number(row[1].decimal)]));
    for(const [key,expected] of [['K²',entry.K2],['p value',entry.p],['skewness z',entry.skew_z],['kurtosis z',entry.kurt_z]])
      assert.ok(Math.abs(cells[key]-expected)<2e-10*Math.max(1,Math.abs(expected)),`${entry.label}: ${key}`);
    assert.deepEqual(report.plots.map(p=>p.kind),['qq','distribution']);
    assert.equal(report.plots[0].series[0].label,'Outcome');
    assert.equal(Boolean(report.warnings?.length),entry.values.length<=20);
  }
  for(const sample of [[1,2,3,4,5,6,7],Array(8).fill(1)])
    assert.equal((await run(`normaltest(${JSON.stringify(sample)})`)).ok,false);
});
