import test from 'node:test';
import assert from 'node:assert/strict';
import {createDesktopStorage} from '../frontend/desktop-storage.js';

test('GUI imports legacy saved data and exposes CLI/MCP registrations on startup',async()=>{
  let registry={cohort:{source:'4\n5',kind:'list'}};
  const changes=[];
  const storage=createDesktopStorage({readState:async()=>({datasets:{legacy:'1\n2'},datasetKinds:{legacy:'list'}}),writeState:async()=>true},async(_,args)=>{
    changes.push(args);
    for(const [key,value] of Object.entries(args.changes))if(!args.bootstrap||!registry[key])registry[key]=value;
    return {datasets:structuredClone(registry)};
  });
  const state=await storage.readState();
  assert.deepEqual(state.datasets,{cohort:'4\n5',legacy:'1\n2'});
  state.datasets.legacy='7\n8';assert.equal(await storage.writeState(state),true);
  assert.deepEqual(Object.keys(changes.at(-1).changes),['legacy']);
  registry.cohort={source:'10\n11',kind:'list'};
  assert.equal(await storage.writeState({...state,theme:'dark'}),true);
  assert.equal(registry.cohort.source,'10\n11','an unrelated GUI preference change cannot overwrite an external dataset edit');
});

test('unread registry blocks writes and reports the read failure',async()=>{
  let failure,saved=false;
  const storage=createDesktopStorage({readState:async()=>({}),writeState:async()=>{saved=true;return true;}},async()=>{throw new Error('Invalid registry');});
  await storage.readState({onError:error=>failure=error});
  assert.match(failure.message,/Invalid registry/);assert.equal(await storage.writeState({datasets:{}}),false);assert.equal(saved,false);
});
