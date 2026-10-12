import {csvRows,statisticsColumnCount,statisticsColumnNames,statisticsKindForColumns,statisticsCsvHasHeader,statisticsNumericCell} from './workspace-commands.js';

const numeric=/^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$/;
export function defaultStatisticsGroupValues(cuts){return Array.from({length:Math.max(1,cuts.trim().split(/[,;\s]+/).filter(Boolean).length)+1},(_,i)=>String(i)).join(',');}
export function statisticsGroupedColumn(source,kind,column,cutPoints,header,groupValues=''){
  const count=statisticsColumnCount(kind);
  if(!Number.isInteger(column)||column<0||column>=count)throw new Error('Choose valid data columns');
  const texts=cutPoints.trim().split(/[,;\s]+/).filter(Boolean),cuts=texts.map(text=>numeric.test(text)?Number(text):NaN);
  if(!cuts.length||!cuts.every(Number.isFinite))throw new Error('Enter finite numeric cut points');
  if(cuts.some((value,i)=>i>0&&value<=cuts[i-1]))throw new Error('Cut points must be strictly increasing');
  const name=header.trim();if(!name)throw new Error('Enter a new column header');
  const raw=csvRows(source+'\n',{skipHeader:false,preserveEmptyRows:true}),width=Math.max(count,...raw.map(row=>row.length));
  if(width>=100)throw new Error('Column count must be between 1 and 100');
  const hasHeader=statisticsCsvHasHeader(raw),aliases=statisticsColumnNames(width);
  const oldNames=hasHeader?aliases.map((alias,i)=>raw[0][i]||alias):aliases;
  if(oldNames.some(old=>old.toLowerCase()===name.toLowerCase()))throw new Error('New column header already exists');
  const ranges=[`< ${texts[0]}`,...texts.slice(1).map((text,i)=>`${texts[i]} ≤ x < ${text}`),`≥ ${texts.at(-1)}`];
  const labels=groupValues.trim()?groupValues.split(/[,;\r\n]/).map(text=>text.trim()):ranges.map((_,i)=>String(i)),counts=labels.map(()=>0);
  if(labels.length!==ranges.length||labels.some(label=>!label))throw new Error('Enter one group value per interval');
  if(new Set(labels).size!==labels.length)throw new Error('Group values must be distinct');
  let omitted=0;
  const rows=(hasHeader?raw.slice(1):raw).map(row=>{
    const text=statisticsNumericCell(row[column]),value=numeric.test(text)?Number(text):NaN;
    let label='';
    if(!Number.isFinite(value))omitted++;
    else {
      let lo=0,hi=cuts.length;
      while(lo<hi){const mid=Math.floor((lo+hi)/2);if(value<cuts[mid])hi=mid;else lo=mid+1;}
      counts[lo]++;label=labels[lo];
    }
    return [...Array.from({length:width},(_,i)=>row[i]??''),label];
  });
  if(!counts.some(Boolean))throw new Error('No finite numeric values in selected column');
  const updated=[oldNames.concat(name),...rows];
  if(!statisticsCsvHasHeader([[name],['1']]))throw new Error('Use a text column header');
  const quote=text=>/[",\r\n\t]/.test(text)?'"'+text.replaceAll('"','""')+'"':text;
  return {csv:updated.map(row=>row.map(quote).join(',')).join('\n'),kind:statisticsKindForColumns(width+1),labels,ranges,counts,omitted};
}
