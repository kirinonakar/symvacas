import {computationLimitsRemoved} from './computation-limits.js';
import {parse,latexInput} from './parser.js';
import {statisticsComparisonData} from './statistics-comparison-data.js';
import {hasExplicitStatisticsHeader,registerStatisticsHeader} from './statistics-headers.js';
function csvRecordDelimiter(source,start){
  // Excel separates columns with tabs; commas inside those cells are literal.
  let quoted=false;
  for(let i=start;i<source.length;i++){const ch=source[i];if(ch==='"')quoted=!quoted;else if(!quoted){if(ch==='\t')return '\t';if(ch==='\n'||ch==='\r')break;}}
  return ',';
}
export function statisticsCsvHasHeader(rows){
  if(hasExplicitStatisticsHeader(rows))return true;
  const first=rows[0];if(!first?.some(Boolean))return false;
  const labels=first.map(cell=>cell.toLowerCase());
  if(['x','n','value','y','x,y','group,value','date,value','date,y','x,y,z'].includes(labels.join(','))||labels.length>3&&labels.every((cell,i)=>cell===statisticsColumnNames(labels.length)[i]))return true;
  function dataCell(cell){
    if(!cell)return false;
    const normalized=cell.replace(/,/g,'');
    if(['pi','π','e','E','tau','τ','∞'].includes(cell)||Number.isFinite(Number(normalized))||/^(?:NaN|[+-]?Infinity)$/i.test(cell)||/^\d{4}([-/.])\d{1,2}\1\d{1,2}$/.test(cell))return true;
    if(/^[\p{L}_][\p{L}\p{N}_]*(?:\s+[\p{L}_][\p{L}\p{N}_]*)*$/u.test(cell))return false;
    // Column names may carry a parenthesized unit (e.g. 자산(만원)); numeric calls such as sqrt(2) stay data.
    if(/^[\p{L}_][\p{L}\p{N}_]*(?:\s+[\p{L}_][\p{L}\p{N}_]*)*\s*\([^()]*[\p{L}%][^()]*\)$/u.test(cell))return false;
    try{return parse(latexInput(cell)).kind!=='symbol';}catch{return false;}
  }
  return first.every(Boolean)&&first.every(cell=>!dataCell(cell))&&(rows.slice(1).some(row=>row.length===first.length&&row.some(dataCell))||rows.length>1&&rows.slice(1).every(row=>row.every(cell=>!cell)));
}

