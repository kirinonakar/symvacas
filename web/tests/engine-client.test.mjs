import test from 'node:test';
import assert from 'node:assert/strict';
import {EngineClient} from '../engine-client.js';
import {parse} from '../parser.js';

test('SEM bootstrap survives the ordinary deadline, keeps a bounded deadline and remains cancellable',async t=>{
  const {engine,workers,tick}=runtime(t);workers[0].message({type:'ready'});
  const request={tree:parse('sem([[1,2,3,4,5,6]],[1,1,1,2,2,2],[[1,2]],[],complete,[],configural,ml,[],0,20,7)')};
  const result=engine.execute(request);tick(60001);assert.equal(workers[0].terminated,false);
  tick(724998);assert.equal(workers[0].terminated,false);tick(1);
  assert.equal((await result).ok,false);assert.equal(workers[0].terminated,true);
  workers[1].message({type:'ready'});const next=engine.execute(request);engine.cancel();assert.equal((await next).error,'계산이 중지되었습니다.');
});

function runtime(t) {
  const workers=[],statuses=[];
  const original=Object.getOwnPropertyDescriptor(globalThis,'Worker');
  class Worker {
    constructor(){workers.push(this);this.terminated=false;}
    terminate(){this.terminated=true;}
    postMessage(data){this.request=data;}
    message(data){this.onmessage({data});}
  }
  globalThis.Worker=Worker;
  t.mock.timers.enable({apis:['setTimeout','Date']});
  t.after(()=>{
    if(original)Object.defineProperty(globalThis,'Worker',original);
    else delete globalThis.Worker;
  });
  const engine=new EngineClient();
  engine.addEventListener('status',event=>statuses.push(event.detail));
  return {engine,workers,statuses,tick:ms=>t.mock.timers.tick(ms)};
}

test('stalled cold startup retries once and becomes ready without a page refresh',async t=>{
  const {engine,workers,statuses,tick}=runtime(t);
  workers[0].message({type:'status',message:'SymPy 계산 엔진 로딩…'});
  tick(119999);assert.equal(workers.length,1);
  tick(1);assert.equal(workers.length,2);assert.equal(workers[0].terminated,true);
  assert.equal(statuses.at(-1),'계산 엔진 로딩을 다시 시도합니다…');
  workers[0].message({type:'ready'});assert.equal(engine.ready,false,'queued messages from the old worker are ignored');
  workers[0].onerror({message:'stale error'});assert.equal(workers.length,2);
  workers[1].message({type:'ready'});assert.equal(engine.ready,true);
  tick(120000);assert.equal(workers.length,2);assert.equal(engine.ready,true,'readiness clears the startup timeout');
  const result=engine.execute({action:'calculate'});
  workers[1].message({type:'result',id:workers[1].request.id,result:{ok:true,exact:'2'}});
  assert.deepEqual(await result,{ok:true,exact:'2'});
});

test('two stalled attempts end with a retryable error instead of an infinite loop',t=>{
  const {engine,workers,statuses,tick}=runtime(t);
  tick(120000);tick(120000);
  assert.equal(workers.length,2);assert.equal(workers[1].terminated,true);assert.equal(engine.ready,false);
  assert.equal(statuses.at(-1),'계산 엔진 로딩 시간이 초과되었습니다. 다시 로딩을 눌러 주세요.');
  tick(120000);assert.equal(workers.length,2);
  engine.cancel();assert.equal(workers.length,3,'manual retry remains available after startup failure');
  workers[2].message({type:'ready'});assert.equal(engine.ready,true);
});

for(const kind of ['fatal','error'])test(`${kind} during startup retries once and then reports the failure`,t=>{
  const {engine,workers,statuses,tick}=runtime(t);
  const fail=worker=>kind==='fatal'?worker.message({type:'fatal',error:'download failed'}):worker.onerror({message:'download failed'});
  fail(workers[0]);assert.equal(workers.length,2);assert.equal(workers[0].terminated,true);
  fail(workers[1]);assert.equal(engine.ready,false);assert.equal(statuses.at(-1),'download failed');
  tick(240000);assert.equal(workers.length,2,'failed workers leave no live startup timers');
});

test('a runtime error settles a calculation without treating it as cold startup',async t=>{
  const {engine,workers,statuses,tick}=runtime(t);
  workers[0].message({type:'ready'});
  const result=engine.execute({action:'calculate'});
  workers[0].onerror({message:'runtime failed'});
  assert.deepEqual(await result,{ok:false,error:'runtime failed'});
  assert.equal(engine.pending,null);assert.equal(engine.ready,false);assert.equal(statuses.at(-1),'runtime failed');
  tick(240000);assert.equal(workers.length,1);
});

