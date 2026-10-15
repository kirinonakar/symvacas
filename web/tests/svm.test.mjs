import test from 'node:test';
import assert from 'node:assert/strict';
import {JSDOM} from 'jsdom';
import {fork} from 'node:child_process';
import {statisticsCommand} from '../workspace-commands.js';
import {statisticsRequest} from '../statistics-request.js';
import {renderRegressionReport,regressionResidualCSV} from '../regression-report.js';
import {regressionEquationCopyText,statisticsResultMarkdown} from '../statistics-markdown.js';
import {setLanguage} from '../i18n.js';

test('SVM command supports selected response and validates parameters',()=>{
  const command=statisticsCommand('y,a,b\n0,-1,4\n1,2,4\n,3,5',{
    op:'regression',kind:'columns:3',regression:'svc',responseColumn:0,
    svmKernel:'linear',svmC:'2',svmGamma:'auto',svmEpsilon:'0.1'});
  assert.equal(command,'regression([[-1,4,0],[2,4,1]],svc,[linear,2,auto,0.1])');
  for(const settings of [{svmC:'0'},{svmC:''},{svmGamma:'0'},{svmEpsilon:'-1'},{svmKernel:'bad'},{svmC:'1],oops('}]){
    assert.throws(()=>statisticsCommand('-1,0\n1,1',{op:'regression',kind:'xy',regression:'svm',...settings}),/SVM/);
  }
  assert.equal(statisticsCommand('-1,0\n1,1',{op:'regression',kind:'xy',regression:'svc',svmKernel:'linear',svmGamma:'bad',svmEpsilon:'bad'}),
    'regression([[-1,0],[1,1]],svc,[linear,1,auto,0.1])');
});

test('packaged WASM SVM returns scores, predictions, ROC and a copyable report',{timeout:60000},async context=>{
  const worker=fork(new URL('./worker-bridge.mjs',import.meta.url),[],{execArgv:['--experimental-wasm-jspi']});
  context.after(()=>worker.kill());
  const receive=predicate=>new Promise((resolve,reject)=>{
    const timer=setTimeout(()=>finish(new Error('SVM worker timed out')),30000);
    const listener=data=>data.type==='fatal'?finish(new Error(data.error)):predicate(data)?finish(null,data):undefined;
    function finish(error,data){clearTimeout(timer);worker.off('message',listener);worker.off('error',finish);error?reject(error):resolve(data);}
    worker.on('message',listener);worker.on('error',finish);
  });
  await receive(data=>data.type==='ready');
  const pending=receive(data=>data.type==='result'&&data.id===1);
  worker.send({id:1,request:statisticsRequest('regression([[-1,-1,0],[-1,1,1],[1,-1,1],[1,1,0]],svc,[rbf,10,auto,0.1])')});
  const result=(await pending).result;
  assert.equal(result.ok,true,result.error);
  assert.equal(result.regression.accuracy,1);
  assert.deepEqual(result.regression.confusionMatrix,[[2,0],[0,2]]);
  assert.equal(result.regression.threshold,0);
  assert.equal(result.reusable,false);
  assert.match(regressionEquationCopyText(result),/^f\(x\) = /);
  assert.match(regressionResidualCSV(result.regression),/decisionScore/);
  const markdown=statisticsResultMarkdown(result);
  assert.match(markdown,/Decision score/);
  assert.match(markdown,/SVM classification/);
  assert.doesNotMatch(markdown,/unavailable|Residual diagnostics|linear coefficients|epsilon/);
  const dom=new JSDOM('<main></main>'),previous=globalThis.document;
  globalThis.document=dom.window.document;setLanguage('en');
  context.after(()=>{globalThis.document=previous;dom.window.close();});
  const main=document.querySelector('main');renderRegressionReport(main,result.regression);
  assert.match(main.textContent,/Support vectors/);
  assert.match(main.textContent,/Decision score/);
  assert.match(main.textContent,/Decision threshold=0/);
  assert.match(main.textContent,/not probabilities/);
  assert.doesNotMatch(main.textContent,/α=|L1=/);
  assert.ok(main.querySelector('[data-roc-curve]'));
  assert.match(main.textContent,/Model: SVC/);
  assert.match(main.textContent,/Training accuracy/);
  assert.match(main.textContent,/Cross-validated accuracy/);
  assert.match(main.textContent,/Classification predictions/);
  assert.doesNotMatch(main.textContent,/Residual diagnostics|ε=|df=|linear coefficients/);
  const plot=main.querySelector('[data-svm-decision-plot]');assert.ok(plot);
  assert.equal(plot.querySelectorAll('[data-svm-observation]').length,4);
  assert.equal(plot.querySelectorAll('[data-svm-support]').length,result.regression.supportVectors);
  assert.ok(plot.querySelector('[data-svm-level="0"]'));
  assert.ok(main.querySelector('[data-svm-decision-equation]'));
  assert.ok([...main.querySelectorAll('th')].some(header=>header.textContent==='Signed coefficient (αᵢyᵢ)'));
  assert.match(main.textContent,/aᵢ = αᵢyᵢ/);
  assert.match(markdown,/Signed coefficient/);
  assert.match(main.textContent,/f\(x\).*class 1/);
  assert.doesNotMatch(regressionResidualCSV(result.regression),/residual|standardized/);
  const svrPending=receive(data=>data.type==='result'&&data.id===2);
  worker.send({id:2,request:statisticsRequest('regression([[-2,-3],[-1,-1],[0,1],[1,3],[2,5]],svr,[linear,10,auto,0])')});
  const svr=(await svrPending).result;
  assert.equal(svr.ok,true,svr.error);
  assert.ok(Number(svr.regression.rSquared)>.99999);
  assert.ok(svr.curve.length>100);
  assert.equal(svr.regression.task,'regression');
});
