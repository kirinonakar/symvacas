import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {JSDOM} from 'jsdom';
import {logisticComparisonPlan} from '../logistic-comparison.js';
import {advancedStatisticsSchema as schema} from '../advanced-statistics-schema.js';
import {guidedStatisticsCommand,createAdvancedStatistics} from '../advanced-statistics.js';
import {logisticComparisonPlot} from '../logistic-comparison-plot.js';

test('nested logistic selects one complete union and aligns validation by unique headers',()=>{
  const opts={response:'0',basePredictors:'3',addedPredictors:'1',validation:'external',threshold:'0.5',level:'0.95',resamples:'200',seed:'0'};
  const rows=[['0','1,234','','4'],['1','','ignore','5'],['0','2','','6']];
  const other=[['8','1','9',''],['10','0','11',''],['','1','3','']];
  const result=logisticComparisonPlan(rows,opts,['event (x)','MRI (y)','unused (z)','age (x4)'],other,['age (x)','event (y)','MRI (z)','unused (x4)']);
  assert.equal(result.expression,'logisticcompare([[4,1234,0],[6,2,0]],1,external,[[8,9,1],[10,11,0]],0.5,0.95,200,0,[3,3])');
  assert.equal(result.labels['model:A'],'age (x4)');
  assert.equal(result.labels['model:B'],'age (x4) + MRI (y)');
  assert.throws(()=>logisticComparisonPlan(rows,opts,['a','a','b','c'],other,['a','b','c','d']),/unique column headers/);
  assert.throws(()=>logisticComparisonPlan(rows,opts,['event','MRI','unused','age'],other,['age','event','other','unused']),/unique column headers/);
  assert.throws(()=>logisticComparisonPlan(rows,{...opts,addedPredictors:'3'},[],other),/distinct baseline/);
});

test('nested logistic defaults to stratified CV and permits an intercept-only baseline',()=>{
  const definition=schema.find(d=>d.id==='logisticcompare');
  assert.match(guidedStatisticsCommand(definition,definition.exampleRows),/,crossvalidation,5,0.5,0.95,200,0,/);
  assert.match(guidedStatisticsCommand(definition,[['1','2','0'],['2','3','1']],{basePredictors:''}),/\],0,crossvalidation,/);
});

test('validation dataset selector accepts the currently selected training dataset',context=>{
  const dom=new JSDOM(readFileSync(new URL('../index.html',import.meta.url),'utf8'));
  const previous=globalThis.document;globalThis.document=dom.window.document;
  context.after(()=>{dom.window.close();globalThis.document=previous;});
  const csv='age,MRI,event\n1,2,0\n3,4,1',fields={'dataset-list':'D1','statistics-models-kind':'logisticcompare','statistics-models-input':'current','statistics-form-logisticcompare-validation':'external','statistics-form-logisticcompare-validationDataset':'D1'};
  const option=document.createElement('option');option.value='D1';document.getElementById('dataset-list').append(option);document.getElementById('dataset-list').value='D1';
  const tools=createAdvancedStatistics({state:{fields,datasets:{D1:csv}},persist:()=>{},data:()=>csv,columnLimit:()=>3,section:'models'});
  assert.equal(document.getElementById('statistics-form-modelcompare-validationDataset').value,'D1');
  assert.equal(tools.expression(),'modelcompare([[1,2,0],[3,4,1]],1,logistic,external,[[1,2,0],[3,4,1]],0.95,200,0,[[threshold,0.5],[excludedrows,0],[excludedvalidation,0]],0)');
  assert.equal(document.getElementById('statistics-models-status').textContent,'2 rows');
});

// Generated SVG contract only; this does not establish browser interaction QA.
class Node {
  constructor(tag,document){this.tag=tag;this.ownerDocument=document;this.attrs={};this.children=[];this.style={};}
  setAttribute(key,value){this.attrs[key]=String(value);}
  append(...nodes){for(const node of nodes){node.parentNode=this;this.children.push(node);}}
  after(node){const parent=this.parentNode;node.parentNode=parent;parent.children.splice(parent.children.indexOf(this)+1,0,node);}
  querySelectorAll(tag){return this.children.flatMap(node=>[...(node.tag===tag?[node]:[]),...node.querySelectorAll(tag)]);}
}
test('ROC renders both models, AUC intervals, chance diagonal and export actions together',context=>{
  const previous=globalThis.document;context.after(()=>globalThis.document=previous);
  const document={createElement:tag=>new Node(tag,document),createElementNS:(_,tag)=>new Node(tag,document)};globalThis.document=document;
  const plot={kind:'roc-comparison',title:'ROC / AUC comparison',evaluation:'crossvalidation',series:[
    {label:'Model A',auc:.7,interval:[.6,.8],points:[[0,0],[.4,.8],[1,1]]},
    {label:'Model B',auc:.8,interval:[.7,.9],points:[[0,0],[.2,.8],[1,1]]}]};
  const figure=logisticComparisonPlot(plot),paths=figure.querySelectorAll('path');
  assert.equal(paths.length,2);assert.notEqual(paths[0].attrs.stroke,paths[1].attrs.stroke);
  assert.equal(paths[0].attrs.d,'M58,378 L229.20000000000002,117.19999999999999 L486,52');
  assert.ok(figure.querySelectorAll('text').some(n=>n.textContent==='Model B · AUC=0.8 · CI [0.7, 0.9]'));
  assert.equal(figure.querySelectorAll('line').filter(n=>n.attrs['data-reference']==='chance').length,1);
  assert.equal(figure.querySelectorAll('button').length,2);
  const calibration=logisticComparisonPlot({...plot,kind:'calibration-comparison',series:plot.series.map(s=>({...s,points:[[.2,.1,10],[.8,.7,20]]}))});
  assert.equal(calibration.querySelectorAll('circle').length,4);
  assert.ok(calibration.querySelectorAll('title').every(n=>n.textContent.includes('n=')));
  for(const plot of [figure,calibration]){
    const lines=plot.querySelectorAll('line'),texts=plot.querySelectorAll('text');
    assert.equal(lines.filter(node=>node.attrs['data-grid']).length,10);
    assert.ok(lines.filter(node=>node.attrs['data-grid']).every(node=>node.attrs.stroke==='var(--line)'));
    assert.deepEqual(lines.filter(node=>node.attrs['data-axis']).map(node=>node.attrs['data-axis']),['x','y']);
    for(const axis of ['x','y'])assert.deepEqual(texts.filter(node=>node.attrs['data-axis-tick']===axis).map(node=>node.textContent),['0','0.25','0.5','0.75','1']);
    assert.equal(texts.filter(node=>node.attrs['data-axis-label']).length,2);
  }
});
