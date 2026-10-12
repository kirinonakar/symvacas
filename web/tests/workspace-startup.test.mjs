import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {JSDOM} from 'jsdom';
import {createAppState,restoreFields,restoreSelect} from '../app-state.js';
import {createWorkspaces} from '../workspaces.js';
import {setLanguage} from '../i18n.js';
import {setComputationLimitsRemoved} from '../computation-limits.js';

// Exercise production workspace construction against the real page HTML.
// This runs in a DOM emulator, not in the user's browser or a browser automation tool.
const html=readFileSync(new URL('../index.html',import.meta.url),'utf8');
function fixture(context,saved={}){
  const dom=new JSDOM(html,{url:'http://localhost:8080/',pretendToBeVisual:true}),window=dom.window;
  const globals={window,document:window.document,navigator:window.navigator,localStorage:window.localStorage,Event:window.Event,
    getComputedStyle:window.getComputedStyle.bind(window),requestAnimationFrame:window.requestAnimationFrame.bind(window),cancelAnimationFrame:window.cancelAnimationFrame.bind(window)};
  const descriptors=Object.fromEntries(Object.keys(globals).map(key=>[key,Object.getOwnPropertyDescriptor(globalThis,key)]));
  for(const [key,value] of Object.entries(globals))Object.defineProperty(globalThis,key,{configurable:true,writable:true,value});
  context.after(()=>{dom.window.close();for(const key of Object.keys(globals)){if(descriptors[key])Object.defineProperty(globalThis,key,descriptors[key]);else delete globalThis[key];}setComputationLimitsRemoved(false);});
  window.HTMLElement.prototype.scrollIntoView=()=>{};
  const state=createAppState(saved);setLanguage(state.language);setComputationLimitsRemoved(state.removeComputationLimit);restoreFields(state);
  const noop=()=>{},errors=[];
  const workspaces=createWorkspaces({state,engine:{ready:false},ui:{toast:noop,pickFile:noop,openDialog:noop,clipboard:noop},persist:noop,
    restoreSelect:id=>restoreSelect(state,id),requestOptions:()=>({}),isBusy:()=>false,error:message=>errors.push(message),changeMode:noop,replaceInput:noop,insert:noop,evaluate:noop,showResult:noop,showStatisticsResult:noop,clearResult:noop,
    graphs:{render:noop,run:noop}});
  workspaces.initialize();
  return {window,state,workspaces,errors};
}

test('fresh page constructs and initializes every workspace without a cached dataset',context=>{
  const {window,workspaces,errors}=fixture(context);
  assert.equal(typeof workspaces.runStatisticsModelWorkflow,'function');
  assert.ok(window.document.getElementById('statistics-models-kind').options.length);
  assert.ok(window.document.getElementById('probability-category').options.length);
  assert.deepEqual(errors,[]);
});

test('saved guided statistics menu is restored after its handlers and caches initialize',context=>{
  const {window,errors}=fixture(context,{fields:{mode:'statistics','statistics-op':'mcnemar','statistics-data':'20,8\n2,15','statistics-kind':'xy'}});
  assert.equal(window.document.getElementById('statistics-general-kind').value,'mcnemar');
  assert.ok(window.document.getElementById('statistics-general-kind').onchange);
  assert.deepEqual(errors,[]);
});

test('nested comparison opens Model Comparison with Logistic and the current response and predictors',context=>{
  const {window,state,errors}=fixture(context,{fields:{mode:'statistics',
    'statistics-data':'event,age,marker\n0,20,2\n1,30,3\n0,40,4\n1,50,5',
    'statistics-kind':'xyz','regression-kind':'logistic','regression-response-choice':'0',
    'statistics-models-kind':'modelcompare','statistics-models-input':'example',
    'statistics-form-modelcompare-family':'cox','statistics-form-modelcompare-response-auto':true}});
  const get=id=>window.document.getElementById(id);
  assert.equal(get('regression-compare').hidden,false);
  get('statistics-models').open=false;get('regression-compare').click();
  assert.equal(get('statistics-models-kind').value,'modelcompare');
  assert.equal(get('statistics-form-modelcompare-family').value,'logistic');
  assert.equal(get('statistics-models-input').value,'current');
  assert.equal(get('statistics-models').open,true);
  assert.equal(get('statistics-form-modelcompare-response').value,'0');
  assert.equal(get('statistics-form-modelcompare-basePredictors').value,'1');
  assert.equal(get('statistics-form-modelcompare-addedPredictors').value,'2');
  assert.equal(state.fields['statistics-form-modelcompare-response-auto'],false);
  // Re-entering from another comparison family must restore Logistic every time.
  const family=get('statistics-form-modelcompare-family');family.value='linear';family.onchange();
  get('regression-compare').click();
  assert.equal(get('statistics-form-modelcompare-family').value,'logistic');
  assert.deepEqual(errors,[]);
});

