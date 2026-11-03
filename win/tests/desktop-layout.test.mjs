import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {JSDOM} from 'jsdom';
import {createDesktopLayout} from '../frontend/desktop-layout.js';

const html=readFileSync(new URL('../../web/index.html',import.meta.url),'utf8');
const key='symvacas.desktop-layout.v1';
function setup(context,saved,storageOverride){
  const dom=new JSDOM(html,{url:'http://tauri.localhost/'}),{document}=dom.window;
  const resizeObservers=[];
  dom.window.ResizeObserver=class {
    constructor(callback){this.callback=callback;this.targets=[];resizeObservers.push(this);}
    observe(target){this.targets.push(target);}
    disconnect(){this.targets=[];}
  };
  if(saved!==undefined)dom.window.localStorage.setItem(key,typeof saved==='string'?saved:JSON.stringify(saved));
  let width=1000;
  for(const mode of ['graph','statistics'])document.querySelector(`.workspace[data-mode="${mode}"]`).getBoundingClientRect=()=>({left:100,width});
  // jsdom has no layout engine: supply pane dimensions and splitter visibility
  // to exercise drag math and accessibility without opening a browser/app.
  const style=document.createElement('style');style.textContent='.desktop-splitter{display:block}';document.head.append(style);
  const source=document.getElementById('graph-source');source.value='a*sin(x)';let edits=0;
  source.addEventListener('input',()=>edits++);
  const layout=createDesktopLayout(document,storageOverride);
  context.after(()=>{layout.dispose();dom.window.close();});
  const splitter=mode=>document.querySelector(`.workspace[data-mode="${mode}"] > [role="separator"]`);
  const keyboard=(mode,key,shiftKey=false)=>splitter(mode).dispatchEvent(new dom.window.KeyboardEvent('keydown',{key,shiftKey,bubbles:true,cancelable:true}));
  const pointer=(target,type,x,id=7)=>{
    const event=new dom.window.MouseEvent(type,{clientX:x,button:0,bubbles:true,cancelable:true});
    Object.defineProperty(event,'pointerId',{value:id});target.dispatchEvent(event);
  };
  return {dom,document,layout,source,resizeObservers,get edits(){return edits;},splitter,keyboard,pointer,setWidth:value=>{width=value;dom.window.dispatchEvent(new dom.window.Event('resize'));},saved:()=>JSON.parse(dom.window.localStorage.getItem(key))};
}

test('desktop groups existing graph controls and datasets without losing live edits',context=>{
  const app=setup(context),{document}=app;
  assert.equal(document.getElementById('graph-source'),app.source);
  assert.equal(app.source.value,'a*sin(x)');
  app.source.dispatchEvent(new app.dom.window.Event('input'));assert.equal(app.edits,1);
  for(const id of ['graph-source','graph-ranges','graph-parameters','graph-surface-rendering','graph-analysis','graph-coordinates'])assert.ok(document.getElementById('desktop-graph-input').contains(document.getElementById(id)),id);
  assert.equal(document.getElementById('graph-analysis').nextElementSibling.id,'graph-coordinates');
  for(const id of ['graph-plot','graph-formulas','graph-save-svg'])assert.ok(document.getElementById('desktop-graph-output').contains(document.getElementById(id)),id);
  for(const id of ['dataset-list','csv-open','statistics-data','statistics-grid','statistics-table-toggle'])assert.ok(document.getElementById('desktop-statistics-input').contains(document.getElementById(id)),id);
  assert.deepEqual([...document.querySelector('.desktop-dataset-transfers').children].map(node=>node.id),['dataset-name','dataset-save','dataset-delete','csv-open','csv-save']);
  for(const id of ['statistics-summary','statistics-analysis','statistics-models','statistics-tests','statistics-advanced','statistics-summary-result','statistics-error','statistics-collapse-all'])assert.ok(document.getElementById('desktop-statistics-output').contains(document.getElementById(id)),id);
  const ids=[...document.querySelectorAll('[id]')].map(node=>node.id);assert.equal(new Set(ids).size,ids.length);
});

test('dragging clamps both panes, persists independent ratios and restores them',context=>{
  const app=setup(context),{dom,splitter,pointer}=app;
  pointer(splitter('graph'),'pointerdown',450);
  pointer(dom.window,'pointermove',700,8);assert.equal(splitter('graph').getAttribute('aria-valuenow'),'36','other pointer ignored');
  pointer(dom.window,'pointermove',-200);
  assert.equal(splitter('graph').getAttribute('aria-valuenow'),'28');
  pointer(dom.window,'pointermove',2000);
  assert.equal(splitter('graph').getAttribute('aria-valuenow'),'68');
  pointer(dom.window,'pointerup',2000);
  assert.equal(dom.window.document.documentElement.classList.contains('desktop-resizing'),false);
  assert.equal(app.saved().statistics,.5);
  const graph=app.saved().graph;
  app.keyboard('statistics','ArrowLeft',true);
  assert.equal(app.saved().statistics,.4);assert.equal(app.saved().graph,graph);
  const restored=setup(context,app.saved());
  assert.equal(restored.splitter('graph').getAttribute('aria-valuenow'),'68');
  assert.equal(restored.splitter('statistics').getAttribute('aria-valuenow'),'40');
});

