import test from 'node:test';
import assert from 'node:assert/strict';
import {fork} from 'node:child_process';
import {readFileSync} from 'node:fs';
import {statisticsRequest} from '../statistics-request.js';

test('production WASM preserves REML slope SE across origins and units',{timeout:180000},async t=>{
  const worker=fork(new URL('./worker-bridge.mjs',import.meta.url),[],{execArgv:['--experimental-wasm-jspi']});
  t.after(()=>worker.kill());
  function receive(predicate){
    return new Promise((resolve,reject)=>{
      const timer=setTimeout(()=>finish(new Error('Mixed-model worker timed out')),60000);
      function finish(error,value){clearTimeout(timer);worker.off('message',message);worker.off('error',finish);error?reject(error):resolve(value);}
      function message(value){if(value.type==='fatal')finish(new Error(value.error));else if(predicate(value))finish(null,value);}
      worker.on('message',message);worker.on('error',finish);
    });
  }
  await receive(value=>value.type==='ready');let id=0;
  const cases=JSON.parse(readFileSync(new URL('../../tests/fixtures/mixed_se_reference.json',import.meta.url),'utf8')).cases;
  for(const name of ['intercept reml','unbalanced reml','slope reml']){
    const entry=cases.find(value=>value.name===name);
    const dx=1e6,dy=1e6,sx=1e3;
    const rows=entry.rows.map(([group,x,...rest])=>[group,(x+dx)*sx,...rest.slice(0,-1),rest.at(-1)+dy]);
    const current=++id,pending=receive(value=>value.type==='result'&&value.id===current);
    worker.send({id:current,request:{...statisticsRequest(`mixedmodel(${JSON.stringify(rows)},${entry.slope},reml)`),precision:15}});
    const result=(await pending).result;assert.equal(result.ok,true,`${name}: ${result.error}`);
    const table=result.statisticsReport.sections.find(section=>section.title==='coefficients');
    assert.ok(table,name);
    for(let j=1;j<entry.estimates.length;j++){
      const factor=j===1?sx:1;
      for(const [column,expected] of [['estimate',entry.estimates[j]],['SE',entry.SE[j]],['Lower 95% CI',entry.CI95[j][0]],['Upper 95% CI',entry.CI95[j][1]]]){
        const actual=Number(table.rows[j][table.columns.indexOf(column)].decimal)*factor;
        assert.ok(Math.abs(actual-expected)<3e-6,`${name}: ${column} ${actual} != ${expected}`);
      }
    }
  }
});
