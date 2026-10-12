import test from 'node:test';
import assert from 'node:assert/strict';
import {statisticsPlot,statisticsPlotPanels} from '../statistics-plot.js';
import {statisticsNamedBarData,statisticsScatterData} from '../statistics-plot-data.js';

// Test generated SVG coordinates and counts; this does not establish browser QA.
class Node {
  constructor(tag,document){this.tag=tag;this.ownerDocument=document;this.attrs={};this.children=[];this.style={};}
  setAttribute(key,value){this.attrs[key]=String(value);}
  append(...nodes){for(const node of nodes){node.parentNode=this;this.children.push(node);}}
  prepend(...nodes){for(const node of nodes)node.parentNode=this;this.children.unshift(...nodes);}
  replaceChildren(...nodes){this.children=[];this.append(...nodes);}
  after(node){const parent=this.parentNode;node.parentNode=parent;parent.children.splice(parent.children.indexOf(this)+1,0,node);}
  querySelectorAll(tag){return this.children.flatMap(node=>[...(node.tag===tag?[node]:[]),...node.querySelectorAll(tag)]);}
  querySelector(tag){return this.querySelectorAll(tag)[0]||null;}
}
test('grouped scatter renders every pair as a point with matching legend colors and selected axis labels',context=>{
  const previous=globalThis.document;context.after(()=>globalThis.document=previous);
  const document={createElement:tag=>new Node(tag,document),createElementNS:(_,tag)=>new Node(tag,document)};globalThis.document=document;
  const container=new Node('div',document);
  const scatterData=statisticsScatterData([['A','1','10'],['B','2','20'],['A','3','30'],['A','','40']],{columnCount:3,grouping:'first',xColumn:2,yColumn:1});
  statisticsPlot(container,[],{type:'scatter',scatterData,xAxisLabel:'Height',yAxisLabel:'Weight'});
  const circles=container.querySelectorAll('circle'),legend=container.children.find(node=>node.className==='statistics-plot-legend');
  assert.equal(circles.length,3);assert.equal(container.querySelectorAll('path').length,0);
  assert.deepEqual(legend.children.map(node=>node.textContent),['A (n=2)','B (n=1)']);
  assert.deepEqual(legend.children.map(node=>circles.filter(point=>point.attrs.fill===node.style.color).length),[2,1]);
  assert.ok(container.querySelectorAll('text').some(node=>node.attrs['data-axis-label']==='x'&&node.textContent==='Height'));
  assert.ok(container.querySelectorAll('text').some(node=>node.attrs['data-axis-label']==='y'&&node.textContent==='Weight'));
  assert.equal(container.querySelectorAll('button').length,2);
});
test('five occurrences of 3 produce one bar at the value tick with height five and export controls',context=>{
  const previous=globalThis.document;context.after(()=>globalThis.document=previous);
  const document={createElement:tag=>new Node(tag,document),createElementNS:(_,tag)=>new Node(tag,document)};globalThis.document=document;
  const container=new Node('div',document);
  statisticsPlot(container,Array.from({length:5},()=>['3']),{type:'bar'});
  const [bar]=container.querySelectorAll('rect'),svg=container.querySelector('svg');
  assert.equal(container.querySelectorAll('rect').length,1);
  assert.equal(bar.attrs['data-value'],'3');assert.equal(bar.attrs['data-count'],'5');
  assert.ok(Math.abs(Number(bar.attrs.x)+Number(bar.attrs.width)/2-400)<1e-9);
  assert.equal(Number(bar.attrs.height),300);assert.equal(Number(bar.attrs.y),40);
  const tick=svg.children.find(node=>node.tag==='text'&&node.textContent==='3');assert.equal(Number(tick.attrs.x),400);
  assert.ok(svg.children.some(node=>node.tag==='text'&&node.textContent==='5'));
  assert.equal(container.querySelectorAll('button').length,2);
  assert.equal(svg.attrs['aria-label'],'Bar');
  statisticsPlot(container,[['0'],['3'],['3'],['3'],['3'],['3'],['10'],['10']],{type:'bar'});
  const bars=container.querySelectorAll('rect'),three=bars.find(bar=>bar.attrs['data-value']==='3'),ten=bars.find(bar=>bar.attrs['data-value']==='10');
  assert.equal(Number(three.attrs.height)/Number(ten.attrs.height),5/2);
  assert.ok(Number(three.attrs.x)-Number(bars[0].attrs.x)<Number(ten.attrs.x)-Number(three.attrs.x),'numeric gaps 3 and 7 have different widths');
  const grouped=statisticsPlotPanels([['A','3'],['A','3'],['B','3'],['B','4']],{grouping:'first',columnCount:2});
  statisticsPlot(container,[],{type:'bar',series:grouped[0].series});
  assert.deepEqual(container.querySelectorAll('rect').map(bar=>[bar.attrs['data-series'],bar.attrs['data-value'],bar.attrs['data-count']]),[['A','3','2'],['B','3','1'],['B','4','1']]);
});

