import test from 'node:test';
import assert from 'node:assert/strict';
import {advancedStatisticsSchema} from '../advanced-statistics-schema.js';
import {guidedStatisticsCommand,advancedStatisticsRows,advancedStatisticsExampleRows} from '../advanced-statistics.js';
import {statisticsRequest} from '../statistics-request.js';
import {extensionStatisticsPlan} from '../statistics-extension-forms.js';
import {fork} from 'node:child_process';
import {readFileSync} from 'node:fs';
import {stratifiedStatisticsData} from '../statistics-stratified-data.js';

const countsCsv=`severity,treatment,improved,not_improved,total
mild,A,16,2,18
mild,B,144,36,180
moderate,A,40,20,60
moderate,B,30,30,60
severe,A,60,120,180
severe,B,4,16,20`;
const patientCsv=`patient_id,severity,treatment,improved
1,moderate,A,1
2,severe,A,1
3,severe,A,0
4,mild,B,1
5,moderate,B,0
6,mild,B,1`;
const definitions=id=>advancedStatisticsSchema.find(item=>item.id===id);
const defaults=id=>Object.fromEntries(definitions(id).controls.map(f=>[f.key,f.default]));
const expected=[['16','2','144','36'],['40','20','30','30'],['60','120','4','16']];

test('grouped counts and individual patient data produce identical stratum tables',()=>{
  const definition=definitions('mantelhaenszel'),opts=defaults('mantelhaenszel');
  const rows=advancedStatisticsRows(countsCsv,5),names=countsCsv.split('\n')[0].split(',');
  const counted=stratifiedStatisticsData(rows,opts,names);
  assert.deepEqual(counted.tables,expected);
  assert.equal(counted.labels['stratum:1'],'mild');assert.equal(counted.labels['count:1'],'A · improved');
  assert.deepEqual(stratifiedStatisticsData(rows,{...opts,countType:'total'},names).tables,expected);
  const observations=advancedStatisticsExampleRows(definition,{layout:'observations'});
  assert.equal(observations.length,518);
  assert.deepEqual(stratifiedStatisticsData(observations,{...opts,layout:'observations'}).tables,expected);
  const snippet=stratifiedStatisticsData(advancedStatisticsRows(patientCsv,4),{...opts,layout:'observations'},['patient_id','severity','treatment','improved']);
  assert.deepEqual(snippet.tables,[['1','0','0','1'],['1','1','0','0'],['0','0','2','0']]);
  assert.deepEqual(Object.fromEntries(Object.entries(snippet.labels).filter(([key])=>key.startsWith('stratum:'))),{'stratum:1':'moderate','stratum:2':'severe','stratum:3':'mild'});
  const repeated=[...rows.slice(1),['mild','A','10','1','11'],['mild','A','6','1','7']];
  const summed=stratifiedStatisticsData(repeated,opts);
  assert.deepEqual(summed.tables,expected);
  assert.deepEqual(stratifiedStatisticsData(rows,{...opts,groupA:'B',groupB:'A'}).tables,expected.map(row=>[...row.slice(2),...row.slice(0,2)]));
});

test('ambiguous groups, nonbinary outcomes, invalid totals and incomplete rows are rejected',()=>{
  const opts=defaults('mantelhaenszel'),rows=advancedStatisticsRows(countsCsv,5);
  assert.throws(()=>stratifiedStatisticsData(rows,{...opts,groupB:'A'}),/different treatment/);
  assert.throws(()=>stratifiedStatisticsData([...rows,['mild','C','1','2','3']],opts),/two selected groups/);
  assert.throws(()=>stratifiedStatisticsData([['mild','A','4','1','3']],{...opts,countType:'total'}),/at least/);
  assert.throws(()=>stratifiedStatisticsData([['mild','A','1.5','2','3']],opts),/integer/);
  assert.throws(()=>stratifiedStatisticsData([['1','mild','A','unknown']],{...opts,layout:'observations'}),/two selected outcome/);
  assert.throws(()=>stratifiedStatisticsData([['1','mild','A','1']],{...opts,layout:'observations',nonEventValue:'1'}),/different outcome/);
  assert.throws(()=>stratifiedStatisticsData([['mild','A','','2']],opts),/Complete/);
});