test('calculations can finish after 20 seconds and the next request expires after response grace',async t=>{
  const {engine,workers,tick}=runtime(t);
  workers[0].message({type:'ready'});
  const slow=engine.execute({action:'evaluate'});
  tick(25000);assert.equal(workers.length,1);assert.ok(engine.pending);
  workers[0].message({type:'result',id:workers[0].request.id,result:{ok:true,exact:'2'}});
  assert.equal((await slow).exact,'2');
  const stalled=engine.execute({action:'evaluate'});
  tick(64999);assert.equal(workers.length,1);assert.ok(engine.pending);
  tick(1);assert.equal(workers[0].terminated,true);assert.equal(workers.length,2);
  assert.deepEqual(await stalled,{ok:false,error:'계산 시간이 60초를 초과했습니다.'});
  workers[1].message({type:'ready'});
  const next=engine.execute({action:'evaluate'});
  workers[1].message({type:'result',id:workers[1].request.id,result:{ok:true}});
  assert.equal((await next).ok,true);
});

test('engine limit details arriving during response grace reach the caller',async t=>{
  const {engine,workers,tick}=runtime(t);
  workers[0].message({type:'ready'});
  const result=engine.execute({action:'evaluate'});
  tick(64000);
  assert.equal(workers[0].terminated,false);
  const response={ok:false,error:'Computation limit reached. Reduce expression complexity.'};
  workers[0].message({type:'result',id:workers[0].request.id,result:response});
  assert.deepEqual(await result,response);
  tick(1000);assert.equal(workers.length,1,'a delivered response clears the fallback timer');
});

test('background previews leave editing unlocked and foreground work waits for them',async t=>{
  const {engine,workers}=runtime(t),busy=[];
  engine.addEventListener('busy',event=>busy.push(event.detail));
  workers[0].message({type:'ready'});
  const preview=engine.execute({tree:{kind:'number',value:'1'}},{background:true});
  const previewId=workers[0].request.id;
  assert.deepEqual(busy,[],'a preview does not lock the keypad');
  const commit=engine.execute({tree:{kind:'number',value:'2'}});
  assert.deepEqual(busy,[true],'explicit work locks controls while waiting');
  assert.equal(workers[0].request.id,previewId,'requests never overlap in the worker');
  workers[0].message({type:'result',id:previewId,result:{ok:true,exact:'1'}});
  assert.equal((await preview).exact,'1');
  await Promise.resolve();
  assert.notEqual(workers[0].request.id,previewId);
  workers[0].message({type:'result',id:workers[0].request.id,result:{ok:true,exact:'2'}});
  assert.equal((await commit).exact,'2');
  assert.equal(busy.at(-1),false);
});

test('cancelled foreground work waiting for a preview cannot run on the restarted worker',async t=>{
  const {engine,workers}=runtime(t);
  workers[0].message({type:'ready'});
  const preview=engine.execute({},{background:true});
  const fit=engine.execute({action:'regression'});
  engine.cancel();
  // The replacement may be ready before the preview promise continuation runs.
  workers[1].message({type:'ready'});
  assert.equal((await preview).ok,false);
  assert.equal((await fit).ok,false);
  assert.equal(workers[1].request,undefined);
  const next=engine.execute({action:'regression'});
  workers[1].message({type:'result',id:workers[1].request.id,result:{ok:true}});
  assert.equal((await next).ok,true);
});

test('bounded previews return cooperatively without restarting the warm worker',async t=>{
  const {engine,workers,tick}=runtime(t);
  workers[0].message({type:'ready'});
  const request={tree:{kind:'number',value:'1'},budget:60};
  const preview=engine.execute(request,{background:true,preview:true});
  assert.equal(workers[0].request.request.budget,2);
  assert.equal(request.budget,60,'preview settings do not mutate the committed request');
  tick(2000);
  workers[0].message({type:'result',id:workers[0].request.id,result:{ok:false,error:'Computation limit reached'}});
  assert.equal((await preview).ok,false);
  tick(1000);assert.equal(workers.length,1);assert.equal(engine.ready,true);
});

test('a stalled preview restarts only at its deadline and automatically runs queued foreground work',async t=>{
  const {engine,workers,tick}=runtime(t),busy=[];
  engine.addEventListener('busy',event=>busy.push(event.detail));
  workers[0].message({type:'ready'});
  const preview=engine.execute({tree:{kind:'number',value:'1'}},{background:true,preview:true});
  const staleId=workers[0].request.id;
  tick(2500);
  const request={action:'python',budget:60},onInput=async()=> 'answer';
  const commit=engine.execute(request,{context:'python',onInput});
  tick(499);assert.equal(workers.length,1);
  tick(1);assert.equal(workers.length,2);assert.equal(workers[0].terminated,true);
  assert.equal((await preview).ok,false);
  assert.equal(workers[1].request,undefined,'foreground waits for initialization');
  assert.ok(!busy.includes(false),'controls remain locked across the restart');
  workers[0].message({type:'result',id:staleId,result:{ok:true,exact:'stale'}});
  workers[1].message({type:'ready'});
  assert.deepEqual(workers[1].request.request,request);
  assert.equal(engine.pending.context,'python');assert.equal(engine.pending.onInput,onInput);
  tick(3000);assert.equal(workers.length,2,'foreground receives its own full deadline');
  workers[1].message({type:'result',id:workers[1].request.id,result:{ok:true,exact:'2'}});
  assert.equal((await commit).exact,'2');assert.equal(busy.at(-1),false);
});

