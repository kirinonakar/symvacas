import test from 'node:test';
import assert from 'node:assert/strict';
import {JSDOM} from 'jsdom';
import {statisticsPlot,statisticsPlotPanels} from '../statistics-plot.js';
import {raincloudSummary} from '../statistics-plot-data.js';

test('raincloud Tukey whiskers exclude an outlier and handle empty, constant and extreme samples',()=>{
  assert.deepEqual(raincloudSummary([0,1,2,3,4,100,NaN,Infinity]),{low:0,q1:1.25,median:2.5,q3:3.75,high:4});
  assert.deepEqual(raincloudSummary([3,3,3]),{low:3,q1:3,median:3,q3:3,high:3});
  assert.deepEqual(raincloudSummary([8]),{low:8,q1:8,median:8,q3:8,high:8});
  assert.equal(raincloudSummary([NaN,Infinity]),null);
  assert.ok(Object.values(raincloudSummary([-1e308,0,1e308])).every(Number.isFinite));
});

for(const orientation of ['horizontal','vertical'])test(`raincloud ${orientation} separates half density, box and every raw observation`,context=>{
  const dom=new JSDOM('<div id="plot"></div>'),previous=globalThis.document;
  globalThis.document=dom.window.document;context.after(()=>{globalThis.document=previous;dom.window.close();});
  const container=document.getElementById('plot'),series=[{label:'A',values:[0,1,2,3,4,100,NaN]},{label:'B',values:Array(40).fill(3)},{label:'single',values:[8]}];
  statisticsPlot(container,[],{type:'raincloud',orientation,series});
  const svg=container.querySelector('svg'),points=[...svg.querySelectorAll('[data-raw-point]')],cloud=svg.querySelector('[data-half-violin]');
  assert.equal(svg.getAttribute('aria-label'),'Raincloud plot');assert.equal(svg.dataset.orientation,orientation);
  assert.equal(points.length,47);assert.equal(svg.querySelectorAll('[data-box]').length,3);
  assert.equal(svg.querySelectorAll('[data-half-violin]').length,1,'constant and singleton samples omit the cloud');
  assert.equal(container.querySelectorAll('button').length,2,'SVG/PNG export controls');
  const [,,width]=svg.getAttribute('viewBox').split(' ').map(Number),center=orientation==='vertical'?110+.5*(width-150)/3:45;
  const coordinates=cloud.getAttribute('d').match(/-?\d+(?:\.\d+)?(?:e[+-]?\d+)?/gi).map(Number);
  const categories=coordinates.filter((_,i)=>i%2===(orientation==='vertical'?0:1));
  assert.ok(categories.every(value=>value<=center-4+1e-8),'cloud stays on one side');
  const box=svg.querySelector('[data-box="A"]'),category=orientation==='vertical'?'x':'y',extent=orientation==='vertical'?'width':'height';
  assert.equal(Number(box.getAttribute(category)),center+1);assert.equal(Number(box.getAttribute(extent)),10);
  const raw=points.filter(point=>point.dataset.rawPoint==='A');
  const axis=orientation==='vertical'?'cy':'cx',cross=orientation==='vertical'?'cx':'cy';
  assert.ok(raw.every(point=>Number(point.getAttribute(cross))>center+11));
  assert.deepEqual(raw.map(point=>Number(point.dataset.value)),[0,1,2,3,4,100]);
  assert.equal(Number(raw.at(-1).getAttribute(axis)),orientation==='vertical'?40:740,'outlier retains its value-axis position');
  assert.deepEqual([...svg.querySelectorAll('[data-whisker]')].slice(0,2).map(node=>Number(node.dataset.whisker)),[0,4]);
  const dense=points.filter(point=>point.dataset.rawPoint==='B');
  for(let i=0;i<dense.length;i++)for(let j=0;j<i;j++){
    const distance=Math.hypot(Number(dense[i].getAttribute('cx'))-Number(dense[j].getAttribute('cx')),Number(dense[i].getAttribute('cy'))-Number(dense[j].getAttribute('cy')));
    assert.ok(distance>=2*Number(dense[i].getAttribute('r'))-1e-8,'duplicates remain distinct');
  }
  assert.doesNotMatch(svg.outerHTML,/NaN|Infinity/);
  const before=svg.outerHTML;statisticsPlot(container,[],{type:'raincloud',orientation,series});assert.equal(container.querySelector('svg').outerHTML,before);
  const panels=statisticsPlotPanels([['A','1','10'],['B','2','20'],['A','','30']],{grouping:'first',columnCount:3});
  assert.equal(panels.length,2);assert.deepEqual(panels[1].series.map(entry=>entry.values),[[10,30],[20]]);
  statisticsPlot(container,[],{type:'raincloud',series:[{label:'empty',values:[NaN]}]});assert.equal(container.children.length,0);
});
