import test from 'node:test';
import assert from 'node:assert/strict';
import {installEngine,initializeEngine} from '../engine-bootstrap.js';
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

test('missing wheels stop startup before Python imports or partial installation',async()=>{
  const f=fixture(),fetcher=f.options.fetcher;
  f.options.fetcher=(url,options)=>fetchEngineAsset((input,init)=>String(input).endsWith('sympy.whl')?Promise.resolve(new Response('missing',{status:404})):fetcher(input,init),url,options);
  await assert.rejects(installEngine(f.pyodide,f.options),/404/);
  assert.equal(f.unpacked.length,0);assert.equal(f.python.length,0);
});

test('engine downloads overlap runtime startup and share its manifest request',async()=>{
  const f=fixture();
  let releaseRuntime,runtimeReady=false,lock;
  const pending=initializeEngine(options=>{
    lock=options.lockFileContents;
    return new Promise(resolve=>{releaseRuntime=()=>resolve(f.pyodide);});
  },f.options,()=>{runtimeReady=true;});
  await new Promise(resolve=>setImmediate(resolve));
  assert.deepEqual(f.requests.map(item=>item.url.split('/').at(-1)).sort(),
    ['engine.zip','mpmath.whl','pyodide-lock.json','sympy.whl']);
  assert.equal((await lock).packages.sympy.file_name,'sympy.whl');
  assert.equal(runtimeReady,false);assert.equal(f.unpacked.length,0);
  releaseRuntime();
  assert.equal(await pending,f.pyodide);assert.equal(runtimeReady,true);
  assert.deepEqual(f.unpacked.map(item=>item.body),['mpmath.whl','sympy.whl','engine.zip']);
  assert.equal(f.requests.filter(item=>item.url.endsWith('pyodide-lock.json')).length,1);
});

test('overlapping startup reports download failure even while the runtime is pending',async()=>{
  const f=fixture(),fetcher=f.options.fetcher;
  f.options.fetcher=(url,options)=>String(url).endsWith('sympy.whl')
    ?Promise.reject(new Error('wheel unavailable')):fetcher(url,options);
  await assert.rejects(initializeEngine(()=>new Promise(()=>{}),f.options),/wheel unavailable/);
  assert.equal(f.unpacked.length,0);assert.equal(f.python.length,0);
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

test('stalled WASM streams remain bounded and abort their network request',async()=>{
  let signal;
  const response=await fetchEngineAsset(async(_,options)=>{
    signal=options.signal;
    return new Response(new ReadableStream({}),{headers:{'Content-Type':'application/wasm'}});
  },'runtime.wasm',{},15);
  await assert.rejects(response.arrayBuffer(),/timed out/);
  assert.equal(signal.aborted,true);
});
test('a download that never resolves fails after two bounded attempts',async()=>{
  let requests=0;
  await assert.rejects(fetchEngineAsset(()=>{requests++;return new Promise(()=>{});},'engine.zip',{},10),/timed out/);
  assert.equal(requests,2);
});
