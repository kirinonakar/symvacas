// Pure request builders shared by CLI/MCP and their tests. No DOM or script eval.
import {parse,latexInput} from '../../web/parser.js';
import {statisticsRequest} from '../../web/statistics-request.js';
import {equationCommand,csvRows,statisticsDetectedColumns,statisticsKindForColumns,statisticsDatasetSource} from '../../web/workspace-commands.js';

const numeric=/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$/;
function symbolName(value){
  if(typeof value!=='string'||!value.trim())throw new Error('Variable/dataset name must be a nonempty symbol');
  const tree=parse(value.trim());
  if(tree.kind!=='symbol'||tree.value!==value.trim())throw new Error('Variable/dataset name must be one symbol: '+value);
  return tree.value;
}

export function statisticsInput({expression,datasets={},registeredDatasets={}}){
  if(typeof expression!=='string'||!expression.trim())throw new Error('Enter a statistics expression');
  if(!datasets||typeof datasets!=='object')throw new Error('datasets must be a named object or an array (named data)');
  const input=statisticsRequest(latexInput(expression));
  const values=Object.create(null);
  function dataset(value,depth=0){
    if(!Array.isArray(value)||depth>1)throw new Error('A dataset must be a numeric vector or a table');
    return value.map(cell=>{
      if(Array.isArray(cell))return dataset(cell,depth+1);
      if(cell===null)return {kind:'symbol',value:'NA',args:[]};
      if(typeof cell==='number'&&Number.isFinite(cell))return String(cell);
      if(typeof cell==='string'&&cell.trim())return numeric.test(cell.trim())?cell.trim():parse(latexInput(cell));
      throw new Error('Dataset cells must be finite numbers, numeric strings, calculator expressions or null (NA)');
    });
  }
  for(const [name,data] of Object.entries(Array.isArray(datasets)?{data:datasets}:datasets))values[symbolName(name)]=dataset(data);
  // Inline array placeholders are generated to avoid names referenced in the expression.
  for(const [name,data] of Object.entries(input.statisticsDatasets)){
    if(Object.hasOwn(values,name))throw new Error('Dataset name conflicts with an inline dataset: '+name);
    values[name]=data;
  }
  const visited=new Set();
  function visit(tree){
    if(tree?.kind==='symbol'&&!Object.hasOwn(values,tree.value)&&Object.hasOwn(registeredDatasets,tree.value)&&!visited.has(tree.value)){
      visited.add(tree.value);const record=registeredDatasets[tree.value];
      const literal=statisticsRequest(statisticsDatasetSource(record.source,record.kind));
      values[tree.value]=literal.statisticsDatasets[literal.tree.value]??literal.tree.args;
      for(const row of values[tree.value])for(const cell of Array.isArray(row)?row:[row])if(typeof cell==='object')visit(cell);
    }
    for(const child of tree?.args||[])visit(child);
  }
  visit(input.tree);
  return {action:'evaluate',tree:input.tree,statisticsDatasets:values};
}

export function datasetInput({data,csv}){
  if((data===undefined)===(csv===undefined))throw new Error('Provide either data (vector/table) or csv text');
  let source=csv;
  if(data!==undefined){
    if(!Array.isArray(data)||!data.length)throw new Error('Provide a nonempty vector or row-major table');
    const rows=Array.isArray(data[0])?data:data.map(cell=>[cell]);
    const width=rows[0]?.length;
    if(!width||rows.some(row=>!Array.isArray(row)||row.length!==width))throw new Error('Dataset rows must have equal column counts');
    const quote=cell=>{
      if(cell===null)return 'NA';
      if(!['string','number'].includes(typeof cell)||typeof cell==='number'&&!Number.isFinite(cell))throw new Error('Invalid dataset cell');
      const value=String(cell);return /[",\r\n\t]/.test(value)?'"'+value.replace(/"/g,'""')+'"':value;
    };
    source=rows.map(row=>row.map(quote).join(',')).join('\n');
  }
  if(typeof source!=='string'||!source.trim())throw new Error('Provide nonempty CSV/TSV text');
  const rows=csvRows(source),columns=statisticsDetectedColumns(source);
  if(rows.length>5001||columns>101)throw new Error('Dataset limit: 5000 data rows and 101 columns');
  return {source,kind:statisticsKindForColumns(columns)};
}

export function equationInput({equations,variables='x',method='solve',initialGuess='0,1',independentVariable='x',initialConditions='',hint='',steps=true}){
  if(!['solve','nsolve','dsolve','pdsolve'].includes(method))throw new Error('Method must be solve, nsolve, dsolve or pdsolve');
  const lines=Array.isArray(equations)?equations:[equations];
  if(!lines.length||lines.some(line=>typeof line!=='string'||!line.trim()))throw new Error('Provide an equation or a nonempty array of equations');
  const differential=['dsolve','pdsolve'].includes(method);
  const names=(Array.isArray(variables)?variables:typeof variables==='string'?(differential?[variables]:variables.split(',')):[]).map(value=>{
    if(differential&&typeof value==='string'){
      const tree=parse(latexInput(value));
      if(tree.kind==='call'&&tree.args.length&&tree.args.every(arg=>arg.kind==='symbol'))return latexInput(value);
    }
    return symbolName(value);
  });
  if(!names.length||new Set(names).size!==names.length)throw new Error('Choose distinct variables');
  if(['dsolve','pdsolve'].includes(method)&&names.length!==1)throw new Error('Choose one dependent variable for differential equations');
  if(typeof steps!=='boolean'||typeof initialConditions!=='string'||typeof hint!=='string')throw new Error('Invalid equation options');
  let guess=initialGuess;
  if(Array.isArray(guess))guess='['+guess.join(',')+']';
  else if(typeof guess==='number'&&Number.isFinite(guess))guess=String(guess);
  if(typeof guess!=='string'||!guess.trim())throw new Error('Enter a numeric initial guess or bounds');
  const source=equationCommand({kind:method,source:lines.join('\n'),variable:names.join(','),
    extra:method==='dsolve'?symbolName(independentVariable):guess,initial:initialConditions,hint});
  return {action:'evaluate',tree:parse(source),equationSteps:steps,solutionSteps:steps};
}
