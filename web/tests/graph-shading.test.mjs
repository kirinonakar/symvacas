import test from 'node:test';
import assert from 'node:assert/strict';
import {graphShadings} from '../graph-shading.js';
import {graphSvg} from '../graph-export.js';
import {JSDOM} from 'jsdom';

test('shading preserves strictness for reversed, chained and band constraints',()=>{
  for(const [source,strict] of [['y<x',true],['x>y',true],['y>=x',false],['x<=y',false]]){
    assert.equal(graphShadings(`[s] ${source}`,'cartesian')[0].strict,strict);
  }
  const region=graphShadings('[shade] -1<x<=1, 2>=y>x','cartesian')[0];
  assert.deepEqual(region.constraints.map(({strict})=>strict),[true,false,false,true]);
  const band=graphShadings('[s] sin(x), cos(x), -1<x<=2, y<0','cartesian')[0];
  assert.deepEqual(band.xBounds.map(({strict})=>strict),[true,false]);
  assert.equal(band.yBounds[0].strict,true);
});

test('canvas and SVG draw separate strict and inclusive shading boundaries without solid overlays',context=>{
  const dom=new JSDOM('<div id="plot"></div>'),oldDocument=globalThis.document;
  globalThis.document=dom.window.document;
  context.after(()=>{globalThis.document=oldDocument;dom.window.close();});
  dom.window.HTMLCanvasElement.prototype.getContext=()=>({measureText:text=>({width:text.length*6})});
  const container=dom.window.document.getElementById('plot'),bounds={xmin:-2,xmax:2,ymin:-2,ymax:2};
  const boundary=[[[-1,-1],[-1,0],[-1,1]],[[1,-1],[1,0],[1,1]]];
  for(const source of [{sourceIndex:0},{shadeIndex:0}]){
    const result={curves:source.sourceIndex===0?[boundary.flat()]:[],shadings:[{...source,boundary,boundaryStyles:['dashed','solid'],fill:[]}]};
    const svg=graphSvg(container,result,bounds,{colors:['#123abc']});
    const doc=new JSDOM(svg,{contentType:'image/svg+xml'}).window.document;
    const paths=[...doc.querySelectorAll('path[stroke="#123abc"]')];
    assert.equal(paths.length,2);
    assert.equal(paths[0].getAttribute('stroke-dasharray'),'6 4');
    assert.equal(paths[0].getAttribute('stroke-linecap'),'butt');
    assert.equal(paths[1].hasAttribute('stroke-dasharray'),false);
    assert.equal(paths[1].getAttribute('stroke-linecap'),'round');
    assert.equal((paths[0].getAttribute('d').match(/M/g)||[]).length,1);
    const hidden=graphSvg(container,result,bounds,{colors:['#123abc'],hiddenShadings:[0],hiddenCurves:[0]});
    assert.doesNotMatch(hidden,/#123abc/);
  }
});
