import {defineFunction} from './function-transfer.js';
import {astSource} from './ast-source.js';
import {csvRows,statisticsKindForColumns} from './workspace-commands.js';
import {statisticsHeaderKeys,restoreStatisticsHeaderKeys} from './statistics-headers.js';

const object=value=>value&&typeof value==='object'&&!Array.isArray(value);
const identifier=name=>/^[A-Za-z][A-Za-z0-9_]*$/.test(name)&&!['__proto__','constructor','prototype'].includes(name);
export function validDatasetKind(kind){return ['list','xy','xyz'].includes(kind)||/^columns:\d+$/.test(kind)&&Number(kind.slice(8))>=1&&Number(kind.slice(8))<=100;}
function validateAst(node){
  if(!object(node)||typeof node.kind!=='string'||(node.value!==undefined&&typeof node.value!=='string'))throw new Error('Invalid expression data');
  if(node.args!==undefined){if(!Array.isArray(node.args))throw new Error('Invalid expression data');node.args.forEach(validateAst);}
}
export function dataSnapshot(state){
  return {format:'symvacas.data',version:1,variables:state.variables,functions:state.functions,
    datasets:Object.fromEntries(Object.entries(state.datasets).map(([name,csv])=>[name,{csv,kind:validDatasetKind(state.datasetKinds[name])?state.datasetKinds[name]:statisticsKindForColumns(csvRows(csv)[0]?.length||1)}])),assumptions:state.assumptions,...(statisticsHeaderKeys().length?{statisticsHeaders:statisticsHeaderKeys()}:{})};
}
export function encodeData(state){return JSON.stringify(dataSnapshot(state),null,2);}
export function decodeData(text){
  const root=JSON.parse(text.replace(/^\uFEFF/,''));
  if(!object(root)||root.format!=='symvacas.data'||root.version!==1||!object(root.variables)||!object(root.functions)||!object(root.datasets)||!object(root.assumptions))throw new Error('Invalid SymvaCAS data file');
  for(const [name,node] of Object.entries(root.variables)){if(!identifier(name))throw new Error('Invalid variable name');validateAst(node);}
  for(const [name,entry] of Object.entries(root.functions)){
    if(!object(entry))throw new Error('Invalid function data');
    const definition=defineFunction(name,entry.parameters,entry.source||astSource(entry.body));
    if(entry.body!==undefined)validateAst(entry.body);else entry.body=definition.body;
    if(entry.answerSource!==undefined)validateAst(entry.answerSource);
  }
  for(const [name,entry] of Object.entries(root.datasets))if(!identifier(name)||!object(entry)||typeof entry.csv!=='string'||!validDatasetKind(entry.kind))throw new Error('Invalid statistics data');
  for(const [name,entry] of Object.entries(root.assumptions))if(!identifier(name)||!Array.isArray(entry)||entry.some(value=>!['real','positive','negative','integer','nonzero'].includes(value)))throw new Error('Invalid symbol assumptions');
  if(root.statisticsHeaders!==undefined&&(!Array.isArray(root.statisticsHeaders)||root.statisticsHeaders.some(value=>typeof value!=='string'||!/^\d+:\d+:\d+$/.test(value))))throw new Error('Invalid statistics header metadata');
  return root;
}
export function mergeData(state,data){
  restoreStatisticsHeaderKeys([...statisticsHeaderKeys(),...(data.statisticsHeaders||[])]);
  const fields={...state.fields},selected=fields['dataset-list'],entry=data.datasets[selected];
  if(selected&&entry&&fields['statistics-data']===state.datasets[selected]){
    fields['statistics-data']=entry.csv;
    fields['statistics-kind']=entry.kind.startsWith('columns:')?'columns':entry.kind;
    if(entry.kind.startsWith('columns:'))fields['statistics-columns']=entry.kind.slice(8);
  }
  return {...state,fields,statisticsHeaderKeys:statisticsHeaderKeys(),variables:{...state.variables,...data.variables},functions:{...state.functions,...data.functions},assumptions:{...state.assumptions,...data.assumptions},
    datasets:{...state.datasets,...Object.fromEntries(Object.entries(data.datasets).map(([name,entry])=>[name,entry.csv]))},
    datasetKinds:{...state.datasetKinds,...Object.fromEntries(Object.entries(data.datasets).map(([name,entry])=>[name,entry.kind]))}};
}
// Recreate defaults on reload; only user data survives, including answer-linked functions.
export function resetSettingsState(state){return {variables:state.variables,functions:state.functions,datasets:state.datasets,datasetKinds:state.datasetKinds,assumptions:state.assumptions,...(statisticsHeaderKeys().length?{statisticsHeaderKeys:statisticsHeaderKeys()}:{})};}
export function deleteDataState(state){
  restoreStatisticsHeaderKeys([]);
  const fields={...state.fields,'statistics-data':'','dataset-list':'','dataset-name':''};
  for(const key of Object.keys(fields))if(/^statistics-.*-(source|workflow-source|workflow-labels)$/.test(key))delete fields[key];
  return {...state,variables:{},functions:{},datasets:{},datasetKinds:{},assumptions:{},statisticsHeaderKeys:[],fields};
}
