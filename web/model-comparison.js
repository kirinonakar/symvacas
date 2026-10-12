import {statisticsColumnNames,statisticsNumericCell} from './workspace-commands.js';

export function modelComparisonRoles(opts){return opts.family==='cox'?['time','event']:['lmm','glmm','gee'].includes(opts.family)?['subject','response']:['response'];}
export function modelComparisonPlan(rows,opts,names=[],validationRows,validationNames=[]){
  const width=Math.max(0,...rows.map(row=>row.length)),family=opts.family,labels=names.length?names:statisticsColumnNames(width);
  const column=key=>{let at=Number(opts[key]);if(at===-1)at=width-1;if(!Number.isInteger(at)||at<0||at>=width)throw new Error('Choose valid data columns');return at;};
  const choose=(text,excluded=[])=>{
    const values=text==='auto'?Array.from({length:width},(_,i)=>i).filter(i=>!excluded.includes(i)):String(text).split(',').filter(value=>value.trim()).map(Number);
    if(new Set(values).size!==values.length||values.some(i=>!Number.isInteger(i)||i<0||i>=width||excluded.includes(i)))throw new Error('Choose distinct baseline and added predictors');return values;
  };
  const list=values=>`[${values.join(',')}]`,table=values=>list(values.map(list));
  const pairs=text=>{
    if(!String(text||'').trim())return '[]';
    const values=String(text).split(';').map(pair=>pair.split(',').map(value=>value.trim()));
    if(values.some(pair=>pair.length!==2||pair.some(value=>!/^\d+$/.test(value)||Number(value)<1)))throw new Error('Use positive model parameter pairs separated by semicolons');return table(values);
  };
  const numeric=/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$/;
  const complete=(data,indices)=>data.map(row=>indices.map(i=>statisticsNumericCell(String(row[i]??'').trim()))).filter(row=>!row.some(value=>!value||/^(?:NA|NaN|[+-]?Infinity)$/i.test(value)));
  let indices,base=[],added=[],optionPairs=[],mode=opts.validation,argument=mode==='holdout'?opts.holdout:mode==='crossvalidation'?opts.folds:'0',resamples=opts.resamples;
  const labelMap={};
  if(['cfa','sem'].includes(family)){
    indices=choose(opts.indicators);if(!indices.length)throw new Error('Select common observed indicators');
    const factors=String(opts.factors).trim().replace(/^\[(.*)\]$/,'$1').split(',').map(value=>value.trim());
    if(factors.length!==indices.length||factors.some(value=>!/^\d+$/.test(value)||Number(value)<1))throw new Error('Factor ID count must match selected indicators');
    optionPairs=[['factors',list(factors)],['estimator',opts.estimator],...['basepaths','addedpaths','basecross','addedcross','baseresidual','addedresidual'].map(key=>[key,pairs(opts[key])])];mode='fit';resamples='0';argument='0';
    labelMap['model:A']=indices.map(i=>labels[i]).join(', ');labelMap['model:B']=labelMap['model:A'];
  }else{
    const roles=modelComparisonRoles(opts),reserved=roles.map(column);if(new Set(reserved).size!==reserved.length)throw new Error('Roles must use different columns');
    base=choose(opts.basePredictors,reserved);added=choose(opts.addedPredictors,[...reserved,...base]);if(!added.length)throw new Error('Choose at least one added predictor');
    const leading=family==='cox'?reserved:['lmm','glmm','gee'].includes(family)?[column('subject')]:[];
    indices=[...leading,...base,...added,...(family==='cox'?[]:[column('response')])];
    labelMap['model:A']=base.map(i=>labels[i]).join(' + ')||'Intercept only';labelMap['model:B']=[...base,...added].map(i=>labels[i]).join(' + ');labelMap.response=labels[family==='cox'?column('event'):column('response')];
    added.forEach((i,j)=>labelMap[`candidate:${j+1}`]=labels[i]);
    [...base,...added].forEach((i,j)=>labelMap[`x${j+1}`]=labels[i]);
    if(['lmm','glmm','gee'].includes(family)){mode='fit';resamples='0';argument='0';}
    if(['logistic','mlclassification'].includes(family))optionPairs.push(['threshold',opts.threshold]);
    if(family==='cox')optionPairs.push(['ties',opts.ties]);
    if(['lmm','glmm'].includes(family)){
      const slope=text=>{if(!/^\d+$/.test(String(text)))throw new Error('Random slope position must be a nonnegative integer');return String(text);};
      optionPairs.push(['randoma',slope(opts.randomA)],['randomb',opts.randomB==='same'?slope(opts.randomA):slope(opts.randomB)]);
    }
    if(['glmm','gee'].includes(family))optionPairs.push(['responsefamily',opts.responsefamily]);
    if(family==='glmm')optionPairs.push(['points',opts.points]);
    if(family==='gee')optionPairs.push(['correlation',opts.correlation]);
    if(['mlclassification','mlregression'].includes(family))optionPairs.push(['algorithm',opts.algorithm],['alpha',opts.alpha],['ratio',opts.ratio],['trees',opts.trees],['depth',opts.depth],['forestseed',opts.seed]);
  }
  let selected=complete(rows,indices),other;
  if(['lmm','glmm','gee'].includes(family)){
    const ids=[...new Set(selected.map(row=>row[0]))];selected=selected.map(row=>[String(ids.indexOf(row[0])+1),...row.slice(1)]);
  }
  if(selected.some(row=>row.some(value=>!numeric.test(value))))throw new Error('Enter finite numeric data');
  if(!selected.length)throw new Error('Complete selected rows required');
  optionPairs.push(['excludedrows',String(rows.length-selected.length)]);
  if(mode==='external'){
    if(!validationRows?.length)throw new Error('Choose a validation dataset');
    const plain=text=>String(text).replace(/ \((?:x|y|z|x\d+)\)$/,'');
    const source=labels.map(plain),otherNames=(validationNames.length?validationNames:statisticsColumnNames(validationRows[0].length)).map(plain);
    const at=indices.map(i=>{const found=otherNames.flatMap((name,j)=>name===source[i]?[j]:[]);if(found.length!==1||source.filter(name=>name===source[i]).length!==1)throw new Error('Validation dataset must have matching unique column headers');return found[0];});
    other=complete(validationRows,at);if(!other.length)throw new Error('Complete validation rows required');argument=table(other);optionPairs.push(['excludedvalidation',String(validationRows.length-other.length)]);
  }
  // Numeric and enumeration options are emitted as AST data, never executable text.
  const safe=/^[\p{L}][\p{L}\p{N}_]*$|^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$|^\[[\d,\[\]\s]*\]$/u;
  if([family,mode,String(argument).startsWith('[')?'0':argument,opts.level,resamples,opts.seed,...optionPairs.flat()].some(value=>!safe.test(String(value))))throw new Error('Invalid model comparison option');
  const options=table(optionPairs),candidates=['cfa','sem'].includes(family)?'0':opts.candidates;
  if(!['0','1'].includes(String(candidates)))throw new Error('Invalid candidate comparison mode');
  return {expression:`modelcompare(${table(selected)},${base.length},${family},${mode},${argument},${opts.level},${resamples},${opts.seed},${options},${candidates})`,labels:labelMap};
}