test('keyboard and double-click reset; resize clamps visually without erasing the saved preference',context=>{
  const app=setup(context),separator=app.splitter('statistics');
  app.keyboard('statistics','ArrowRight');assert.equal(separator.getAttribute('aria-valuenow'),'52');
  app.keyboard('statistics','Home');assert.equal(separator.getAttribute('aria-valuenow'),'30');
  app.keyboard('statistics','End');assert.equal(separator.getAttribute('aria-valuenow'),'68');
  const preferred=app.saved().statistics;
  app.setWidth(700);assert.equal(separator.getAttribute('aria-valuenow'),'53');
  assert.equal(app.saved().statistics,preferred);
  app.setWidth(1000);assert.equal(separator.getAttribute('aria-valuenow'),'68');
  app.keyboard('statistics','Enter');assert.equal(separator.getAttribute('aria-valuenow'),'50');
  app.keyboard('graph','ArrowLeft');assert.equal(app.splitter('graph').getAttribute('aria-valuenow'),'34');
  app.splitter('graph').dispatchEvent(new app.dom.window.MouseEvent('dblclick'));
  assert.equal(app.saved().graph,.36);
});

test('sidebar preference and accessible labels survive locale changes and reload',async context=>{
  const app=setup(context),button=app.document.getElementById('desktop-sidebar-toggle');
  assert.equal(button.getAttribute('aria-expanded'),'true');button.click();
  assert.equal(app.document.getElementById('workspace-navigation').hidden,true);
  assert.equal(button.getAttribute('aria-expanded'),'false');
  app.document.documentElement.lang='ko';await new Promise(resolve=>setImmediate(resolve));
  assert.equal(button.getAttribute('aria-label'),'사이드바 펼치기');
  assert.equal(app.document.getElementById('desktop-statistics-input').getAttribute('aria-label'),'데이터셋');
  const restored=setup(context,app.saved());
  assert.equal(restored.document.documentElement.dataset.desktopSidebar,'collapsed');
  restored.document.getElementById('desktop-sidebar-toggle').click();
  assert.equal(restored.document.getElementById('workspace-navigation').hidden,false);
});

test('malformed or unavailable storage leaves all layout controls usable',context=>{
  for(const saved of ['{bad', {graph:'NaN',statistics:null,collapsed:'true'}]){
    const app=setup(context,saved);
    assert.equal(app.splitter('graph').getAttribute('aria-valuenow'),'36');
    assert.equal(app.splitter('statistics').getAttribute('aria-valuenow'),'50');
  }
  const app=setup(context,undefined,{getItem(){throw Error('unavailable');},setItem(){throw Error('unavailable');}});
  app.document.getElementById('desktop-sidebar-toggle').click();app.keyboard('graph','ArrowRight');
  assert.equal(app.splitter('graph').getAttribute('aria-valuenow'),'38');
});

test('resizing refreshes the statistics gutter and virtual table for the new viewport',context=>{
  const app=setup(context);let gutters=0,rows=0;
  app.document.getElementById('statistics-data').addEventListener('scroll',()=>gutters++);
  const table=app.document.createElement('table');table.refreshEditableTable=()=>rows++;
  app.document.getElementById('statistics-grid').append(table);
  app.setWidth(1200);assert.equal(gutters,1);assert.equal(rows,1);
  app.layout.dispose();app.setWidth(1400);assert.equal(gutters,1);assert.equal(rows,1);
});

test('statistics dragging continues while its editor observes the changing width',context=>{
  const app=setup(context),separator=app.splitter('statistics');
  const observer=app.resizeObservers.find(observer=>observer.targets.includes(app.document.getElementById('statistics-editor')));
  app.pointer(separator,'pointerdown',600);
  app.pointer(app.dom.window,'pointermove',650);observer.callback();
  assert.equal(app.document.documentElement.classList.contains('desktop-resizing'),true);
  app.pointer(app.dom.window,'pointermove',700);observer.callback();
  assert.equal(separator.getAttribute('aria-valuenow'),'60');
  app.pointer(app.dom.window,'pointerup',700);
  assert.equal(Math.round(app.saved().statistics*100),60);
});

test('calculator tabs and collapsing preserve the calculator DOM and saved selection',async context=>{
  const app=setup(context),get=id=>app.document.getElementById(id);
  const display=get('calculator-display'),keypad=app.document.querySelector('.keypad-workspace');
  assert.equal(display.parentElement.tagName,'MAIN');assert.equal(keypad.parentElement,display.parentElement);
  assert.equal(display.parentElement.parentElement.id,'desktop-workspace-shell');
  assert.equal(get('desktop-tab-history').getAttribute('aria-selected'),'true');
  get('desktop-tab-functions').click();assert.equal(get('desktop-panel-history').hidden,true);
  assert.equal(get('desktop-panel-functions').hidden,false);
  get('desktop-calculator-close').focus();get('desktop-calculator-close').click();
  assert.equal(get('desktop-calculator-panel').hidden,true);
  assert.equal(app.document.activeElement,get('desktop-calculator-toggle'));
  assert.equal(app.saved().calculatorTab,'functions');assert.equal(app.saved().calculatorCollapsed,true);
  const restored=setup(context,app.saved()),restoredGet=id=>restored.document.getElementById(id);
  restoredGet('desktop-calculator-toggle').click();
  assert.equal(restoredGet('desktop-calculator-panel').hidden,false);
  assert.equal(restoredGet('desktop-tab-functions').getAttribute('aria-selected'),'true');
  const event=new restored.dom.window.KeyboardEvent('keydown',{key:'ArrowLeft',bubbles:true,cancelable:true});
  restoredGet('desktop-tab-functions').dispatchEvent(event);
  assert.equal(event.defaultPrevented,true);assert.equal(restored.document.activeElement,restoredGet('desktop-tab-history'));
  restored.document.documentElement.lang='ko';await new Promise(resolve=>setImmediate(resolve));
  assert.equal(restoredGet('desktop-tab-functions').textContent,'함수');
});
