// Graph source parsing, formula labels, input history, and curve identities.
import {parse,latexInput} from './parser.js';
import {graphExpression} from './function-transfer.js';

export function graphInputTree(source,kind='cartesian'){
  const tree=parse(latexInput(source));
  return kind==='cartesian'?graphExpression(tree):tree;
}

export function implicitFormula(source){
  try{const tree=parse(latexInput(source));return tree.kind==='relation'?source:`${source}=0`;}catch{return source;}
}

export function cartesianFormula(source,index=0){
  try{
    const tree=parse(latexInput(source)),hasY=node=>node.kind==='symbol'&&node.value==='y'||(node.args||[]).some(hasY);
    if(tree.kind==='relation')return source;
    if(hasY(tree))return `${source}=0`;
  }catch{}
  return `f${index+1}(x)=${source}`;
}

export function graphExpressionTarget(source){
  const normalized=latexInput(source),tree=parse(normalized);
  const hasVector=node=>['list','tuple'].includes(node.kind)&&node.args.length===3||(node.args||[]).some(hasVector);
  if(hasVector(tree))return {kind:'space',source:normalized};
  const hasZ=node=>node.kind==='symbol'&&node.value==='z'||(node.args||[]).some(hasZ);
  if(tree.kind==='relation'){
    if(!['=','=='].includes(tree.value))throw new Error('Graph an expression, y = f(x), or an equation F(x,y)=0');
    if(tree.args[0].kind==='symbol'&&tree.args[0].value==='z'&&!hasZ(tree.args[1]))return {kind:'surface',source:normalized.slice(tree.args[1].start,tree.args[1].end)};
  }
  return {kind:hasZ(tree)?'surface':'cartesian',source:normalized};
}

export function isImplicitSurface(source){
  try{
    const tree=parse(latexInput(source)),hasZ=node=>node.kind==='symbol'&&node.value==='z'||(node.args||[]).some(hasZ);
    return tree.kind==='relation'?!(tree.args[0].kind==='symbol'&&tree.args[0].value==='z'&&!hasZ(tree.args[1])):hasZ(tree);
  }catch{return false;}
}

export function surfaceFormula(source){
  try{if(parse(latexInput(source)).kind==='relation')return source;}catch{}
  return isImplicitSurface(source)?`${source}=0`:`z=${source}`;
}

export function parametricFormula(source,index,space=false){
  try{if(parse(latexInput(source)).kind==='relation')return source;}catch{}
  return `${space?'C':'f'}${index+1}(t)=${source}`;
}

export function splitTopLevel(source){
  const values=[];let depth=0,start=0;
  for(let i=0;i<source.length;i++){if('([{'.includes(source[i]))depth++;if(')]}'.includes(source[i]))depth--;if(source[i]===','&&!depth){values.push(source.slice(start,i).trim());start=i+1;}}
  values.push(source.slice(start).trim());return values.filter(Boolean);
}

export const graphCurveLimit=kind=>kind==='differential'?1:['surface','space'].includes(kind)?5:20;

export const graphSourceLimit=kind=>kind==='differential'?1:['surface','space'].includes(kind)?5:24;

export const hasImplicitSurface=source=>graphSources(source,'surface').some(isImplicitSurface);

export function graphSources(source,kind){
  return source.split(/\r?\n/).map(s=>s.trim()).filter(Boolean).slice(0,graphSourceLimit(kind));
}

export function isGraphShading(source){return /^\[(?:shade|s)\]/.test(source.trim());}

export function graphShadingBody(source){return source.trim().replace(/^\[(?:shade|s)\]/,'').trim();}

export function graphExpressions(source,kind){
  return graphSources(source,kind).filter(s=>!isGraphShading(s)).slice(0,graphCurveLimit(kind)).map(s=>s.replace(kind==='differential'?/^dy\/dt\s*=\s*/:kind==='sequence'?/^u\(n\)\s*=\s*/:kind==='polar'?/^r\s*=\s*/:/^\s*=/,''));
}

export function appendGraphSource(existing,source,kind='cartesian'){
  const lines=existing.split(/\r?\n/).filter(line=>line.trim());
  const limit=graphCurveLimit(kind);
  if(lines.some(line=>line.trim()===source.trim()))return existing;
  if(lines.length>=graphSourceLimit(kind)||lines.filter(line=>!isGraphShading(line)).length>=limit)throw new Error('Graph limit reached. Remove a function before adding another.');
  return existing.trimEnd()+(lines.length?'\n':'')+source;
}

export function removeGraphSource(existing,index,kind='cartesian',shading=false){
  const lines=existing.split(/\r?\n/),visible=lines.map((source,index)=>({source,index})).filter(line=>line.source.trim()).slice(0,graphSourceLimit(kind));
  const target=visible.filter(line=>isGraphShading(line.source)===shading).slice(0,shading?4:graphCurveLimit(kind))[index];
  return target?lines.filter((_,i)=>i!==target.index).join('\n'):existing;
}

export function removeGraphInputLine(source,index){
  const lines=source.split(/\r?\n/);
  return index>=0&&index<lines.length?lines.filter((_,i)=>i!==index).join('\n'):source;
}

export function createGraphInputHistory(){
  const histories=new Map();
  return {
    remember(kind,snapshot){
      const history=histories.get(kind)||[],last=history.at(-1);
      if(last?.source===snapshot.source&&last.derivative===snapshot.derivative&&last.secondDerivative===snapshot.secondDerivative)return;
      history.push(structuredClone(snapshot));if(history.length>100)history.shift();histories.set(kind,history);
    },
    undo:kind=>histories.get(kind)?.pop(),
    canUndo:kind=>!!histories.get(kind)?.length
  };
}

export function graphSelectedCurveIndex(sourceIndex,derivativeOrder=0,derivativeIndex=-1,secondDerivativeIndex=-1){
  return derivativeOrder===1?derivativeIndex:derivativeOrder===2?secondDerivativeIndex:sourceIndex;
}

export function graphAnalysisTarget(curve,derivative,secondDerivative){
  if(curve===-1)return derivative===null?null:{source:derivative,order:1};
  if(curve===-2)return secondDerivative===null?null:{source:secondDerivative,order:2};
  return curve>=0?{source:curve,order:0}:null;
}

export function graphAnalysisCurves(count,derivative,secondDerivative){
  const curves=Array.from({length:count},(_,i)=>({key:i,label:`f${i+1}`}));
  if(derivative!==null&&derivative>=0&&derivative<count)curves.push({key:-1,label:`f${derivative+1}′`});
  if(secondDerivative!==null&&secondDerivative>=0&&secondDerivative<count)curves.push({key:-2,label:`f${secondDerivative+1}″`});
  return curves;
}
