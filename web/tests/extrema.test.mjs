import test from 'node:test';
import assert from 'node:assert/strict';
import {fork} from 'node:child_process';
import {readFileSync} from 'node:fs';
import {parse} from '../parser.js';
import {parseCatalogHelp,helpExampleInput} from '../catalog-help.js';

function nextMessage(worker,predicate) {
  return new Promise((resolve,reject)=>{
    const timer=setTimeout(()=>done(new Error('Worker message timed out')),30000);
    const onMessage=data=>{if(data.type==='fatal')done(new Error(data.error));else if(predicate(data))done(null,data);};
    function done(error,data){clearTimeout(timer);worker.off('message',onMessage);worker.off('error',done);error?reject(error):resolve(data);}
    worker.on('message',onMessage);worker.on('error',done);
  });
}

test('help examples run through the production WASM calculator and graph extrema search',{timeout:60000},async t=>{
  const worker=fork(new URL('./worker-bridge.mjs',import.meta.url),[],{execArgv:['--experimental-wasm-jspi']});
  t.after(()=>worker.kill());
  await nextMessage(worker,data=>data.type==='ready');
  let id=0;
  async function execute(request){
    const current=++id;
    const pending=nextMessage(worker,data=>data.type==='result'&&data.id===current);
    worker.send({id:current,request});
    return (await pending).result;
  }
  const examples=language=>parseCatalogHelp(readFileSync(new URL(`../catalog_help${language}.md`,import.meta.url),'utf8'))
    .filter(block=>block.kind==='entry'&&/^(minimum|maximum|discriminant)\(/.test(block.signature)&&block.example?.includes('→'));
  const english=examples(''),korean=examples('_ko');
  assert.equal(english.length,10);
  assert.deepEqual(korean.map(block=>helpExampleInput(block.example)),english.map(block=>helpExampleInput(block.example)));
  for(const block of english){
    const source=helpExampleInput(block.example);
    const expected=block.example.split('→')[1].trim();
    const tree=parse(source);
    const result=await execute({tree});
    if(expected.startsWith('no ')){
      assert.equal(result.ok,false,source);assert.match(result.error,/unbounded|not attained/,source);
    }else{
      assert.equal(result.ok,true,`${source}: ${result.error}`);assert.equal(result.exact,expected,source);
    }
    if(tree.value==='discriminant'||tree.args.length===5)continue;
    const graph=await execute({action:'graphAnalysis',trees:[tree.args[0]],analysis:tree.value,a:-2,b:2});
    assert.equal(graph.ok,result.ok,`${source}: ${graph.error}`);
    if(graph.ok){
      assert.ok(graph.points.length,source);
      const numeric=expected==='1/4'?.25:Number(expected);
      for(const [,value] of graph.points)assert.equal(value,numeric,source);
    }else assert.match(graph.error,/unbounded|not attained/,source);
  }
});
