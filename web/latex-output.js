import {parse,latexInput,latexSymbolLabels} from './parser.js';
import {roundNumber} from './display-format.js';

const functions=new Set('sin cos tan sec csc cot sinh cosh tanh arcsin arccos arctan ln log exp'.split(' '));
const relations={'==':'=','<=':'\\leq ','≤':'\\leq ','>=':'\\geq ','≥':'\\geq ','!=':'\\neq ','->':'\\to ','→':'\\to ','×':'\\times ','÷':'\\div '};
const escape=value=>String(value).replace(/[\\_{}%&#$]/g,char=>char==='\\'?'\\backslash ':'\\'+char);
const fence=value=>`\\left(${value}\\right)`;
const mathTrees=new WeakMap();
export function registerMathCopy(element,tree,digits=10){element.setAttribute('data-math-copy-node','');mathTrees.set(element,{tree,digits});}
function symbol(value){
  const name=Object.entries(latexSymbolLabels).find(([,label])=>label===value)?.[0]||value;
  if(Object.hasOwn(latexSymbolLabels,name))return '\\'+name;
  if(['oo','∞'].includes(name))return '\\infty';
  if(name==='E')return 'e';
  if(name==='I')return 'i';
  if(name==='EmptySet')return '\\varnothing';
  if(name.includes('_')){const index=name.indexOf('_');return `${symbol(name.slice(0,index))}_{\\mathrm{${escape(name.slice(index+1))}}}`;}
  return name.length<=1?name:`\\mathrm{${escape(name)}}`;
}
export function latexTree(node){
  const {kind,value:v='',args:a=[]}=node;
  const p=i=>a[i]?latexTree(a[i]):'';
  const operand=i=>a[i]&&(['sum','relation','unary'].includes(a[i].kind)||a[i].kind==='binary'&&['+','-'].includes(a[i].value))?fence(p(i)):p(i);
  const power=()=>`${a[0]?.kind==='power'||a[0]?.kind==='binary'&&a[0].value==='^'?fence(p(0)):operand(0)}^{${p(1)}}`;
  const fraction=()=>`\\frac{${p(0)}}{${p(1)}}`;
  function call(name){
    const args=a.map(latexTree).join(', ');
    switch(name){
      case 'sqrt':return `\\sqrt{${p(0)}}`;
      case 'cbrt':return `\\sqrt[3]{${p(0)}}`;
      case 'nthroot':return `\\sqrt[${p(1)}]{${p(0)}}`;
      case 'abs':case 'Abs':return `\\left|${p(0)}\\right|`;
      case 'exp':return `e^{${p(0)}}`;
      case 'log':return a.length===2?`\\log_{${p(1)}}${fence(p(0))}`:`\\log${fence(args)}`;
      case 'integrate':case 'Integral':case 'sum':case 'Sum':case 'product':case 'Product':{
        const b=a[1]?.kind==='tuple'?a[1].args:a.slice(1),integral=['integrate','Integral'].includes(name),op=integral?'\\int':name.toLowerCase()==='sum'?'\\sum':'\\prod';
        const limits=b.length>=3?`_{${integral?'':latexTree(b[0])+'='}${latexTree(b[1])}}^{${latexTree(b[2])}}`:'';
        return `${op}${limits} ${p(0)}${integral?'\\,d'+(b[0]?latexTree(b[0]):''):''}`;
      }
      case 'diff':case 'Derivative':return `\\frac{d${a.length>2?'^{'+p(2)+'}':''}}{d${p(1)}${a.length>2?'^{'+p(2)+'}':''}}${fence(p(0))}`;
      case 'limit':case 'Limit':return `\\lim_{${p(1)} \\to ${p(2)}${a[3]?.value==='right'?'^{+}':a[3]?.value==='left'?'^{-}':''}} ${p(0)}`;
      case 'factorial':return operand(0)+'!';
      case 'percent':return operand(0)+'\\%';
      case 'degree':return operand(0)+'^{\\circ}';
      case 'mixed':return `${p(0)}\\,\\frac{${p(1)}}{${p(2)}}`;
      default:return (functions.has(name)?'\\'+name:`\\operatorname{${escape(name)}}`)+fence(args);
    }
  }
  switch(kind){
    case 'number':case 'float':case 'fixed-number':{const parts=v.split(/[eE]/);return parts.length===2?`${parts[0]} \\times 10^{${parts[1].replace(/^\+/,'')}}`:v;}
    case 'symbol':case 'snapshot_symbol':return symbol(v);
    case 'group':case 'parentheses':return fence(p(0));
    case 'binary':switch(v){case '/':return fraction();case '^':return power();case '*':return operand(0)+' \\cdot '+operand(1);default:return p(0)+(relations[v]||v)+(v==='-'?operand(1):p(1));}
    case 'fraction':return fraction();
    case 'power':return power();
    case 'root':return `\\sqrt{${p(0)}}`;
    case 'indexed-root':return `\\sqrt[${p(1)}]{${p(0)}}`;
    case 'unary':return v+operand(0);
    case 'relation':return a.map(latexTree).join(' '+(relations[v]||v)+' ');
    case 'sum':return a.map((x,i)=>i&&x.kind!=='unary'?'+'+latexTree(x):latexTree(x)).join('');
    case 'product':case 'explicit-product':case 'implicit-product':return a.map((_,i)=>operand(i)).join(' \\cdot ');
    case 'call':case 'function':case 'frozen_call':return call(v);
    case 'integral':return call('integrate');
    case 'derivative':return call('diff');
    case 'point-derivative':return `\\left.\\frac{d}{d${p(1)}}${fence(p(0))}\\right|_{${p(1)}=${p(2)}}`;
    case 'limit':return call('limit');
    case 'large-operator':return call(['Π','∏'].includes(v)?'product':'sum');
    case 'logarithm':return call('log');
    case 'postfix':return operand(0)+({'%':'\\%','°':'^{\\circ}'}[v]||v);
    case 'mixed':return p(0)+'\\,'+p(1);
    case 'dms':case 'sexagesimal':return a.map((_,i)=>p(i)+(['^{\\circ}','^{\\prime}','^{\\prime\\prime}'][i]||'')).join('');
    case 'matrix':return '\\begin{bmatrix}'+a.map(row=>row.args.map(latexTree).join(' & ')).join(' \\\\ ')+'\\end{bmatrix}';
    case 'list':return a.length&&a.every(x=>x.kind==='list'&&x.args.length===a[0].args.length)?latexTree({...node,kind:'matrix'}):'\\left['+a.map(latexTree).join(', ')+'\\right]';
    case 'set':return '\\left\\{'+a.map(latexTree).join(', ')+'\\right\\}';
    case 'tuple':return fence(a.map(latexTree).join(', '));
    case 'row-operation':return `\\xrightarrow{${p(0)}}${p(1)}`;
    case 'row':return `\\text{${escape(v)}: }${p(0)}`;
    case 'rows':return a.map(latexTree).join('\n');
    case 'piecewise':return '\\begin{cases}'+a.map(x=>latexTree(x.args[0])+' & '+latexTree(x.args[1])).join(' \\\\ ')+'\\end{cases}';
    case 'restricted':return p(0);
    case 'quantity':return p(0)+`\\,\\mathrm{${escape(v)}}`;
    case 'text':case 'constant':case 'input-text':try{return latexTree(parse(v));}catch{return `\\text{${escape(v)}}`;}
    default:return v?symbol(v):a.map(latexTree).join(' ');
  }
}
export function latexFormulaTree(tree,digits=10){
  const rounded=node=>({...node,value:['number','float','fixed-number','text'].includes(node.kind)?roundNumber(node.value||'',digits):node.value,args:(node.args||[]).map(rounded)});
  return latexTree(rounded(tree));
}
export function mathCopyText(source,enabled){
  if(!enabled)return source;
  return source.split('\n').map(line=>{if(!line.trim())return line;try{return latexTree(parse(latexInput(line)));}catch{return line;}}).join('\n');
}

/** Native Copy/Cut on math inputs and rendered formulas, using the current option. */
export function bindMathCopy(root,isEnabled){
  const copy=event=>{
    if(!isEnabled()||!event.clipboardData)return;
    const field=event.target.closest?.('input,textarea');
    let text;
    if(field){
      if(!field.matches('#expression,[data-math-copy],#graph-source,#equation-source,#equation-a,#equation-b,#equation-c,#equation-d,#equation-variable,#equation-extra,#equation-initial'))return;
      text=mathCopyText(field.value.slice(field.selectionStart,field.selectionEnd),true);
    }else{
      const selection=root.defaultView.getSelection();if(!selection?.rangeCount)return;
      let target=selection.getRangeAt(0).commonAncestorContainer;if(target.nodeType!==1)target=target.parentElement;
      let formula=target.closest?.('[data-math-copy-node]');
      if(!formula)return;
      while(formula.parentElement?.closest('[data-math-copy-node]')?.textContent.trim()===selection.toString().trim())formula=formula.parentElement.closest('[data-math-copy-node]');
      const stored=mathTrees.get(formula);
      text=formula.textContent.trim()===selection.toString().trim()?latexFormulaTree(stored.tree,stored.digits):mathCopyText(selection.toString(),true);
    }
    if(!text)return;
    event.clipboardData.setData('text/plain',text);event.preventDefault();
    if(event.type==='cut'&&field&&!field.readOnly&&!field.disabled){field.setRangeText('',field.selectionStart,field.selectionEnd,'end');field.dispatchEvent(new root.defaultView.Event('input',{bubbles:true}));}
  };
  root.addEventListener('copy',copy);root.addEventListener('cut',copy);
  return ()=>{root.removeEventListener('copy',copy);root.removeEventListener('cut',copy);};
}
