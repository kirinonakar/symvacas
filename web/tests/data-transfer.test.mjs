import test from 'node:test';
import assert from 'node:assert/strict';
import {encodeData,decodeData,mergeData,resetSettingsState,deleteDataState} from '../data-transfer.js';
import {createAppState,createPersistence} from '../app-state.js';
import {defineFunction} from '../function-transfer.js';
import {readFileSync} from 'node:fs';

const saved=()=>({variables:{Ans:{kind:'number',value:'9'},a:{kind:'number',value:'1'}},functions:{f:defineFunction('f',['x'],'x+1')},datasets:{D1:'x,group\n1,A\n2,B'},datasetKinds:{D1:'columns:2'},assumptions:{a:['positive']}});
test('Android and Web accept and re-export the same portable data fixture',()=>{
  const fixture=readFileSync(new URL('../../tests/fixtures/data_transfer.json',import.meta.url),'utf8');
  const data=decodeData(fixture),state=mergeData(createAppState(),data);
  assert.deepEqual(decodeData(encodeData(state)),data);
  assert.equal(state.datasets.D1,'점수,그룹\n1,A\n2,B');
  assert.equal(state.functions.f.body.args[0].kind,'snapshot_symbol');
});
test('portable data roundtrip preserves names, categorical CSV and guarded ASTs',()=>{
  const state=saved();state.functions.f.body={kind:'restricted',args:[state.functions.f.body,{kind:'relation',value:'!=',args:[{kind:'symbol',value:'x'},{kind:'number',value:'0'}]}]};
  state.functions.f.answerSource=state.variables.Ans;
  const decoded=decodeData('\uFEFF'+encodeData(state));
  assert.deepEqual(decoded.functions,state.functions);
  assert.deepEqual(decoded.datasets.D1,{csv:state.datasets.D1,kind:'columns:2'});
  const merged=mergeData({...saved(),datasets:{Other:'5'},datasetKinds:{Other:'list'},digits:12},decoded);
  assert.equal(merged.datasets.Other,'5');assert.equal(merged.datasets.D1,state.datasets.D1);assert.equal(merged.digits,12);
  assert.deepEqual(merged.assumptions,state.assumptions);
});
test('reset clears every setting and draft while retaining all data and answer-linked functions',()=>{
  const state=createAppState({...saved(),history:[{mode:'scientific',source:'1+1'}],fields:{expression:'abc',mode:'statistics'},statisticsSections:{summary:false},graph:{sources:{cartesian:'x^3'}},precision:150,language:'ko',favorites:['stats([])'],calcModeStepByStep:true});
  const reset=createAppState(resetSettingsState(state),'en');
  for(const key of ['variables','functions','datasets','datasetKinds','assumptions'])assert.deepEqual(reset[key],state[key]);
  for(const key of ['fields','statisticsSections','graph'])assert.deepEqual(reset[key],{});
  assert.deepEqual(reset.history,[]);assert.deepEqual(reset.favorites,[]);assert.equal(reset.precision,30);assert.equal(reset.language,'en');assert.equal(reset.calcModeStepByStep,false);
  const cleared=deleteDataState(state);
  for(const key of ['variables','functions','datasets','datasetKinds','assumptions'])assert.deepEqual(cleared[key],{});
  assert.equal(cleared.precision,150);assert.equal(cleared.fields['statistics-data'],'');assert.equal(cleared.history.length,1);
});
test('invalid import fails atomically, including versions, reserved names and dataset types',()=>{
  const state=saved(),source=encodeData(state);
  for(const change of [data=>data.version=2,data=>data.variables.a={kind:7},data=>data.datasets.D1.kind='columns:101',data=>data.functions.skewness=defineFunction('f',['x'],'x'),data=>data.assumptions.a=['unknown']]){
    const data=JSON.parse(source);change(data);assert.throws(()=>decodeData(JSON.stringify(data)));assert.equal(encodeData(state),source);
  }
  assert.deepEqual(decodeData(encodeData({variables:{},functions:{},datasets:{},datasetKinds:{},assumptions:{}})).datasets,{});
});
test('overwriting a selected saved dataset refreshes its draft but retains unsaved edits',()=>{
  const state={...saved(),fields:{'dataset-list':'D1','statistics-data':saved().datasets.D1}},data=decodeData(encodeData(saved()));
  data.datasets.D1={csv:'x,y,z\n1,2,3',kind:'columns:3'};
  assert.equal(mergeData(state,data).fields['statistics-data'],data.datasets.D1.csv);
  assert.equal(mergeData(state,data).fields['statistics-columns'],'3');
  state.fields['statistics-data']='unsaved';assert.equal(mergeData(state,data).fields['statistics-data'],'unsaved');
  const legacy={...saved(),datasetKinds:{}};assert.equal(decodeData(encodeData(legacy)).datasets.D1.kind,'xy');
});
test('a stopped persistence handler cannot overwrite a reset or import on pagehide',()=>{
  const oldDocument=globalThis.document,oldStorage=globalThis.localStorage;
  let writes=0;globalThis.document={querySelectorAll:()=>[]};globalThis.localStorage={setItem:()=>writes++};
  try {
    const persistence=createPersistence({state:createAppState(),snapshot:()=>({expression:'old',graph:{}}),onPersist:()=>{},toast:()=>{}});
    persistence.schedulePersist();persistence.dispose();persistence.persist();assert.equal(writes,0);
  } finally {globalThis.document=oldDocument;globalThis.localStorage=oldStorage;}
});
