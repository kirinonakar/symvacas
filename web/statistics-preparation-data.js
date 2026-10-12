import {csvRows,statisticsColumnCount,statisticsColumnNames,statisticsKindForColumns,statisticsCsvHasHeader,statisticsNumericCell} from './workspace-commands.js';
import {registerStatisticsHeader} from './statistics-headers.js';
import {parse} from './parser.js';
import {computationLimitsRemoved} from './computation-limits.js';

const numeric=/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$/;
const identifier=/^[\p{L}][\p{L}\p{N}_]*$/u;
export function preparationDataset(source,kind){
  const raw=csvRows(source+'\n',{skipHeader:false,preserveEmptyRows:true}),width=Math.max(statisticsColumnCount(kind),...raw.map(row=>row.length));
  const header=statisticsCsvHasHeader(raw),aliases=statisticsColumnNames(width);
  return {headers:header?aliases.map((name,i)=>raw[0][i]||name):aliases,rows:(header?raw.slice(1):raw).map(row=>Array.from({length:width},(_,i)=>row[i]??''))};
}
function number(cell){const text=statisticsNumericCell(cell);return numeric.test(text)&&Number.isFinite(Number(text))?Number(text):NaN;}
function indices(text,width,defaults=[]){
  const values=text==='auto'?defaults:String(text).split(',').filter(value=>value.trim()).map(Number);
  if(values.some(value=>!Number.isInteger(value)||value<0||value>=width)||new Set(values).size!==values.length)throw new Error('Choose valid data columns');
  return values;
}
function validateHeaders(headers){
  if(!headers.length||headers.length>100)throw new Error('Column count must be between 1 and 100');
  if(headers.some(name=>!name.trim()||!statisticsCsvHasHeader([[name],['1']])))throw new Error('Use a text column header');
  if(new Set(headers.map(name=>name.toLowerCase())).size!==headers.length)throw new Error('New column header already exists');
}
function result(headers,rows,changed,omitted=0,filter=false){
  if(!filter)validateHeaders(headers);
  else if(!headers.length||headers.length>100)throw new Error('Column count must be between 1 and 100');
  if(!filter&&!rows.length||!computationLimitsRemoved()&&rows.length>5000)throw new Error('Enter 1–5000 data rows');
  const all=[headers,...rows];registerStatisticsHeader(all);
  const quote=text=>/[",\r\n\t]/.test(text)?'"'+text.replaceAll('"','""')+'"':text;
  return {csv:all.map(row=>row.length===1&&!row[0]?'""':row.map(quote).join(',')).join('\n'),kind:statisticsKindForColumns(headers.length),headers,rows,changed,omitted};
}
export function preparationTransform(source,kind,operation,settings={}){
  const {headers,rows}=preparationDataset(source,kind),width=headers.length;
  if(!rows.some(row=>row.some(Boolean)))throw new Error('Enter data first');
  const get=(key,fallback='')=>String(settings[key]??fallback);
  if(operation==='filter'){
    const match=get('match','all');if(!['all','any'].includes(match))throw new Error('Choose how to combine filter conditions');
    const predicates=preparationFilterConditions(get('conditions','[{"column":"0","operator":"notBlank","value":""}]')).map(condition=>{
      if(!/^[0-9]+$/.test(String(condition.column)))throw new Error('Choose valid data columns');
      const column=Number(condition.column);indices(String(column),width);
      const op=condition.operator,value=condition.value;
      if(['eq','neq','lt','lte','gt','gte'].includes(op)){
        const target=number(value);if(!Number.isFinite(target))throw new Error('Enter a finite numeric filter value');
        return row=>{const n=number(row[column]);return Number.isFinite(n)&&({eq:()=>n===target,neq:()=>n!==target,lt:()=>n<target,lte:()=>n<=target,gt:()=>n>target,gte:()=>n>=target})[op]();};
      }
      if(!['textEquals','textNotEquals','contains','startsWith','endsWith','blank','notBlank'].includes(op))throw new Error('Choose a valid filter operator');
      if(['contains','startsWith','endsWith'].includes(op)&&!value.trim())throw new Error('Enter a text filter value');
      return row=>{const cell=row[column];return ({textEquals:()=>cell===value,textNotEquals:()=>cell!==value,contains:()=>cell.includes(value),startsWith:()=>cell.startsWith(value),endsWith:()=>cell.endsWith(value),blank:()=>!cell.trim(),notBlank:()=>!!cell.trim()})[op]();};
    });
    const output=rows.filter(row=>match==='all'?predicates.every(test=>test(row)):predicates.some(test=>test(row)));
    return result(headers,output,rows.length-output.length,0,true);
  }
  if(operation==='wideToLong'){
    const ids=indices(get('ids','0'),width),measures=indices(get('measures','auto'),width,headers.map((_,i)=>i).filter(i=>!ids.includes(i)));
    if(!measures.length||measures.some(i=>ids.includes(i)))throw new Error('Choose distinct ID and measurement columns');
    const outHeaders=[...(ids.length?ids.map(i=>headers[i]):[get('rowHeader','row_id').trim()]),get('variableHeader','variable').trim(),get('valueHeader','value').trim()];
    validateHeaders(outHeaders);if(!computationLimitsRemoved()&&rows.length*measures.length>5000)throw new Error('Enter 1–5000 data rows');
    const output=rows.flatMap((row,index)=>measures.map(column=>[...(ids.length?ids.map(i=>row[i]):[String(index+1)]),headers[column],row[column]]));
    return result(outHeaders,output,output.length);
  }
  if(operation==='longToWide'){
    const ids=indices(get('ids','0'),width),variable=Number(get('variable','1')),value=get('value','-1')==='-1'?width-1:Number(get('value'));
    if(!ids.length||![variable,value].every(i=>Number.isInteger(i)&&i>=0&&i<width)||variable===value||ids.includes(variable)||ids.includes(value))throw new Error('Choose distinct ID, variable and value columns');
    const variables=[],groups=new Map(),policy=get('duplicates','error');
    if(!['error','first','last','sum','mean'].includes(policy))throw new Error('Invalid duplicate policy');
    for(const row of rows){
      if(ids.some(i=>!row[i])||!row[variable])throw new Error('ID and variable cells must not be blank');
      const id=JSON.stringify(ids.map(i=>row[i])),name=row[variable];if(!variables.includes(name))variables.push(name);
      if(ids.length+variables.length>100)throw new Error('Column count must be between 1 and 100');
      if(!groups.has(id))groups.set(id,{ids:ids.map(i=>row[i]),values:new Map()});
      const entry=groups.get(id).values;if(!entry.has(name))entry.set(name,[]);entry.get(name).push(row[value]);
    }
    const output=[...groups.values()].map(group=>[...group.ids,...variables.map(name=>{
      const cells=group.values.get(name)||[];
      if(cells.length>1&&policy==='error')throw new Error('Duplicate ID / variable pair; choose an aggregation');
      if(['sum','mean'].includes(policy)){
        const usable=cells.filter(Boolean).map(number);if(usable.some(value=>!Number.isFinite(value)))throw new Error('Aggregation requires finite numeric values');
        if(!usable.length)return '';
        const aggregate=policy==='mean'?usable.reduce((sum,value)=>sum+value/usable.length,0):usable.reduce((sum,value)=>sum+value,0);
        if(!Number.isFinite(aggregate))throw new Error('Aggregation result is not finite');return String(aggregate);
      }
      return (policy==='last'?cells.at(-1):cells[0])??'';
    })]);
    return result([...ids.map(i=>headers[i]),...variables.map(name=>get('prefix')+name)],output,output.length);
  }
  if(operation==='recode'){
    const column=Number(get('column','0'));indices(String(column),width);
    const method=get('method','exact'),otherwise=get('otherwise','keep'),output=get('output','append');
    if(!['exact','intervals'].includes(method)||!['keep','blank','value'].includes(otherwise)||!['append','replace'].includes(output))throw new Error('Invalid recode option');
    const mapping=new Map();let cuts=[],labels=[];
    if(method==='exact'){
      for(const line of get('rules').split(/\r?\n/).filter(line=>line.trim())){
        const match=/^(.*?)\s*,\s*(.*)$/.exec(line);if(!match||!match[1].trim())throw new Error('Use one old value, new value mapping per line');
        const key=match[1].trim()==='<missing>'?'':match[1].trim();if(mapping.has(key))throw new Error('Duplicate value mapping');mapping.set(key,match[2].trim());
      }
      if(!mapping.size)throw new Error('Enter value mappings');
    }else{
      cuts=get('cuts').trim().split(/[,;\s]+/).filter(Boolean).map(number);
      if(!cuts.length||cuts.some(value=>!Number.isFinite(value))||cuts.some((value,i)=>i>0&&value<=cuts[i-1]))throw new Error('Cut points must be strictly increasing');
      labels=get('groups','0,1').split(/[,;\r\n]/).map(value=>value.trim());if(labels.length!==cuts.length+1)throw new Error('Enter one group value per interval');
    }
    let changed=0;
    const values=rows.map(row=>{
      const original=row[column];let found=false,replacement='';
      if(method==='exact'){found=mapping.has(original);if(found)replacement=mapping.get(original);}
      else {const n=number(original);if(Number.isFinite(n)){let index=0;while(index<cuts.length&&n>=cuts[index])index++;found=true;replacement=labels[index];}}
      if(!found)replacement=otherwise==='keep'?original:otherwise==='value'?get('otherwiseValue'):'';
      if(replacement!==original)changed++;return replacement;
    });
    const outHeaders=headers.slice();if(output==='append')outHeaders.push(get('header','recoded').trim());else outHeaders[column]=get('header','recoded').trim();
    return result(outHeaders,rows.map((row,i)=>output==='append'?[...row,values[i]]:row.map((cell,j)=>j===column?values[i]:cell)),changed);
  }
  if(operation==='derive'){
    const tree=parse(get('formula')),bindings=new Map(headers.map((name,i)=>[name,i]).filter(([name])=>identifier.test(name)));
    for(const [i,name] of statisticsColumnNames(width).entries())if(!bindings.has(name))bindings.set(name,i);
    validateFormula(tree,bindings);
    let omitted=0;
    const output=rows.map(row=>{const value=evaluate(tree,row,bindings);if(!Number.isFinite(value)){omitted++;return [...row,''];}return [...row,String(value===0?0:value)];});
    if(omitted===rows.length)throw new Error('No finite derived values; check the formula and data');
    return result([...headers,get('header','derived').trim()],output,rows.length-omitted,omitted);
  }
  throw new Error('Unknown preparation operation');
}
export function preparationFilterConditions(text){
  let conditions;try{conditions=JSON.parse(text);}catch{throw new Error('Enter valid filter conditions');}
  if(!Array.isArray(conditions)||!conditions.length||conditions.some(item=>!item||typeof item!=='object'||!['string','number'].includes(typeof item.column)||typeof item.operator!=='string'||typeof item.value!=='string'))throw new Error('Enter valid filter conditions');
  return conditions;
}
const unary=new Set('abs sqrt exp ln log10 sin cos tan asin acos atan floor ceil sign percent degree'.split(' '));
function validateFormula(node,bindings){
  if(node.kind==='number')return;
  if(node.kind==='symbol'){if(!bindings.has(node.value)&&!['pi','e','true','false'].includes(node.value))throw new Error('Unknown column in formula: '+node.value);return;}
  if(node.kind==='group'||node.kind==='unary'&&['+','-'].includes(node.value)){}
  else if(node.kind==='binary'&&['+','-','*','/','^','mod'].includes(node.value)){}
  else if(node.kind==='relation'&&['=','==','!=','<','>','<=','>='].includes(node.value)){}
  else if(node.kind==='call'){
    const n=node.args.length,name=node.value;
    if(!(unary.has(name)&&n===1||['log','round'].includes(name)&&[1,2].includes(n)||name==='pow'&&n===2||name==='if'&&n===3||['min','max','sum','mean'].includes(name)&&n>=1))throw new Error('Unsupported function or argument count: '+name);
  }else throw new Error('Unsupported formula expression');
  node.args.forEach(arg=>validateFormula(arg,bindings));
}
function evaluate(node,row,bindings){
  if(node.kind==='number')return Number(node.value);
  if(node.kind==='symbol')return bindings.has(node.value)?number(row[bindings.get(node.value)]):({pi:Math.PI,e:Math.E,true:1,false:0})[node.value];
  if(node.kind==='group')return evaluate(node.args[0],row,bindings);
  if(node.kind==='call'&&node.value==='if'){const condition=evaluate(node.args[0],row,bindings);return Number.isFinite(condition)?evaluate(node.args[condition===0?2:1],row,bindings):NaN;}
  const args=node.args.map(arg=>evaluate(arg,row,bindings));if(args.some(value=>!Number.isFinite(value)))return NaN;
  const [a,b]=args,op=node.value;
  if(node.kind==='unary')return op==='-'?-a:a;
  if(node.kind==='binary')return ({'+':()=>a+b,'-':()=>a-b,'*':()=>a*b,'/':()=>a/b,'^':()=>a**b,mod:()=>((a%b)+b)%b})[op]();
  if(node.kind==='relation')return Number(({'=':()=>a===b,'==':()=>a===b,'!=':()=>a!==b,'<':()=>a<b,'>':()=>a>b,'<=':()=>a<=b,'>=':()=>a>=b})[op]());
  if(op==='log')return Math.log(a)/(args.length===2?Math.log(b):1);
  if(op==='round'){const digits=b??0;if(!Number.isInteger(digits)||Math.abs(digits)>15)return NaN;const scale=10**digits;return Math.sign(a)*Math.floor(Math.abs(a)*scale+.5)/scale;}
  if(op==='pow')return a**b;if(op==='sum')return args.reduce((sum,value)=>sum+value,0);if(op==='mean')return args.reduce((sum,value)=>sum+value/args.length,0);
  if(op==='min')return Math.min(...args);if(op==='max')return Math.max(...args);
  if(op==='ln')return Math.log(a);if(op==='sign')return Math.sign(a);if(op==='percent')return a/100;if(op==='degree')return a*Math.PI/180;
  return Math[op](a);
}
