// Exact reported 23-curve animation. Measures WASM worker round trips, not UI FPS.
// Run: node web/tests/benchmark-space-animation.mjs
import assert from 'node:assert/strict';
import {fork} from 'node:child_process';
import {performance} from 'node:perf_hooks';
import {writeFileSync} from 'node:fs';
import {graphInputTree} from '../graph-input.js';

export const sources=[
  '[cos(t+a),sin(t+a),t/4]',
  '[-cos(t+a),-sin(t+a),t/4]',
  '[(1-2*t)*cos(k*pi/2+a), (1-2*t)*sin(k*pi/2+a), k*pi/8] {0<t<1} {0<t<1, k=[0,0.2,0.4,0.6,0.8,1.0,1.2,1.4,1.6,1.8,2.0,2.2,2.4,2.6,2.8,3.0,3.2,3.4,3.6,3.8,4]}'
];
export const request={action:'graph',angle:'RAD',graphKind:'space',trees:sources.map(source=>graphInputTree(source,'space')),
  min:0,max:2*Math.PI,xMin:-5,xMax:5,yMin:-5,yMax:5,surfaceZMin:-5,surfaceZMax:5,samples:200,parameters:{a:0}};

if(process.argv.includes('--write-request')){
  writeFileSync(new URL('../../build/space-animation-request.json',import.meta.url),JSON.stringify(request));
}else{
  const worker=fork(new URL('./worker-bridge.mjs',import.meta.url),[],{execArgv:['--experimental-wasm-jspi']});
  let id=0;
  function receive(predicate){return new Promise((resolve,reject)=>{
    const timer=setTimeout(()=>done(new Error('Worker timed out')),60000);
    function done(error,value){clearTimeout(timer);worker.off('message',message);worker.off('error',done);error?reject(error):resolve(value);}
    function message(value){if(value.type==='fatal')done(new Error(value.error));else if(predicate(value))done(null,value);}
    worker.on('message',message);worker.on('error',done);
  });}
  try{
    await receive(value=>value.type==='ready');
    for(const samples of [200,500]){
      const durations=[];let last;
      for(let frame=0;frame<23;frame++){
        const current=++id,pending=receive(value=>value.type==='result'&&value.id===current),start=performance.now();
        worker.send({id:current,request:{...request,samples,parameters:{a:4*Math.sin(frame/7)}}});
        last=(await pending).result;
        const elapsed=performance.now()-start;
        assert.equal(last.ok,true,last.error);assert.equal(last.spaceCurves.length,23);assert.deepEqual(last.parameters,['a']);
        if(frame>=3)durations.push(elapsed);
      }
      durations.sort((a,b)=>a-b);
      console.log(JSON.stringify({samples,medianMs:+durations[10].toFixed(2),p95Ms:+durations[18].toFixed(2),
        points:last.spaceCurves.reduce((sum,curve)=>sum+curve.length,0),bytes:JSON.stringify(last).length}));
    }
  }finally{worker.kill();}
}
