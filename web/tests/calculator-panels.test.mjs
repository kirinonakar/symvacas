import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {JSDOM} from 'jsdom';
import {createAppState} from '../app-state.js';
import {createAppDialogs} from '../app-dialogs.js';
import {setLanguage} from '../i18n.js';

async function setup(context){
  const dom=new JSDOM(readFileSync(new URL('../index.html',import.meta.url),'utf8'),{url:'http://localhost/'});
  const {window}=dom,{document}=window,descriptors=new Map();
  const globals={window,document,NodeFilter:window.NodeFilter,fetch:async()=>new Response(JSON.stringify({Scientific:['sin()','cos()'],Symbolic:['diff(,x)']}))};
  for(const [key,value] of Object.entries(globals)){
    descriptors.set(key,Object.getOwnPropertyDescriptor(globalThis,key));Object.defineProperty(globalThis,key,{configurable:true,writable:true,value});
  }
  context.after(()=>{dom.window.close();for(const [key,descriptor] of descriptors){if(descriptor)Object.defineProperty(globalThis,key,descriptor);else delete globalThis[key];}});
  setLanguage('en');window.matchMedia=()=>({matches:false,addEventListener(){}});
  let closes=0;document.getElementById('dialog').close=()=>closes++;
  const state=createAppState({history:[{source:'1+2',exact:'3',star:false},{source:'2+2',exact:'4',star:true}]}),insertions=[],reuses=[];
  const noop=()=>{};let dialogs;
  const calculator={insert:(...args)=>insertions.push(args),replaceInput:(...args)=>reuses.push(args),clearHistorySelection:noop};
  dialogs=createAppDialogs({state,calculator,persist:()=>dialogs?.refreshPanels(),ui:{toast:noop,pickFile:noop,openDialog:(_title,content)=>document.getElementById('dialog-body').replaceChildren(content)},
    changeMode:mode=>{document.getElementById('mode').value=mode;},pressKey:noop,refreshDisplays:noop,renderMatrix:noop,error:noop,reloadState:noop});
  await dialogs.initialize();
  const host=document.createElement('aside');document.body.append(host);
  return {window,document,state,dialogs,host,insertions,reuses,get closes(){return closes;}};
}

test('inline history refreshes live, keeps search focus, reuses entries, and preserves starred records on clear',async context=>{
  const app=await setup(context),{host,state,dialogs}=app;
  const dispose=dialogs.mountCalculatorPanel(host,'history');
  assert.equal(host.querySelectorAll('.list-row').length,2);
  const search=host.querySelector('input');search.value='1+2';search.dispatchEvent(new app.window.Event('input'));search.focus();
  assert.equal(host.querySelectorAll('.list-row').length,1);
  state.history.unshift({source:'10+20',exact:'30'});dialogs.refreshPanels();
  assert.equal(app.document.activeElement,search);assert.equal(search.value,'1+2');
  host.querySelector('.list-row button:last-child').click();
  assert.deepEqual(app.reuses,[['1+2',{uncommit:true}]]);assert.equal(app.closes,0);
  search.value='';search.dispatchEvent(new app.window.Event('input'));
  assert.equal(host.querySelectorAll('.list-row').length,3);
  host.querySelector('.history-actions button:last-child').click();
  assert.deepEqual(state.history.map(item=>item.source),['2+2']);
  assert.equal(host.querySelectorAll('.list-row').length,1);
  dispose();state.history=[];dialogs.refreshPanels();assert.equal(host.querySelectorAll('.list-row').length,1);
});

test('inline functions share catalog search, favorites, recent and custom functions with the dialog',async context=>{
  const app=await setup(context),{host,dialogs,state}=app;
  dialogs.mountCalculatorPanel(host,'functions');
  assert.equal(host.querySelectorAll('.catalog-entry').length,2);
  host.querySelector('.catalog-entry button:first-child').click();
  assert.deepEqual(app.insertions,[['sin()',4]]);assert.deepEqual(state.recent,['sin()']);assert.equal(app.closes,0);
  host.querySelector('.catalog-entry button:last-child').click();assert.deepEqual(state.favorites,['sin()']);
  app.document.getElementById('catalog-button').click();
  app.document.querySelector('#dialog-body [data-category="Favorites"]').click();
  assert.equal(app.document.querySelector('#dialog-body .catalog-entry button').textContent,'sin()');
  state.functions.f={parameters:['x','y']};dialogs.refreshPanels();host.querySelector('[data-category="Custom"]').click();
  assert.equal(host.querySelector('.catalog-entry button').textContent,'f(,)');
  const search=host.querySelector('input');search.value='DIFF';search.dispatchEvent(new app.window.Event('input'));
  assert.equal(host.querySelectorAll('.catalog-entry').length,1);assert.equal(host.querySelector('.catalog-entry button').textContent,'diff(,x)');
  const first=host.querySelector('.catalog-entry');dialogs.refreshPanels();assert.equal(host.querySelector('.catalog-entry'),first,'unchanged state does not rebuild the focused list');
});
