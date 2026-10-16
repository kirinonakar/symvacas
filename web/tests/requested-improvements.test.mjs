import test from 'node:test';
import assert from 'node:assert/strict';
import {fork} from 'node:child_process';
import {parse} from '../parser.js';
import {statisticsRequest} from '../statistics-request.js';
import {savedStatisticsDatasets} from '../statistics-bindings.js';


test('production WASM runs real roots, domain exclusions, ranks, ODE bounds and large float64 logistic fits',{timeout:60000},async t=>{
  const worker=fork(new URL('./worker-bridge.mjs',import.meta.url),[],{execArgv:['--experimental-wasm-jspi']});
  t.after(()=>worker.kill());
  function receive(predicate){
    return new Promise((resolve,reject)=>{
      const timer=setTimeout(()=>done(new Error('Worker message timed out')),30000);
      function done(error,value){clearTimeout(timer);worker.off('message',message);worker.off('error',done);error?reject(error):resolve(value);}
      function message(value){if(value.type==='fatal')done(new Error(value.error));else if(predicate(value))done(null,value);}
      worker.on('message',message);worker.on('error',done);
    });
  }
  await receive(value=>value.type==='ready');let id=0;
  async function execute(request){const current=++id,pending=receive(value=>value.type==='result'&&value.id===current);worker.send({id:current,request});return (await pending).result;}
  const saved={datasets:{D1:'value\n0.1\n\n0.2\n1/2',D2:'x,y\n1,2\n2,4\n3,6'},datasetKinds:{D1:'list',D2:'xy'}};
  for(const [source,expected] of [['sumdata(D1)','4/5'],['mean(D1)','4/15']]){
    const tree=parse(source),result=await execute({tree,statisticsDatasets:savedStatisticsDatasets(tree,saved)});
    assert.equal(result.ok,true,result.error);assert.equal(result.exact,expected);
  }
  const namedRegression=parse('regression(D2,linear)'),fit=await execute({tree:namedRegression,statisticsDatasets:savedStatisticsDatasets(namedRegression,saved)});
  assert.equal(fit.ok,true,fit.error);assert.equal(fit.regression.n,3);
  saved.datasets.D1=Array.from({length:5000},(_,i)=>String(i+1)).join('\n');
  const namedMean=parse('mean(D1)'),largeMean=await execute({tree:namedMean,statisticsDatasets:savedStatisticsDatasets(namedMean,saved)});
  assert.equal(largeMean.ok,true,largeMean.error);assert.equal(largeMean.exact,'5001/2');
  for(const source of ['cbrt(-8)','nthroot(-8,3)']){
    const result=await execute({tree:parse(source)});assert.equal(result.ok,true,result.error);assert.equal(result.exact,'-2');
  }
  for(const source of ['cbrt(x)','nthroot(x,3)']){
    const result=await execute({action:'graph',trees:[parse(source)],min:-8,max:8});
    assert.equal(result.ok,true,result.error);assert.ok(result.curves[0].some(point=>point?.[0]<0&&point[1]<0));
  }
  const solve=await execute({tree:parse('solve(x/x=1,x)')});assert.equal(solve.ok,true,solve.error);assert.equal(solve.exact,'Complement(Complexes, {0})');
  const derivative=await execute({tree:parse('diff(abs(x),x)')});assert.equal(derivative.exact,'sign(x)');
  const rootDerivative=await execute({tree:parse('diff(cbrt(x),x)')});assert.equal(rootDerivative.ok,true,rootDerivative.error);assert.doesNotMatch(rootDerivative.exact,/Derivative|DiracDelta/);assert.ok(rootDerivative.conditions.length);
  const limit=await execute({tree:parse('limit(1/x,x,0)')});assert.equal(limit.ok,false);assert.match(limit.error,/left-hand limit = -oo.*right-hand limit = oo/);
  const undefinedCall=await execute({tree:parse('foo([1,2],[3,4])')});assert.match(undefinedCall.error,/Undefined function: foo/);
  for(const name of ['pearson','spearman','kendall']){
    const result=await execute(statisticsRequest(`${name}([1,2,3],[1,2,3])`));
    assert.equal(result.ok,true,result.error);assert.equal(result.statisticsReport.analysis,name);
    const summary=result.statisticsReport.sections.find(section=>section.title==='Summary');
    assert.ok(Math.abs(Number(summary.rows.find(row=>row[0]==='p')[1].decimal)-(name==='pearson'?0:1/3))<1e-12);
  }
  for(const [source,kinds] of [['1/x',['vertical','horizontal']],['tan(x)',['vertical','vertical']]]){
    const result=await execute({action:'graphAnalysis',analysis:'asymptotes',trees:[parse(source)],a:-2,b:2});
    assert.equal(result.ok,true,result.error);assert.deepEqual(result.asymptotes.map(item=>item.kind),kinds);
  }
  const ode=await execute({tree:parse('dsolve(diff(y(x),x)=x*y(x)^2+y(x)^3,y(x),x)')});
  assert.equal(ode.ok,false);assert.match(ode.error,/numerical differential-equation graph/);
  let seed=123;const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/2**32;};
  const rows=Array.from({length:5000},()=>{
    const xs=Array.from({length:5},()=>random()*4-2),eta=.2+xs.reduce((sum,x,i)=>sum+x*[.5,-.4,.3,.2,-.1][i],0);
    return [...xs,random()<1/(1+Math.exp(-eta))?1:0].map(String);
  });
  const logistic=await execute({tree:{kind:'call',value:'regression',args:[{kind:'symbol',value:'largeData'},{kind:'symbol',value:'logistic'}]},statisticsDatasets:{largeData:rows},precision:20});
  assert.equal(logistic.ok,true,logistic.error);assert.equal(logistic.regression.numericBackend,'float64');
  assert.equal(logistic.regression.n,5000);assert.equal(logistic.regression.residuals.length,5000);
  assert.ok(logistic.regression.coefficients.every(coefficient=>Number.isFinite(Number(coefficient.se))));
});
