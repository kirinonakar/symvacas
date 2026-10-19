import test from 'node:test';
import assert from 'node:assert/strict';
import {fork} from 'node:child_process';
import {readFileSync} from 'node:fs';
import {parse} from '../parser.js';
import {graphInputTree} from '../graph-input.js';
import {latexPaste} from '../math-input.js';
import {graphShadings} from '../graph-shading.js';
import {radialSurfaceGeometry,prepareSurfaceFaces} from '../surface-geometry.js';

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

  const animatedComma=graphInputTree('-1<x<1, -1<y<ax');
  for(const a of [0,1e-12,-1e-12,1,-1,2.3,-2.3,4,-4]){
    const result=await execute({action:'graph',graphKind:'cartesian',angle:'RAD',trees:[animatedComma],
      min:-10,max:10,yMin:-5,yMax:5,samples:200,parameters:{a}});
    assert.deepEqual(result.parameters,['a']);
    const shade=result.shadings[0];
    assert.equal(shade.fill.length,1);
    assert.deepEqual(shade.boundaryStyles,['dashed','dashed','dashed','dashed']);
    const polygon=shade.fill[0];
    assert.ok(polygon.length<=8);
    for(const [x,y] of polygon)assert.ok(x>=-1-1e-10&&x<=1+1e-10&&y>=-1-1e-10&&y<=a*x+1e-10);
    const area=Math.abs(polygon.reduce((sum,p,i)=>{const q=polygon[(i+1)%polygon.length];return sum+p[0]*q[1]-q[0]*p[1];},0))/2;
    const amplitude=Math.abs(a),expected=amplitude<=1?2:1+(amplitude+1/amplitude)/2;
    assert.ok(Math.abs(area-expected)<1e-9,`a=${a}: area ${area}`);
  }

  // Exact reported LaTeX must reach the shared analytic contour path after
  // parsing and WASM packaging, with real-domain and denominator semantics.
  const radialSineSources=[
    String.raw`\frac{\sin\left(a \cdot x^{2}+a \cdot y^{2}\right)}{\left(x^{2}+y^{2}\right)}`,
    String.raw`\sin\left(\sqrt{a \cdot x^{2}+a \cdot y^{2}}\right)`,
  ];
  for(const [index,source] of radialSineSources.entries()){
    const tree=graphInputTree(source);
    for(const a of [1e-12,-1e-12,.3,1,-1,5])for(const view of [[-10,10,-5,5],[2,4,-1,1]]){
      const [min,max,yMin,yMax]=view;
      const result=await execute({action:'graph',graphKind:'cartesian',angle:'RAD',trees:[tree],
        min,max,yMin,yMax,samples:200,parameters:{a}});
      assert.deepEqual(result.implicitCurves,[true]);
      assert.deepEqual(result.parameters,['a']);
      const radii=new Set();let previous=null;
      for(const point of result.curves[0]){
        if(point===null){previous=null;continue;}
        const [x,y]=point,r=Math.hypot(x,y);
        assert.ok(x>=min-1e-9&&x<=max+1e-9&&y>=yMin-1e-9&&y<=yMax+1e-9);
        if(index===0)assert.ok(r>0,'The denominator excludes the origin');
        if(previous)assert.ok(Math.abs(r-Math.hypot(...previous))<1e-9,'Separate circles must not connect');
        const phase=index===0?a*r*r:Math.sqrt(Math.max(0,a*r*r));
        assert.ok(Math.abs(Math.sin(phase))<1e-10);
        if(index===1&&a<0)assert.equal(r,0);
        radii.add(r.toFixed(8));previous=point;
      }
      const nearest=(lo,hi)=>lo<=0&&hi>=0?0:Math.min(Math.abs(lo),Math.abs(hi));
      const rmin=Math.hypot(nearest(min,max),nearest(yMin,yMax));
      const rmax=Math.hypot(Math.max(Math.abs(min),Math.abs(max)),Math.max(Math.abs(yMin),Math.abs(yMax)));
      const expected=new Set();
      if(index===1&&rmin===0)expected.add((0).toFixed(8));
      if(index===0||a>0){
        const last=Math.floor((index===0?Math.abs(a)*rmax*rmax:Math.sqrt(a)*rmax)/Math.PI);
        for(let n=1;n<=last;n++){
          const radius=index===0?Math.sqrt(n*Math.PI/Math.abs(a)):n*Math.PI/Math.sqrt(a);
          if(radius>=rmin)expected.add(radius.toFixed(8));
        }
      }
      assert.deepEqual(radii,expected,`${source}, a=${a}, view=${view}`);
    }
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
  const animatedPiecewise=graphInputTree('f(x)={0<=x<=TR:1-e^(-x/T1),TR<x<TR+TE:(1-e^(-TR/T1))*e^(-(x-TR)/T2)}');
  for(const [TR,TE,T1,T2] of [[3,4,1,2],[2.25,.00001,.5,1],[-1,3,2,1],[2,-1,1,2],[0,2,1,2],[3,4,1,0],[3,4,0,2]]){
    const animated=await execute({action:'graph',graphKind:'cartesian',angle:'RAD',trees:[animatedPiecewise],
      min:-2,max:10,yMin:-1,yMax:2,samples:200,parameters:{TR,TE,T1,T2}});
    assert.deepEqual(animated.parameters,['T1','T2','TE','TR']);
    assert.deepEqual(animated.implicitCurves,[false]);
    const points=animated.curves[0].filter(Boolean);
    if(T1===0){assert.deepEqual(points,[]);continue;}
    assert.ok(points.length>=2);
    for(const [x,y] of points){
      const first=0<=x&&x<=TR;
      assert.ok(first||TR<x&&x<TR+TE&&T2!==0);
      const expected=first?1-Math.exp(-x/T1):(1-Math.exp(-TR/T1))*Math.exp(-(x-TR)/T2);
      assert.ok(Math.abs(y-expected)<=1e-9*Math.max(1,Math.abs(expected)));
    }
  }
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

  // Use the reported paste text through the production parser and WASM graph engine.
  const roseTree=graphInputTree(String.raw`\[
(x^2+y^2)^4=
\left[
(x^3-3xy^2)\cos t+
(3x^2y-y^3)\sin t
\right]^2
\]`);
  for(const graphKind of ['cartesian','implicit'])for(const phase of [undefined,0,.4,Math.PI/2]){
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
  const torusSource='[R=2+0.35*sin(6*u-3*t),x=(R+cos(v))*cos(u),y=(R+cos(v))*sin(u),z=sin(v)]';
  const wavesSource='[r1=sqrt((x-2)^2+y^2),r2=sqrt((x+2)^2+y^2),z=sin(4*r1-5*t)/(1+0.2*r1)+sin(4*r2-5*t)/(1+0.2*r2)]';
  const vortexSource=String.raw`z = e^{\left(\left(-0.08\right) \cdot \left(x^{2}+y^{2}\right)\right)} \cdot \sin\left(5 \cdot \operatorname{atan2}\left(y, x\right)-2 \cdot \sqrt{x^{2}+y^{2}}-3 \cdot t\right)`;
  for(const time of [0,.7]){
    const request={action:'graph',graphKind:'surface',angle:'RAD',min:-4,max:4,surfaceYMin:-4,surfaceYMax:4,surfaceSamples:48,parameters:{t:time}};
    const torus=await execute({...request,trees:[graphInputTree(torusSource,'surface')],surfaceUMin:0,surfaceUMax:2*Math.PI,surfaceVMin:-Math.PI,surfaceVMax:Math.PI});
    assert.equal(torus.parametricSurface,true);assert.deepEqual(torus.parameters,['t']);
    for(const [j,row] of torus.surface.entries())for(const [i,p] of row.entries()){
      const u=2*Math.PI*i/48,v=-Math.PI+2*Math.PI*j/48,r=2+.35*Math.sin(6*u-3*time)+Math.cos(v);
      [r*Math.cos(u),r*Math.sin(u),Math.sin(v)].forEach((n,axis)=>assert.ok(Math.abs(n-p[axis])<1e-12));
    }
    const waves=await execute({...request,trees:[graphInputTree(wavesSource,'surface')]});
    assert.deepEqual(waves.parameters,['t']);
    for(const row of waves.surface)for(const [x,y,z] of row){
      const expected=[Math.hypot(x-2,y),Math.hypot(x+2,y)].reduce((sum,r)=>sum+Math.sin(4*r-5*time)/(1+.2*r),0);
      assert.ok(Math.abs(z-expected)<1e-12);
    }
    const vortex=await execute({...request,trees:[graphInputTree(vortexSource,'surface')]});
    assert.equal(vortex.angularSurface,true);assert.deepEqual(vortex.parameters,['t']);
    for(const row of vortex.surface)for(const [x,y,z] of row){
      assert.ok(Math.hypot(x,y)>0);
      const expected=Math.exp(-.08*(x*x+y*y))*Math.sin(5*Math.atan2(y,x)-2*Math.hypot(x,y)-3*time);
      assert.ok(Math.abs(z-expected)<1e-12);
    }
    const box={xmin:-4,xmax:4,ymin:-4,ymax:4,zmin:-1,zmax:1};
    for(const sampled of [torus,vortex]){
      const geometry=prepareSurfaceFaces(sampled.surface,box);
      assert.ok(geometry.faces.length>2000);
      assert.ok(geometry.faces.every(face=>face.levels?.every(Number.isFinite)));
    }
    const mixed=await execute({...request,trees:[graphInputTree(torusSource,'surface'),graphInputTree(wavesSource,'surface'),parse('z=x+y')]});
    assert.equal(mixed.surfaces.length,3);assert.deepEqual(mixed.parameters,['t']);
  }
  for(const a of [1,4,0,-1]){
    const root=await execute({action:'graph',graphKind:'surface',angle:'RAD',trees:[graphInputTree('sin(sqrt(ax^2+ay^2))','surface')],
      min:-3,max:3,surfaceYMin:-3,surfaceYMax:3,surfaceSamples:48,parameters:{a}});
    assert.deepEqual(root.parameters,['a']);
    if(a<0)assert.equal(root.surface.flat().filter(Boolean).length,1);
    else for(const row of root.surface)for(const [x,y,z] of row)assert.ok(Math.abs(z-Math.sin(Math.sqrt(a*(x*x+y*y))))<1e-12);
  }
  const radialSource=String.raw`\frac{\sin\left(a \cdot x^{2}+a \cdot y^{2}\right)}{\left(x^{2}+y^{2}\right)}`;
  for(const a of [1,2,-3,0,1e-12,20,100]){
    const radial=await execute({action:'graph',graphKind:'surface',angle:'RAD',trees:[graphInputTree(radialSource,'surface')],
      min:-10,max:10,surfaceYMin:-5,surfaceYMax:5,surfaceSamples:96,parameters:{a}});
    assert.deepEqual(radial.parameters,['a']);
    assert.deepEqual(radial.surfaceRings[0],[0,a,0,1]);
    for(const [radius,z] of radial.surfaceRings){
      const r=radius*radius,expected=r===0?a:Math.sin(a*r)/r;
      assert.ok(Math.abs(z-expected)<1e-12);
    }
    if(Math.abs(a)>=1){
      const geometry=radialSurfaceGeometry(radial.surfaceRings);
      for(const face of geometry.triangles){
        const [x,y,z]=[0,1,2].map(axis=>face.reduce((sum,p)=>sum+p[axis],0)/3),r=x*x+y*y;
        const error=Math.abs(z-(r===0?a:Math.sin(a*r)/r))*200/(1.2173*Math.abs(a));
        assert.ok(error<1.5,`a=${a}: projected mesh error ${error}`);
      }
    }
  }
  const space=await graph('space','[t,t^2,t^3]');
  assert.ok(space.spaceCurves[0].length>1);
  for(const [x,y,z] of space.spaceCurves[0]){
    assert.ok(Math.abs(y-x*x)<1e-12);
    assert.ok(Math.abs(z-x*x*x)<1e-12);
  }
  const integral=await execute({action:'graphAnalysis',trees:[parse('x')],analysis:'integral',a:0,b:1});
  assert.equal(integral.value,.5);
  assert.ok(integral.integralFill.length>0);

  const periodicTrees=[String.raw`\sin\left(x\right)`,
    String.raw`\sin\left(x\right) = \left(-3\right) \cdot \cos\left(x\right)`].map(source=>graphInputTree(source));
  for(const trees of [periodicTrees,[...periodicTrees].reverse()]){
    const intersections=await execute({action:'graphAnalysis',graphKind:'cartesian',angle:'RAD',
      trees,analysis:'intersection',selected:0,other:1,a:-10,b:10});
    assert.equal(intersections.count,6);
    assert.equal(intersections.truncated,false);
    for(const [index,[x,y]] of intersections.points.entries()){
      assert.ok(Math.abs(x-(-Math.atan(3)+(index-2)*Math.PI))<1e-7);
      assert.ok(Math.abs(y-Math.sin(x))<1e-7);
      assert.ok(Math.abs(Math.sin(x)+3*Math.cos(x))<1e-7);
    }
  }
  const solutions=await execute({tree:parse('solveset(sin(x) + 3*cos(x), x, domain=S.Reals)'),
    angle:'RAD',variables:{x:{kind:'number',value:'99'}}});
  assert.equal(solutions.tree.kind,'rows');
  assert.equal(solutions.tree.args.filter(row=>row.value==='solutions').length,2);
  assert.equal(solutions.tree.args.filter(row=>row.value==='branch').length,2);
  assert.ok(solutions.exact.includes('atan(3)'));
  assert.ok(solutions.exact.includes('∈ ℤ'));
  assert.ok(!solutions.exact.includes('ImageSet'));
  for(const [source,expected] of [
    ['solveset(x^2+1,x)','{-I, I}'],
    ['solveset(x^2+1=0,x,domain=S.Reals)','EmptySet'],
    ['solveset(x^2-4,x,S.Reals)','{-2, 2}'],
    ['solveset(x^2-2,x,domain=S.Integers)','EmptySet']
  ])assert.equal((await execute({tree:parse(source)})).exact,expected);
});
