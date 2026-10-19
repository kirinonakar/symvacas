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
import {parse} from '../parser.js';

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

test('failed calculator previews stay suppressed after engine recovery until input changes',async context=>{
  let calculator;context.after(()=>calculator?.dispose());
  const requests=[],noop=()=>{},engine={ready:true,execute:async(request,options)=>{
    requests.push({request,options});
    return options?.preview?{ok:false,error:'preview expired'}:{ok:true,exact:'2',decimal:'2',tree:{kind:'number',value:'2'}};
  }};
  const {window,state,errors}=fixture(context,{fields:{mode:'scientific',expression:'1+1'}},engine);
  calculator=createCalculator({state,engine,isBusy:()=>false,ui:{toast:noop,openDialog:noop,clipboard:noop},persist:noop,schedulePersist:noop,
    requestOptions:()=>({}),error:message=>errors.push(message),changeMode:noop,updateButtons:noop,pressKey:noop,modeDialog:noop,variablesDialog:noop,matrixInsertDialog:noop,graphs:{}});
  const settle=()=>new Promise(resolve=>setTimeout(resolve,150));
  calculator.schedulePreview();await settle();
  assert.equal(requests.length,1);assert.equal(requests[0].options.preview,true);
  calculator.resetPreview();await settle();
  assert.equal(requests.length,1,'a recovered engine does not retry unchanged failed input');
  await calculator.evaluate('1+1');
  assert.equal(requests.length,2);assert.equal(requests[1].options?.preview,undefined,'explicit calculation remains available');
  window.document.getElementById('expression').value='2+2';
  calculator.replaceInput('2+2',{uncommit:true});await settle();
  assert.equal(requests.length,3);assert.equal(requests[2].options.preview,true);
  assert.deepEqual(errors,[]);
});

