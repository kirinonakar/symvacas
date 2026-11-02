import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {JSDOM} from 'jsdom';
import {IDBFactory} from 'fake-indexeddb';

test('assembled desktop UI initializes every workspace with a native engine',async context=>{
  const html=await readFile(new URL('../dist/index.html',import.meta.url),'utf8');
  const dom=new JSDOM(html,{url:'http://tauri.localhost/',pretendToBeVisual:true});
  const {window}=dom,properties=new Map();
  const globals={window,document:window.document,navigator:window.navigator,location:window.location,
    localStorage:window.localStorage,indexedDB:new IDBFactory(),getComputedStyle:window.getComputedStyle,
    requestAnimationFrame:window.requestAnimationFrame.bind(window),cancelAnimationFrame:window.cancelAnimationFrame.bind(window),
    NodeFilter:window.NodeFilter,MutationObserver:window.MutationObserver,HTMLElement:window.HTMLElement,HTMLInputElement:window.HTMLInputElement,
    HTMLTextAreaElement:window.HTMLTextAreaElement,ResizeObserver:class {observe(){}disconnect(){}},
    fetch:async path=>{
      const relative=new URL(path,'http://tauri.localhost/').pathname.slice(1);
      const content=await readFile(new URL('../dist/'+relative,import.meta.url));
      return new Response(content,{status:200});
    }};
  for(const [name,value] of Object.entries(globals)){
    properties.set(name,Object.getOwnPropertyDescriptor(globalThis,name));
    Object.defineProperty(globalThis,name,{configurable:true,writable:true,value});
  }
  let osDark=false,nativeTheme=null;
  const themeListeners=new Set();
  const media={matches:false,addEventListener:(_event,listener)=>themeListeners.add(listener),removeEventListener:(_event,listener)=>themeListeners.delete(listener)};
  window.matchMedia=()=>media;
  const refreshNativeTheme=()=>{
    const next=nativeTheme===null?osDark:nativeTheme==='dark';
    if(media.matches!==next){media.matches=next;for(const listener of themeListeners)listener({matches:next});}
  };
  window.HTMLElement.prototype.scrollIntoView=()=>{};
  window.HTMLCanvasElement.prototype.getContext=()=>new Proxy({measureText:()=>({width:0}),canvas:{}},{get:(target,key)=>target[key]||(()=>{})});
  window.HTMLDialogElement.prototype.showModal=function(){this.open=true;};
  window.HTMLDialogElement.prototype.close=function(){this.open=false;};
  const calls=[];
  window.__TAURI__={core:{Channel:class {},invoke:async(name,args)=>{
    calls.push(name);
    if(name==='set_window_theme'){nativeTheme=args.theme;refreshNativeTheme();return;}
    if(name==='native_start')return {type:'ready',python:'3.14.10'};
    if(name==='native_execute')return {ok:false,error:'No preview requested'};
    if(name==='python_status')return {ready:true,path:'C:\\App\\python_embeded',python:'3.14.10',sympy:'1.14.0',mpmath:'1.3.0'};
    if(name==='integration_info')return {cli:'C:\\App\\symvacas-cli.exe',mcp:{}};
    if(name==='sync_statistics_datasets')return {datasets:{}};
  }}};
  context.after(()=>{
    window.dispatchEvent(new window.Event('pagehide'));dom.window.close();
    for(const [name,descriptor] of properties)if(descriptor)Object.defineProperty(globalThis,name,descriptor);else delete globalThis[name];
  });
  await import('../dist/desktop-bootstrap.js');
  const flush=()=>new Promise(resolve=>setImmediate(resolve));
  const chooseTheme=async choice=>{const select=window.document.getElementById('theme');select.value=choice;select.onchange();await flush();};
  await flush();
  assert.equal(nativeTheme,null,'startup system mode follows Windows');
  osDark=true;refreshNativeTheme();await flush();
  assert.equal(window.document.documentElement.dataset.theme,'dark');
  await chooseTheme('dark');assert.equal(nativeTheme,'dark');
  await chooseTheme('system');assert.equal(nativeTheme,null,'same-color system selection releases the native override');
  osDark=false;refreshNativeTheme();await flush();
  assert.equal(window.document.documentElement.dataset.theme,'light');assert.equal(nativeTheme,null);
  await chooseTheme('dark');
  assert.equal(window.document.documentElement.dataset.theme,'dark');
  await chooseTheme('system');
  assert.equal(window.document.documentElement.dataset.theme,'light','switching from explicit dark restores the OS light theme');
  osDark=true;refreshNativeTheme();await flush();
  assert.equal(window.document.documentElement.dataset.theme,'dark');
  await chooseTheme('light');osDark=false;refreshNativeTheme();osDark=true;refreshNativeTheme();await flush();
  assert.equal(window.document.documentElement.dataset.theme,'light','an explicit theme stays fixed across OS changes');
  assert.equal(window.document.documentElement.dataset.engine,'ready');
  assert.equal(window.document.getElementById('status').textContent,'Engine ready · CPython');
  assert.ok(calls.includes('native_start'));
  for(const mode of ['graph','python','equation','matrix','vector','statistics','probability','programmer','units','constants','tip','currency','functions','scientific']){
    const select=window.document.getElementById('mode');select.value=mode;select.onchange();
    assert.equal(window.document.documentElement.dataset.workspace,mode);
  }
  assert.ok(!window.document.getElementById('dialog').open,'installed runtime does not show first-install prompt');
});
