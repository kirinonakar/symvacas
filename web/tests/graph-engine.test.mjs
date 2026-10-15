import test from 'node:test';
import assert from 'node:assert/strict';
import {fork} from 'node:child_process';
import {parse} from '../parser.js';
import {graphInputTree} from '../graph-input.js';
import {graphShadings} from '../graph-shading.js';

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
  const heartTree=graphInputTree('(-1+y^2/b^2+x^2/a^2)^3-x^2*y^3/(a^2*b^3)=0');
  for(const [a,b] of [[2,2],[1e-6,2],[2,1e-12],[-1e-80,1e-100],[0,1],[1,0],[-2,-2]]){
    const heart=await execute({action:'graph',graphKind:'cartesian',angle:'RAD',trees:[heartTree],
      min:-10,max:10,yMin:-5,yMax:5,samples:200,parameters:{a,b}});
    assert.deepEqual(heart.parameters,['a','b']);
    const points=heart.curves[0].filter(Boolean);
    if(a===0||b===0){assert.deepEqual(points,[]);continue;}
    assert.ok(points.length>100);
    for(const [x,y] of points){
      const u=x/a,v=y/b;
      assert.ok(Math.abs((u*u+v*v-1)**3-u*u*v**3)<1e-7);
    }
    assert.ok(Math.max(...points.map(point=>point[1]/b))>1.23);
    assert.ok(Math.min(...points.map(point=>point[1]/b))<-.99);
  }
  for(const [a,b] of [[4.9,4.9],[-4.9,4.9],[4.9,-4.9],[-4.9,-4.9]]){
    for(const [min,max,yMin,yMax] of [[-10,10,-5,5],[-1,3,-2,2]]){
      const heart=await execute({action:'graph',graphKind:'cartesian',angle:'RAD',trees:[heartTree],
        min,max,yMin,yMax,samples:200,parameters:{a,b}});
      let visible=false;
      for(let i=0;i<=2400&&!visible;i++){
        const u=-1.2+i/1000,c=Math.abs(u)**(2/3),d=c*c-4*u*u+4;
        if(d>=0)visible=[(c-Math.sqrt(d))/2,(c+Math.sqrt(d))/2]
          .some(v=>u*a>=min&&u*a<=max&&v*b>=yMin&&v*b<=yMax);
      }
      assert.equal(heart.curves[0].some(Boolean),visible);
      for(const [x,y] of heart.curves[0].filter(Boolean)){
        assert.ok(x>=min&&x<=max&&y>=yMin&&y<=yMax);
        const u=x/a,v=y/b;
        assert.ok(Math.abs((u*u+v*v-1)**3-u*u*v**3)<1e-7);
      }
    }
  }
  for(const [a,b] of [[1,0],[-3,.7],[0,1],[6,2]]){
    const animated=await execute({action:'graph',graphKind:'cartesian',angle:'RAD',
      trees:['a \\cdot \\sin\\left(x+b\\right)','a \\cdot \\cos\\left(x+b\\right) > y'].map(source=>graphInputTree(source)),
      parameters:{a,b},min:-10,max:10,yMin:-5,yMax:5,samples:200});
    assert.deepEqual(animated.parameters,['a','b']);
    const shade=animated.shadings[0];
    assert.deepEqual(shade.boundaryStyles,['dashed']);
    assert.ok(shade.fill.length<=5);
    assert.ok(JSON.stringify(animated).length<60000);
    for(const [x,y] of animated.curves[0].filter(Boolean))assert.ok(Math.abs(y-a*Math.sin(x+b))<1e-10);
    for(const [x,y] of shade.boundary[0].filter(Boolean))assert.ok(Math.abs(y-a*Math.cos(x+b))<1e-8);
    for(const polygon of shade.fill)for(const [x,y] of polygon){assert.ok(y<=a*Math.cos(x+b)+1e-8);assert.ok(y>=-5&&y<=5);}
    const band=await execute({action:'graph',graphKind:'cartesian',angle:'RAD',
      trees:[graphInputTree('a \\cdot \\sin\\left(x+b\\right) < y < a \\cdot \\cos\\left(x+b\\right)')],
      parameters:{a,b},min:-10,max:10,yMin:-5,yMax:5,samples:200});
    assert.deepEqual(band.shadings[0].boundaryStyles,['dashed','dashed']);
    assert.ok(band.shadings[0].fill.length<=5);
    if(a===0){assert.deepEqual(band.shadings[0].fill,[]);assert.deepEqual(band.shadings[0].boundary,[[],[]]);}
    for(const polygon of band.shadings[0].fill)for(const [x,y] of polygon){
      assert.ok(y>=a*Math.sin(x+b)-1e-8&&y<=a*Math.cos(x+b)+1e-8);
      assert.ok(y>=-5&&y<=5);
    }
  }
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
  const mixed=await execute({action:'graph',graphKind:'cartesian',angle:'RAD',
    trees:['y = x^2','x^2 + y^2 = 9','r = 2cos(3θ)','(cos(t), sin(t))','x^2+y^2<4','y\\ge x^2-2'].map(source=>graphInputTree(source)),
    min:-4,max:4,yMin:-4,yMax:4,parameterMin:0,parameterMax:2*Math.PI});
  assert.deepEqual(mixed.curveKinds,['cartesian','cartesian','polar','parametric','inequality','inequality']);
  assert.deepEqual(mixed.parameters,[]);
  assert.deepEqual(mixed.curveStyles.slice(4),['dashed','solid']);
  assert.deepEqual(mixed.shadings.map(shade=>shade.sourceIndex),[4,5]);
  assert.deepEqual(mixed.shadings.map(shade=>shade.boundaryStyles),[['dashed'],['solid']]);
  assert.ok(mixed.shadings[0].boundary[0].length>100);
  assert.ok(!mixed.shadings[0].boundary[0].includes(null));
  const shaded=await execute({action:'graph',graphKind:'cartesian',angle:'RAD',trees:[],min:-4,max:4,yMin:-4,yMax:4,
    shadings:graphShadings('[s] -1<x<=1, -2<=y<x\n[s] y>x','cartesian')});
  assert.deepEqual(shaded.shadings.map(shade=>shade.boundaryStyles),[['solid','dashed','dashed','solid'],['dashed']]);
  for(const [index,shade] of mixed.shadings.entries()){
    assert.ok(shade.fill.length);
    for(const polygon of shade.fill)for(const [x,y] of polygon){
      assert.ok(index===0?x*x+y*y<=4.0001:y-x*x+2>=-.0001);
    }
  }
  const separateRanges=await execute({action:'graph',graphKind:'cartesian',angle:'RAD',trees:['(cos(t),sin(t))','r=2cos(3θ)'].map(source=>graphInputTree(source)),
    min:-4,max:4,yMin:-4,yMax:4,parameterMin:1,parameterMax:2,thetaMin:-.5,thetaMax:.5});
  assert.deepEqual(separateRanges.curveParameters.map(values=>[values[0],values.at(-1)]),[[1,2],[-.5,.5]]);
  const logarithmic=await graph('cartesian','10^x',{min:-3,max:3,yMin:.001,yMax:1000,yLog:true});
  assert.ok(logarithmic.curves[0].filter(Boolean).length<=10);
  for(const [x,y] of logarithmic.curves[0].filter(Boolean))assert.ok(Math.abs(x-Math.log10(y))<1e-10);
  const logImplicit=await graph('cartesian','x^2+y^2=1',{min:-2,max:2,yMin:.001,yMax:2,yLog:true});
  for(const [x,y] of logImplicit.curves[0].filter(Boolean)){assert.ok(y>0);assert.ok(Math.abs(x*x+y*y-1)<1e-4);}
  const thetaPolar=await graph('polar','r=2*cos(3*theta)',{variable:'t',min:0,max:2*Math.PI});
  assert.ok(thetaPolar.curveParameters[0].length>30);
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
