// CSV itself cannot distinguish an all-text data row from an explicitly set header.
// Remember exact normalized datasets whose first row was created as a header.
const keys=new Set();
function key(rows){
  let a=2166136261,b=3335557771,count=0;
  const feed=value=>{a=Math.imul(a^value,16777619);b=Math.imul(b^value,2246822519);};
  for(const raw of rows){
    const row=raw.map(cell=>String(cell??'').trim());while(row.length&&!row.at(-1))row.pop();if(!row.length)continue;
    count++;feed(row.length);
    for(const cell of row){feed(cell.length);for(let i=0;i<cell.length;i++)feed(cell.charCodeAt(i));}
  }
  return `${a>>>0}:${b>>>0}:${count}`;
}
export const hasExplicitStatisticsHeader=rows=>keys.size>0&&keys.has(key(rows));
export function registerStatisticsHeader(rows){if(rows[0]?.some(Boolean)&&!rows[0].some(cell=>String(cell).trim()&&Number.isFinite(Number(cell))))keys.add(key(rows));}
export const statisticsHeaderKeys=()=>[...keys];
export function restoreStatisticsHeaderKeys(saved){keys.clear();for(const value of Array.isArray(saved)?saved:[])if(typeof value==='string'&&/^\d+:\d+:\d+$/.test(value))keys.add(value);}