test('SVM workspace restores task and kernel controls and updates dependent fields',context=>{
  const {window,errors}=fixture(context,{fields:{mode:'statistics','statistics-data':'y,a,b\n0,-1,7\n1,1,7',
    'statistics-kind':'columns','statistics-columns':'3','regression-kind':'svm','regression-svm-task':'classification',
    'regression-svm-kernel':'linear','regression-svm-c':'2','regression-response':'0','regression-response-auto':false,'regression-response-choice':'0'}});
  const get=id=>window.document.getElementById(id);
  assert.equal(get('regression-kind').value,'svm');
  assert.equal(get('regression-svm').hidden,false);
  assert.equal(get('regression-forest').hidden,true);
  assert.equal(get('regression-svm-gamma').closest('label').hidden,true);
  assert.equal(get('regression-svm-epsilon').closest('label').hidden,true);
  assert.equal(get('regression-response').value,'0');
  assert.equal(get('regression-svm-c').value,'2');
  get('regression-svm-kernel').value='rbf';get('regression-svm-kernel').dispatchEvent(new window.Event('change'));
  get('regression-svm-task').value='regression';get('regression-svm-task').dispatchEvent(new window.Event('change'));
  assert.equal(get('regression-svm-gamma').closest('label').hidden,false);
  assert.equal(get('regression-svm-epsilon').closest('label').hidden,false);
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
  expression.value='2x+3';expression.setSelectionRange(1,2);
  paste(expression,'\\boxed{x+1}');assert.equal(expression.value,'2(x+1)+3');assert.equal(expression.selectionStart,6);
  graph.select();paste(graph,'\\[\n\\boxed{r=|\\cos(3\\theta-t)|}\n\\]');assert.equal(graph.value,'r=abs(cos(3theta-t))');
  graph.select();paste(graph,'\\[\n(x^2+y^2)^4=\n\\left[\n(x^3-3xy^2)\\cos t+\n(3x^2y-y^3)\\sin t\n\\right]^2\n\\]');
  assert.equal(graph.value,'(x^2+y^2)^4=((x^3-3x*y^2)cos(t)+(3x^2y-y^3)sin(t))^2');
  assert.equal(document.getElementById('graph-line-numbers').children.length,1);
  equation.select();paste(equation,'\\boxed{xy=1}\n\\boxed{y=2}');assert.equal(equation.value,'x*y=1\ny=2');
  const escapedPolar=String.raw`\\[ \boxed{r=|\cos(3\theta-t)|} \\]`;
  const escapedImplicit=String.raw`\\[ (x^2+y^2)^4= \left[ (x^3-3xy^2)\cos t+ (3x^2y-y^3)\sin t \right]^2 \\]`;
  expression.select();paste(expression,escapedPolar);assert.equal(expression.value,'r=abs(cos(3theta-t))');
  const blockExpected='(x^2+y^2)^4=((x^3-3x*y^2)cos(t)+(3x^2y-y^3)sin(t))^2\nr=abs(cos(3theta-t))';
  for(const field of [graph,equation]){
    field.value='x=1\nold\ny=0';field.setSelectionRange(4,7);
    paste(field,escapedImplicit+'  '+escapedPolar);
    assert.equal(field.value,`x=1\n${blockExpected}\ny=0`);assert.equal(field.selectionStart,4+blockExpected.length);
  }
  assert.equal(document.getElementById('graph-line-numbers').children.length,4);
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

test('RCL saved statistics inserts dataset names and replaces empty catalog lists',async context=>{
  let calculator;context.after(()=>calculator?.dispose());
  const {window,state,errors}=fixture(context),document=window.document,noop=()=>{};
  const ui={toast:message=>errors.push(message),openDialog:(_title,content)=>document.getElementById('dialog').replaceChildren(content),clipboard:noop,pickFile:noop};
  const requests=[],engine={ready:false,execute:async request=>{requests.push(request);return {ok:true,exact:'6',decimal:'6',tree:{kind:'number',value:'6'}};}};
  calculator=createCalculator({state,engine,isBusy:()=>false,ui,persist:noop,schedulePersist:noop,requestOptions:()=>({}),error:message=>errors.push(message),changeMode:noop,updateButtons:noop,pressKey:noop,modeDialog:noop,variablesDialog:noop,matrixInsertDialog:noop,graphs:{}});
  window.matchMedia=()=>({matches:false,addEventListener:noop,removeEventListener:noop});
  document.getElementById('dialog').close=noop;
  const dialogs=createAppDialogs({state,ui,persist:noop,calculator,changeMode:noop,pressKey:noop,refreshDisplays:noop,renderMatrix:noop,error:message=>errors.push(message),reloadState:noop});
  Object.assign(state.datasets,{Sample:'1\n2\n3',Pairs:'1,2\n3,4',Triples:'1,2,3\n4,5,6'});
  Object.assign(state.datasetKinds,{Sample:'list',Pairs:'xy',Triples:'xyz'});
  const field=document.getElementById('expression');
  state.favorites=['sumdata([])'];
  document.getElementById('catalog-button').click();
  document.querySelector('#dialog [data-category="Favorites"]').click();
  [...document.querySelectorAll('#dialog .catalog-entry button')].find(button=>button.textContent==='sumdata([])').click();
  assert.equal(field.value,'sumdata([])');
  assert.equal(field.selectionStart,9);
  assert.equal(field.selectionEnd,9);
  function recall(marked,name='Sample',selection=null){
    const caret=marked.indexOf('|');field.value=marked.replace('|','');field.setSelectionRange(...(selection||[caret,caret]));
    dialogs.variables();
    [...document.querySelectorAll('#dialog button')].find(button=>button.textContent===name).click();
    return field.value;
  }
  for(const name of ['sumdata','mean','median','variance','stdev','mode','skewness','kurtosis','quartiles','stats']){
    assert.equal(recall(`${name}([|])`),`${name}(Sample)`);
    assert.equal(parse(field.value).args[0].value,'Sample');
  }
  assert.equal(recall('variance([|],0)'),'variance(Sample,0)');
  assert.equal(recall('correlation([4,5,6],[|])'),'correlation([4,5,6],Sample)');
  assert.equal(recall('mean([ | ])'),'mean(Sample)');
  assert.equal(recall('regression([|],linear)','Pairs'),'regression(Pairs,linear)');
  assert.equal(parse(field.value).args[0].value,'Pairs');
  assert.equal(recall('regression([|],multiple)','Triples'),'regression(Triples,multiple)');
  assert.equal(recall('mean(|)'),'mean(Sample)');
  assert.equal(recall('|'),'Sample');
  assert.equal(recall('mean([4,|])'),'mean([4,Sample])');
  assert.equal(recall('mean([])|','Sample',[5,7]),'mean(Sample)');
  calculator.showResult({ok:true,exact:'2',decimal:'2',tree:{kind:'number',value:'2'}},'mean(Sample)');
  assert.equal(recall('mean([|])'),'Sample');
  engine.ready=true;calculator.replaceInput('sumdata(Sample)',{uncommit:true});
  await calculator.evaluate();
  assert.equal(requests.at(-1).tree.args[0].value,'Sample');
  assert.deepEqual(requests.at(-1).statisticsDatasets,{Sample:['1','2','3']});
  state.datasets.Sample='4\n5';calculator.replaceInput('mean(Sample)',{uncommit:true});
  calculator.handleKey('CALC');
  await new Promise(resolve=>setTimeout(resolve,0));
  assert.equal(calculator.calcActive,false);
  assert.deepEqual(requests.at(-1).statisticsDatasets,{Sample:['4','5']});
  await new Promise(resolve=>setTimeout(resolve,0));
  assert.deepEqual(errors,[]);
});

test('graph converts input-based LaTeX paste before updating its rows and drafts',async context=>{
  const {window,get,graphs,errors}=graphFixture(context,{source:'x=1\n2x+3\ny=0'}),field=get('graph-source');
  function insert(text,{inputType='insertFromPaste',isComposing=false,data=text}={}){
    field.dispatchEvent(new window.InputEvent('beforeinput',{bubbles:true,inputType,data,isComposing}));
    field.setRangeText(text,field.selectionStart,field.selectionEnd,'end');
    field.dispatchEvent(new window.InputEvent('input',{bubbles:true,inputType,data,isComposing}));
  }
  field.setSelectionRange(5,6);
  insert('\\frac{1}{5}');
  assert.equal(field.value,'x=1\n2(1/5)+3\ny=0');
  assert.equal(field.selectionStart,10);
  assert.equal(graphs.snapshot().sources.cartesian,field.value);
  assert.equal(get('graph-line-numbers').children.length,3);
  field.select();
  insert('\\[x=1\\] \\[y=\\sqrt{2}\\]',{data:null});
  assert.equal(field.value,'x=1\ny=sqrt(2)');
  assert.equal(field.selectionStart,field.value.length);
  assert.equal(graphs.snapshot().sources.cartesian,field.value);
  assert.equal(get('graph-line-numbers').children.length,2);
  field.value='{x<0:x^2,0}';field.select();
  insert('\\frac{x}{2}',{data:null});
  assert.equal(field.value,'x/2');
  field.select();field.setRangeText('\\sqrt{x}',0,field.value.length,'end');
  field.dispatchEvent(new window.InputEvent('input',{bubbles:true,inputType:'insertText',data:'\\sqrt{x}'}));
  assert.equal(field.value,'sqrt(x)');
  assert.equal(graphs.snapshot().sources.cartesian,'sqrt(x)');
  field.select();insert('\\sqrt{x}',{inputType:'insertCompositionText',isComposing:true});
  assert.equal(field.value,'\\sqrt{x}');
  field.select();insert('x_value+TE');assert.equal(field.value,'x_value+TE');
  await new Promise(resolve=>setTimeout(resolve,0));
  assert.deepEqual(errors,[]);
});

test('calculator sends expressions to the selected graph category and preserves other drafts',async context=>{
  let graphs,calculator;context.after(()=>{calculator?.dispose();graphs?.dispose();});
  const {window,state,errors}=fixture(context),get=id=>window.document.getElementById(id),noop=()=>{},modes=[];
  graphs=createGraphWorkspace({execute:async()=>({ok:true}),options:()=>({displayDigits:10,angle:'RAD'}),onError:message=>errors.push(message),persist:noop,isBusy:()=>false,isReady:()=>false});
  calculator=createCalculator({state,engine:{ready:false},isBusy:()=>false,ui:{toast:message=>errors.push(message),openDialog:noop,clipboard:noop,pickFile:noop},persist:noop,schedulePersist:noop,requestOptions:()=>({displayDigits:10}),error:message=>errors.push(message),changeMode:mode=>modes.push(mode),updateButtons:noop,pressKey:noop,modeDialog:noop,variablesDialog:noop,matrixInsertDialog:noop,graphs});
  const cartesian=get('graph-source').value;
  for(const [kind,source,expected] of [['polar','r=2cos(3theta)','r=2cos(3theta)'],['parametric','(cos(t),sin(t))','(cos(t),sin(t))'],['space','(t,t^2,t^3)','(t,t^2,t^3)'],['surface','z=x^2+y^2','x^2+y^2'],['sequence','n^2','n^2'],['differential','t-y','t-y']]){
    get('graph-kind').value=kind;get('graph-kind').onchange();
    get('graph-source').value='';get('graph-source').oninput();
    calculator.replaceInput(source,{uncommit:true});calculator.handleKey('TO_GRAPH');
    assert.equal(get('graph-kind').value,kind);
    assert.equal(get('graph-source').value,expected);
    assert.equal(graphs.snapshot().sources.cartesian,cartesian);
    assert.equal(modes.at(-1),'graph');
  }
  get('graph-kind').value='polar';get('graph-kind').onchange();
  calculator.replaceInput('r=1+cos(theta)',{uncommit:true});calculator.handleKey('TO_GRAPH');
  assert.equal(get('graph-source').value,'r=2cos(3theta)\nr=1+cos(theta)');
  calculator.handleKey('TO_GRAPH');assert.equal(get('graph-source').value,'r=2cos(3theta)\nr=1+cos(theta)');
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

test('bare comma inequalities reach the graph worker as one selectable region',async context=>{
  const source='-1<x<1, -1<y<x';
  const {get,graphs,requests,errors}=graphFixture(context,{source:`${source}\ny=x`});
  await graphs.run();
  assert.equal(requests.length,1);
  assert.equal(requests[0].trees.length,2);
  assert.equal(requests[0].trees[0].args.length,2);
  assert.deepEqual(requests[0].shadings,[]);
  assert.equal(get('graph-formulas').children.length,2);
  assert.ok(get('graph-formulas').firstElementChild.querySelector('.graph-formula-eye'));
  assert.equal(get('graph-derivative').disabled,true);
  assert.deepEqual(errors,[]);
});

test('surface clipboard and keyboard paste convert aligned coordinates before source parsing',async context=>{
  const [body,expected]=readFileSync(new URL('../../math/src/test/resources/latex-input.tsv',import.meta.url),'utf8').split(/\r?\n/)
    .find(line=>line.startsWith(String.raw`\begin{aligned}r&=`)).split('\t');
  const source=`\\[\n${body.replaceAll(String.raw`\\`,'\\\\\n')}\n\\]`;
  const {window,get,graphs,requests,errors}=graphFixture(context);
  get('graph-kind').value='surface';get('graph-kind').onchange();
  const field=get('graph-source');field.value='z=0\nold\nz=1';field.setSelectionRange(4,7);
  const event=new window.Event('paste',{bubbles:true,cancelable:true});Object.defineProperty(event,'clipboardData',{value:{getData:()=>source}});
  field.dispatchEvent(event);
  assert.equal(event.defaultPrevented,true);assert.equal(field.value,`z=0\n${expected}\nz=1`);
  assert.equal(field.selectionStart,4+expected.length);assert.equal(get('graph-line-numbers').children.length,3);
  assert.equal(get('graph-u-ranges').hidden,false);assert.equal(get('graph-v-ranges').hidden,false);
  field.select();field.dispatchEvent(new window.InputEvent('beforeinput',{bubbles:true,inputType:'insertFromPaste',data:source}));
  field.value=source;field.setSelectionRange(source.length,source.length);
  field.dispatchEvent(new window.InputEvent('input',{bubbles:true,inputType:'insertFromPaste',data:source}));
  assert.equal(field.value,expected);assert.equal(get('graph-line-numbers').children.length,1);
  assert.equal(graphs.snapshot().sources.surface,expected);
  await graphs.run();assert.equal(requests.at(-1).trees.length,1);
  assert.equal(requests.at(-1).trees[0].args.length,4);assert.deepEqual(errors,[]);
});

test('surface height colors restore, persist and hide only the solid color picker',context=>{
  const {get,graphs,errors}=graphFixture(context,{saved:{surface:{colorMode:'rainbow'}}});
  get('graph-kind').value='surface';get('graph-kind').onchange();
  assert.equal(get('graph-surface-color-mode').value,'rainbow');
  assert.equal(get('graph-surface-color-mode-label').hidden,false);
  assert.equal(get('graph-surface-color').closest('label').hidden,true);
  assert.equal(graphs.snapshot().surface.colorMode,'rainbow');
  get('graph-surface-color-mode').value='solid';get('graph-surface-color-mode').onchange();
  assert.equal(get('graph-surface-color').closest('label').hidden,false);
  assert.equal(graphs.snapshot().surface.colorMode,'solid');
  get('graph-kind').value='space';get('graph-kind').onchange();
  assert.equal(get('graph-surface-color-mode-label').hidden,true);
  assert.deepEqual(errors,[]);
});

test('parametric surfaces send independent u/v ranges, preserve them and expose only t as a slider',async context=>{
  const source='[R=2+.35*sin(6*u-3*t),x=(R+cos(v))*cos(u),y=(R+cos(v))*sin(u),z=sin(v)]';
  const {get,graphs,requests,errors}=graphFixture(context,{saved:{sources:{surface:source},ranges:{'graph-u-min':-1,'graph-u-max':2,'graph-v-min':3,'graph-v-max':4}},
    execute:()=>({ok:true,parameters:['t'],surface:[[[0,0,0],[1,0,1]],[[0,1,1],[1,1,0]]],zMin:0,zMax:1,parametricSurface:true})});
  get('graph-kind').value='surface';get('graph-kind').onchange();
  assert.equal(get('graph-u-ranges').hidden,false);assert.equal(get('graph-v-ranges').hidden,false);
  assert.equal(get('graph-t-ranges').hidden,true);
  await graphs.run();
  assert.deepEqual(errors,[]);
  assert.deepEqual([requests.at(-1).surfaceUMin,requests.at(-1).surfaceUMax,requests.at(-1).surfaceVMin,requests.at(-1).surfaceVMax],[-1,2,3,4]);
  assert.deepEqual([...get('graph-parameters').querySelectorAll('[data-parameter]')].map(node=>node.dataset.parameter),['t']);
  get('graph-u-max').value='5';get('graph-u-max').onchange();await graphs.run();
  assert.equal(requests.at(-1).surfaceUMax,5);
  assert.equal(graphs.snapshot().ranges['graph-u-max'],5);
  get('graph-source').value='[r1=sqrt((x-2)^2+y^2),z=sin(r1-t)]';get('graph-source').oninput();
  assert.equal(get('graph-mixed-ranges').hidden,true);
  get('graph-source').value=source;get('graph-source').oninput();
  assert.equal(get('graph-u-ranges').hidden,false);
  assert.equal(graphs.snapshot().ranges['graph-u-max'],5);
});


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
