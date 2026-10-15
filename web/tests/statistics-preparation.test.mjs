import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {preparationTransform,preparationDataset} from '../statistics-preparation-data.js';
import {statisticsPreparationSchema} from '../statistics-preparation-schema.js';
import {statisticsDataRows,statisticsCsvHasHeader,csvRows} from '../workspace-commands.js';
import {statisticsHeaderKeys,restoreStatisticsHeaderKeys} from '../statistics-headers.js';
import {encodeData,decodeData,mergeData,resetSettingsState} from '../data-transfer.js';
import {createPreparationTools} from '../statistics-preparation-tools.js';

const fixture=JSON.parse(readFileSync(new URL('../../tests/fixtures/statistics_preparation.json',import.meta.url),'utf8'));
test('row filters share Android numeric, text, missingness, AND/OR and original row preservation semantics',()=>{
  const fixture=JSON.parse(readFileSync(new URL('../../tests/fixtures/statistics_row_filter.json',import.meta.url),'utf8'));
  for(const item of fixture.cases){
    const source=fixture[item.source],kind=item.source==='multi'?'xyz':'xy',input=preparationDataset(source,kind);
    const result=preparationTransform(source,kind,'filter',{match:item.match,conditions:JSON.stringify(item.conditions)});
    assert.deepEqual(result.headers,input.headers);assert.deepEqual(result.rows,item.rows.map(i=>input.rows[i]));
    assert.equal(result.changed,input.rows.length-item.rows.length);assert.equal(result.omitted,0);
    if(result.rows.length)assert.deepEqual(preparationDataset(result.csv,result.kind),{headers:result.headers,rows:result.rows});
  }
  for(const item of fixture.invalid)assert.throws(()=>preparationTransform(fixture.numeric,'xy','filter',item),error=>error.message===item.error);
});
test('wide/long, recoding and row formulas share Android reference rows, labels, missingness and boundary semantics',()=>{
  for(const item of fixture.cases){
    const result=preparationTransform(item.source,item.kind,item.id,item.settings);
    assert.deepEqual(result.headers,item.headers);assert.equal(result.changed,item.changed);assert.equal(result.omitted,item.omitted);assert.equal(result.rows.length,item.rows.length);
    item.rows.forEach((row,i)=>row.forEach((cell,j)=>{
      if(item.numericColumns?.includes(j)&&cell!=='')assert.ok(Math.abs(Number(result.rows[i][j])-Number(cell))<=1e-12*Math.max(1,Math.abs(Number(cell))));
      else assert.equal(result.rows[i][j],cell);
    }));
    assert.deepEqual(preparationDataset(result.csv,result.kind).headers,item.headers);
    assert.deepEqual(preparationDataset(result.csv,result.kind).rows,result.rows);
  }
});
test('invalid roles, duplicate pairs, mappings and unsafe or undefined formulas fail before data can be replaced',()=>{
  for(const item of fixture.invalid)assert.throws(()=>preparationTransform(item.source,item.kind,item.id,item.settings),error=>error.message===item.error);
});
test('wide to long to wide roundtrip retains precision, quoted IDs and blank measurements',()=>{
  const original='ID,before,after\n"A,B",1.2000,\nC,2,4';
  const long=preparationTransform(original,'xyz','wideToLong'),wide=preparationTransform(long.csv,long.kind,'longToWide');
  assert.equal(wide.csv,original);
});
test('all-text recoded headers survive stored settings and editing rather than becoming observations',()=>{
  const result=preparationTransform('Gender\n1\n2','list','recode',{rules:'1, male\n2, female',output:'replace',header:'Sex'});
  const saved=statisticsHeaderKeys();restoreStatisticsHeaderKeys([]);
  assert.equal(statisticsCsvHasHeader(csvRows(result.csv,{skipHeader:false})),false);
  restoreStatisticsHeaderKeys(saved);
  assert.ok(saved.includes('4021414396:2881141766:3'),'header identity uses the same stable encoding on Android and Web');
  assert.deepEqual(statisticsDataRows(result.csv,'list'),[['male'],['female']]);
  const state={variables:{},functions:{},assumptions:{},datasets:{D1:result.csv},datasetKinds:{D1:'list'},fields:{}};
  const portable=decodeData(encodeData(state));restoreStatisticsHeaderKeys([]);
  mergeData(state,portable);assert.deepEqual(statisticsDataRows(result.csv,'list'),[['male'],['female']]);
  assert.ok(resetSettingsState(state).statisticsHeaderKeys.includes('4021414396:2881141766:3'));
});