test('R-style named heights and adjacent grouped heights render as values rather than frequencies',context=>{
  const previous=globalThis.document;context.after(()=>globalThis.document=previous);
  const document={createElement:tag=>new Node(tag,document),createElementNS:(_,tag)=>new Node(tag,document)};globalThis.document=document;
  const container=new Node('div',document);
  statisticsPlot(container,[],{type:'bar',namedBars:statisticsNamedBarData([['A','5'],['B','8'],['C','3']])});
  const bars=container.querySelectorAll('rect');
  assert.deepEqual(bars.map(bar=>[bar.attrs['data-name'],bar.attrs['data-value']]),[['A','5'],['B','8'],['C','3']]);
  assert.deepEqual(bars.map(bar=>Number(bar.attrs.height)),[187.5,300,112.5]);
  assert.ok(Number(bars[0].attrs.x)<Number(bars[1].attrs.x)&&Number(bars[1].attrs.x)<Number(bars[2].attrs.x));
  assert.ok(container.querySelectorAll('text').some(node=>node.textContent==='A'));
  const namedBars=statisticsNamedBarData([['A','G1','5'],['B','G1','8'],['A','G2','3'],['B','G2','4']],{columnCount:3,grouping:'column:1'});
  statisticsPlot(container,[],{type:'bar',namedBars});
  const grouped=container.querySelectorAll('rect');
  assert.deepEqual(grouped.map(bar=>[bar.attrs['data-name'],bar.attrs['data-series'],bar.attrs['data-value']]),[['A','G1','5'],['A','G2','3'],['B','G1','8'],['B','G2','4']]);
  assert.ok(Number(grouped[0].attrs.x)+Number(grouped[0].attrs.width)<Number(grouped[1].attrs.x));
  assert.notEqual(grouped[0].attrs.fill,grouped[1].attrs.fill);
  assert.equal(container.querySelectorAll('button').length,2);
});

test('KDE switches histogram to density, overlays whole bins and draws one matching curve per series',context=>{
  const previous=globalThis.document;context.after(()=>globalThis.document=previous);
  const document={createElement:tag=>new Node(tag,document),createElementNS:(_,tag)=>new Node(tag,document)};globalThis.document=document;
  const container=new Node('div',document),series=[{label:'A',values:[-1,0,1]},{label:'B',values:[-1,0,1,-1,0,1]}];
  statisticsPlot(container,[],{type:'histogram',series,histogramKde:true});
  const svg=container.querySelector('svg');assert.equal(svg.attrs['data-y-axis'],'density');
  assert.ok(container.querySelectorAll('text').some(node=>node.textContent==='Density'));
  const bars=container.querySelectorAll('rect'),groups=['A','B'].map(name=>bars.filter(bar=>bar.attrs['data-series']===name));
  groups.forEach(group=>assert.ok(Math.abs(group.reduce((area,bar)=>area+Number(bar.attrs['data-density'])*(2/group.length),0)-1)<1e-12));
  groups[0].forEach((bar,i)=>{assert.equal(bar.attrs.x,groups[1][i].attrs.x);assert.equal(bar.attrs.width,groups[1][i].attrs.width);assert.equal(bar.attrs.height,groups[1][i].attrs.height);});
  const curves=container.querySelectorAll('path');assert.equal(curves.length,2);
  curves.forEach((curve,i)=>{assert.equal(curve.attrs.stroke,groups[i][0].attrs.fill);assert.doesNotMatch(curve.attrs.d,/NaN|Infinity/);});
  assert.equal(container.querySelectorAll('button').length,2);
  statisticsPlot(container,[],{type:'histogram',series,histogramKde:false});
  assert.equal(container.querySelector('svg').attrs['data-y-axis'],'count');assert.equal(container.querySelectorAll('path').length,0);
  statisticsPlot(container,[],{type:'histogram',series:[{label:'C',values:[3,3,3]}],histogramKde:true});
  assert.equal(container.querySelectorAll('path').length,0);assert.equal(container.querySelector('svg').attrs['data-y-axis'],'density');
  assert.ok(container.children[0].children[0].textContent.includes('KDE unavailable'));
});
