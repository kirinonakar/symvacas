// Production WASM sampling and CPU geometry costs; excludes actual GPU/device FPS.
// Run: node web/tests/benchmark-surface-animation.mjs
import assert from 'node:assert/strict';
import {fork} from 'node:child_process';
import {performance} from 'node:perf_hooks';
import {graphInputTree} from '../graph-input.js';
import {prepareSurfaceFaces,radialSurfaceGeometry} from '../surface-geometry.js';
import {surfaceGpuGeometry} from '../surface-gpu.js';

const worker=fork(new URL('./worker-bridge.mjs',import.meta.url),[],{execArgv:['--experimental-wasm-jspi']});
let id=0;
function receive(predicate){
  return new Promise((resolve,reject)=>{
    const timer=setTimeout(()=>done(new Error('Worker timed out')),60000);
    function done(error,value){clearTimeout(timer);worker.off('message',message);worker.off('error',done);error?reject(error):resolve(value);}
    function message(value){if(value.type==='fatal')done(new Error(value.error));else if(predicate(value))done(null,value);}
    worker.on('message',message);worker.on('error',done);
  });
}
async function execute(request){
  const current=++id,pending=receive(value=>value.type==='result'&&value.id===current);
  worker.send({id:current,request});const result=(await pending).result;
  assert.equal(result.ok,true,result.error);return result;
}
try{
  await receive(value=>value.type==='ready');
  for(const count of [32,96]){
    const request={action:'graph',angle:'RAD',graphKind:'surface',trees:[graphInputTree('sin(a*x^2+a*y^2)/(x^2+y^2)','surface')],
      min:-10,max:10,surfaceYMin:-5,surfaceYMax:5,surfaceSamples:count};
    const sampling=[],prepare=[],buffers=[];
    for(let i=0;i<23;i++){
      let start=performance.now();
      const result=await execute({...request,parameters:{a:3*Math.sin(i/20)}});
      const sampleMs=performance.now()-start;
      start=performance.now();
      const radial=result.surfaceRings?radialSurfaceGeometry(result.surfaceRings):null;
      const prepared=prepareSurfaceFaces(result.surface,{xmin:-10,xmax:10,ymin:-5,ymax:5,zmin:result.zMin,zmax:result.zMax},radial?.triangles,radial?.normals);
      const prepareMs=performance.now()-start;
      start=performance.now();surfaceGpuGeometry(prepared);const bufferMs=performance.now()-start;
      if(i>=3){sampling.push(sampleMs);prepare.push(prepareMs);buffers.push(bufferMs);}
    }
    const median=values=>+values.sort((a,b)=>a-b)[10].toFixed(2);
    console.log(JSON.stringify({count,samplingMedianMs:median(sampling),prepareMedianMs:median(prepare),buffersMedianMs:median(buffers)}));
  }
}finally{worker.kill();}