test('preparation preview stays separate from data, preserves focused fields and blocks applying an outdated preview',context=>{
  const registry=new Map();
  class Node {
    constructor(tag){this.tagName=tag.toUpperCase();this.children=[];this.style={};this.dataset={};this.events={};this.value='';}
    set id(value){this._id=value;registry.set(value,this);}get id(){return this._id;}
    append(...nodes){this.children.push(...nodes);}
    replaceChildren(...nodes){const remove=node=>{if(node.id)registry.delete(node.id);node.children.forEach(remove);};this.children.forEach(remove);this.children=[];this.append(...nodes);}
    addEventListener(event,callback){this.events[event]=callback;}
    querySelectorAll(selector){
      const matches=node=>selector==='input:checked'?node.tagName==='INPUT'&&node.checked:selector.startsWith('input[data-preparation-field=')?node.tagName==='INPUT'&&node.dataset.preparationField===selector.match(/="(.*)"/)[1]:node.tagName===selector.toUpperCase();
      return this.children.flatMap(node=>[...(matches(node)?[node]:[]),...node.querySelectorAll(selector)]);
    }
  }
  const previous=globalThis.document;context.after(()=>globalThis.document=previous);
  const root=new Node('div');root.id='statistics-preparation-tools';
  globalThis.document={createElement:tag=>new Node(tag),getElementById:id=>registry.get(id),documentElement:{dataset:{}}};
  let source='Code\n1\n2',kind='list',applied=0,tools;
  tools=createPreparationTools({state:{fields:{},statisticsSections:{}},data:()=>source,kind:()=>kind,persist:()=>{},applyData:result=>{applied++;source=result.csv;kind=result.kind;tools.update();}});
  tools.update();
  const rules=registry.get('statistics-preparation-recode-rules');rules.value='1, male\n2, female';rules.events.input();
  assert.equal(registry.get('statistics-preparation-recode-rules'),rules,'typing retains the same textarea');
  const panel=registry.get('statistics-preparation-tool-recode'),[preview,apply]=panel.children.at(-1).children;
  preview.onclick();assert.equal(source,'Code\n1\n2');assert.equal(apply.disabled,false);
  const header=registry.get('statistics-preparation-recode-header');header.value='Sex';header.events.input();
  assert.equal(apply.disabled,true);apply.onclick();assert.equal(applied,0);
  preview.onclick();apply.onclick();assert.equal(applied,1);
  assert.deepEqual(preparationDataset(source,kind).headers,['Code','Sex']);
  assert.equal(apply.disabled,true);
  source='test,group,test1,x3\n1,2,3,4';kind='columns:4';tools.update();
  const columnLabels=['test (x)','group (y)','test1 (z)','x3 (x4)'];
  for(const field of ['recode-column','longToWide-variable','longToWide-value']){
    assert.deepEqual(registry.get(`statistics-preparation-${field}`).children.map(option=>option.textContent),columnLabels);
  }
  const wide=registry.get('statistics-preparation-tool-wideToLong');
  for(const columns of wide.querySelectorAll('fieldset'))assert.deepEqual(columns.children.slice(1).map(label=>label.textContent),columnLabels);
  source='1,2,3,4';tools.update();
  assert.deepEqual(registry.get('statistics-preparation-recode-column').children.map(option=>option.textContent),['x','y','z','x4']);
});
