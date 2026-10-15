import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {JSDOM} from 'jsdom';
import {createAppState,createPersistence,restoreFields,restoreSelect} from '../app-state.js';
import {createWorkspaces} from '../workspaces.js';
import {createGraphWorkspace} from '../graph-workspace.js';
import {createCalculator} from '../calculator.js';
import {createAppDialogs} from '../app-dialogs.js';
import {setLanguage} from '../i18n.js';
import {setComputationLimitsRemoved} from '../computation-limits.js';

// Exercise production workspace construction against the real page HTML.
// This runs in a DOM emulator, not in the user's browser or a browser automation tool.
const html=readFileSync(new URL('../index.html',import.meta.url),'utf8');
function fixture(context,saved={},engine={ready:false},usePersistence=false){
  const dom=new JSDOM(html,{url:'http://localhost:8080/',pretendToBeVisual:true}),window=dom.window;
  const globals={window,document:window.document,navigator:window.navigator,localStorage:window.localStorage,Event:window.Event,NodeFilter:window.NodeFilter,
    getComputedStyle:window.getComputedStyle.bind(window),requestAnimationFrame:window.requestAnimationFrame.bind(window),cancelAnimationFrame:window.cancelAnimationFrame.bind(window)};
  const descriptors=Object.fromEntries(Object.keys(globals).map(key=>[key,Object.getOwnPropertyDescriptor(globalThis,key)]));
  for(const [key,value] of Object.entries(globals))Object.defineProperty(globalThis,key,{configurable:true,writable:true,value});
  context.after(()=>{dom.window.close();for(const key of Object.keys(globals)){if(descriptors[key])Object.defineProperty(globalThis,key,descriptors[key]);else delete globalThis[key];}setComputationLimitsRemoved(false);});
  window.HTMLElement.prototype.scrollIntoView=()=>{};
  const state=createAppState(saved);setLanguage(state.language);setComputationLimitsRemoved(state.removeComputationLimit);restoreFields(state);
  const noop=()=>{},errors=[];
  const persistence=usePersistence?createPersistence({state,snapshot:()=>({expression:'',graph:{}}),onPersist:noop,toast:noop}):null;
  context.after(()=>persistence?.dispose());
  const workspaces=createWorkspaces({state,engine,ui:{toast:noop,pickFile:noop,openDialog:noop,clipboard:noop},persist:persistence?.persist||noop,
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

test('calculator, graph and equation production inputs convert pasted LaTeX immediately',async context=>{
  let graphs,calculator;context.after(()=>{calculator?.dispose();graphs?.dispose();});
  const {window,state,errors}=fixture(context),document=window.document,noop=()=>{};
  graphs=createGraphWorkspace({execute:async()=>({ok:true}),options:()=>({displayDigits:10,angle:'RAD'}),onError:message=>errors.push(message),persist:noop,isBusy:()=>false,isReady:()=>false});
  const copies=[],ui={toast:message=>errors.push(message),openDialog:noop,clipboard:text=>copies.push(text),pickFile:noop};
  calculator=createCalculator({state,engine:{ready:false},isBusy:()=>false,ui,persist:noop,schedulePersist:noop,requestOptions:()=>({displayDigits:10}),error:message=>errors.push(message),changeMode:noop,updateButtons:noop,pressKey:noop,modeDialog:noop,variablesDialog:noop,matrixInsertDialog:noop,graphs});
  function paste(field,text){const event=new window.Event('paste',{bubbles:true,cancelable:true});Object.defineProperty(event,'clipboardData',{value:{getData:()=>text}});field.dispatchEvent(event);assert.equal(event.defaultPrevented,true);}
  const expression=document.getElementById('expression');expression.value='2x+3';expression.setSelectionRange(1,2);
  paste(expression,'$\\frac{1}{5}$');assert.equal(expression.value,'2(1/5)+3');assert.equal(expression.selectionStart,6);
  const graph=document.getElementById('graph-source');graph.select();
  paste(graph,'$\\sqrt{x}$\n\\frac{x+1}{2}');assert.equal(graph.value,'sqrt(x)\n(x+1)/2');assert.equal(document.getElementById('graph-line-numbers').children.length,2);
  assert.equal(graphs.snapshot().sources.cartesian,graph.value);
  const equation=document.getElementById('equation-source');equation.select();
  paste(equation,'x=\\frac{1}{2}\ny=\\sqrt{2}');assert.equal(equation.value,'x=1/2\ny=sqrt(2)');assert.equal(equation.selectionStart,equation.value.length);
  const coefficient=document.getElementById('equation-a');coefficient.select();paste(coefficient,'\\sqrt{2}');assert.equal(coefficient.value,'sqrt(2)');
  window.matchMedia=()=>({matches:false,addEventListener:noop,removeEventListener:noop});
  createAppDialogs({state,ui,persist:noop,calculator,changeMode:noop,pressKey:noop,refreshDisplays:noop,renderMatrix:noop,error:noop,reloadState:noop});
  document.getElementById('settings-dialog').showModal=()=>{};
  document.getElementById('settings-button').click();
  const option=document.querySelector('[data-setting="copyAsLatex"]');assert.equal(option.type,'checkbox');assert.equal(option.checked,false);
  expression.value='1/2';expression.select();document.getElementById('copy').click();assert.equal(copies.pop(),'1/2');
  option.checked=true;option.dispatchEvent(new window.Event('change'));assert.equal(state.copyAsLatex,true);
  document.getElementById('copy').click();assert.equal(copies.pop(),'\\frac{1}{2}');
  const fraction={kind:'fraction',args:[{kind:'number',value:'1'},{kind:'number',value:'2'}]};
  calculator.showResult({ok:true,exact:'1/2',decimal:'0.5',tree:fraction,decimalTree:{kind:'number',value:'0.5'}},'1/2');
  document.getElementById('answer-copy').click();assert.equal(copies.pop(),'\\frac{1}{2}');
  option.checked=false;option.dispatchEvent(new window.Event('change'));document.getElementById('answer-copy').click();assert.equal(copies.pop(),'1/2');
  await new Promise(resolve=>setTimeout(resolve,0));
  assert.deepEqual(errors,[]);
});

function graphFixture(context,{source='a*x',execute,saved={},displayDigits=3}={}){
  const {window,errors}=fixture(context),get=id=>window.document.getElementById(id);
  // Exercise the real DOM and controllers; drawing pixels is outside this DOM test.
  window.HTMLCanvasElement.prototype.getContext=()=>null;
  get('graph-source').value=source;
  const requests=[];
  const graphs=createGraphWorkspace({
    execute:async request=>{requests.push(request);return execute?execute(request):{ok:true,parameters:['a'],curves:[[[-1,-1],[0,0],[1,1]]]};},
    options:()=>({displayDigits,angle:'RAD'}),onError:message=>errors.push(message),persist:()=>{},isBusy:()=>false,saved,
  });
  context.after(()=>graphs.dispose());
  return {window,get,graphs,requests,errors};
}


test('graph discards an analysis response after its source changes',async context=>{
  let complete;
  const {get,graphs,errors}=graphFixture(context,{source:'x',execute:request=>request.action==='graphAnalysis'?
    new Promise(resolve=>{complete=resolve;}):{ok:true,parameters:[],curves:[[[-1,-1],[0,0],[1,1]]]}});
  await graphs.run();
  const analysis=get('graph-analysis-run').onclick();
  get('graph-source').value='x+1';get('graph-source').oninput();
  complete({ok:true,analysis:'root',points:[[0,0]],count:1});
  await analysis;
  assert.equal(get('graph-analysis-result').children.length,0);
  assert.equal(graphs.snapshot().sources.cartesian,'x+1');
  assert.deepEqual(errors,[]);
});

test('graph ignores an obsolete sampling response and runs the current source',async context=>{
  let complete,calls=0;
  const {get,graphs,requests,errors}=graphFixture(context,{source:'x',execute:()=>++calls===1?
    new Promise(resolve=>{complete=resolve;}):{ok:true,parameters:[],curves:[[[-1,0],[0,1],[1,2]]]}});
  const previous=graphs.run();
  get('graph-source').value='x+1';get('graph-source').oninput();
  complete({ok:false,error:'Obsolete request'});
  await previous;
  assert.deepEqual(errors,[]);
  await graphs.run();
  assert.equal(requests.length,2);
  assert.equal(requests.at(-1).trees[0].value,'+');
  assert.equal(get('graph-table').querySelectorAll('tbody tr').length,3);
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
