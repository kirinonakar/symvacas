import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {JSDOM} from 'jsdom';
import {createAppState,createPersistence,restoreFields,restoreSelect} from '../app-state.js';
import {createWorkspaces} from '../workspaces.js';
import {setLanguage} from '../i18n.js';
import {setComputationLimitsRemoved} from '../computation-limits.js';

// Exercise production workspace construction against the real page HTML.
// This runs in a DOM emulator, not in the user's browser or a browser automation tool.
const html=readFileSync(new URL('../index.html',import.meta.url),'utf8');
function fixture(context,saved={},engine={ready:false},usePersistence=false){
  const dom=new JSDOM(html,{url:'http://localhost:8080/',pretendToBeVisual:true}),window=dom.window;
  const globals={window,document:window.document,navigator:window.navigator,localStorage:window.localStorage,Event:window.Event,
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

test('raincloud menu restores grouping and orientation, redraws and persists orientation changes',context=>{
  const {window,state,workspaces,errors}=fixture(context,{fields:{mode:'statistics','statistics-kind':'xy','statistics-data':'group,value\nA,1\nA,2\nB,3','statistics-plot-type':'raincloud','statistics-plot-grouping':'first','statistics-plot-orientation':'vertical'}},{ready:false},true);
  const get=id=>window.document.getElementById(id);
  assert.equal(get('statistics-plot-type').value,'raincloud');assert.equal(get('statistics-plot-orientation-label').hidden,false);
  get('statistics-plot-run').click();
  assert.equal(get('statistics-plot').querySelector('svg').dataset.orientation,'vertical');
  assert.equal(get('statistics-plot').querySelectorAll('[data-raw-point]').length,3);
  get('statistics-plot-orientation').value='horizontal';get('statistics-plot-orientation').onchange();
  assert.equal(state.fields['statistics-plot-orientation'],'horizontal');
  workspaces.render();assert.equal(get('statistics-plot').querySelector('svg').dataset.orientation,'horizontal');
  assert.deepEqual(errors,[]);
});

for(const dated of [false,true])test(`regression visualization retains a visible fitted line and ${dated?'date':'numeric'} X ticks after redraw`,async context=>{
  const requests=[],data=dated?'date,y\n2026-10-01,3\n2026-10-02,5\n2026-10-03,7':'1,3\n2,5\n3,7';
  const {window,workspaces,errors}=fixture(context,{fields:{mode:'statistics','statistics-kind':'xy','statistics-data':data,'statistics-plot-type':'scatter','regression-kind':'linear'}},
    {ready:true,execute:async request=>{requests.push(request);return {ok:true,exact:'2*x+1',decimal:'2*x+1',curve:[[1,3],[2,5],[3,7]]};}});
  const document=window.document,get=id=>document.getElementById(id);
  await document.querySelector('[data-run="regression"]').onclick();
  assert.deepEqual(requests[0].statisticsDatasets[requests[0].tree.args[0].value],[['1','3'],['2','5'],['3','7']]);
  function check(){
    const curve=document.querySelector('#statistics-plot path[data-curve="1"]');
    assert.ok(curve);assert.equal(curve.getAttribute('stroke'),'var(--danger)');assert.match(curve.getAttribute('d'),/^M.*L.*L/);
    assert.equal(document.querySelectorAll('#statistics-plot circle').length,3);
    const labels=[...document.querySelectorAll('#statistics-plot text[data-axis="x"]')].map(node=>node.textContent);
    if(dated)assert.deepEqual(labels,['2026-10-01','2026-10-02','2026-10-03']);
    else assert.ok(labels.every(label=>!label.includes('2026-')));
  }
  check();get('statistics-plot-run').click();check();workspaces.render();check();
  const style=document.createElement('style');style.textContent=readFileSync(new URL('../calculator.css',import.meta.url),'utf8');document.head.append(style);
  for(const [theme,color] of [['light','#aa3438'],['dark','#ffa29d']]){
    document.documentElement.dataset.theme=theme;
    assert.equal(window.getComputedStyle(document.documentElement).getPropertyValue('--danger').trim(),color);
  }
  if(!dated){
    get('statistics-scatter-x').value='1';get('statistics-scatter-x').onchange();
    assert.equal(document.querySelector('#statistics-plot path[data-curve]'),null);
    get('statistics-scatter-x').value='0';get('statistics-scatter-x').onchange();check();
  }
  assert.deepEqual(errors,[]);
});

test('saved guided statistics menu is restored after its handlers and caches initialize',context=>{
  const {window,errors}=fixture(context,{fields:{mode:'statistics','statistics-op':'mcnemar','statistics-data':'20,8\n2,15','statistics-kind':'xy'}});
  assert.equal(window.document.getElementById('statistics-general-kind').value,'mcnemar');
  assert.ok(window.document.getElementById('statistics-general-kind').onchange);
  assert.deepEqual(errors,[]);
});

test('summary action sends the selected categorical column and its literal labels to the engine',async context=>{
  const requests=[];
  const {window,errors}=fixture(context,{fields:{mode:'statistics','statistics-data':'event,sex\n0,m\n1,f\n,m','statistics-kind':'xy'}},
    {ready:true,execute:async request=>{requests.push(request);return {ok:true};}});
  window.document.getElementById('statistics-summary-column').value='1';
  await window.document.querySelector('[data-run="statistics-summary"]').onclick();
  assert.equal(requests.length,1);
  const request=requests[0];assert.equal(request.tree.value,'stats');assert.equal(request.tree.args[1].value,'categorical');
  assert.deepEqual(request.statisticsDatasets[request.tree.args[0].value],['0','1','0']);
  assert.deepEqual(request.statisticsTermLabels,{'sample:1':'sex (y)','summary:category:0':'m','summary:category:1':'f'});
  assert.deepEqual(errors,[]);
});

test('Overall is the first Summary action and sends all columns before switching back to a column summary',async context=>{
  const requests=[],item=JSON.parse(readFileSync(new URL('../../tests/fixtures/statistics_summary.json',import.meta.url),'utf8')).overallCases[0];
  const {window,errors}=fixture(context,{fields:{mode:'statistics','statistics-data':item.source,'statistics-kind':item.kind}},
    {ready:true,execute:async request=>{requests.push(request);return {ok:true};}});
  const document=window.document,overall=document.getElementById('statistics-summary-overall');
  assert.equal(document.querySelector('#statistics-summary button'),overall);
  await overall.onclick();
  assert.equal(requests.length,1);
  const request=requests[0];assert.equal(request.tree.args[1].value,'overall');
  assert.deepEqual(request.statisticsDatasets[request.tree.args[0].value],[['20','30'],['0','1','1'],['0','1','0'],[],['8']]);
  assert.deepEqual(request.statisticsTermLabels,item.labels);
  document.querySelector('[data-run="statistics-summary"]').click();
  await new Promise(resolve=>setTimeout(resolve,0));
  assert.equal(requests.length,2);assert.equal(requests[1].tree.args.length,1);
  assert.deepEqual(requests[1].statisticsTermLabels,{'sample:1':'age (x)'});
  assert.deepEqual(errors,[]);
});

test('grouped t test value checkboxes send selected columns and persist a single-column fallback',async context=>{
  const requests=[],item=JSON.parse(readFileSync(new URL('../../tests/fixtures/statistics_t_columns.json',import.meta.url),'utf8')).cases[0];
  const {window,errors}=fixture(context,{fields:{mode:'statistics','statistics-data':item.source,'statistics-kind':'columns','statistics-columns':'4','statistics-op':'ttest2','statistics-grouping':'groups','statistics-t-columns-choice':'1,2,3'}},
    {ready:true,execute:async request=>{requests.push(request);return {ok:true};}});
  const document=window.document,checks=()=>[...document.querySelectorAll('#statistics-t-columns input')];
  assert.equal(document.getElementById('statistics-t-columns').hidden,false);
  assert.deepEqual(checks().map(input=>input.value),['1','2','3']);assert.ok(checks().every(input=>input.checked));
  await document.querySelector('[data-run="statistics"]').onclick();
  assert.equal(requests[0].tree.args[3].value,'batch');assert.deepEqual(requests[0].statisticsTermLabels,item.labels);
  for(const value of ['2','3']){const input=checks().find(input=>input.value===value);input.checked=false;input.onchange();}
  assert.equal(document.getElementById('statistics-t-columns-choice').value,'1');
  await document.querySelector('[data-run="statistics"]').onclick();
  assert.equal(requests[1].tree.args.length,3);
  const group=document.getElementById('statistics-group-column');group.value='1';group.onchange();
  assert.ok(checks().every(input=>input.value!=='1'));
  assert.deepEqual(errors,[]);
});

for(const op of ['chi2independence','fisherexact','mannwhitney','wilcoxon','kruskal','anova','ztest2'])test(`${op} exposes grouped value-column checkboxes and executes the combined request`,async context=>{
  const requests=[],item=JSON.parse(readFileSync(new URL('../../tests/fixtures/statistics_grouped_columns.json',import.meta.url),'utf8')).cases.find(item=>item.settings.op===op);
  const settings=item.settings,columns=settings.kind==='xyz'?3:Number(settings.kind.split(':')[1]);
  const {window,errors}=fixture(context,{fields:{mode:'statistics','statistics-data':item.source,'statistics-kind':'columns','statistics-columns':String(columns),'statistics-op':op,'statistics-grouping':'groups',
    'statistics-t-columns-choice':settings.valueColumns,'statistics-pair-matching':settings.matching||'order','statistics-subject-column':String(settings.subjectColumn||0),'statistics-anova-method':settings.anovaMethod||'welch','statistics-sigma':settings.sigma||'1','statistics-sigma-y':settings.sigmaY||'1'}},
    {ready:true,execute:async request=>{requests.push(request);return {ok:true};}});
  const document=window.document;
  assert.equal(document.getElementById('statistics-t-columns').hidden,false);
  assert.ok([...document.querySelectorAll('#statistics-t-columns input:checked')].length>1);
  if(op==='fisherexact')assert.deepEqual([...document.getElementById('statistics-first-group').options].map(option=>option.value),['m','f']);
  await document.querySelector('[data-run="statistics"]').onclick();
  assert.equal(requests.length,1);assert.ok(requests[0].tree.args.some(node=>node.value==='batch'));
  assert.deepEqual(requests[0].statisticsTermLabels,item.labels);
  assert.deepEqual(errors,[]);
});

test('statistics paste handlers filter Markdown headings in selection replacements and table cells',async context=>{
  const {window,errors}=fixture(context,{fields:{mode:'statistics','statistics-data':'12\n34','statistics-kind':'list'}});
  const document=window.document,field=document.getElementById('statistics-data');
  function paste(input,text){
    const event=new window.Event('paste',{bubbles:true,cancelable:true});
    Object.defineProperty(event,'clipboardData',{value:{getData:()=>text}});
    input.dispatchEvent(event);assert.equal(event.defaultPrevented,true);
  }
  field.setSelectionRange(0,2);paste(field,'# note\n56\n## skipped\n78');
  assert.equal(field.value,'56\n78\n34');assert.equal(field.selectionStart,5);
  document.getElementById('statistics-table-toggle').click();
  const cell=document.querySelector('#statistics-grid input[data-row="0"][data-column="0"]');
  cell.select();paste(cell,'# cell note\n"1,234"');
  assert.equal(cell.value,'1234');assert.equal(field.value,'1234\n78\n34');
  cell.select();paste(cell,'# only a comment');
  assert.equal(cell.value,'');assert.equal(field.value,'""\n78\n34');
  await new Promise(resolve=>setTimeout(resolve,180));
  assert.deepEqual(errors,[]);
});

test('statistics data paste converts Excel and Markdown tables to CSV before updating controls',async context=>{
  const {window,errors}=fixture(context,{fields:{mode:'statistics','statistics-kind':'xy'}});
  const field=window.document.getElementById('statistics-data');
  for(const source of ['\r\nx\ty\r\n1\t2\r\n\r\n3\t4\r\n\r\n','## Data\n\n| x | y |\n| --- | --- |\n| 1 | 2 |\n\n| 3 | 4 |\n']){
    field.setSelectionRange(0,field.value.length);
    const event=new window.Event('paste',{bubbles:true,cancelable:true});
    Object.defineProperty(event,'clipboardData',{value:{getData:()=>source}});
    field.dispatchEvent(event);assert.equal(event.defaultPrevented,true);
    assert.equal(field.value.replaceAll('\r\n','\n'),'x,y\n1,2\n3,4');
    assert.equal(field.selectionStart,field.value.length);
  }
  await new Promise(resolve=>setTimeout(resolve,180));assert.deepEqual(errors,[]);
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
