import test from 'node:test';
import assert from 'node:assert/strict';
import {fork} from 'node:child_process';
import {statisticsRequest} from '../statistics-request.js';
import {regressionResidualCSV} from '../regression-report.js';

test('packaged WASM SVM returns classification scores and regression predictions',{timeout:60000},async context=>{
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
  const classificationFields=regressionResidualCSV(result.regression).split('\n',1)[0].split(',');
  assert.ok(classificationFields.includes('decisionScore'));
  assert.ok(!classificationFields.includes('residual'));
  const svrPending=receive(data=>data.type==='result'&&data.id===2);
  worker.send({id:2,request:statisticsRequest('regression([[-2,-3],[-1,-1],[0,1],[1,3],[2,5]],svr,[linear,10,auto,0])')});
  const svr=(await svrPending).result;
  assert.equal(svr.ok,true,svr.error);
  assert.ok(Number(svr.regression.rSquared)>.99999);
  assert.ok(svr.curve.length>100);
  assert.equal(svr.regression.task,'regression');
  assert.ok(Number(svr.regression.mae)<1e-6);
  const regressionFields=regressionResidualCSV(svr.regression).split('\n',1)[0].split(',');
  for(const field of ['predictionError','absoluteError','supportVector'])assert.ok(regressionFields.includes(field));
});
