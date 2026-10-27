import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {JSDOM} from 'jsdom';
import {createWorkspaceNavigation} from '../workspace-navigation.js';
import {setLanguage,translateDOM} from '../i18n.js';

const html=readFileSync(new URL('../index.html',import.meta.url),'utf8');
function fixture(context) {
  const dom=new JSDOM(html),{window}=dom;
  const previous=Object.fromEntries(['document','NodeFilter'].map(name=>[name,Object.getOwnPropertyDescriptor(globalThis,name)]));
  for(const name of ['document','NodeFilter'])Object.defineProperty(globalThis,name,{configurable:true,value:window[name]});
  context.after(()=>{
    dom.window.close();setLanguage('en');
    for(const name of ['document','NodeFilter']) {
      if(previous[name])Object.defineProperty(globalThis,name,previous[name]);
      else delete globalThis[name];
    }
  });
  setLanguage('en');
  const modes=[],scrolls=[];
  window.HTMLElement.prototype.scrollIntoView=function(options){scrolls.push({id:this.id,options});};
  let navigation;
  const changeMode=mode=>{
    modes.push(mode);
    window.document.getElementById('mode').value=mode;
    window.document.querySelectorAll('[data-mode]').forEach(section=>section.hidden=!section.dataset.mode.split(' ').includes(mode));
    navigation.update(mode);
  };
  navigation=createWorkspaceNavigation({changeMode});
  return {document:window.document,navigation,changeMode,modes,scrolls};
}

test('every existing workspace is available and selection follows both navigation paths',context=>{
  const {document,navigation,changeMode,modes}=fixture(context);
  const buttons=[...document.querySelectorAll('[data-workspace-target]')];
  assert.deepEqual(buttons.map(button=>button.dataset.workspaceTarget),[...document.getElementById('mode').options].map(option=>option.value));
  assert.equal(document.querySelector('[aria-current="page"]').dataset.workspaceTarget,'scientific');
  for(const button of buttons) {
    button.click();
    assert.equal(modes.at(-1),button.dataset.workspaceTarget);
    assert.equal(document.getElementById('mode').value,button.dataset.workspaceTarget);
    assert.deepEqual([...document.querySelectorAll('[aria-current="page"]')],[button]);
  }
  changeMode('graph');navigation.update('graph');
  assert.equal(document.querySelector('[aria-current="page"]').dataset.workspaceTarget,'graph');
});

test('statistics shortcuts switch workspace, reopen each section, scroll and focus its heading',context=>{
  const {document,changeMode,scrolls}=fixture(context);
  const shortcuts=[...document.querySelectorAll('.workspace-navigation-section')];
  assert.deepEqual(shortcuts.map(button=>button.getAttribute('aria-controls')),[
    'statistics-summary','statistics-visualize','statistics-regression','statistics-models','statistics-analysis','statistics-tests','statistics-advanced'
  ]);
  const statisticsItem=document.querySelector('[data-workspace-target="statistics"]').parentElement;
  assert.ok(shortcuts.every(button=>statisticsItem.contains(button)));
  for(const button of shortcuts) {
    changeMode('graph');
    const section=document.getElementById(button.getAttribute('aria-controls'));
    for(let parent=section;parent;parent=parent.parentElement) {
      if(parent.tagName==='DETAILS')parent.open=false;
    }
    button.click();
    assert.equal(document.getElementById('mode').value,'statistics');
    assert.equal(section.closest('.workspace').hidden,false);
    assert.equal(section.open,true);
    for(let parent=section.parentElement;parent;parent=parent.parentElement) {
      if(parent.tagName==='DETAILS')assert.equal(parent.open,true,'containing sections also reopen for nested shortcuts');
    }
    assert.deepEqual(scrolls.at(-1),{id:section.id,options:{block:'start'}});
    assert.equal(document.activeElement,section.querySelector(':scope > summary'));
    assert.deepEqual([...document.querySelectorAll('[aria-current="location"]')],[button]);
  }
  const instrument=document.querySelector('.instrument');
  instrument.scrollIntoView=options=>scrolls.push({id:'instrument',options});
  const data=document.getElementById('statistics-data').value;
  document.querySelector('[data-workspace-target="statistics"]').click();
  assert.deepEqual(scrolls.at(-1),{id:'instrument',options:{block:'start'}},'clicking the active statistics mode returns to the page start');
  assert.equal(document.querySelector('[aria-current="location"]'),null,'clear the previous section selection');
  assert.equal(document.getElementById('statistics-data').value,data);
  assert.equal(document.getElementById('statistics-advanced').open,true,'returning to the top preserves expanded analyses');
  changeMode('python');
  assert.equal(document.querySelector('[aria-current="location"]'),null);
  assert.equal(document.querySelectorAll('.workspace-navigation-section').length,7,'shortcuts remain available in other workspaces');
});

test('sidebar mode and section labels follow language changes without losing their actions',context=>{
  const {document,modes}=fixture(context);
  const advanced=document.querySelector('[aria-controls="statistics-advanced"]');
  const graph=document.querySelector('[data-workspace-target="graph"]');
  assert.equal(advanced.textContent,'Advanced analysis');
  setLanguage('ko');translateDOM();
  assert.equal(advanced.textContent,'고급 분석');
  assert.equal(graph.textContent,'그래프');
  advanced.click();assert.equal(modes.at(-1),'statistics');
  setLanguage('en');translateDOM();
  assert.equal(advanced.textContent,'Advanced analysis');
  assert.equal(graph.textContent,'Graph');
});
