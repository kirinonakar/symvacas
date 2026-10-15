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
  const extended=JSON.parse(readFileSync(new URL('../../tests/fixtures/sphericity_posthoc_reference.json',import.meta.url),'utf8'));
  for(const entry of [extended.cases[3],...extended.cases.slice(4,7)]){
    const literal=value=>Array.isArray(value)?`[${value.map(literal).join(',')}]`:String(value);
    const current=++id,pending=receive(data=>data.type==='result'&&data.id===current);
    worker.send({id:current,request:{...statisticsRequest(`${entry.function}(${entry.arguments.map(literal).join(',')})`),precision:15}});
    const result=(await pending).result;assert.equal(result.ok,true,`${entry.function}: ${result.error}`);
    for(const [path,expected] of entry.expected){
      const section=result.statisticsReport.sections.find(section=>section.title===(path.length===1?'Summary':path[0]));
      const cell=path.length===1?section.rows.find(row=>row[0]===path[0])[1]:section.rows[path[1]][section.columns.indexOf(path[2])];
      assert.ok(Math.abs(Number(cell.decimal)-expected)<=entry.tolerance*Math.max(1,Math.abs(expected)),`${entry.function}: ${path}`);
    }
  }
  const repeated=extended.repeated_report;
  {
    const current=++id,pending=receive(data=>data.type==='result'&&data.id===current);
    worker.send({id:current,request:{...statisticsRequest(`repeatedanova(${JSON.stringify(repeated.rows)})`),precision:15,
      statisticsTermLabels:{'feature:1':'x','feature:2':'y','feature:3':'z'}}});
    const result=(await pending).result;assert.equal(result.ok,true,result.error);
    const sections=Object.fromEntries(result.statisticsReport.sections.map(section=>[section.title,section]));
    const number=(title,row,column)=>Number(sections[title].rows[row][sections[title].columns.indexOf(column)].decimal);
    assert.deepEqual(sections['Condition summaries'].rows.map(row=>row[0]),['x','y','z']);
    for(const [i,expected] of repeated.conditions.entries()){
      assert.ok(Math.abs(number('Condition summaries',i,'Mean')-expected.mean)<1e-12);
      assert.ok(Math.abs(number('Condition summaries',i,'SD')-expected.sd)<1e-12);
    }
    for(const [i,expected] of repeated.contrasts.entries()){
      assert.ok(Math.abs(number('Assumption checks',i,'Statistic')-expected.W)<2e-8);
      assert.ok(Math.abs(number('Assumption checks',i,'p value')-expected.p)<2e-7);
      assert.equal(number('Assumption checks',i,'n'),5);
    }
    for(const [i,expected] of repeated.pairs.entries())for(const [column,key] of [['Mean difference','difference'],['Lower 95% CI','lower'],['Upper 95% CI','upper'],['Adjusted p value','holm_p']])
      assert.ok(Math.abs(number('Paired t post-hoc (Holm)',i,column)-expected[key])<2e-10);
  }
  for(const analysis of ['chi2independence','fisherexact']){
    const current=++id,pending=receive(data=>data.type==='result'&&data.id===current);
    worker.send({id:current,request:{...statisticsRequest(`${analysis}([0,0,1,1,1],[0,1,0,1,1])`),statisticsTermLabels:{'table:row':'Treatment','table:column':'Outcome'}}});
    const result=(await pending).result;assert.equal(result.ok,true,result.error);
    const sections=result.statisticsReport.sections;
    assert.equal(sections.filter(section=>section.title==='Compared columns').length,1,analysis);
    assert.deepEqual(sections.find(section=>section.title==='Effect size').columns,['Effect size','Value','Rating']);
  }
});
