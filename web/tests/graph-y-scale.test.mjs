import test from 'node:test';
import assert from 'node:assert/strict';
import {yFraction,yAtFraction,logYTicks,yScaleSegment,clipYPolygon,fitYRange,yScaleLine} from '../graph-y-scale.js';
import {transformBounds,nearestPoint,curvePointAtX} from '../graph-view.js';
import {graphPreviewRequest} from '../graph-sampling.js';
const close=(actual,expected)=>assert.ok(Math.abs(actual-expected)<1e-9,`${actual} != ${expected}`);

test('decades are equally spaced, inverse coordinates and gesture anchors retain actual values',()=>{
  assert.deepEqual([1,10,100].map(y=>yFraction(y,1,100,true)),[0,.5,1]);close(yAtFraction(.5,1,100,true),10);
  assert.deepEqual(logYTicks(1,100),[1,10,100]);
  const bounds={xmin:0,xmax:6,ymin:1,ymax:100};
  const zoom=transformBounds(bounds,{x:.5,y:.5},{x:.5,y:.5},2,2,true);
  close(yAtFraction(.5,zoom.ymin,zoom.ymax,true),10);close(zoom.ymax/zoom.ymin,10);
  const pan=transformBounds(bounds,{x:.5,y:.5},{x:.5,y:.6},1,1,true);close(pan.ymax/pan.ymin,100);
  const preview=graphPreviewRequest({graphKind:'cartesian',min:0,max:6,xMin:0,xMax:6,yMin:1,yMax:100,yLog:true});
  assert.ok(preview.yMin>0&&preview.yMin<1&&preview.yMax>100);
});

test('log clipping, shading, fitting and trace work in positive data coordinates',()=>{
  const bounds={xmin:0,xmax:6,ymin:.01,ymax:100};
  const line=yScaleSegment([0,.001],[6,1000],bounds,true);close(line[0][0],1);close(line[1][0],5);
  const polygon=clipYPolygon([[-1,-1],[7,-1],[7,10],[-1,10]],bounds);assert.equal(polygon.length,4);assert.ok(polygon.every(p=>p[1]>0));
  assert.equal(fitYRange([-1,0],true),null);const fit=fitYRange([-100,0,1,100],true);assert.ok(fit[0]>0&&fit[0]<1&&fit[1]>100);
  const curve=[[0,1],[2,100]];assert.deepEqual(curvePointAtX(curve,1,null,{yLog:true}),[1,10]);
  const pick=nearestPoint({curves:[[[0,-1],[1,1],[1,10],[1,100]]]}, {xmin:0,xmax:2,ymin:1,ymax:100},{x:.5,y:.5},0,true);assert.deepEqual(pick.point,[1,10]);
  for(const [x,y] of yScaleLine([0,-1],[4,3],{xmin:0,xmax:4,ymin:.01,ymax:10},true)){assert.ok(y>0);close(y,x-1);}
});


test('SVG logarithmic axes put 1, 10 and 100 at equal distances and keep clipping finite',async context=>{
  const {JSDOM}=await import('jsdom'),{graphSvg}=await import('../graph-export.js');
  const dom=new JSDOM('<div id="plot"></div>'),oldDocument=globalThis.document;
  globalThis.document=dom.window.document;context.after(()=>{globalThis.document=oldDocument;dom.window.close();});
  dom.window.HTMLCanvasElement.prototype.getContext=()=>({measureText:text=>({width:text.length*6})});
  const svg=graphSvg(dom.window.document.getElementById('plot'),{curves:[[[0,1],[1,10],[2,100]],[[0,-1],[1,0]]],shadings:[{sourceIndex:0,fill:[[[-1,-1],[3,-1],[3,100],[-1,100]]]}]},
    {xmin:0,xmax:2,ymin:1,ymax:100},{yLog:true,colors:['#aa1122','#1133bb'],analysis:{line:[[0,-1],[2,100]]}});
  const doc=new JSDOM(svg,{contentType:'image/svg+xml'}).window.document;
  const labels=[...doc.querySelectorAll('text[text-anchor="end"]')];
  const positions=[1,10,100].map(value=>Number(labels.find(label=>label.textContent===String(value)).getAttribute('y')));
  close(positions[0]-positions[1],positions[1]-positions[2]);
  assert.doesNotMatch(svg,/NaN|Infinity/);for(const path of doc.querySelectorAll('path[stroke="#1133bb"]'))assert.equal(path.getAttribute("d"),"");
  const fill=[...doc.querySelectorAll('path[fill="#aa1122"]')];assert.equal(fill.length,1);
});
