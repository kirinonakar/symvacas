import test from 'node:test';
import assert from 'node:assert/strict';
import {fork} from 'node:child_process';
import {advancedStatisticsSchema} from '../advanced-statistics-schema.js';
import {advancedStatisticsExampleRows,guidedStatisticsCommand} from '../advanced-statistics.js';
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
