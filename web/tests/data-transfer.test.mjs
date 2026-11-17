import test from 'node:test';
import assert from 'node:assert/strict';
import {encodeData,decodeData,mergeData} from '../data-transfer.js';
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
test('invalid import fails atomically, including versions, reserved names and dataset types',()=>{
  const state=saved(),source=encodeData(state);
  for(const change of [data=>data.version=2,data=>data.variables.a={kind:7},data=>data.datasets.D1.kind='columns:101',data=>data.functions.skewness=defineFunction('f',['x'],'x'),data=>data.assumptions.a=['unknown']]){
    const data=JSON.parse(source);change(data);assert.throws(()=>decodeData(JSON.stringify(data)));assert.equal(encodeData(state),source);
  }
  assert.deepEqual(decodeData(encodeData({variables:{},functions:{},datasets:{},datasetKinds:{},assumptions:{}})).datasets,{});
});
test('a stopped persistence handler cannot overwrite a reset or import on pagehide',()=>{
  const oldDocument=globalThis.document,oldStorage=globalThis.localStorage;
  let writes=0;globalThis.document={querySelectorAll:()=>[]};globalThis.localStorage={setItem:()=>writes++};
  try {
    const persistence=createPersistence({state:createAppState(),snapshot:()=>({expression:'old',graph:{}}),onPersist:()=>{},toast:()=>{}});
    persistence.schedulePersist();persistence.dispose();persistence.persist();assert.equal(writes,0);
  } finally {globalThis.document=oldDocument;globalThis.localStorage=oldStorage;}
});