test('cancelling during preview recovery discards queued work even if a replacement becomes ready',async t=>{
  const {engine,workers,tick}=runtime(t);
  workers[0].message({type:'ready'});
  const preview=engine.execute({},{background:true,preview:true});
  const commit=engine.execute({action:'evaluate'});
  tick(3000);assert.equal((await preview).ok,false);
  engine.cancel();assert.equal((await commit).error,'계산이 중지되었습니다.');
  workers[1].message({type:'ready'});workers[2].message({type:'ready'});
  assert.equal(workers[1].request,undefined);assert.equal(workers[2].request,undefined);
});

test('failed preview recovery settles queued work after the bounded startup retries',async t=>{
  const {engine,workers,tick}=runtime(t),busy=[];
  engine.addEventListener('busy',event=>busy.push(event.detail));
  workers[0].message({type:'ready'});
  const preview=engine.execute({},{background:true,preview:true});
  const commit=engine.execute({action:'evaluate'});
  tick(3000);assert.equal((await preview).ok,false);
  tick(120000);tick(120000);
  assert.equal((await commit).ok,false);assert.equal(engine.queued,null);
  assert.equal(busy.at(-1),false);
});

test('only calculation previews have a short hard deadline, including when limits are removed',async t=>{
  const {engine,workers,tick}=runtime(t);
  workers[0].message({type:'ready'});
  const preview=engine.execute({removeComputationLimit:true},{background:true,preview:true});
  tick(2999);assert.equal(workers.length,1);
  tick(1);assert.equal((await preview).ok,false);assert.equal(workers.length,2);
  workers[1].message({type:'ready'});
  const graph=engine.execute({action:'graph'},{background:true});
  tick(3000);assert.equal(workers.length,2);
  workers[1].message({type:'result',id:workers[1].request.id,result:{ok:true}});
  assert.equal((await graph).ok,true);
});

test('Python input pauses the deadline and resumes with the remaining execution budget',async t=>{
  const {engine,workers,tick}=runtime(t);
  workers[0].message({type:'ready'});
  let answer;
  const result=engine.execute({action:'python'},{onInput:()=>new Promise(resolve=>answer=resolve)});
  const id=workers[0].request.id;
  tick(5000);
  workers[0].message({type:'input',id,inputId:1,prompt:'a=',output:'before\n'});
  tick(60000);assert.equal(workers.length,1);assert.ok(engine.pending);
  answer('');await Promise.resolve();
  assert.deepEqual(workers[0].request,{type:'input',id,inputId:1,value:''});
  tick(59999);assert.equal(workers.length,1);
  tick(1);assert.equal(workers.length,2);
  assert.match((await result).error,/60/);
});

test('cancel and stale input replies cannot resume a replacement worker',async t=>{
  const {engine,workers}=runtime(t);
  workers[0].message({type:'ready'});
  let answer,signal;
  const result=engine.execute({action:'python'},{onInput:request=>{signal=request.signal;return new Promise(resolve=>answer=resolve);}});
  const id=workers[0].request.id;
  workers[0].message({type:'input',id:999,inputId:1});assert.equal(signal,undefined);
  workers[0].message({type:'input',id,inputId:1});
  engine.cancel();assert.equal(signal.aborted,true);
  workers[1].message({type:'ready'});
  answer('late');await Promise.resolve();
  assert.equal(workers[1].request,undefined);assert.equal((await result).ok,false);
});

test('unlimited requests survive the execution deadline and can still be cancelled',async t=>{
  const {engine,workers,tick}=runtime(t);
  workers[0].message({type:'ready'});
  const result=engine.execute({tree:{kind:'number',value:'2'},removeComputationLimit:true});
  tick(600000);
  assert.ok(engine.pending);assert.equal(workers.length,1);
  engine.cancel();
  assert.equal((await result).ok,false);assert.equal(workers[0].terminated,true);
  workers[1].message({type:'ready'});
  const limited=engine.execute({});tick(65000);
  assert.equal((await limited).ok,false);assert.equal(workers[1].terminated,true);
});

test('unlimited Python input resumes without reinstalling an execution timer',async t=>{
  const {engine,workers,tick}=runtime(t);
  workers[0].message({type:'ready'});
  const result=engine.execute({action:'python',removeComputationLimit:true},{onInput:async()=> 'answer'});
  workers[0].message({type:'input',id:engine.pending.id,inputId:1});
  await Promise.resolve();await Promise.resolve();
  tick(600000);
  assert.ok(engine.pending);assert.equal(workers.length,1);
  workers[0].message({type:'result',id:engine.pending.id,result:{ok:true}});
  assert.equal((await result).ok,true);
});