test('stratified tests select distinct count columns and serialize their options',()=>{
  for(const id of ['mantelhaenszel','breslowday']){
    const definition=advancedStatisticsSchema.find(item=>item.id===id);
    assert.ok(definition);assert.equal(definition.group,'Categorical data');
    const opts=Object.fromEntries(definition.controls.map(f=>[f.key,f.default]));
    const command=extensionStatisticsPlan(id,definition.exampleRows,opts).expression;
    assert.equal(command,definition.example);
    assert.equal(guidedStatisticsCommand(definition,definition.exampleRows),definition.example);
    assert.equal(statisticsRequest(command).tree.value,id);
    const rows=[['ignored','22','8','18','12']];
    const reordered={...opts,layout:'tables',a:'4',b:'3',c:'2',d:'1',method:id==='breslowday'?'tarone':'corrected',level:'.99'};
    assert.equal(extensionStatisticsPlan(id,rows,reordered).expression,`${id}([[12,18,8,22]],${reordered.method},.99)`);
    assert.throws(()=>extensionStatisticsPlan(id,rows,{...reordered,b:reordered.a}),/different columns/);
    assert.throws(()=>extensionStatisticsPlan(id,[['1','','2','3']],{...opts,layout:'tables'}),/Complete/);
  }
});

test('production WASM engine executes both stratified presets',{timeout:60000},async context=>{
  const worker=fork(new URL('./worker-bridge.mjs',import.meta.url),[],{execArgv:['--experimental-wasm-jspi']});
  context.after(()=>worker.kill());
  const receive=predicate=>new Promise((resolve,reject)=>{
    const timeout=setTimeout(()=>finish(new Error('Stratified worker timed out')),30000);
    const listener=data=>{if(data.type==='fatal')finish(new Error(data.error));else if(predicate(data))finish(null,data);};
    function finish(error,data){clearTimeout(timeout);worker.off('message',listener);worker.off('error',finish);error?reject(error):resolve(data);}
    worker.on('message',listener);worker.on('error',finish);
  });
  await receive(data=>data.type==='ready');
  const fixture=JSON.parse(readFileSync(new URL('../../tests/fixtures/stratified_statistics_reference.json',import.meta.url),'utf8'));
  const reference=fixture.cases.find(c=>JSON.stringify(c.arguments[0])===JSON.stringify(expected.map(row=>row.map(Number)))).expected['Pooled odds ratio'];
  for(const [id,name] of ['mantelhaenszel','breslowday'].entries()){
    const definition=advancedStatisticsSchema.find(item=>item.id===name);
    const pending=receive(data=>data.type==='result'&&data.id===id);
    worker.send({id,request:statisticsRequest(guidedStatisticsCommand(definition,definition.exampleRows))});
    const {result}=await pending;
    assert.equal(result.ok,true,result.error);
    assert.equal(result.statisticsReport.analysis,name);
    const or=result.statisticsReport.highlights.find(item=>item.label==='Pooled odds ratio');
    assert.ok(Math.abs(Number(or.value.decimal)-reference)<1e-9);
  }
  const plan=extensionStatisticsPlan('mantelhaenszel',advancedStatisticsRows(patientCsv,4),{...defaults('mantelhaenszel'),layout:'observations'},['patient_id','severity','treatment','improved']);
  const pending=receive(data=>data.type==='result'&&data.id===2);
  worker.send({id:2,request:{...statisticsRequest(plan.expression),statisticsTermLabels:plan.labels}});
  const {result}=await pending;assert.equal(result.ok,true,result.error);
  const excluded=result.statisticsReport.sections.find(s=>s.title==='Excluded strata');
  assert.deepEqual(excluded.rows.map(row=>row[0]),['severe','mild']);
  const strata=result.statisticsReport.sections.find(s=>s.title==='Strata');
  assert.equal(strata.rows[0][0],'moderate');assert.ok(strata.columns.includes('A · improved = 1'));
});
