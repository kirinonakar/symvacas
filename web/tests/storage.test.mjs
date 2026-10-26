import test from 'node:test';
import assert from 'node:assert/strict';
import {IDBFactory,IDBObjectStore} from 'fake-indexeddb';
import {createStorage} from '../storage.js';
import {createAppState,createPersistence} from '../app-state.js';
import {deleteDataState,resetSettingsState} from '../data-transfer.js';

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

test('only changed records are written; deletions, in-place edits and variable size transitions survive reload',async context=>{
  const f=fixture(),state=workspace();await f.storage.readState();await f.storage.writeState(state);
  const put=IDBObjectStore.prototype.put,changed=[];
  context.mock.method(IDBObjectStore.prototype,'put',function(value,key){changed.push(JSON.parse(key));return put.call(this,value,key);});
  state.theme='light';assert.equal(await f.storage.writeState(state),true);
  assert.deepEqual(changed,[['meta','settings']]);changed.length=0;
  state.fields.expression='3+3';state.history[0].star=false;state.variables.M={kind:'number',value:'7'};
  state.variables.a={kind:'matrix',args:Array.from({length:3000},()=>({kind:'number',value:'9'}))};
  delete state.datasets.large;delete state.datasetKinds.large;
  assert.equal(await f.storage.writeState(state),true);
  assert.ok(changed.some(key=>key[0]==='fields'&&key[1]==='expression'));
  assert.ok(!changed.some(key=>key[0]==='datasets'||key[1]==='statistics-data'));
  assert.deepEqual(await f.fresh().readState(),state);
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

test('blocked localStorage does not prevent IndexedDB saving or restoration',async()=>{
  const idb=new IDBFactory(),fresh=()=>createStorage({indexedDB:()=>idb,localStorage:()=>{throw new Error('Denied');}});
  const storage=fresh(),state=workspace();assert.deepEqual(await storage.readState(),{});
  assert.equal(await storage.writeState(state),true);assert.deepEqual(await fresh().readState(),state);
});

test('overlapping writes capture independent snapshots and finish in request order',async()=>{
  const f=fixture(),state=workspace();
  const first=f.storage.writeState(state);state.fields.expression='10';
  const second=f.storage.writeState(state);state.fields.expression='unsaved';
  assert.equal(await first,true);assert.equal(await second,true);
  assert.equal((await f.fresh().readState()).fields.expression,'10');
});

test('data deletion and settings reset remove stale records from IndexedDB',async()=>{
  const f=fixture(),state=workspace();await f.storage.writeState(state);
  const reset=resetSettingsState(state);await f.storage.writeState(reset);
  assert.deepEqual(await f.fresh().readState(),reset);
  const deleted=deleteDataState(state);await f.storage.writeState(deleted);
  assert.deepEqual(await f.fresh().readState(),deleted);
});

test('persistence batches writes, flushes drafts, honors history preference and protects replacement',async context=>{
  const descriptor=Object.getOwnPropertyDescriptor(globalThis,'document');
  Object.defineProperty(globalThis,'document',{configurable:true,value:{querySelectorAll:()=>[]}});
  context.after(()=>{if(descriptor)Object.defineProperty(globalThis,'document',descriptor);else delete globalThis.document;});
  const f=fixture(),state=workspace(),warnings=[];await f.storage.readState();
  let fail=false,writes=0;
  const persistence=createPersistence({state,snapshot:()=>({expression:'current draft',graph:{sources:{cartesian:'x^2'}}}),onPersist:()=>{},toast:message=>warnings.push(message),
    saveState:async next=>{writes++;return fail?false:f.storage.writeState(next);}});
  context.after(()=>persistence.dispose());
  for(let i=0;i<10;i++)persistence.persist();
  assert.equal(state.fields.expression,'current draft','export has the current draft before disk saving');assert.equal(writes,0);
  await new Promise(resolve=>setTimeout(resolve,300));assert.equal(writes,1);
  state.persistHistory=false;await persistence.flush();
  assert.deepEqual((await f.fresh().readState()).history,[]);assert.equal(state.history.length,1);
  fail=true;await persistence.flush();await persistence.flush();assert.equal(warnings.length,1);
  const replacement={variables:{},theme:'light'};
  assert.equal(await persistence.replace(replacement),false);
  fail=false;assert.equal(await persistence.flush(),true,'autosave resumes after failed replacement');
  persistence.schedulePersist();assert.equal(await persistence.replace(replacement),true);
  assert.equal(await persistence.flush(),false,'old workspace cannot overwrite successful replacement');
  assert.deepEqual(await f.fresh().readState(),replacement);
});
