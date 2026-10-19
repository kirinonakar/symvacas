import test from 'node:test';
import assert from 'node:assert/strict';
import {fork} from 'node:child_process';
import {readFileSync} from 'node:fs';
import {statisticsRequest} from '../statistics-request.js';
import {advancedStatisticsSchema} from '../advanced-statistics-schema.js';
import {socialStatisticsPlan} from '../statistics-social-forms.js';

test('MANCOVA selected-column plan runs in production WASM with independent references',{timeout:60000},async context=>{
  const worker=fork(new URL('./worker-bridge.mjs',import.meta.url),[],{execArgv:['--experimental-wasm-jspi']});
  context.after(()=>worker.kill());
  const receive=predicate=>new Promise((resolve,reject)=>{
    const timeout=setTimeout(()=>finish(new Error('MANCOVA worker timed out')),30000);
    const listener=data=>{if(data.type==='fatal')finish(new Error(data.error));else if(predicate(data))finish(null,data);};
    function finish(error,data){clearTimeout(timeout);worker.off('message',listener);worker.off('error',finish);error?reject(error):resolve(data);}
    worker.on('message',listener);worker.on('error',finish);
  });
  await receive(data=>data.type==='ready');let id=0;
  const fixture=JSON.parse(readFileSync(new URL('../../tests/fixtures/mancova_reference.json',import.meta.url),'utf8'));
  for(const entry of fixture.cases){
    const [rows,c,level]=entry.arguments;
    const opts={group:'0',covariates:Array.from({length:c},(_,i)=>i+1).join(','),responses:'auto',level:String(level),slopes:'test'};
    const plan=socialStatisticsPlan('mancova',rows.map(row=>row.map(String)),opts);
    const current=++id,pending=receive(data=>data.type==='result'&&data.id===current);
    worker.send({id:current,request:{...statisticsRequest(plan.expression),precision:15,statisticsTermLabels:plan.labels}});
    const result=(await pending).result;assert.equal(result.ok,true,result.error);
    assert.equal(result.statisticsReport.title,'MANCOVA');
    for(const [path,expected] of entry.expected){
      const section=result.statisticsReport.sections.find(section=>section.title===path[0]);assert.ok(section,String(path));
      const actual=Number(section.rows[path[1]][section.columns.indexOf(path[2])].decimal);
      assert.ok(Math.abs(actual-expected)<=entry.tolerance*Math.max(1,Math.abs(expected)),`${entry.name} ${path}: ${actual} != ${expected}`);
    }
    assert.equal(result.statisticsReport.plots.filter(plot=>plot.kind==='intervals').length,rows[0].length-c-1);
  }
  const definition=advancedStatisticsSchema.find(d=>d.id==='mancova');
  const current=++id,pending=receive(data=>data.type==='result'&&data.id===current);
  worker.send({id:current,request:statisticsRequest(definition.example)});
  const result=(await pending).result;assert.equal(result.ok,true,result.error);
});
