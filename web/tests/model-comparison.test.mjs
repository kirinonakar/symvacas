import test from 'node:test';
import assert from 'node:assert/strict';
import {fork} from 'node:child_process';
import {readFileSync} from 'node:fs';
import {JSDOM} from 'jsdom';
import {advancedStatisticsSchema} from '../advanced-statistics-schema.js';
import {advancedStatisticsExampleRows,createAdvancedStatistics,guidedStatisticsCommand} from '../advanced-statistics.js';
import {statisticsRequest} from '../statistics-request.js';

const definition=advancedStatisticsSchema.find(d=>d.id==='modelcompare');
const settings=family=>({family,basePredictors:family==='cox'?'2':['lmm','glmm','gee'].includes(family)?'1':'0',...(family==='gee'?{responsefamily:'gaussian'}:{})});

test('every model comparison family preserves metadata through production request parsing',()=>{
  for(const family of Object.keys(definition.exampleRowsByFamily)){
    const opts=settings(family),rows=advancedStatisticsExampleRows(definition,opts);
    const request=statisticsRequest(guidedStatisticsCommand(definition,rows,opts));
    assert.equal(request.tree.args[2].kind,'symbol',family);
    assert.equal(request.tree.args[2].value,family);
    const pairs=request.tree.args[8].args;
    assert.ok(pairs.every(pair=>pair.args[0].kind==='symbol'),family);
    assert.ok(pairs.some(pair=>pair.args[0].value==='excludedrows'),family);
  }
  const request=statisticsRequest(guidedStatisticsCommand(definition,definition.exampleRows,{validation:'external',_validationRows:definition.exampleRows}));
  assert.ok(request.tree.args[8].args.some(pair=>pair.args[0].kind==='symbol'&&pair.args[0].value==='excludedvalidation'));
});

test('analysis failures remain visible beside the model form and clear when inputs change',context=>{
  const dom=new JSDOM(readFileSync(new URL('../index.html',import.meta.url),'utf8'));
  const previous=globalThis.document;globalThis.document=dom.window.document;
  context.after(()=>{dom.window.close();globalThis.document=previous;});
  const state={fields:{'statistics-models-kind':'modelcompare','statistics-models-input':'example'},datasets:{}};
  document.documentElement.dataset.engine='ready';
  const api=createAdvancedStatistics({state,persist:()=>{},data:()=>'',columnLimit:()=>3,section:'models'});
  const status=document.getElementById('statistics-models-status'),button=document.querySelector('[data-run="statistics-models"]');
  assert.equal(button.disabled,false);
  api.showResult({ok:false,error:'Singular model'},api.context());
  api.render();
  assert.equal(status.textContent,'Singular model');assert.equal(status.getAttribute('role'),'alert');
  const folds=document.getElementById('statistics-form-modelcompare-folds');folds.value='3';folds.dispatchEvent(new dom.window.Event('input'));
  assert.notEqual(status.textContent,'Singular model');assert.equal(status.classList.contains('error'),false);
  const added=document.querySelectorAll('#statistics-form-modelcompare-addedPredictors ~ label input');
  assert.ok(added.length);
  for(const check of added){check.checked=false;check.dispatchEvent(new dom.window.Event('change'));}
  assert.equal(button.disabled,true);assert.match(status.textContent,/added predictor/);assert.equal(status.getAttribute('role'),'alert');
  api.showError('Request failed');assert.equal(status.textContent,'Request failed');
});

test('model comparison forms execute through production WASM and return visible reports',{timeout:180000},async context=>{
  const worker=fork(new URL('./worker-bridge.mjs',import.meta.url),[],{execArgv:['--experimental-wasm-jspi']});
  context.after(()=>worker.kill());
  const receive=predicate=>new Promise((resolve,reject)=>{
    const timeout=setTimeout(()=>finish(new Error('Model comparison worker timed out')),60000);
    const listener=data=>{if(data.type==='fatal')finish(new Error(data.error));else if(predicate(data))finish(null,data);};
    function finish(error,data){clearTimeout(timeout);worker.off('message',listener);worker.off('error',finish);error?reject(error):resolve(data);}
    worker.on('message',listener);worker.on('error',finish);
  });
  await receive(data=>data.type==='ready');let id=0;
  for(const family of ['linear','logistic','cox','gee']){
    const opts=settings(family),rows=advancedStatisticsExampleRows(definition,opts);
    const source=guidedStatisticsCommand(definition,rows,opts),current=++id,pending=receive(data=>data.type==='result'&&data.id===current);
    worker.send({id:current,request:{...statisticsRequest(source),precision:12}});
    const result=(await pending).result;
    assert.equal(result.ok,true,`${family}: ${result.error}`);
    assert.equal(result.statisticsReport.analysis,'modelcompare');
    assert.ok(result.statisticsReport.sections.length>0,family);
  }
});
