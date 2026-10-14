import test from 'node:test';
import assert from 'node:assert/strict';
import {graphSamplingInterval,graphPreviewRequest,graphSamplingIdentity} from '../graph-sampling.js';
import {createGraphComputation} from '../graph-computation.js';

function clock(){
  let now=0,id=0;const timers=new Map();
  return {
    setTimer(callback,delay){const key=++id;timers.set(key,{callback,at:now+delay});return key;},
    clearTimer(key){timers.delete(key);},
    advance(ms){const end=now+ms;while(true){const entry=[...timers].sort((a,b)=>a[1].at-b[1].at)[0];if(!entry||entry[1].at>end)break;now=entry[1].at;timers.delete(entry[0]);entry[1].callback();}now=end;},
    get now(){return now;}
  };
}

test('continuous dragging samples every 80ms instead of waiting for release',()=>{
  const time=clock(),samples=[];let view=0;
  const sampler=graphSamplingInterval(()=>samples.push({at:time.now,view}),time);
  for(let i=0;i<30;i++){view=i;sampler.schedule();time.advance(16);}
  assert.deepEqual(samples.map(sample=>sample.at),[80,160,240,320,400,480]);
  assert.deepEqual(samples.map(sample=>sample.view),[4,9,14,19,24,29]);
  sampler.schedule();sampler.cancel();time.advance(100);
  assert.equal(samples.length,6);
  sampler.schedule();time.advance(80);assert.equal(samples.length,7);
});

const request={action:'graph',graphKind:'cartesian',trees:[{kind:'symbol',value:'x'}],min:-10,max:10,xMin:-10,xMax:10,yMin:-5,yMax:5,surfaceYMin:-5,surfaceYMax:5,samples:500,parameters:{a:1},derivativeSelected:0,precision:15};

test('preview fills a margin without changing the visible bounds or source request',()=>{
  const preview=graphPreviewRequest(request);
  assert.deepEqual([preview.min,preview.max,preview.xMin,preview.xMax,preview.yMin,preview.yMax],[-13,13,-13,13,-6.5,6.5]);
  assert.equal(preview.samples,200);assert.equal(request.min,-10);assert.equal(request.samples,500);
  assert.equal(graphSamplingIdentity(preview),graphSamplingIdentity(request));
  assert.equal(graphSamplingIdentity({...request,min:20,max:40,xMin:20,xMax:40,yMin:0,yMax:10}),graphSamplingIdentity(request));
});

test('sampling identity rejects changed expressions, derivatives, parameters and options',()=>{
  for(const changed of [{trees:[{kind:'symbol',value:'y'}]},{graphKind:'implicit'},{derivativeSelected:1},{secondDerivativeSelected:0},{parameters:{a:2}},{precision:30}]){
    assert.notEqual(graphSamplingIdentity({...request,...changed}),graphSamplingIdentity(request));
  }
  for(const graphKind of ['parametric','polar','differential','sequence']){
    const other={...request,graphKind,min:0,max:10};
    assert.notEqual(graphSamplingIdentity({...other,max:20}),graphSamplingIdentity(other));
    const preview=graphPreviewRequest(other);
    assert.deepEqual([preview.min,preview.max],[0,10]);
  }
});

test('animation requests run in the background and stopping rejects an old frame before precise refinement',async()=>{
  const state={animation:{},active:false,running:false,pending:false,viewDragging:false,revision:0,analysisRevision:0,parameters:{a:1},derivative:null,secondDerivative:null};
  const fields={'graph-source':'a*sin(x)','graph-status':'','graph-min':-10,'graph-max':10};
  const requests=[];let complete,draws=0,renders=0;
  const noop=()=>{};
  const computation=createGraphComputation({
    $:id=>({get textContent(){return fields[id];},set textContent(value){fields[id]=value;}}),
    state,surface:{},kind:()=> 'cartesian',value:id=>fields[id]??'',numeric:id=>Number(fields[id]??0),
    expressions:()=>[fields['graph-source']],sourceDrafts:{cartesian:fields['graph-source']},
    currentBounds:()=>({xmin:-10,xmax:10,ymin:-5,ymax:5}),options:()=>({}),
    execute:(request,options)=>{requests.push({request,options});return new Promise(resolve=>{complete=resolve;});},
    isBusy:()=>false,isReady:()=>true,onError:message=>assert.fail(message),
    clearPlot:noop,parameterControls:noop,selections:noop,persist:noop,densityControls:noop,
    queueDraw:()=>draws++,render:()=>renders++,viewSampler:{schedule:noop}
  });
  let running=computation.run();
  assert.equal(requests[0].options.background,true);
  assert.equal(requests[0].request.samples,200);
  const first={ok:true,curves:[[[0,0]]],parameters:['a']};
  complete(first);await running;
  assert.equal(state.result,first);assert.equal(draws,1);assert.equal(renders,0);

  running=computation.run();
  state.parameters.a=2;state.animation=null;state.pending=true;
  complete({ok:true,curves:[[[0,99]]],parameters:['a']});await running;
  assert.equal(state.result,first,'a pre-stop parameter frame cannot overwrite the final state');
  assert.equal(state.pending,true);
  assert.equal(draws,1);

  running=computation.run();
  assert.equal(requests[2].options.background,false);
  assert.equal(requests[2].request.samples,500);
  assert.deepEqual(requests[2].request.parameters,{a:2});
  const final={ok:true,curves:[[[0,0]]],parameters:['a']};
  complete(final);await running;
  assert.equal(state.result,final);assert.equal(renders,1);assert.equal(state.pending,false);
});