test('saved large dataset starts and table editor mounts a bounded number of cells',context=>{
  const data='age,MRI,event\n'+Array.from({length:4000},(_,i)=>`${20+i%50},${i%2},${i%2}`).join('\n');
  const {window,workspaces,errors}=fixture(context,{fields:{mode:'statistics','statistics-data':data,'statistics-kind':'columns','statistics-columns':'3','regression-kind':'logistic'}});
  const document=window.document;
  document.getElementById('statistics-table-toggle').click();
  assert.deepEqual(errors,[]);
  assert.ok(document.querySelectorAll('#statistics-grid input').length>0);
  assert.ok(document.querySelectorAll('#statistics-grid input').length<120);
  assert.ok(document.getElementById('statistics-line-numbers').childElementCount<30);
  workspaces.render();
  assert.equal(document.getElementById('statistics-data').value,data);
  assert.deepEqual(errors,[]);
});

test('row filter saves a separate dataset only after a current nonempty preview',context=>{
  const original='ID,age,group\n"A,B",18,남성\nC,17,여성\nD,40,여성\nE,,여성';
  const {window,state,workspaces,errors}=fixture(context,{datasets:{D1:original,D3:'1\n2'},datasetKinds:{D1:'xyz',D3:'list'},fields:{mode:'statistics','dataset-name':'D1','dataset-list':'D1','statistics-data':original,'statistics-kind':'xyz'}});
  const document=window.document,get=id=>document.getElementById(id),key='statistics-preparation-filter-conditions';
  const edit=(id,value)=>{const node=get(id);node.value=value;node.dispatchEvent(new window.Event('input',{bubbles:true}));return node;};
  const panel=get('statistics-preparation-tool-filter'),[preview,save]=panel.lastElementChild.children;
  assert.equal(save.disabled,true);save.click();assert.deepEqual(Object.keys(state.datasets),['D1','D3']);
  edit(`${key}-0-column`,'1');edit(`${key}-0-operator`,'gte');
  const input=edit(`${key}-0-value`,'18');input.focus();input.setSelectionRange(1,1);edit(`${key}-0-value`,'19');
  assert.equal(get(`${key}-0-value`),input);assert.equal(document.activeElement,input,'typing retains the focused filter input');
  get(`${key}-add`).click();edit(`${key}-1-column`,'2');edit(`${key}-1-operator`,'textEquals');edit(`${key}-1-value`,'여성');
  preview.click();assert.equal(save.disabled,false);assert.equal(get('statistics-data').value,original);assert.equal(state.datasets.D1,original);
  edit(`${key}-0-value`,'100');assert.equal(save.disabled,true);save.click();assert.equal(state.datasets.D4,undefined);
  preview.click();assert.equal(save.disabled,true);assert.ok(panel.textContent.includes('No rows match the filter'));
  edit(`${key}-0-value`,'18');preview.click();save.click();
  assert.equal(state.datasets.D1,original);assert.equal(state.datasets.D3,'1\n2');
  assert.equal(state.datasets.D4,'ID,age,group\nD,40,여성');assert.equal(state.datasetKinds.D4,'xyz');
  assert.equal(get('dataset-name').value,'D4');assert.equal(get('dataset-list').value,'D4');assert.equal(get('statistics-data').value,state.datasets.D4);
  assert.equal(save.disabled,true);save.click();assert.equal(state.datasets.D5,undefined);
  const persisted=createAppState(JSON.parse(JSON.stringify(state)));assert.equal(persisted.datasets.D4,state.datasets.D4);assert.equal(persisted.datasets.D1,original);
  workspaces.render();get('dataset-list').value='D1';get('dataset-list').dispatchEvent(new window.Event('change'));assert.equal(get('statistics-data').value,original);
  // Removing a condition changes the structure; OR allows either numeric or text matches.
  get('statistics-preparation-filter-match').value='any';get('statistics-preparation-filter-match').dispatchEvent(new window.Event('input'));
  preview.click();edit('statistics-preparation-filter-datasetName','D1');assert.equal(save.disabled,false);save.click();
  assert.ok(panel.textContent.includes('Dataset name already exists'));assert.equal(state.datasets.D1,original);assert.equal(save.disabled,false);
  edit('statistics-preparation-filter-datasetName','1invalid');save.click();assert.equal(state.datasets['1invalid'],undefined);assert.equal(save.disabled,false);
  edit('statistics-preparation-filter-datasetName',' Cohort_18 ');save.click();assert.equal(state.datasets.Cohort_18,original);
  assert.equal(get('dataset-name').value,'Cohort_18');assert.equal(get('dataset-list').value,'Cohort_18');assert.equal(state.datasets.D5,undefined);
  assert.equal(createAppState(JSON.parse(JSON.stringify(state))).datasets.Cohort_18,original);
  const remove=get('statistics-preparation-tool-filter').querySelector('fieldset button');remove.click();
  assert.equal(JSON.parse(state.fields[key]).length,1);assert.equal(save.disabled,true);
  assert.deepEqual(errors,[]);
});
