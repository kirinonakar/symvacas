import test from 'node:test';
import assert from 'node:assert/strict';
import {createWorkspaceLayout} from '../workspace-layout.js';
import {layoutFixture} from './layout-fixture.mjs';

test('shared layout moves live graph controls and statistics results into separate panes',()=>{
  const f=layoutFixture(),source=f.find('graph-source'),summary=f.find('statistics-summary');
  const layout=createWorkspaceLayout(f.doc);
  assert.equal(source.parentElement,f.find('desktop-graph-input'));assert.equal(source.value,'sin(x)');
  assert.equal(f.find('graph-parameter-actions').parentElement,f.find('desktop-graph-input'));
  assert.equal(f.find('graph-formulas').parentElement,f.find('desktop-graph-output'));
  assert.equal(f.find('graph-analysis-sliders').parentElement,f.find('desktop-graph-output'));
  f.find('graph-analysis').open=false;f.mutate(f.find('graph-analysis'));assert.equal(f.find('graph-analysis-sliders').hidden,true);
  assert.equal(summary.parentElement,f.find('desktop-statistics-results'));
  assert.equal(f.find('statistics-collapse-all').parentElement,f.find('desktop-statistics-actions'));
  assert.equal(f.find('statistics-editor').parentElement,f.find('desktop-statistics-input'));
  layout.dispose();
});

test('splitters clamp widths, support keyboard reset, and persist their ratios',()=>{
  const f=layoutFixture({saved:{graph:.99,collapsed:true}}),layout=createWorkspaceLayout(f.doc);
  assert.equal(f.find('workspace-navigation').hidden,true);
  const pane=f.find('desktop-graph-input').parentElement,splitter=pane.children[1];
  assert.equal(splitter.getAttribute('aria-valuenow'),'73');
  const key=key=>splitter.dispatchEvent({type:'keydown',key,preventDefault(){}});
  key('Home');assert.equal(splitter.getAttribute('aria-valuenow'),'24');
  key('Enter');assert.equal(splitter.getAttribute('aria-valuenow'),'36');
  assert.equal(JSON.parse(f.storage.get('symvacas.desktop-layout.v1')).graph,.36);
  layout.dispose();
});

test('calculator tabs mount once, switch inline on wide screens, and retain compact dialogs',()=>{
  const f=layoutFixture(),mounted=[],disposed=[];let dialogs=0;
  f.find('history-button').onclick=()=>dialogs++;
  const layout=createWorkspaceLayout(f.doc,undefined,(target,kind)=>{mounted.push(kind);return ()=>disposed.push(kind);});
  assert.deepEqual(mounted,['history','functions']);
  assert.equal(f.find('desktop-calculator-panel').hidden,false);
  f.find('catalog-button').onclick();assert.equal(f.find('desktop-tab-functions').getAttribute('aria-selected'),'true');
  f.find('desktop-panel-functions').focus();f.find('desktop-calculator-close').onclick();
  assert.equal(f.find('desktop-calculator-panel').hidden,true);assert.equal(f.doc.activeElement,f.find('desktop-calculator-toggle'));
  f.find('history-button').onclick();assert.equal(dialogs,0);assert.equal(f.find('desktop-panel-history').hidden,false);
  f.view.innerWidth=600;f.find('history-button').onclick();assert.equal(dialogs,1);
  f.view.innerWidth=1200;f.root.dataset.workspace='graph';f.find('history-button').onclick();assert.equal(dialogs,2);
  f.root.lang='ko';f.mutate(f.root);assert.equal(f.find('desktop-tab-functions').textContent,'함수');
  assert.deepEqual(mounted,['history','functions']);layout.dispose();assert.deepEqual(disposed,['history','functions']);
});

for(const width of [320,600,899,900,1200])test(`graph section order follows the ${width}px layout without replacing controls`,()=>{
  const f=layoutFixture({width,mode:'graph'}),ranges=f.find('graph-ranges'),analysis=f.find('graph-analysis');
  const layout=createWorkspaceLayout(f.doc),input=f.find('desktop-graph-input'),output=f.find('desktop-graph-output');
  const check=compact=>{
    const pane=compact?output:input;
    const sections=['graph-ranges','graph-surface-rendering','graph-analysis','graph-coordinates'].map(f.find);
    for(const section of sections)assert.equal(section.parentElement,pane);
    const positions=sections.map(section=>pane.children.indexOf(section));
    assert.deepEqual(positions,[...positions].sort((a,b)=>a-b));
    if(compact)assert.ok(output.children.indexOf(output.querySelector('.graph-plot-frame'))<positions[0]);
    assert.equal(f.find('graph-ranges'),ranges);assert.equal(ranges.open,true);
    assert.equal(f.find('graph-analysis'),analysis);assert.equal(analysis.open,true);
    assert.equal(f.find('graph-source').value,'sin(x)');
    assert.equal(f.find('graph-analysis-sliders').parentElement,output);
  };
  check(width<900);
  for(const next of [1200,320,900,899]){f.view.innerWidth=next;f.view.dispatchEvent({type:'resize'});check(next<900);}
  layout.dispose();
});

test('statistics collapse action stays in the runtime bar across mode and width changes',()=>{
  const f=layoutFixture({width:375,mode:'statistics'}),collapse=f.find('statistics-collapse-all');let clicks=0;
  collapse.onclick=()=>clicks++;
  const layout=createWorkspaceLayout(f.doc),actions=f.find('desktop-statistics-actions');
  const runtime=f.doc.querySelector('.runtime-bar');
  assert.equal(actions.parentElement,runtime);
  assert.equal(f.doc.querySelector('main').contains(collapse),false);
  assert.equal(actions.hidden,false);collapse.onclick();assert.equal(clicks,1);
  const transfers=f.find('dataset-name').parentElement;
  assert.equal(transfers.className,'desktop-dataset-transfers');
  assert.deepEqual(transfers.children.map(node=>node.id),['dataset-name','dataset-save','dataset-delete','csv-open','csv-save']);
  f.view.innerWidth=900;f.view.dispatchEvent({type:'resize'});
  assert.equal(actions.parentElement,runtime);
  f.view.innerWidth=899;f.view.dispatchEvent({type:'resize'});
  assert.equal(actions.parentElement,runtime);assert.equal(f.find('statistics-collapse-all'),collapse);
  f.root.dataset.workspace='graph';f.mutate(f.root);assert.equal(actions.hidden,true);
  f.root.dataset.workspace='statistics';f.mutate(f.root);assert.equal(actions.hidden,false);
  layout.dispose();
});
