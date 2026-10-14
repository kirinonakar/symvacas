import test from 'node:test';
import assert from 'node:assert/strict';
import {fork} from 'node:child_process';
import {parse} from '../parser.js';

test('packaged graph modules execute every graph kind in the production WASM worker', {timeout:60000}, async t=>{
  const worker=fork(new URL('./worker-bridge.mjs',import.meta.url),[],{execArgv:['--experimental-wasm-jspi']});
  t.after(()=>worker.kill());
  function receive(predicate){
    return new Promise((resolve,reject)=>{
      const timer=setTimeout(()=>done(new Error('Worker message timed out')),30000);
      function done(error,value){clearTimeout(timer);worker.off('message',message);worker.off('error',done);error?reject(error):resolve(value);}
      function message(value){if(value.type==='fatal')done(new Error(value.error));else if(predicate(value))done(null,value);}
      worker.on('message',message);worker.on('error',done);
    });
  }
  await receive(value=>value.type==='ready');
  let id=0;
  async function execute(request){
    const current=++id,pending=receive(value=>value.type==='result'&&value.id===current);
    worker.send({id:current,request});
    const result=(await pending).result;
    assert.equal(result.ok,true,result.error);
    return result;
  }
  const graph=(graphKind,source,options={})=>execute({action:'graph',graphKind,trees:[parse(source)],
    min:-1,max:1,yMin:-2,yMax:2,angle:'RAD',...options});

  const cartesian=await graph('cartesian','a*x',{parameters:{a:2},derivativeSelected:0});
  assert.equal(cartesian.derivativeCurveIndex,1);
  for(const [x,y] of cartesian.curves[0])assert.ok(Math.abs(y-2*x)<1e-12);
  const implicit=await graph('implicit','x^2+y^2=1');
  const contour=implicit.curves[0].filter(Boolean);
  assert.ok(contour.length>20);
  for(const [x,y] of contour)assert.ok(Math.abs(x*x+y*y-1)<1e-5);

  for(const [kind,source] of [['parametric','[a*cos(t),a*sin(t)]'],['polar','a']]){
    const result=await graph(kind,source,{variable:'t',min:0,max:Math.PI*2,parameters:{a:2}});
    const points=result.curves[0],positions=result.curveParameters[0];
    assert.equal(points.length,positions.length);
    assert.ok(points.length>30);
    for(let i=0;i<points.length;i++){
      assert.ok(Math.abs(points[i][0]-2*Math.cos(positions[i]))<1e-12);
      assert.ok(Math.abs(points[i][1]-2*Math.sin(positions[i]))<1e-12);
    }
  }
  const sequence=await graph('sequence','2*u(n-1)',{min:0,max:5,initialTrees:[parse('1')]});
  assert.deepEqual(sequence.curves[0],Array.from({length:6},(_,i)=>[i,2**i]));
  const differential=await graph('differential','y',{t0:0,initialValues:[1]});
  for(const [t,y] of differential.curves[0])assert.ok(Math.abs(y-Math.exp(t))<1e-8);

  const surface=await graph('surface','x+y',{surfaceYMin:-1,surfaceYMax:1,surfaceSamples:12});
  assert.ok(surface.surface.length>1);
  for(const row of surface.surface)for(const [x,y,z] of row)assert.ok(Math.abs(z-x-y)<1e-12);
  const space=await graph('space','[t,t^2,t^3]');
  assert.ok(space.spaceCurves[0].length>1);
  for(const [x,y,z] of space.spaceCurves[0]){
    assert.ok(Math.abs(y-x*x)<1e-12);
    assert.ok(Math.abs(z-x*x*x)<1e-12);
  }
  const integral=await execute({action:'graphAnalysis',trees:[parse('x')],analysis:'integral',a:0,b:1});
  assert.equal(integral.value,.5);
  assert.ok(integral.integralFill.length>0);
});
