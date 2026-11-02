import test from 'node:test';
import assert from 'node:assert/strict';
import {NativeWorker} from '../frontend/native-worker.js';

const tick=()=>new Promise(resolve=>setImmediate(resolve));
class Channel {}

test('native transport relays readiness, input and calculation results',async()=>{
  const calls=[],events=[];
  const worker=new NativeWorker({Channel,invoke:async(name,args)=>{
    calls.push({name,args});
    if(name==='native_start')return {python:'3.14.10'};
    if(name==='native_execute'){
      args.onEvent.onmessage({type:'input',id:args.id,inputId:1,prompt:'Name?'});
      return {ok:true,output:'Hello'};
    }
  }});
  worker.onmessage=({data})=>events.push(data);
  await tick();
  assert.equal(events[0].type,'ready');
  worker.postMessage({id:42,request:{action:'python',source:'print(input())'}});
  await tick();
  assert.deepEqual(events.slice(1).map(e=>e.type),['input','result']);
  worker.postMessage({type:'input',id:42,inputId:1,value:'Alice'});
  await tick();
  assert.equal(calls.at(-1).name,'native_input');
  assert.equal(calls.at(-1).args.value,'Alice');
  worker.terminate();await tick();
  assert.equal(calls.at(-1).name,'native_cancel');
});

test('late responses from terminated workers cannot change UI state',async()=>{
  let finish;const events=[],calls=[];
  const worker=new NativeWorker({Channel,invoke:(name,args)=>{
    calls.push({name,args});
    return name==='native_start'?new Promise(resolve=>finish=resolve):Promise.resolve();
  }});
  worker.onmessage=({data})=>events.push(data);
  await tick();worker.terminate();finish({python:'3.14.10'});await tick();
  assert.equal(events.length,0);
  assert.equal(calls.filter(c=>c.name==='native_cancel').length,2,'cancel again after a late startup completes');
});

test('startup and execution failures reach the shared engine contract',async()=>{
  const events=[];
  const worker=new NativeWorker({Channel,invoke:async()=>{throw new Error('Install Python first');}});
  worker.onmessage=({data})=>events.push(data);
  await tick();assert.equal(events[0].type,'fatal');assert.match(events[0].error,/Install Python/);
  const next=new NativeWorker({Channel,invoke:async name=>{if(name==='native_execute')throw new Error('Process stopped');return {python:'3.14.10'};}});
  next.onmessage=({data})=>events.push(data);await tick();next.postMessage({id:1,request:{}});await tick();
  assert.equal(events.at(-1).result.ok,false);assert.match(events.at(-1).result.error,/Process stopped/);
});
