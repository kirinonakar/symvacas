import test from 'node:test';
import assert from 'node:assert/strict';
import {fork} from 'node:child_process';
import {statisticsCommand} from '../workspace-commands.js';
import {statisticsRequest} from '../statistics-request.js';
import {regressionResidualCSV} from '../regression-report.js';
import {regressionEquationCopyText,statisticsResultMarkdown} from '../statistics-markdown.js';

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
  assert.match(markdown,/Signed coefficient/);
  assert.doesNotMatch(regressionResidualCSV(result.regression),/residual|standardized/);
  const svrPending=receive(data=>data.type==='result'&&data.id===2);
  worker.send({id:2,request:statisticsRequest('regression([[-2,-3],[-1,-1],[0,1],[1,3],[2,5]],svr,[linear,10,auto,0])')});
  const svr=(await svrPending).result;
  assert.equal(svr.ok,true,svr.error);
  assert.ok(Number(svr.regression.rSquared)>.99999);
  assert.ok(svr.curve.length>100);
  assert.equal(svr.regression.task,'regression');
  assert.ok(Number(svr.regression.mae)<1e-6);
  assert.match(regressionEquationCopyText(svr),/^ŷ = /);
  assert.match(statisticsResultMarkdown(svr),/### Prediction function/);
  assert.match(regressionResidualCSV(svr.regression),/predictionError,absoluteError,supportVector/);
  const rbfPending=receive(data=>data.type==='result'&&data.id===3);
  worker.send({id:3,request:statisticsRequest('regression([[-2,104],[-1,101],[0,100],[1,101],[2,104]],svr,[rbf,10,auto,0.1])')});
  const rbf=(await rbfPending).result;
  assert.equal(rbf.ok,true,rbf.error);
  assert.match(statisticsResultMarkdown(rbf),/Prediction function/);
  let id=3;
  for(const kernel of ['linear','rbf'])for(const [mode,binary] of [['svc',true],['svm',true],['svr',false],['svm',false]]){
    const rows=Array.from({length:12},(_,i)=>[i,binary?Number(i>=6):Math.sin(i)+.2*i]);
    const current=++id,done=receive(data=>data.type==='result'&&data.id===current);
    worker.send({id:current,request:statisticsRequest(`regression(${JSON.stringify(rows)},${mode},[${kernel},2,0.4,0.1])`)});
    const result=(await done).result;assert.equal(result.ok,true,`${mode}/${kernel}: ${result.error}`);
    const cv=result.regression.crossValidation;assert.equal(cv.available,true);assert.equal(cv.folds,5);
    assert.equal(cv.predictions.length,12);
    const copy=statisticsResultMarkdown(result);
    if(!binary)for(const metric of ['R²','RMSE','MAE']){
      assert.ok(copy.includes(`Cross-validated ${metric}`),copy);
    }
  }
});
