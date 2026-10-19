// Graph source parsing, formula labels, input history, and curve identities.
import {parse,latexInput} from './parser.js';
import {graphExpression} from './function-transfer.js';

export function graphInputTree(source,kind='cartesian'){
  const normalized=latexInput(source);
  let tree;
  try{tree=parse(normalized);}catch(error){
    // A comma separates constraints only in a Cartesian graph source row.
    // Parsing a list keeps nested call/piecewise commas and empty items honest.
    if(kind!=='cartesian'||!normalized.includes(','))throw error;
    let constraints;
    try{constraints=parse(`[${normalized}]`);}catch{throw error;}
    if(constraints.args.length<2||!isGraphInequality(constraints))throw error;
    tree=constraints;
  }
  return kind==='cartesian'?graphExpression(tree):tree;
}

export function isGraphInequality(tree){
  if(tree.kind==='group')return isGraphInequality(tree.args[0]);
  if(['tuple','list'].includes(tree.kind))return tree.args.length>0&&tree.args.every(isGraphInequality);
  return tree.kind==='relation'&&['<','<=','>','>='].includes(tree.value);
}

export function implicitFormula(source){
  try{const tree=parse(latexInput(source));return tree.kind==='relation'?source:`${source}=0`;}catch{return source;}
}

export function cartesianFormula(source,index=0){
  try{
    const tree=parse(latexInput(source)),hasY=node=>node.kind==='symbol'&&node.value==='y'||(node.args||[]).some(hasY);
    if(isGraphInequality(tree)||tree.kind==='relation'||['list','tuple'].includes(tree.kind))return source;
    if(hasY(tree))return `${source}=0`;
  }catch{
    // Bare comma-separated inequalities need delimiters for formula rendering.
    try{if(isGraphInequality(graphInputTree(source)))return `[${source}]`;}catch{}
  }
  return `f${index+1}(x)=${source}`;
}

export function graphExpressionTarget(source,kind='cartesian'){
  const normalized=latexInput(source),tree=parse(normalized);
  const hasZ=node=>node.kind==='symbol'&&node.value==='z'||(node.args||[]).some(hasZ);
  if(kind==='surface'&&tree.kind==='relation'){
    if(tree.args[0].kind==='symbol'&&tree.args[0].value==='z'&&!hasZ(tree.args[1]))return {kind,source:normalized.slice(tree.args[1].start,tree.args[1].end)};
  }
  return {kind,source:normalized};
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

// Occurrences keep duplicate expressions individually switchable.
export function graphVisibilityKeys(sources,kind,role='curve'){
  const occurrences=new Map();
  return sources.map(source=>{const text=source.trim(),n=occurrences.get(text)||0;occurrences.set(text,n+1);return JSON.stringify([kind,role,text,n]);});
}
export function planarTreeKind(tree){
  if(isGraphInequality(tree))return 'inequality';
  if(tree.kind==='relation'&&['=','=='].includes(tree.value)){
    const [head,body]=tree.args;
    if(['symbol','call'].includes(head.kind)&&head.value==='r')return 'polar';
    tree=body;
  }
  return ['list','tuple'].includes(tree.kind)&&tree.args.length===2?'parametric':'cartesian';
}

export function graphRangeAxes(source,kind){
  const rows=graphExpressions(source,kind);
  if(!rows.length)return new Set();
  if(kind==='polar')return new Set(['theta']);
  if(['parametric','space','differential'].includes(kind))return new Set(['t']);
  if(kind!=='cartesian')return new Set();
  const axes=new Set();
  for(const row of rows)try{const type=planarTreeKind(graphInputTree(row));if(type==='polar')axes.add('theta');else if(type==='parametric')axes.add('t');}catch{}
  return axes;
}
