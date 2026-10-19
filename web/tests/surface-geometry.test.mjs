import test from 'node:test';
import assert from 'node:assert/strict';
import {prepareSurfaceFaces,projectSurfaceFaces,surfaceProjection,radialSurfaceGeometry} from '../surface-geometry.js';
import {createGraphComputation} from '../graph-computation.js';
import {surfaceGpuGeometry} from '../surface-gpu.js';
import {surfaceRainbowRgb,surfaceRainbowStops} from '../surface-colors.js';
import {graphSvg} from '../graph-export.js';
import {JSDOM} from 'jsdom';

const bounds={xmin:-2,xmax:2,ymin:-2,ymax:2,zmin:-1,zmax:8};
const grid=()=>Array.from({length:5},(_,r)=>Array.from({length:5},(_,c)=>[c-2,r-2,(c-2)**2+(r-2)**2]));

test('explicit grid faces share vertex lighting, including clipping and camera rotation',()=>{
  const mesh=grid(),prepared=prepareSurfaceFaces(mesh,{...bounds,zmax:3}),levels=new Map();
  for(const face of prepared.faces){
    assert.equal(face.levels.length,3);
    face.source.forEach((p,i)=>{
      if(levels.has(p))assert.equal(face.levels[i],levels.get(p));
      levels.set(p,face.levels[i]);
    });
  }
  assert.ok(levels.size>10);
  for(const rotation of [0,35,90]){
    const faces=projectSurfaceFaces(prepared,surfaceProjection(bounds,rotation,32));
    assert.ok(faces.some(face=>face.lighting));
    assert.ok(faces.every(face=>face.projected.every(p=>p.every(Number.isFinite))));
  }
  mesh[2][2]=null;
  const hole=prepareSurfaceFaces(mesh,bounds);
  assert.equal(hole.faces.length,24);
  assert.ok(hole.faces.every(face=>face.levels.every(Number.isFinite)));
});

test('surface animation and slider dragging keep explicit density',()=>{
  const state={parameters:{a:1}},surface={samples:96,autoDensity:false,zoom:1,autoZ:true};
  let source='sin(a*x^2+a*y^2)/(x^2+y^2)';
  const computation=createGraphComputation({state,surface,options:()=>({}),kind:()=> 'surface',
    expressions:()=>[source],value:()=>source,currentBounds:()=>bounds,zRange:()=>[-1,8],
    numeric:id=>id.endsWith('min')?-2:2});
  for(const mode of [{},{animation:true},{parameterDragging:true}]){
    Object.assign(state,{animation:false,parameterDragging:false},mode);
    assert.equal(computation.makeRequest().surfaceSamples,96);
  }
  source='x^2+y^2+z^2=1';state.animation=true;
  assert.equal(computation.makeRequest().surfaceSamples,16);
});

test('adaptive radial rings form a watertight disk with shared lighting normals',()=>{
  const radial=radialSurfaceGeometry([[0,1,0,1],[1,.5,-1,12],[2,0,0,20],[3,-.2,0,24]]);
  assert.equal(radial.triangles.length,88);
  let area=0;const edges=new Map();
  for(const face of radial.triangles){
    const [a,b,c]=face,cross=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);
    assert.ok(cross>0);area+=cross/2;
    for(let i=0;i<3;i++){
      const edge=[face[i].join(','),face[(i+1)%3].join(',')].sort().join('|');edges.set(edge,(edges.get(edge)||0)+1);
    }
  }
  assert.ok(Math.abs(area-24*9*Math.sin(2*Math.PI/24)/2)<1e-10);
  assert.equal([...edges.values()].filter(n=>n===1).length,24);
  assert.ok([...edges.values()].every(n=>n===1||n===2));
  const prepared=prepareSurfaceFaces([],bounds,radial.triangles,radial.normals);
  const packed=surfaceGpuGeometry(prepared),wire=surfaceGpuGeometry(prepared,true);
  assert.equal(packed.edges.length,0);assert.ok(wire.edges.length>0);
  assert.deepEqual(packed.vertices,wire.vertices);
  for(let i=0;i<packed.vertices.length;i+=5){
    for(let k=0;k<3;k++)assert.ok(Math.abs(packed.vertices[i+k])<=1+1e-6);
    assert.ok(packed.vertices[i+3]>=0&&packed.vertices[i+3]<=1);
  }
});

test('rainbow ramp and SVG export preserve height colors and the Z legend',()=>{
  surfaceRainbowStops.forEach((rgb,i)=>assert.deepEqual(surfaceRainbowRgb(i/5),rgb));
  assert.deepEqual(surfaceRainbowRgb(-2),surfaceRainbowStops[0]);
  assert.deepEqual(surfaceRainbowRgb(2),surfaceRainbowStops[5]);
  const dom=new JSDOM('<div id="plot"></div>'),previous=globalThis.document;
  globalThis.document=dom.window.document;
  dom.window.HTMLCanvasElement.prototype.getContext=()=>({measureText:text=>({width:String(text).length*7})});
  try{
    const container=dom.window.document.getElementById('plot');
    const svg=graphSvg(container,{surface:[],surfaceRings:[[0,1,0,1],[1,0,-1,12],[3,-.2,0,24]],zMin:-.2,zMax:1},bounds,
      {surfaceView:{colorMode:'rainbow',renderMode:'surface-wireframe',opacity:.5}});
    const xml=new JSDOM(svg,{contentType:'image/svg+xml'}).window.document;
    const gradients=[...xml.querySelectorAll('linearGradient')];
    assert.ok(gradients.length>10);
    assert.ok(gradients.some(g=>g.querySelectorAll('stop').length===6));
    assert.ok(svg.includes('rgb(128,0,255)'));assert.ok(svg.includes('rgb(255,0,0)'));
    assert.ok(!svg.includes('NaN'));assert.ok(!svg.includes('Infinity'));
    assert.ok([...xml.querySelectorAll('text')].some(n=>n.textContent==='-0.2'));
  }finally{globalThis.document=previous;dom.window.close();}
});
