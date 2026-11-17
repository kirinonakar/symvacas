import test from 'node:test';
import assert from 'node:assert/strict';
import {IDBFactory,IDBObjectStore} from 'fake-indexeddb';
import {createStorage} from '../storage.js';
import {createAppState} from '../app-state.js';

const LEGACY='symvacas-web-v1',SETTINGS='symvacas-web-settings-v2';
function fixture(){
  const idb=new IDBFactory(),items=new Map(),writes=[];
  const local={getItem:key=>items.get(key)??null,setItem:(key,value)=>{writes.push([key,value]);items.set(key,value);},removeItem:key=>items.delete(key)};
  const fresh=()=>createStorage({indexedDB:()=>idb,localStorage:()=>local});
  return {idb,items,writes,local,fresh,storage:fresh()};
}
function workspace(){
  return createAppState({theme:'dark',variables:{a:{kind:'number',value:'2'},M:{kind:'matrix',args:Array.from({length:3000},()=>({kind:'number',value:'1'}))}},
    datasets:{large:'a,b\n'+('1,2\n'.repeat(300000))},datasetKinds:{large:'xy'},fields:{expression:'2+2','statistics-data':'1,2\n'.repeat(100000),'python-source':'print(42)'},
    graph:{sources:{cartesian:'sin(x)'}},history:[{source:'2+2',exact:'4',star:true}],functions:{f:{parameters:['x'],source:'x+1'}},matrixCells:{'1:1':'5'}});
}

test('large workspaces migrate once, keep a bounded settings mirror and round-trip full JSON backups',async()=>{
  const f=fixture(),state=workspace();f.items.set(LEGACY,JSON.stringify(state));
  assert.deepEqual(await f.storage.readState(),state);
  assert.equal(f.items.has(LEGACY),false);
  const mirror=JSON.parse(f.items.get(SETTINGS));
  assert.equal(mirror.theme,'dark');assert.deepEqual(mirror.variables,{a:state.variables.a});
  for(const key of ['datasets','history','fields','graph','functions','matrixCells'])assert.equal(Object.hasOwn(mirror,key),false,key);
  assert.ok(f.items.get(SETTINGS).length<16000);
  assert.deepEqual(await f.fresh().readState(),state);
  const backup=JSON.parse(JSON.stringify(state)),other=fixture();
  assert.equal(await other.storage.writeState(backup),true);
  assert.deepEqual(await other.fresh().readState(),state);
});

test('failed transactions preserve the previous complete snapshot and a later write can recover',async context=>{
  const f=fixture(),before=workspace();await f.storage.writeState(before);
  const put=IDBObjectStore.prototype.put;
  const mock=context.mock.method(IDBObjectStore.prototype,'put',function(value,key){
    if(JSON.parse(key)[0]==='fields')throw new DOMException('Storage full','QuotaExceededError');
    return put.call(this,value,key);
  });
  const next={...before,theme:'light',datasets:{new:'4,5'},fields:{expression:'5+5'}};
  assert.equal(await f.storage.writeState(next),false);
  assert.deepEqual(await f.fresh().readState(),before);
  assert.equal(JSON.parse(f.items.get(SETTINGS)).theme,'dark');
  mock.mock.restore();assert.equal(await f.storage.writeState(next),true);
  assert.deepEqual(await f.fresh().readState(),next);
});

test('failed migration retains the original; unavailable IndexedDB cannot overwrite it',async context=>{
  const f=fixture(),before=workspace();f.items.set(LEGACY,JSON.stringify(before));
  const mock=context.mock.method(IDBObjectStore.prototype,'put',()=>{throw new Error('Quota');});
  const errors=[];
  assert.deepEqual(await f.storage.readState({onError:error=>errors.push(error)}),before);
  assert.equal(errors.length,1);assert.equal(f.items.has(LEGACY),true);
  assert.equal(await f.storage.writeState({variables:{}}),false);
  mock.mock.restore();assert.deepEqual(await f.fresh().readState(),before);assert.equal(f.items.has(LEGACY),false);
  const unavailable=createStorage({indexedDB:()=>undefined,localStorage:()=>f.local});
  assert.equal((await unavailable.readState()).theme,'dark');
  assert.equal(await unavailable.writeState({variables:{}}),false);
  assert.deepEqual(await f.fresh().readState(),before);
});

test('overlapping writes capture independent snapshots and finish in request order',async()=>{
  const f=fixture(),state=workspace();
  const first=f.storage.writeState(state);state.fields.expression='10';
  const second=f.storage.writeState(state);state.fields.expression='unsaved';
  assert.equal(await first,true);assert.equal(await second,true);
  assert.equal((await f.fresh().readState()).fields.expression,'10');
});
