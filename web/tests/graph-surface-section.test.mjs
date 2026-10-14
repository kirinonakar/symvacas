import test from 'node:test';
import assert from 'node:assert/strict';
import {surfaceSectionPlane,surfaceSectionSegments,prepareSurfaceFaces,projectSurfaceFaces,surfaceProjection} from '../surface-geometry.js';
const bounds={xmin:-2,xmax:2,ymin:-2,ymax:2,zmin:-2,zmax:2};

test('horizontal sections retain the actual mesh coordinates, group, and exclude disjoint or invalid heights',()=>{
  const faces=[{group:2,points:[[0,0,-1],[2,0,1],[0,2,1]]}];
  assert.deepEqual(surfaceSectionSegments(faces,0),[{group:2,points:[[1,0,0],[0,1,0]]}]);
  assert.deepEqual(surfaceSectionSegments(faces,2),[]);
  assert.deepEqual(surfaceSectionSegments(faces,NaN),[]);
  const vertex=[{points:[[0,0,0],[2,0,1],[0,2,-1]]}];
  assert.deepEqual(surfaceSectionSegments(vertex,0),[{group:0,points:[[0,0,0],[1,1,0]]}]);
  assert.equal(surfaceSectionSegments([{points:[[0,0,0],[1,0,0],[0,1,0]]}],0).length,3);
});

test('x, y and z sections intersect the same geometry under axis permutations and span the other axes',()=>{
  const triangle=[[0,0,-1],[2,0,1],[0,2,1]],expected=[[1,0,0],[0,1,0]];
  for(const axis of [0,1,2]){
    const permute=point=>{const out=[...point];[out[axis],out[2]]=[out[2],out[axis]];return out;};
    const faces=[{group:3,points:triangle.map(permute)}];
    assert.deepEqual(surfaceSectionSegments(faces,0,axis),[{group:3,points:expected.map(permute)}]);
    assert.deepEqual(surfaceSectionSegments(faces,2,axis),[]);
    const box={xmin:-4,xmax:5,ymin:-6,ymax:7,zmin:-8,zmax:9};
    const plane=surfaceSectionPlane(box,.25,axis),ranges=[[-4,5],[-6,7],[-8,9]];
    assert.equal(plane.length,4);
    for(const point of plane){
      assert.equal(point[axis],.25);
      for(const other of [0,1,2].filter(i=>i!==axis))assert.ok(ranges[other].includes(point[other]));
    }
    for(const other of [0,1,2].filter(i=>i!==axis))assert.deepEqual([...new Set(plane.map(p=>p[other]))].sort((a,b)=>a-b),ranges[other]);
  }
});

test('transparency retains back faces of a closed surface and sorts them by depth',()=>{
  const triangles=[[[0,0,0],[1,0,0],[0,1,0]],[[0,0,1],[0,1,1],[1,0,1]]];
  const prepared=prepareSurfaceFaces([],bounds,triangles,[],true),projection=surfaceProjection(bounds,35,32);
  const opaque=projectSurfaceFaces(prepared,projection),transparent=projectSurfaceFaces(prepared,projection,true);
  assert.equal(opaque.length,1);assert.equal(transparent.length,2);
  assert.ok(transparent[0].depth<=transparent[1].depth);
});


test('production SVG rendering honors visibility, strict boundaries, transparency and sections',async context=>{
  const {JSDOM}=await import('jsdom'),{graphSvg}=await import('../graph-export.js');
  const dom=new JSDOM('<div id="plot"></div>');
  const oldDocument=globalThis.document,oldStyle=globalThis.getComputedStyle;
  globalThis.document=dom.window.document;globalThis.getComputedStyle=()=>({getPropertyValue:()=>''});
  context.after(()=>{globalThis.document=oldDocument;globalThis.getComputedStyle=oldStyle;dom.window.close();});
  dom.window.HTMLCanvasElement.prototype.getContext=()=>({measureText:text=>({width:text.length*6})});
  const container=dom.window.document.getElementById('plot'),view={xmin:-2,xmax:2,ymin:-2,ymax:2};
  const result={curves:[[[-1,-1],[1,1]],[[-1,1],[1,-1]]],curveStyles:['solid','dashed'],shadings:[{sourceIndex:1,fill:[[[-1,-1],[1,-1],[1,1]]]}]};
  const shown=graphSvg(container,result,view,{colors:['#ff1234','#1256ff']});
  assert.match(shown,/stroke="#ff1234"/);assert.match(shown,/stroke="#1256ff"/);assert.match(shown,/stroke-dasharray="6 4"/);
  const hidden=graphSvg(container,result,view,{colors:['#ff1234','#1256ff'],hiddenCurves:[1],hiddenShadings:[0]});
  assert.match(hidden,/stroke="#ff1234"/);assert.doesNotMatch(hidden,/#1256ff/);assert.doesNotMatch(hidden,/stroke-dasharray/);
  const surface={surface:[],surfaceVertices:[[0,0,-1],[2,0,1],[0,2,1]],surfaceTriangles:[[0,1,2]],zMin:-2,zMax:2};
  for(const [sliceAxis,slicePosition] of [['x',1],['y',1],['z',0]]){
    const transparent=graphSvg(container,surface,view,{surfaceView:{opacity:.5,sliceEnabled:true,sliceAxis,slicePosition}});
    assert.match(transparent,/opacity="0.5"/);assert.match(transparent,/stroke-width="3"/);assert.match(transparent,/stroke-dasharray="5 4"/);
  }
});
