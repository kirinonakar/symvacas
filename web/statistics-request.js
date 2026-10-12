import {computationLimitsRemoved} from './computation-limits.js';
import {parse} from './parser.js';

const numericToken=/[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?/y;
function numericList(source){
  let at=0;
  const space=()=>{while(/\s/.test(source[at]||'!'))at++;};
  function list(depth){
    if(depth>2||source[at++]!=='[')throw new SyntaxError('Numeric dataset expected');
    space();const values=[];
    if(source[at]===']'){at++;return values;}
    for(;;){
      space();
      if(source[at]==='[')values.push(list(depth+1));
      else {numericToken.lastIndex=at;const token=numericToken.exec(source);if(!token)throw new SyntaxError('Numeric dataset expected');values.push(token[0]);at=numericToken.lastIndex;}
      space();if(source[at]===']'){at++;return values;}
      if(source[at++]!==',')throw new SyntaxError('Numeric dataset expected');
    }
  }
  const data=list(1);space();if(at!==source.length)throw new SyntaxError('Numeric dataset expected');return data;
}

// Split dataset cells, never a formula itself, so each formula retains parser guards.
function expressionList(source){
  let at=0;
  const space=()=>{while(/\s/.test(source[at]||'!'))at++;};
  function list(depth){
    if(depth>2||source[at++]!=='[')throw new SyntaxError('Statistics dataset expected');
    space();const values=[];
    if(source[at]===']'){at++;return values;}
    for(;;){
      space();
      if(source[at]==='[')values.push(list(depth+1));
      else{
        const start=at,stack=[],pairs={'(':')','[':']','{':'}'};
        while(at<source.length){
          const c=source[at];if(!stack.length&&(c===','||c===']'))break;
          if(pairs[c])stack.push(pairs[c]);else if(')]}'.includes(c)&&stack.pop()!==c)throw new SyntaxError('Unbalanced dataset cell');
          at++;
        }
        const cell=source.slice(start,at).trim();if(!cell||stack.length)throw new SyntaxError('Statistics dataset cell expected');
        values.push(/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$/.test(cell)?cell:parse(cell));
      }
      space();if(source[at]===']'){at++;return values;}
      if(source[at++]!==',')throw new SyntaxError('Statistics dataset expected');
    }
  }
  const data=list(1);space();if(at!==source.length)throw new SyntaxError('Statistics dataset expected');return data;
}

// Only Statistics execution uses this path. Keep its formula small and send
// decimal strings and guarded cell ASTs separately, preserving exact values.
export function statisticsRequest(source){
  if(!computationLimitsRemoved()&&source.length>16*1024*1024)throw new SyntaxError('Statistics input size limit');
  const statisticsDatasets={};let formula='',from=0;
  while(from<source.length){
    const start=source.indexOf('[',from);if(start<0){formula+=source.slice(from);break;}
    formula+=source.slice(from,start);let end=start,depth=0;
    do {if(source[end]==='[')depth++;else if(source[end]===']')depth--;end++;}while(end<source.length&&depth);
    const literal=source.slice(start,end);let data;
    try{data=numericList(literal);}catch(error){
      if(source.length>8192)try{data=expressionList(literal);}catch{}
      if(data===undefined){formula+=literal;from=end;continue;}
    }
    let name=`SymvaStatisticsData${Object.keys(statisticsDatasets).length}`;
    while(source.includes(name)||Object.hasOwn(statisticsDatasets,name))name+='Data';
    statisticsDatasets[name]=data;formula+=name;from=end;
  }
  return {tree:parse(formula),statisticsDatasets};
}
