// Real production WASM worker, without browser/UI overhead.
// Run: node web/tests/benchmark-graph-animation.mjs
import assert from 'node:assert/strict';
import {fork} from 'node:child_process';
import {performance} from 'node:perf_hooks';
import {graphInputTree} from '../graph-input.js';

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
  worker.send({id:current,request});
  const result=(await pending).result;
  assert.equal(result.ok,true,result.error);
  return result;
}
try{
  await receive(value=>value.type==='ready');
  const heart='(-1+y^2/b^2+x^2/a^2)^3-x^2*y^3/(a^2*b^3)=0';
  const nearZero=[{a:1e-6,b:2},{a:2,b:1e-12},{a:-1e-80,b:1e-100},{a:0,b:1},{a:1,b:0},{a:-2,b:-2}];
  for(const [sources,scenario] of [[['a*sin(x+b)'],'normal'],[['a*cos(x+b)>y'],'normal'],[['a*sin(x+b)','a*cos(x+b)>y'],'normal'],[['a*sin(x+b)<y<a*cos(x+b)'],'normal'],[[heart],'normal'],[[heart],'near-zero']]){
    const parameters=i=>scenario==='near-zero'?nearZero[i%nearZero.length]:sources[0]===heart?{a:2+Math.sin(i/20),b:1.5+.5*Math.cos(i/20)}:{a:3*Math.sin(i/20),b:i/20};
    const request={action:'graph',angle:'RAD',graphKind:'cartesian',trees:sources.map(source=>graphInputTree(source)),min:-10,max:10,yMin:-5,yMax:5,samples:200};
    for(let i=0;i<3;i++)await execute({...request,parameters:sources[0]===heart?parameters(i):{a:1+i/10,b:i/10}});
    const times=[];let result;
    for(let i=0;i<30;i++){
      const start=performance.now();
      result=await execute({...request,parameters:parameters(i)});
      times.push(performance.now()-start);
    }
    times.sort((a,b)=>a-b);
    console.log(JSON.stringify({sources,scenario,medianMs:+times[15].toFixed(2),p95Ms:+times[28].toFixed(2),responseBytes:Buffer.byteLength(JSON.stringify(result)),polygons:result.shadings?.reduce((sum,shade)=>sum+shade.fill.length,0)||0}));
  }
}finally{worker.kill();}
