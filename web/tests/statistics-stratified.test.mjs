import test from 'node:test';
import assert from 'node:assert/strict';
import {advancedStatisticsSchema} from '../advanced-statistics-schema.js';
import {advancedStatisticsRows,advancedStatisticsExampleRows} from '../advanced-statistics.js';
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
