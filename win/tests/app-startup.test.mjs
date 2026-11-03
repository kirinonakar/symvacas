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
  const calls=[];let calculationResult=null;
  window.__TAURI__={core:{Channel:class {},invoke:async(name,args)=>{
    calls.push(name);
    if(name==='set_window_theme'){nativeTheme=args.theme;refreshNativeTheme();return;}
    if(name==='native_start')return {type:'ready',python:'3.14.10'};
    if(name==='native_execute')return calculationResult||{ok:false,error:'No preview requested'};
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
  const byId=id=>window.document.getElementById(id);
  assert.ok(byId('desktop-panel-history').querySelector('.history-content'));
  assert.ok(byId('desktop-panel-functions').querySelector('.catalog-entry'));
  byId('catalog-button').click();
  assert.equal(byId('desktop-tab-functions').getAttribute('aria-selected'),'true');
  assert.equal(byId('dialog').open,false,'desktop catalog header selects the inline tab');
  byId('clear').click();
  const functionSearch=byId('desktop-panel-functions').querySelector('input');
  functionSearch.value='sin()';functionSearch.dispatchEvent(new window.Event('input'));
  byId('desktop-panel-functions').querySelector('.catalog-entry button').click();
  assert.equal(byId('expression').value,'sin()');assert.equal(byId('expression').selectionStart,4);
  assert.equal(byId('dialog').open,false);
  byId('clear').click();
  const number={kind:'number',value:'3',args:[]};
  calculationResult={ok:true,exact:'3',decimal:'3',resultAst:number,tree:number,decimalTree:number};
  byId('expression').value='1+2';byId('expression').dispatchEvent(new window.Event('input',{bubbles:true}));
  const equals=window.document.querySelector('.key[data-input="="]');assert.ok(equals);equals.click();
  await flush();await flush();
  byId('history-button').click();
  assert.equal(byId('desktop-tab-history').getAttribute('aria-selected'),'true');
  assert.equal(byId('desktop-panel-history').querySelector('.list-row code').textContent,'1+2','a newly calculated result appears in the inline history');
  byId('desktop-calculator-close').click();assert.equal(byId('desktop-calculator-panel').hidden,true);
  byId('desktop-calculator-toggle').click();assert.equal(byId('desktop-calculator-panel').hidden,false);
  calculationResult=null;
  assert.ok(byId('desktop-graph-input').contains(byId('graph-ranges')));
  assert.ok(byId('desktop-statistics-output').contains(byId('statistics-summary-result')));
  const analysisShortcut=window.document.querySelector('.workspace-navigation-section[aria-controls="statistics-tests"]');
  assert.ok(analysisShortcut,'statistics section links survive desktop grouping');
  analysisShortcut.click();
  assert.equal(window.document.documentElement.dataset.workspace,'statistics');
  assert.equal(byId('statistics-analysis').open,true);
  assert.equal(byId('statistics-tests').open,true);
  assert.equal(analysisShortcut.getAttribute('aria-current'),'location');
  byId('statistics-table-toggle').click();
  assert.equal(byId('statistics-grid').hidden,false);
  const cell=byId('statistics-grid').querySelector('input[data-row="0"][data-column="0"]');
  cell.value='42';cell.dispatchEvent(new window.Event('input',{bubbles:true}));
  assert.equal(byId('statistics-data').value.split('\n')[0],'42,2','grid edits still update the analysis source');
  // Let the editor's deferred source refresh finish before tearing down globals.
  await new Promise(resolve=>setTimeout(resolve,200));
  byId('statistics-table-toggle').click();
  assert.equal(byId('statistics-grid').hidden,true);
  byId('statistics-collapse-all').click();
  assert.equal(byId('statistics-tests').open,false);
  const sidebarToggle=byId('desktop-sidebar-toggle');sidebarToggle.click();
  assert.equal(byId('workspace-navigation').hidden,true);sidebarToggle.click();
  assert.equal(byId('workspace-navigation').hidden,false);
  window.document.querySelector('[data-workspace-target="graph"]').click();
  assert.equal(window.document.documentElement.dataset.workspace,'graph');
  assert.equal(byId('graph-source').value,'sin(x)\ncos(x)');
  const analysis=byId('graph-analysis'),sliders=byId('graph-analysis-sliders');
  assert.equal(byId('graph-plot').closest('.graph-plot-frame').nextElementSibling,sliders,'analysis tracks sit directly below the graph at the same pane width');
  assert.equal(sliders.parentElement,byId('desktop-graph-output'));
  analysis.open=true;await flush();assert.equal(sliders.hidden,false);
  byId('graph-analysis-a-slider').value='2';byId('graph-analysis-a-slider').dispatchEvent(new window.Event('input',{bubbles:true}));
  assert.equal(Number(byId('graph-analysis-a').value),2,'moving the existing slider still updates the analysis position');
  analysis.open=false;await flush();assert.equal(sliders.hidden,true);
  analysis.open=true;analysis.hidden=true;await flush();assert.equal(sliders.hidden,true,'unsupported graph kinds do not expose analysis sliders');
  analysis.hidden=false;await flush();assert.equal(sliders.hidden,false);
  assert.ok(!window.document.getElementById('dialog').open,'installed runtime does not show first-install prompt');
});
