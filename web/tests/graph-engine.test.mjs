import test from 'node:test';
import assert from 'node:assert/strict';
import {fork} from 'node:child_process';
import {readFileSync} from 'node:fs';
import {parse} from '../parser.js';
import {graphInputTree} from '../graph-input.js';
import {latexPaste} from '../math-input.js';
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

  const algebraicTrees=[String.raw`\frac{1}{a} \cdot x`,String.raw`x^{2}+y^{3} = a`].map(source=>graphInputTree(source));
  for(const a of [0,1]){
    const result=await execute({action:'graph',graphKind:'cartesian',angle:'RAD',trees:algebraicTrees,
      min:-10,max:10,yMin:-5,yMax:5,samples:200,parameters:{a}});
    assert.deepEqual(result.parameters,['a']);
    const [line,cubic]=result.curves;
    if(a===0)assert.deepEqual(line,[]);
    else{
      assert.ok(line.length<=4);
      assert.ok(line.some(([x,y])=>x===0&&y===0));
      for(const [x,y] of line)assert.ok(Math.abs(x-a*y)<1e-12);
    }
    assert.ok(cubic.length>0&&cubic.length<350);
    for(const point of cubic)if(point){
      const [x,y]=point;
      assert.ok(Math.abs(x*x+y**3-a)<1e-9);
      assert.ok(x>=-10-1e-9&&x<=10+1e-9&&y>=-5-1e-9&&y<=5+1e-9);
    }
    if(a>0)for(const root of [-Math.sqrt(a),Math.sqrt(a)]){
      assert.ok(cubic.some(point=>point&&Math.abs(point[0]-root)<1e-12&&point[1]===0));
    }
  }

  // Reported bare-comma input must fill the intersection, not two independent regions.
  for(const [source,expectedArea,inside,styles] of [
    ['-1<x<1, -1<y<x',2,(x,y)=>x>=-1-1e-8&&x<=1+1e-8&&y>=-1-1e-8&&y<=x+1e-8,['dashed','dashed','dashed','dashed']],
    ['(x^2+y^2)<4, y>=0',2*Math.PI,(x,y)=>x*x+y*y<=4.001&&y>=-1e-8,['dashed','solid']],
  ]){
    const result=await execute({action:'graph',graphKind:'cartesian',angle:'RAD',trees:[graphInputTree(source)],
      min:-3,max:3,yMin:-3,yMax:3,samples:500});
    assert.deepEqual(result.curveKinds,['inequality']);
    assert.equal(result.curves.length,1);
    assert.equal(result.shadings.length,1);
    const shade=result.shadings[0];
    assert.equal(shade.sourceIndex,0);
    assert.deepEqual(shade.boundaryStyles,styles);
    let area=0;
    for(const polygon of shade.fill){
      for(const [x,y] of polygon)assert.ok(inside(x,y),`${source}: ${x},${y}`);
      area+=Math.abs(polygon.reduce((sum,p,i)=>{const next=polygon[(i+1)%polygon.length];return sum+p[0]*next[1]-p[1]*next[0];},0))/2;
    }
    assert.ok(Math.abs(area-expectedArea)<.04,`${source}: area ${area}`);
  }

  const cartesian=await graph('cartesian','a*x',{parameters:{a:2},derivativeSelected:0});
  assert.equal(cartesian.derivativeCurveIndex,1);
  for(const [x,y] of cartesian.curves[0])assert.ok(Math.abs(y-2*x)<1e-12);
  const [relaxationLatex]=readFileSync(new URL('../../math/src/test/resources/latex-input.tsv',import.meta.url),'utf8')
    .split(/\r?\n/).find(line=>line.startsWith(String.raw`\operatorname{f}\left(x\right) = \begin{cases}`)).split('\t');
  const relaxation=await execute({action:'graph',graphKind:'cartesian',angle:'RAD',trees:[graphInputTree(relaxationLatex)],
    min:-100,max:3400,yMin:-1,yMax:2,samples:300,parameters:{T1:900,T2:80,TR:3000,TE:200}});
  assert.deepEqual(relaxation.parameters,['T1','T2','TE','TR']);
  const relaxationPoints=relaxation.curves[0].filter(Boolean);
  assert.ok(relaxationPoints.some(([x])=>x===0));
  assert.ok(relaxationPoints.some(([x])=>x===3000));
  assert.ok(relaxationPoints.some(([x])=>x>3000));
  for(const [x,y] of relaxationPoints){
    assert.ok(x>=0&&x<3200);
    const expected=x<=3000?1-Math.exp(-x/900):(1-Math.exp(-3000/900))*Math.exp(-(x-3000)/80);
    assert.ok(Math.abs(y-expected)<1e-10);
  }
  const heartTree=graphInputTree('(-1+y^2/b^2+x^2/a^2)^3-x^2*y^3/(a^2*b^3)=0');
  for(const [a,b] of [[2,2],[-1e-80,1e-100],[0,1],[1,0]]){
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
  for(const [a,b] of [[4.9,4.9],[-4.9,-4.9]]){
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
  for(const [a,b] of [[-3,.7],[0,1]]){
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

  // Use the reported paste text through the production parser and WASM graph engine.
  const roseTree=graphInputTree(String.raw`\[
(x^2+y^2)^4=
\left[
(x^3-3xy^2)\cos t+
(3x^2y-y^3)\sin t
\right]^2
\]`);
  for(const graphKind of ['cartesian','implicit'])for(const phase of [0,.4]){
    const rose=await execute({action:'graph',graphKind,angle:'RAD',trees:[roseTree],
      min:-10,max:10,yMin:-5,yMax:5,samples:200,...(phase===undefined?{}:{parameters:{t:phase}})});
    assert.deepEqual(rose.parameters,['t']);
    const points=rose.curves[0].filter(Boolean),t=phase??1;
    assert.ok(points.length>100);
    const petals=[[]];
    for(const point of rose.curves[0]){if(point===null)petals.push([]);else petals.at(-1).push(point);}
    assert.equal(petals.length,6);
    for(const path of petals){
      assert.ok(path[0].every(value=>value===0));
      assert.deepEqual(path[0],path.at(-1));
      assert.ok(path.filter(([x,y])=>Math.hypot(x,y)>0&&Math.hypot(x,y)<.3).length>=6);
    }
    for(const [x,y] of points){
      const radius2=x*x+y*y,wave=(x**3-3*x*y*y)*Math.cos(t)+(3*x*x*y-y**3)*Math.sin(t);
      assert.ok(Math.abs(radius2**4-wave**2)<1e-6);
    }
    for(let petal=0;petal<6;petal++){
      const angle=t/3+petal*Math.PI/3,peak=[Math.cos(angle),Math.sin(angle)];
      assert.ok(points.some(([x,y])=>Math.hypot(x-peak[0],y-peak[1])<.15));
    }
  }

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
  const [alignedBody,alignedExpected]=readFileSync(new URL('../../math/src/test/resources/latex-input.tsv',import.meta.url),'utf8').split(/\r?\n/)
    .find(line=>line.startsWith(String.raw`\begin{aligned}r&=`)).split('\t');
  const alignedPaste=latexPaste(`\\[\n${alignedBody.replaceAll(String.raw`\\`,'\\\\\n')}\n\\]`,{multiline:true,surface:true});
  assert.equal(alignedPaste,alignedExpected);
  for(const time of [0,.7]){
    const sampled=await graph('surface',alignedPaste,{min:-4,max:4,surfaceYMin:-4,surfaceYMax:4,surfaceUMin:0,surfaceUMax:2*Math.PI,surfaceVMin:0,surfaceVMax:Math.PI,surfaceSamples:48,parameters:{t:time}});
    assert.deepEqual(sampled.parameters,['t']);assert.equal(sampled.parametricSurface,true);
    for(const [j,row] of sampled.surface.entries())for(const [i,p] of row.entries()){
      const u=2*Math.PI*i/48,v=Math.PI*j/48,r=2+Math.sin(7*u+2*time)*Math.sin(v)**2;
      [r*Math.sin(v)*Math.cos(u),r*Math.sin(v)*Math.sin(u),2*Math.cos(v)+.3*Math.sin(7*u-2*time)*Math.sin(v)].forEach((n,axis)=>assert.ok(Math.abs(n-p[axis])<1e-12));
    }
  }
  const radialSource=String.raw`\frac{\sin\left(a \cdot x^{2}+a \cdot y^{2}\right)}{\left(x^{2}+y^{2}\right)}`;
  for(const a of [1,0]){
    const radial=await execute({action:'graph',graphKind:'surface',angle:'RAD',trees:[graphInputTree(radialSource,'surface')],
      min:-10,max:10,surfaceYMin:-5,surfaceYMax:5,surfaceSamples:96,parameters:{a}});
    assert.deepEqual(radial.parameters,['a']);
    assert.deepEqual(radial.surfaceRings[0],[0,a,0,1]);
    for(const [radius,z] of radial.surfaceRings){
      const r=radius*radius,expected=r===0?a:Math.sin(a*r)/r;
      assert.ok(Math.abs(z-expected)<1e-12);
    }
  }
  const space=await graph('space','[t,t^2,t^3]');
  assert.ok(space.spaceCurves[0].length>1);
  for(const [x,y,z] of space.spaceCurves[0]){
    assert.ok(Math.abs(y-x*x)<1e-12);
    assert.ok(Math.abs(z-x*x*x)<1e-12);
  }
  const narrowSpace=await graph('space','C(t)=(t,k,a) {0.1234<t<0.1235,k=[0,1]}');
  assert.ok(narrowSpace.spaceCurves.every(curve=>curve.length===2&&curve.every(([t])=>t>.1234&&t<.1235)));
  const integral=await execute({action:'graphAnalysis',trees:[parse('x')],analysis:'integral',a:0,b:1});
  assert.equal(integral.value,.5);
  assert.ok(integral.integralFill.length>0);

  const solutions=await execute({tree:parse('solveset(sin(x) + 3*cos(x), x, domain=S.Reals)'),
    angle:'RAD',variables:{x:{kind:'number',value:'99'}}});
  assert.equal(solutions.tree.kind,'rows');
  assert.equal(solutions.tree.args.filter(row=>row.value==='solutions').length,2);
  assert.equal(solutions.tree.args.filter(row=>row.value==='branch').length,2);
  assert.ok(solutions.exact.includes('atan(3)'));
  assert.ok(solutions.exact.includes('∈ ℤ'));
  assert.ok(!solutions.exact.includes('ImageSet'));
});
