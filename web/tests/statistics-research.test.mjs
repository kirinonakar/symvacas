import test from 'node:test';
import assert from 'node:assert/strict';
import {statisticsRequest} from '../statistics-request.js';
import {fork} from 'node:child_process';
import {readFileSync} from 'node:fs';


test('production WASM engine computes the research presets against independent references',{timeout:60000},async context=>{
  const worker=fork(new URL('./worker-bridge.mjs',import.meta.url),[],{execArgv:['--experimental-wasm-jspi']});
  context.after(()=>worker.kill());
  const receive=predicate=>new Promise((resolve,reject)=>{
    const timeout=setTimeout(()=>finish(new Error('Research worker timed out')),30000);
    const listener=data=>{if(data.type==='fatal')finish(new Error(data.error));else if(predicate(data))finish(null,data);};
    function finish(error,data){clearTimeout(timeout);worker.off('message',listener);worker.off('error',finish);error?reject(error):resolve(data);}
    worker.on('message',listener);worker.on('error',finish);
  });
  await receive(data=>data.type==='ready');let id=0;
  const fixture=JSON.parse(readFileSync(new URL('../../tests/fixtures/research_statistics_reference.json',import.meta.url),'utf8'));
  const done=new Set();
  for(const entry of fixture.cases){
    const key=entry.function+(entry.function==='metaanalysis'&&entry.arguments.length>=6?':'+entry.arguments[5]:'');
    if(done.has(key))continue;done.add(key);
    const literal=value=>Array.isArray(value)?`[${value.map(literal).join(',')}]`:String(value);
    const expression=`${entry.function}(${entry.arguments.map(literal).join(',')})`;
    const current=++id,pending=receive(data=>data.type==='result'&&data.id===current);worker.send({id:current,request:statisticsRequest(expression)});
    const result=(await pending).result;assert.equal(result.ok,true,`${entry.function}: ${result.error}`);
    const summary=result.statisticsReport.sections.find(section=>section.title==='Summary');assert.ok(summary,entry.function);
    for(const [path,expected] of entry.expected){
      if(path.length!==1)continue;
      const row=summary.rows.find(row=>row[0]===path[0]);assert.ok(row,`${entry.function}: ${path[0]}`);
      assert.ok(Math.abs(Number(row[1].decimal)-expected)<=entry.tolerance*Math.max(1,Math.abs(expected)),`${entry.function}: ${path[0]}`);
    }
  }
  assert.equal(done.size,10);
  for(const analysis of ['chi2independence','fisherexact']){
    const current=++id,pending=receive(data=>data.type==='result'&&data.id===current);
    worker.send({id:current,request:{...statisticsRequest(`${analysis}([0,0,1,1,1],[0,1,0,1,1])`),statisticsTermLabels:{'table:row':'Treatment','table:column':'Outcome'}}});
    const result=(await pending).result;assert.equal(result.ok,true,result.error);
    const sections=result.statisticsReport.sections;
    assert.equal(sections.filter(section=>section.title==='Compared columns').length,1,analysis);
    assert.deepEqual(sections.find(section=>section.title==='Effect size').columns,['Effect size','Value','Rating']);
  }
});