export function csvRows(source,{maxColumns=100,skipHeader=true,preserveEmptyRows=false}={}){
  source=source.replace(/^\uFEFF/,'');
  const rows=[];let row=[],cell='',quoted=false,delimiter=csvRecordDelimiter(source,0);
  for(let i=0;i<source.length;i++){const ch=source[i];if(ch==='"'){if(quoted&&source[i+1]==='"'){cell+='"';i++;}else quoted=!quoted;}else if(!quoted&&ch===delimiter){row.push(cell.trim());cell='';}else if(!quoted&&(ch==='\n'||ch==='\r')){if(ch==='\r'&&source[i+1]==='\n')i++;row.push(cell.trim());if(row.some(Boolean)||preserveEmptyRows)rows.push(row);row=[];cell='';delimiter=csvRecordDelimiter(source,i+1);}else cell+=ch;}
  if(quoted)throw new Error('Unclosed CSV quote');row.push(cell.trim());if(row.some(Boolean)||preserveEmptyRows&&source.length&&!/[\r\n]$/.test(source))rows.push(row);
  if(!rows.length||!computationLimitsRemoved()&&rows.length>5000)throw new Error('Enter 1–5000 data rows');
  if(skipHeader&&statisticsCsvHasHeader(rows))rows.shift();
  if(!rows.length)throw new Error('Enter data below the header');
  const columns=Math.max(...rows.map(r=>r.length));if(!computationLimitsRemoved()&&columns>maxColumns)throw new Error(`Use up to ${maxColumns} data columns`);return rows.map(r=>Array.from({length:columns},(_,i)=>r[i]||''));
}
function markdownCells(line){
  line=line.trim();if(line.startsWith('|'))line=line.slice(1);if(line.endsWith('|')&&!line.endsWith('\\|'))line=line.slice(0,-1);
  const cells=[];let cell='';
  for(let index=0;index<line.length;index++){const ch=line[index];if(ch==='\\'&&line[index+1]==='|'){cell+='|';index++;}else if(ch==='|'){cells.push(cell.trim());cell='';}else cell+=ch;}
  cells.push(cell.trim());return cells;
}
function markdownCsvCell(cell){return /[",\r\n\t]/.test(cell)?`"${cell.replace(/"/g,'""')}"`:cell;}
export function statisticsImportRows(rows){
  const header=statisticsCsvHasHeader(rows);
  return rows.map((row,index)=>index===0&&header?row:row.map(statisticsNumericCell));
}
export function statisticsPasteCell(raw){
  return statisticsNumericPasteCell(statisticsPasteDataLines(raw));
}
function statisticsPasteDataLines(source){
  // Omit blank lines and unindented Markdown headings, preserving quoted CSV values.
  const parts=source.split(/(\r\n|\n|\r)/);let quoted=false,result='',separator='',hasLine=false;
  for(let index=0;index<parts.length;index+=2){
    const line=parts[index];
    if(!quoted&&(!line.trim()||/^#{1,6} /.test(line.replace(/^\uFEFF/,''))))continue;
    result+=(hasLine?separator:'')+line;hasLine=true;separator=parts[index+1]??'';
    for(const ch of line)if(ch==='"')quoted=!quoted;
  }
  return result;
}
function statisticsNumericPasteCell(raw){
  const trimmed=raw.trim(),quoted=trimmed.startsWith('"')&&trimmed.endsWith('"'),value=quoted?trimmed.slice(1,-1):trimmed,number=statisticsNumericCell(value);
  if(quoted&&/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$/.test(number))return raw.replace(trimmed,number);
  return number!==value.trim()?raw.replace(/,/g,''):raw;
}
function statisticsSpreadsheetCsv(source){
  if(!source.includes('\t'))return null;
  let cell='',quoted=false,hasTab=false,result='';
  function appendCell(){
    const number=statisticsNumericCell(cell);
    result+=markdownCsvCell(number!==cell.trim()?cell.replace(/,/g,''):cell);cell='';
  }
  for(let index=0;index<source.length;index++){
    const ch=source[index];
    if(ch==='"'){
      if(quoted&&source[index+1]==='"'){cell+='"';index++;}else quoted=!quoted;
    }else if(!quoted&&ch==='\t'){
      hasTab=true;appendCell();result+=',';
    }else if(!quoted&&(ch==='\n'||ch==='\r')){
      appendCell();result+=ch;
      if(ch==='\r'&&source[index+1]==='\n'){result+='\n';index++;}
    }else cell+=ch;
  }
  appendCell();return hasTab&&!quoted?result:null;
}
export function statisticsPasteText(source,{singleColumn=false}={}){
  const filtered=statisticsPasteDataLines(source),markdown=markdownTableCsv(filtered);
  if(markdown===null){const spreadsheet=statisticsSpreadsheetCsv(filtered);if(spreadsheet!==null)return spreadsheet;}
  const text=markdown??filtered,lines=text.split(/\r\n|\n|\r/);
  const grouped=cell=>statisticsNumericCell(cell)!==cell.trim();
  // List mode accepts an unquoted spreadsheet column with thousands separators.
  if(markdown===null&&singleColumn&&!text.includes('\t')&&lines.some(grouped)&&lines.every(line=>!line.includes(',')||grouped(line)))
    return text.replace(/[^\r\n]+/g,line=>grouped(line)?line.replace(/,/g,''):line);
  let start=0,quoted=false,delimiter=csvRecordDelimiter(text,0),result='';
  function appendCell(end){
    result+=statisticsNumericPasteCell(text.slice(start,end));
  }
  for(let index=0;index<text.length;index++){
    const ch=text[index];if(ch==='"')quoted=!quoted;
    if(!quoted&&(ch===delimiter||ch==='\n'||ch==='\r')){
      appendCell(index);result+=ch;start=index+1;
      if(ch==='\n'||ch==='\r')delimiter=csvRecordDelimiter(text,index+1);
    }
  }
  appendCell(text.length);return result;
}
export function markdownTableCsv(source){
  const lines=source.replace(/^\uFEFF/,'').trim().split(/\r\n|\n|\r/).filter(line=>line.trim());
  if(lines[0]?.startsWith('```')&&lines.at(-1)?.startsWith('```')){lines.shift();lines.pop();}
  if(lines.length<2||lines.some(line=>!line.includes('|')))return null;
  const header=markdownCells(lines[0]),separator=markdownCells(lines[1]);
  if(!header.length||separator.length!==header.length||!separator.every(cell=>/^:?-{3,}:?$/.test(cell)))return null;
  const rows=[header,...lines.slice(2).map(markdownCells)];
  if(rows.slice(1).some(row=>row.length>header.length))return null;
  return rows.map(row=>Array.from({length:header.length},(_,index)=>markdownCsvCell(row[index]||'')).join(',')).join('\n');
}
export function statisticsColumnCount(kind){
  if(Object.hasOwn({list:1,xy:2,xyz:3},kind))return {list:1,xy:2,xyz:3}[kind];
  const match=/^columns:(\d+)$/.exec(kind||'');
  return match&&Number(match[1])>=1&&Number(match[1])<=100?Number(match[1]):0;
}
export function statisticsDetectedColumns(source){
  if(!source.trim())return 1;
  return Math.max(1,...csvRows(source,{skipHeader:false,preserveEmptyRows:true}).map(row=>row.length));
}
export function statisticsColumnNames(count){return Array.from({length:count},(_,i)=>['x','y','z'][i]||`x${i+1}`);}
export function statisticsColumnLabels(source,kind){
  const names=statisticsColumnNames(statisticsColumnCount(kind));
  try{const raw=csvRows(source,{skipHeader:false,preserveEmptyRows:true});if(statisticsCsvHasHeader(raw))return names.map((name,i)=>raw[0][i]&&raw[0][i]!==name?`${raw[0][i]} (${name})`:name);}catch{}
  return names;
}
export function statisticsHeatMapColumnNames(source,kind){
  const names=statisticsColumnNames(statisticsColumnCount(kind));
  try{const rows=csvRows(source,{skipHeader:false,preserveEmptyRows:true});if(statisticsCsvHasHeader(rows))return names.map((name,index)=>rows[0][index]||name);}catch{}
  return names;
}
export function statisticsKindForColumns(count){return ['list','xy','xyz'][count-1]||`columns:${count}`;}
export function statisticsAddColumn(source,columnCount){
  const rows=csvRows(source+'\n',{skipHeader:false,preserveEmptyRows:true});
  const count=Math.max(columnCount,...rows.map(row=>row.length));
  if(!Number.isInteger(count)||count<1||count>=100)throw new Error('Column count must be between 1 and 100');
  const header=statisticsCsvHasHeader(rows),name=statisticsColumnNames(count+1).at(-1);
  const updated=rows.map((row,index)=>[...Array.from({length:count},(_,i)=>row[i]??''),index===0&&header?name:'']);
  if(header)registerStatisticsHeader(updated);
  return {csv:updated.map(row=>row.map(markdownCsvCell).join(',')).join('\n'),kind:statisticsKindForColumns(count+1)};
}
export function statisticsRenameColumn(source,columnCount,column,header){
  if(!Number.isInteger(column)||column<0||column>=columnCount)throw new Error('Choose valid data columns');
  const name=header.trim();if(!name)throw new Error('Enter a new column header');
  const raw=csvRows(source+'\n',{skipHeader:false,preserveEmptyRows:true}),width=Math.max(columnCount,...raw.map(row=>row.length));
  const hasHeader=statisticsCsvHasHeader(raw),aliases=statisticsColumnNames(width);
  const names=hasHeader?aliases.map((alias,i)=>raw[0][i]||alias):aliases;
  if(names.some((other,i)=>i!==column&&other.toLowerCase()===name.toLowerCase()))throw new Error('New column header already exists');
  names[column]=name;
  if(!statisticsCsvHasHeader([[name],['1']]))throw new Error('Use a text column header');
  const rows=(hasHeader?raw.slice(1):raw).map(row=>Array.from({length:width},(_,i)=>row[i]??''));
  registerStatisticsHeader([names,...rows]);
  return [names,...(rows.length?rows:[names.map(()=>'')])].map(row=>row.length===1&&!row[0]?'\"\"':row.map(markdownCsvCell).join(',')).join('\n');
}
export function statisticsDataRows(source,kind){
  const columns=statisticsColumnCount(kind);
  if(!columns)throw new Error('Select List, x,y data, or x,y,z data');
  return csvRows(source,{preserveEmptyRows:true}).map(row=>Array.from({length:columns},(_,i)=>row[i]||''));
}
export function statisticsNumericCell(cell){
  const text=String(cell??'').trim();
  return /^[+-]?\d{1,3}(?:,\d{3})+(?:\.\d+)?(?:[eE][+-]?\d+)?$/.test(text)?text.replace(/,/g,''):text;
}
function statisticsDate(value){
  const match=/^(\d{4})([-/.])(\d{1,2})\2(\d{1,2})$/.exec(String(value??'').trim());if(!match)return null;
  const year=Number(match[1]),month=Number(match[3])-1,day=Number(match[4]),date=new Date(0);
  date.setUTCFullYear(year,month,day);
  return date.getUTCFullYear()===year&&date.getUTCMonth()===month&&date.getUTCDate()===day?date.getTime():null;
}
export function statisticsDateAxis(rows){
  const values=rows.map(row=>String(row[0]??'').trim()).filter(Boolean),dates=values.map(statisticsDate).filter(at=>at!==null);
  const numericCount=values.filter(value=>Number.isFinite(Number(statisticsNumericCell(value)))).length;
  if(!dates.length||dates.length<numericCount)return null;
  return {origin:dates.reduce((low,at)=>Math.min(low,at),Infinity)-86400000};
}
export function statisticsDateLabel(origin,value){
  const date=new Date(origin+Math.floor(value+.5)*86400000);
  return Number.isFinite(date.getTime())?date.toISOString().slice(0,10):'';
}
export function numericStatisticsRows(rows,dateAxis=statisticsDateAxis(rows)){
  return rows.map(row=>row.map((cell,j)=>{
    if(j!==0||!dateAxis)return statisticsNumericCell(cell);
    const at=statisticsDate(cell);return at===null?'':String((at-dateAxis.origin)/86400000);
  }));
}
function summaryColumn(rows,numeric,column){
  const values=numeric.map(row=>row[column]||'').filter(Boolean);
  const constants=new Set(['pi','π','e','E','tau','τ','∞']);
  function numericValue(value){
    try{const numeric=node=>(node.kind!=='symbol'||constants.has(node.value))&&node.args.every(numeric);return numeric(parse(latexInput(value)));}catch{return false;}
  }
  if(values.every(numericValue))return {values,categorical:false,labels:[]};
  const labels=[...new Set(rows.map(row=>row[column]||'').filter(Boolean))],indices=new Map(labels.map((value,index)=>[value,index]));
  return {values:rows.map(row=>row[column]||'').filter(Boolean).map(value=>indices.get(value)),categorical:true,labels};
}
export function statisticsSummaryPlan(source,kind,column=0){
  const rows=statisticsDataRows(source,kind),numeric=numericStatisticsRows(rows);
  const data=summaryColumn(rows,numeric,column),label=statisticsColumnLabels(source,kind)[column];
  if(!data.values.length)throw new Error('Enter at least one data value');
  return {source:`stats([${data.values.join(',')}]${data.categorical?',categorical':''})`,
    termLabels:{'sample:1':label,...Object.fromEntries(data.labels.map((value,index)=>[`summary:category:${index}`,value]))}};
}
export function statisticsOverallPlan(source,kind){
  const rows=statisticsDataRows(source,kind),numeric=numericStatisticsRows(rows),labels=statisticsColumnLabels(source,kind);
  const columns=labels.map((_,column)=>summaryColumn(rows,numeric,column));
  if(!columns.some(column=>column.values.length))throw new Error('Enter at least one data value');
  return {source:`stats([${columns.map(column=>`[${column.values.join(',')}]`).join(',')}],overall,[${columns.map(column=>Number(column.categorical)).join(',')}])`,
    termLabels:Object.fromEntries(columns.flatMap((column,index)=>[[`overall:column:${index}`,labels[index]],...column.labels.map((value,category)=>[`overall:category:${index}:${category}`,value])]))};
}
const vector=values=>'['+values.join(',')+']';
export function statisticsDatasetSource(source,kind){
  const rows=numericStatisticsRows(statisticsDataRows(source,kind));
  return vector(statisticsColumnCount(kind)===1?rows.map(row=>row[0]).filter(Boolean):rows.filter(row=>row.every(Boolean)).map(vector));
}
export const statisticsGroupedColumnTests=new Set(['ttest2','ttestpaired','ztest2','chi2independence','fisherexact','mannwhitney','wilcoxon','kruskal','anova','welchanova']);
export function statisticsGroupedTestData(source,{op='ttest2',valueColumns='single',valueColumn=1,groupColumn=0,firstGroup='',secondGroup='',matching='order',subjectColumn=0,kind}={}){
  const rows=statisticsDataRows(source,kind),labels=statisticsColumnLabels(source,kind),paired=['ttestpaired','wilcoxon'].includes(op),all=['kruskal','anova','welchanova','chi2independence'].includes(op),categorical=['chi2independence','fisherexact'].includes(op);
  const columns=valueColumns==='single'?[Number(valueColumn)]:String(valueColumns).split(',').filter(Boolean).map(Number);
  if(!columns.length||new Set(columns).size!==columns.length||columns.some(index=>!Number.isInteger(index)||index<0||index>=labels.length||index===Number(groupColumn)||paired&&matching==='subject'&&index===Number(subjectColumn)))throw new Error('Choose distinct value columns excluding group and subject roles');
  const comparisons=columns.map(column=>({column,label:labels[column],...statisticsComparisonData(rows,{grouping:'groups',group:groupColumn,value:column,firstGroup,secondGroup,matching,subject:subjectColumn},{paired,all})}));
  const termLabels={...Object.fromEntries(comparisons[0].labels.map((label,i)=>[`sample:${i+1}`,label])),...Object.fromEntries(comparisons.map((item,index)=>[`batch:column:${index}`,item.label]))};
  if(categorical)for(const [index,item] of comparisons.entries()){
    const valid=rows.filter(row=>item.labels.includes(String(row[groupColumn]||'').trim())&&String(row[item.column]||'').trim());
    const values=valid.map(row=>row[item.column].trim()),binary=values.length>0&&values.every(value=>{const numeric=Number(statisticsNumericCell(value));return numeric===0||numeric===1;});
    const categories=[...new Set(values.map(value=>binary?String(Number(statisticsNumericCell(value))):value))];
    const codes=new Map(categories.map((value,at)=>[value,binary?Number(value):at]));
    item.groupCodes=valid.map(row=>item.labels.indexOf(row[groupColumn].trim()));item.categoryCodes=valid.map(row=>codes.get(binary?String(Number(statisticsNumericCell(row[item.column]))):row[item.column].trim()));
    termLabels[`batch:binary:${index}`]=binary?'yes':'no';
    for(const category of categories)termLabels[`batch:category:${index}:${codes.get(category)}`]=category;
  }
  return {comparisons,termLabels,paired,categorical};
}
export const statisticsGroupedTTestData=statisticsGroupedTestData;
export function statisticsGroupedTestPlan(source,settings={}){
  const {op='ttest2',extra='0',tail='two',sigma='1',sigmaY='1',yatesCorrection=true,anovaMethod='welch'}=settings;
  if(['ttest2','ttestpaired'].includes(op))return statisticsGroupedTTestPlan(source,settings);
  const data=statisticsGroupedTestData(source,settings),vector=values=>'['+values.map(statisticsNumericCell).join(',')+']',batch=data.comparisons.length>1||data.categorical;
  const samples=data.categorical?[data.comparisons.map(item=>item.groupCodes),data.comparisons.map(item=>item.categoryCodes)]:data.comparisons[0].labels.map((_,at)=>data.comparisons.map(item=>item.samples[at]));
  const argumentsSource=samples.map(columns=>batch?'['+columns.map(vector).join(',')+']':vector(columns[0]));
  const name=op==='anova'&&anovaMethod!=='classic'?'welchanova':op;
  return {source:`${name}(${op==='ztest2'?`${extra},${sigma},${sigmaY},`:''}${argumentsSource.join(',')}${batch?',batch':''}${op==='chi2independence'?','+(yatesCorrection?1:0):''}${!['kruskal','anova','welchanova','chi2independence'].includes(op)&&tail!=='two'?','+tail:''})`,termLabels:data.termLabels};
}
export function statisticsGroupedTTestPlan(source,settings={}){
  const data=statisticsGroupedTTestData(source,settings),{op='ttest2',extra='0',tail='two',independentMethod='welch'}=settings;
  const vector=values=>'['+values.map(statisticsNumericCell).join(',')+']';
  const samples=data.comparisons.map(item=>item.samples);
  const batch=samples.length>1;
  const left=batch?'['+samples.map(pair=>vector(pair[0])).join(',')+']':vector(samples[0][0]);
  const right=batch?'['+samples.map(pair=>vector(pair[1])).join(',')+']':vector(samples[0][1]);
  return {source:`${op}(${extra},${left},${right}${batch?',batch':''}${op==='ttest2'&&independentMethod==='student'?',student':''}${tail==='two'?'':','+tail})`,termLabels:data.termLabels};
}
export function statisticsAnalysisData(source,{op='stats',column=0,grouping='columns',groupColumns='auto',firstGroup='',secondGroup='',groupColumn=0,valueColumn=1,valueColumns,matching='order',subjectColumn=0,kind}={}){
  if(grouping==='groups'&&statisticsGroupedColumnTests.has(op)&&valueColumns!==undefined){
    const data=statisticsGroupedTestData(source,{op,valueColumns,valueColumn,groupColumn,firstGroup,secondGroup,matching,subjectColumn,kind}),first=data.comparisons[0];
    return {...data,rows:statisticsDataRows(source,kind),groups:new Map(first.labels.map((label,i)=>[label,first.samples[i]])),pairs:first.matrix,first:0,second:1,omitted:first.omitted,samples:first.labels.map((label,i)=>({label,values:first.samples[i]}))};
  }
  const paired=['regression','correlation','ttestpaired','wilcoxon','chi2independence','fisherexact'].includes(op)&&!(op==='wilcoxon'&&statisticsColumnCount(kind)===1);
  const categorical=['chi2independence','fisherexact'].includes(op);
  const grouped=grouping==='groups'&&!['regression','correlation'].includes(op),raw=kind?statisticsDataRows(source,kind):csvRows(source),rows=grouped||categorical?raw:numericStatisticsRows(raw),width=rows[0]?.length||1;
  const columnNames=statisticsColumnNames(width);
  const pairSelection=categorical||op==='wilcoxon'||op==='ttestpaired';
  const pairFirst=grouped&&categorical?Number(groupColumn):pairSelection&&firstGroup?columnNames.indexOf(firstGroup):0;
  const pairSecond=grouped&&categorical?Number(valueColumn):pairSelection&&secondGroup?columnNames.indexOf(secondGroup):1;
  let pairs=pairFirst>=0&&pairSecond>=0&&pairFirst!==pairSecond?rows.filter(row=>row[pairFirst]&&row[pairSecond]).map(row=>[row[pairFirst],row[pairSecond]]):[];
  if(categorical)return {rows,groups:new Map(),pairs,paired,categorical,first:pairFirst,second:pairSecond,samples:[{label:columnNames[pairFirst],values:pairs.map(row=>row[0])},{label:columnNames[pairSecond],values:pairs.map(row=>row[1])}]};
  if(['regression','correlation'].includes(op))return {rows,groups:new Map(),pairs,paired,categorical,first:0,second:1,samples:[{label:columnNames[0],values:pairs.map(row=>row[0])},{label:columnNames[1],values:pairs.map(row=>row[1])}]};
  const all=['anova','welchanova','tukey','gameshowell','kruskal'].includes(op),two=['ttest2','ztest2','mannwhitney'].includes(op)||paired;
  const plan=statisticsComparisonData(rows,{grouping:grouped?'groups':'columns',columns:groupColumns,group:groupColumn,value:valueColumn,first:paired?pairFirst:columnNames.indexOf(firstGroup)>=0?columnNames.indexOf(firstGroup):0,second:paired?pairSecond:columnNames.indexOf(secondGroup)>=0?columnNames.indexOf(secondGroup):1,firstGroup,secondGroup,matching,subject:subjectColumn,...(!two&&!all?{first:column}: {})},{all,paired,single:!two&&!all});
  const labels=grouped?plan.labels:plan.labels.map(at=>columnNames[Number(at)]);
  if(paired)pairs=plan.matrix;
  const groups=new Map();if(grouped)for(let i=0;i<plan.labels.length;i++)groups.set(plan.labels[i],plan.samples[i]);
  return {rows,groups,pairs,paired,categorical,first:0,second:1,omitted:plan.omitted,samples:labels.map((label,i)=>({label,values:plan.samples[i]}))};
}
export function statisticsCategoryLabels(pairs,first,second,shared=false){
  const left=[...new Set(shared?pairs.flat():pairs.map(row=>row[0]))],right=shared?left:[...new Set(pairs.map(row=>row[1]))];
  return {'table:row':first,'table:column':second,...Object.fromEntries(left.map((label,i)=>[`table:row:${i+1}`,label])),...Object.fromEntries(right.map((label,i)=>[`table:column:${i+1}`,label]))};
}
export function statisticsCommand(source,{op='stats',column=0,extra='0',tail='two',sigma='1',sigmaY='1',yatesCorrection=true,regression='linear',firth='auto',degree='3',alpha='0.1',l1Ratio='0.5',trees='100',maxDepth='10',seed='0',priorSD='2.5',credibleLevel='0.95',varianceShape='2',varianceScale='1',bayesianMethod='analytic',nutsSamples='500',nutsWarmup='500',nutsMaxDepth='8',nutsSeed='0',nutsChains='2',responseColumn,formula='A*exp(-k*x)+C',variable='x',initials='',grouping='columns',groupColumns='auto',firstGroup='',secondGroup='',groupColumn=0,valueColumn=1,valueColumns,matching='order',subjectColumn=0,anovaMethod='welch',independentMethod='welch',kind}={}){
  if(grouping==='groups'&&statisticsGroupedColumnTests.has(op)&&valueColumns!==undefined)return statisticsGroupedTestPlan(source,{op,extra,tail,sigma,sigmaY,yatesCorrection,anovaMethod,independentMethod,groupColumn,valueColumn,valueColumns,firstGroup,secondGroup,matching,subjectColumn,kind}).source;
  if(op==='regression'&&kind&&kind!=='xy'&&!(statisticsColumnCount(kind)>1&&['multiple','logistic','ridge','lasso','elasticnet','logisticridge','logisticlasso','logisticelasticnet','randomforest','randomforestclassifier','randomforestregressor','bayeslinear','bayeslogistic'].includes(regression)))throw new Error('Regression needs x,y data');
  const {rows,groups,pairs,categorical,first,second,samples:activeSamples}=statisticsAnalysisData(source,{op,column,grouping,groupColumns,firstGroup,secondGroup,groupColumn,valueColumn,matching,subjectColumn,kind});
  const samples=activeSamples.map(sample=>sample.values),data=samples[0];
  if(!categorical){for(const number of samples.flat().filter(Boolean))parse(number);}
  const tailArgument=tail==='two'?'':','+tail;
  if(op==='regression'){
    if(['multiple','logistic','ridge','lasso','elasticnet','logisticridge','logisticlasso','logisticelasticnet','randomforest','randomforestclassifier','randomforestregressor','bayeslinear','bayeslogistic'].includes(regression)){
      const complete=rows.filter(row=>row.every(Boolean));
      const flexible=regression.startsWith('bayes')||['ridge','lasso','elasticnet','logisticridge','logisticlasso','logisticelasticnet','randomforest','randomforestclassifier','randomforestregressor','bayeslinear','bayeslogistic'].includes(regression);
      if(flexible?complete.length<2:complete.length<=rows[0].length)throw new Error(flexible?'Regression needs at least two complete rows':'Add more data points than fit parameters');
      const response=responseColumn===undefined?rows[0].length-1:Number(responseColumn);
      if(!Number.isInteger(response)||response<0||response>=rows[0].length)throw new Error('Select a dependent variable column');
      const order=rows[0].map((_,i)=>i).filter(i=>i!==response).concat(response);
      const samplerOptions=bayesianMethod==='nuts'?`,[nuts,${nutsSamples},${nutsWarmup},${nutsMaxDepth},${nutsSeed},${nutsChains}]`:'';
      const regressionOptions=regression.startsWith('bayes')?`,[${priorSD},${credibleLevel}${regression==='bayeslinear'?`,${varianceShape},${varianceScale}`:''}${samplerOptions}]`:['elasticnet','logisticelasticnet'].includes(regression)?`,[${alpha},${l1Ratio}]`:['ridge','lasso','logisticridge','logisticlasso'].includes(regression)?','+alpha:regression.startsWith('randomforest')?`,[${trees},${maxDepth},${seed}]`:regression==='logistic'&&firth==='firth'?',firth':'';
      return `regression(${vector(complete.map(row=>vector(order.map(i=>row[i]))))},${regression}${regressionOptions})`;
    }
    if(pairs.length<2)throw new Error('Regression needs at least two complete x,y rows');
    return `regression(${vector(pairs.map(p=>vector(regression==='polynomial'&&Number(responseColumn)===0?[p[1],p[0]]:p.slice(0,2))))},${regression}${regression==='polynomial'?','+degree:regression==='custom'?`,${formula},${variable}${initials.trim()?','+initials:''}`:''})`;
  }
  if(categorical){if(first===second||first<0||second<0)throw new Error('Choose two different columns');if(pairs.length<2)throw new Error('Enter at least two complete rows in the selected columns.');const left=[...new Set(pairs.map(r=>r[0]))],right=[...new Set(pairs.map(r=>r[1]))];if(op==='fisherexact'&&(left.length!==2||right.length!==2))throw new Error('Fisher exact needs exactly two categories in each selected column.');if(op==='chi2independence'&&(left.length<2||right.length<2))throw new Error('Each selected column needs at least two categories.');return `${op}(${vector(pairs.map(r=>left.indexOf(r[0])+1))},${vector(pairs.map(r=>right.indexOf(r[1])+1))}${op==='fisherexact'?tailArgument:','+(yatesCorrection?1:0)})`;}
  if(op==='wilcoxon'&&statisticsColumnCount(kind)===1){if(!data?.length)throw new Error('Select a nonempty data column');return `wilcoxon(${vector(data)}${tailArgument})`;}
  if(['correlation','ttestpaired','wilcoxon'].includes(op)){if(pairs.length<2)throw new Error('Enter at least two complete paired rows');return `${op}(${op==='ttestpaired'?extra+',':''}${vector(pairs.map(r=>r[0]))},${vector(pairs.map(r=>r[1]))}${op!=='correlation'?tailArgument:''})`;}
  if(op==='mannwhitney'){const [a,b]=samples;if(!a?.length||!b?.length||first===second)throw new Error('Select two different nonempty samples');return `mannwhitney(${vector(a)},${vector(b)}${op==='ttest2'&&independentMethod==='student'?',student':''}${tailArgument})`;}
  if(['ttest2','ztest2'].includes(op)){const [a,b]=samples;if(!a?.length||!b?.length||first===second)throw new Error('Select two different nonempty samples');return `${op}(${extra},${op==='ztest2'?sigma+','+sigmaY+',':''}${vector(a)},${vector(b)}${op==='ttest2'&&independentMethod==='student'?',student':''}${tailArgument})`;}
  if(['anova','welchanova','tukey','gameshowell','kruskal'].includes(op)){if(samples.length<2||samples.some(s=>s.length<(op==='kruskal'?1:2)))throw new Error('Enter at least two observations in each group');return `${op==='anova'&&anovaMethod!=='classic'?'welchanova':op}(${samples.map(vector).join(',')})`;}
  if(!data?.length)throw new Error('Select a nonempty data column');
  if(op==='ttest')return `ttest(${extra},${vector(data)}${tailArgument})`;
  if(op==='ztest')return `ztest(${extra},${sigma},${vector(data)}${tailArgument})`;
  if(op==='tinterval')return `tinterval(${extra},${vector(data)})`;
  if(op==='zinterval')return `zinterval(${extra},${sigma},${vector(data)})`;
  return `${op}(${vector(data)})`;
}
export function distributionCommand({family='normal',query='cdf',x='1',a='-1.96',b='1.96',p='.975',mean='0',sigma='1',df='10',df2='10',trials='10',success='.5',lambda='2',k='3'}={}){
  const names={normal:['normpdf','normcdf','invnorm'],t:['tpdf','tcdf','invt'],chi2:['chi2pdf','chi2cdf'],f:['fpdf','fcdf'],binomial:['binompdf','binomcdf'],poisson:['poissonpdf','poissoncdf'],geometric:['geometpdf','geometcdf']},functions=names[family];
  const discrete=['binomial','poisson','geometric'].includes(family),index=query==='pdf'||query==='list-pdf'?0:query==='quantile'?2:1,name=functions?.[index];if(!name)throw new Error('This distribution does not support that query');
  if(discrete){const parameters=family==='binomial'?[trials,success]:[family==='poisson'?lambda:success];if(!query.startsWith('list'))parameters.push(k);return `${name}(${parameters.join(',')})`;}
  const parameters=family==='normal'?[mean,sigma]:family==='f'?[df,df2]:[df];
  const inputs=query==='interval'?[a,b]:[query==='quantile'?p:x];if(family==='normal'&&query==='cdf')inputs.unshift('-oo');return `${name}(${[...inputs,...parameters].join(',')})`;
}
export function polynomialEquation(coefficients,variable='x'){
  if(!/^[A-Za-z][A-Za-z0-9_]*$/.test(variable))throw new Error('Enter a valid variable name');
  let source='';for(const [index,coefficient] of coefficients.entries()){const raw=coefficient.trim()||'0';if(raw==='0')continue;const numeric=/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$/.test(raw),negative=numeric&&raw.startsWith('-'),magnitude=negative?raw.slice(1):raw,power=coefficients.length-index-1;source+=source?(negative?'-':'+'):negative?'-':'';if(!power)source+=numeric?magnitude:`(${magnitude})`;else{if(magnitude!=='1')source+=(numeric?magnitude:`(${magnitude})` )+'*';source+=variable+(power>1?'^'+power:'');}}
  return (source||'0')+'=0';
}
export function equationCommand({kind='solve',source,variable='x',extra='0,1',initial='',hint=''}){
  const equations=source.split(/\r?\n/).map(s=>s.trim()).filter(Boolean).map(latexInput);if(!equations.length)throw new Error('Enter an equation');
  const expression=equations.length===1?equations[0]:vector(equations);
  if(kind==='dsolve')return `dsolve(${expression},${variable},${extra}${initial.trim()?','+initial.trim():''})`;
  if(kind==='pdsolve')return `pdsolve(${expression},${variable}${hint.trim()?','+hint.trim():''})`;
  return `${kind}(${expression},${variable.includes(',')?vector(variable.split(',').map(s=>s.trim())):variable}${kind==='nsolve'?','+extra:''})`;
}
