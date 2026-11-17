import test from 'node:test';
import assert from 'node:assert/strict';
import {installEngine} from '../engine-bootstrap.js';
import {fetchEngineAsset} from '../engine-fetch.js';

function fixture(){
  const requests=[],unpacked=[],python=[];
  const lock={packages:Object.fromEntries(['mpmath','sympy'].map(name=>[name,{file_name:name+'.whl',sha256:'00'.repeat(32)}]))};
  const pyodide={runPython:source=>{python.push(source);return '/lib/python3.14/site-packages';},unpackArchive:(body,format,options)=>unpacked.push({body:new TextDecoder().decode(body),format,...options}),loadPackage:()=>{throw new Error('Package manager must not run during startup');}};
  const fetcher=async(url,options)=>{requests.push({url:String(url),options});return new Response(String(url).endsWith('pyodide-lock.json')?JSON.stringify(lock):String(url).split('/').at(-1));};
  const options={runtimeURL:new URL('https://example.test/symvacas/vendor/'),engineURL:new URL('https://example.test/symvacas/engine.zip'),fetcher};
  return {requests,unpacked,python,pyodide,options};
}

test('cold startup installs bundled wheels in dependency order with integrity and nested paths',async()=>{
  const f=fixture();await installEngine(f.pyodide,f.options);
  assert.deepEqual(f.unpacked.map(item=>item.body),['mpmath.whl','sympy.whl','engine.zip']);
  assert.deepEqual(f.unpacked.map(item=>item.extractDir),['/lib/python3.14/site-packages','/lib/python3.14/site-packages','/symvacas']);
  for(const request of f.requests.filter(item=>item.url.endsWith('.whl'))){assert.match(request.url,/\/symvacas\/vendor\//);assert.match(request.options.integrity,/^sha256-/);}
  assert.match(f.python.at(-1),/import calc_engine, script_runner/);
});

test('startup retries a stalled response body and bypasses the HTTP cache',async()=>{
  const requests=[];
  const response=await fetchEngineAsset(async(_,options)=>{
    requests.push(options);
    return requests.length===1?{ok:true,status:200,arrayBuffer:()=>new Promise(()=>{})}:new Response('wheel');
  },'sympy.whl',{},15);
  assert.equal(await response.text(),'wheel');
  assert.equal(requests.length,2);assert.equal(requests[0].signal.aborted,true);assert.equal(requests[1].cache,'reload');
});

test('WASM bytes reach streaming compilation before the download finishes',async()=>{
  let source;
  const response=await fetchEngineAsset(async()=>new Response(new ReadableStream({start(stream){source=stream;}}),
    {headers:{'Content-Type':'application/wasm'}}),'runtime.wasm');
  const reader=response.body.getReader();
  source.enqueue(new Uint8Array([0,97,115,109]));
  assert.deepEqual((await reader.read()).value,new Uint8Array([0,97,115,109]));
  source.enqueue(new Uint8Array([1,0,0,0]));source.close();
  assert.deepEqual((await reader.read()).value,new Uint8Array([1,0,0,0]));
  assert.equal((await reader.read()).done,true);
  // The first chunk has already been consumed; check the actual browser API
  // separately with a complete response routed through the same fetch helper.
  const complete=await fetchEngineAsset(async()=>new Response(new Uint8Array([0,97,115,109,1,0,0,0]),
    {headers:{'Content-Type':'application/wasm'}}),'runtime.wasm');
  assert.ok(await WebAssembly.compileStreaming(complete) instanceof WebAssembly.Module);
});
