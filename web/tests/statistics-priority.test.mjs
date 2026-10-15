import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fork} from 'node:child_process';
import {advancedStatisticsSchema as schema} from '../advanced-statistics-schema.js';
import {guidedStatisticsCommand,advancedStatisticsTermLabels,advancedStatisticsExampleRows} from '../advanced-statistics.js';
import {extensionAnalysisIds} from '../statistics-extension-forms.js';
import {statisticsRequest} from '../statistics-request.js';
const definition=id=>schema.find(d=>d.id===id);

test('all priority methods have runnable selected-column presets and a matching catalog category',()=>{
  const catalog=JSON.parse(readFileSync(new URL('../catalog.json',import.meta.url),'utf8'));
  for(const d of schema.filter(d=>extensionAnalysisIds.has(d.id))){
    assert.equal(guidedStatisticsCommand(d,d.exampleRows),d.example,d.id);
    assert.equal(statisticsRequest(d.example).tree.value,d.id);
    const category=d.section==='advanced'?'Advanced statistics':'General statistics';
    assert.ok(catalog[category].some(source=>source.startsWith(d.id+'(')),d.id);
  }
});

test('Bayesian pairs use subject IDs and one-sample mode ignores hidden second-column roles',()=>{
  const rows=[['s1','A','1'],['s2','B','5'],['s2','A','2'],['s1','B','4']];
  const opts={design:'paired',grouping:'groups',group:'1',value:'2',firstGroup:'A',secondGroup:'B',matching:'subject',subject:'0'};
  assert.ok(guidedStatisticsCommand(definition('bayesttest'),rows,opts).startsWith('bayesttest([1,2],[4,5],paired,'));
  assert.ok(guidedStatisticsCommand(definition('bayesttest'),[['1'],['2'],['4']],{design:'onesample'}).startsWith('bayesttest([1,2,4],[],onesample,'));
  assert.throws(()=>guidedStatisticsCommand(definition('bayesttest'),[['1','2'],['3','']],{design:'paired'}),/Complete/);
});

test('meta named subgroups keep labels and reject overlapping roles; fixed inference resets to z',()=>{
  const rows=[['US','.2','.1'],['KR','.4','.15'],['US','.3','.2'],['KR','.5','.2']],opts={effect:'1',se:'2',group:'0',method:'fixed'};
  assert.equal(guidedStatisticsCommand(definition('metasubgroup'),rows,opts),'metasubgroup([[.2,.1,1],[.4,.15,2],[.3,.2,1],[.5,.2,2]],fixed,0.95,z)');
  assert.deepEqual(advancedStatisticsTermLabels(definition('metasubgroup'),rows,opts),{'group:1':'US','group:2':'KR'});
  assert.throws(()=>guidedStatisticsCommand(definition('metaregression'),rows,{effect:'1',se:'2',predictors:'1'}),/distinct/);
});

test('AFT selected roles encode event values and delayed entry without treating entry as a predictor',()=>{
  const rows=[['dead','40','.2','1'],['alive','50','.3','2'],['dead','60','.4','3'],['dead','70','.1','4']];
  const opts={time:'3',event:'0',eventValue:'dead',truncation:'entry',entry:'2',predictors:'1'};
  assert.equal(guidedStatisticsCommand(definition('parametricsurvival'),rows,opts),'parametricsurvival([[1,1,.2,40],[2,0,.3,50],[3,1,.4,60],[4,1,.1,70]],weibull,0.95,2,6)');
  assert.deepEqual(advancedStatisticsTermLabels(definition('parametricsurvival'),rows,opts,['event','age','entry','time']),{'feature:1':'age'});
  assert.throws(()=>guidedStatisticsCommand(definition('parametricsurvival'),rows,{...opts,predictors:'2'}),/distinct/);
  assert.equal(guidedStatisticsCommand(definition('parametricsurvival'),[['1','1'],['2','0']],{covariates:'none'}),'parametricsurvival([[1,1],[2,0]],weibull,0.95,-1,6)');
});

test('moderators and named subgroups accept raw independent-arm summaries',()=>{
  for(const id of ['metaregression','metasubgroup'])for(const layout of ['binary','continuous']){
    const d=definition(id),rows=advancedStatisticsExampleRows(d,{layout});
    assert.equal(rows[0].length,layout==='binary'?5:7);
    assert.ok(guidedStatisticsCommand(d,rows,{layout}).endsWith(layout==='binary'?',oddsratio,0.5)':',md)'));
  }
  const binary=[['12','100','20','100','2010'],['8','80','15','90','2012']];
  assert.equal(guidedStatisticsCommand(definition('metaregression'),binary,{layout:'binary',predictors:'4'}),'metaregression([[12,100,20,100,2010],[8,80,15,90,2012]],pm,0.95,hksj,oddsratio,0.5)');
  const continuous=[['12','3','50','10','2.5','48','US'],['15','4','60','12','3.5','55','KR']];
  assert.equal(guidedStatisticsCommand(definition('metasubgroup'),continuous,{layout:'continuous',group:'6'}),'metasubgroup([[12,3,50,10,2.5,48,1],[15,4,60,12,3.5,55,2]],pm,0.95,hksj,md)');
  assert.throws(()=>guidedStatisticsCommand(definition('metaregression'),binary,{layout:'binary',predictors:'3'}),/distinct/);
});

test('new numerical methods run in the production WASM engine against independent scalar references',{timeout:60000},async context=>{
  const worker=fork(new URL('./worker-bridge.mjs',import.meta.url),[],{execArgv:['--experimental-wasm-jspi']});context.after(()=>worker.kill());
  const receive=predicate=>new Promise((resolve,reject)=>{
    const timeout=setTimeout(()=>finish(new Error('Priority statistics worker timed out')),30000);
    const listener=data=>{if(data.type==='fatal')finish(new Error(data.error));else if(predicate(data))finish(null,data);};
    function finish(error,data){clearTimeout(timeout);worker.off('message',listener);worker.off('error',finish);error?reject(error):resolve(data);}
    worker.on('message',listener);worker.on('error',finish);
  });
  await receive(data=>data.type==='ready');let id=0;const done=new Set();
  const fixture=JSON.parse(readFileSync(new URL('../../tests/fixtures/priority_statistics_reference.json',import.meta.url),'utf8'));
  const literal=value=>Array.isArray(value)?`[${value.map(literal).join(',')}]`:String(value);
  for(const entry of fixture.cases){
    if(done.has(entry.function))continue;done.add(entry.function);
    const current=++id,pending=receive(data=>data.type==='result'&&data.id===current);
    worker.send({id:current,request:statisticsRequest(`${entry.function}(${entry.arguments.map(literal).join(',')})`)});
    const result=(await pending).result;assert.equal(result.ok,true,`${entry.function}: ${result.error}`);
    for(const [path,expected] of entry.expected.filter(([p])=>p.length===1)){
      const row=result.statisticsReport.sections.flatMap(s=>s.rows).find(r=>r[0]===path[0]);assert.ok(row,`${entry.function}: ${path[0]}`);
      assert.ok(Math.abs(Number(row[1].decimal)-expected)<=entry.tolerance*Math.max(1,Math.abs(expected)),`${entry.function}: ${path[0]}`);
    }
    assert.ok(result.statisticsReport.plots.length,entry.function);
  }
  const d=definition('designsize'),current=++id,pending=receive(data=>data.type==='result'&&data.id===current);worker.send({id:current,request:statisticsRequest(d.example)});
  const result=(await pending).result;assert.equal(result.ok,true,result.error);assert.ok(result.statisticsReport.highlights.length);assert.equal(done.size,11);
});
