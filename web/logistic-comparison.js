import {statisticsColumnNames,statisticsNumericCell} from './workspace-commands.js';

export function logisticComparisonSelections(rows,opts){
  const n=Math.max(0,...rows.map(row=>row.length)),response=Number(opts.response)===-1?n-1:Number(opts.response);
  if(!Number.isInteger(response)||response<0||response>=n)throw new Error('Choose valid data columns');
  const choose=(text,excluded)=>text==='auto'?Array.from({length:n},(_,i)=>i).filter(i=>!excluded.includes(i)):String(text).split(',').filter(Boolean).map(Number);
  const base=choose(opts.basePredictors,[response]),added=choose(opts.addedPredictors,[response,...base]);
  if(!added.length||[...base,...added].some(i=>!Number.isInteger(i)||i<0||i>=n||i===response)||new Set([...base,...added]).size!==base.length+added.length)throw new Error('Choose distinct baseline and added predictors');
  return {base,added,response,indices:[...base,...added,response],n};
}
export function logisticComparisonLabels(rows,opts,names=[]){
  const plan=logisticComparisonSelections(rows,opts),labels=names.length?names:statisticsColumnNames(plan.n);
  return {'model:A':plan.base.map(i=>labels[i]).join(' + ')||'Intercept only','model:B':[...plan.base,...plan.added].map(i=>labels[i]).join(' + '),'response':labels[plan.response]};
}
export function logisticComparisonPlan(rows,opts,names=[],validationRows,validationNames=[]){
  const plan=logisticComparisonSelections(rows,opts),missing=cell=>!String(cell??'').trim()||/^(?:NA|NaN|nan|[+-]?Infinity)$/i.test(String(cell).trim());
  const complete=(data,indices)=>data.map(row=>indices.map(i=>statisticsNumericCell(String(row[i]??'').trim()))).filter(row=>!row.some(missing));
  const train=complete(rows,plan.indices);if(!train.length)throw new Error('Complete selected rows required');
  const mode=opts.validation;let argument,validationCount=0;
  const list=values=>`[${values.join(',')}]`,table=values=>list(values.map(list));
  if(mode==='external'){
    if(!validationRows?.length)throw new Error('Choose a validation dataset');
    const plain=label=>String(label).replace(/ \((?:x|y|z|x\d+)\)$/,'');
    const sourceNames=(names.length?names:statisticsColumnNames(plan.n)).map(plain),other=(validationNames.length?validationNames:statisticsColumnNames(validationRows[0].length)).map(plain);
    const indices=plan.indices.map(i=>{const matches=other.flatMap((name,j)=>name===sourceNames[i]?[j]:[]);if(matches.length!==1||sourceNames.filter(name=>name===sourceNames[i]).length!==1)throw new Error('Validation dataset must have matching unique column headers');return matches[0];});
    const selected=complete(validationRows,indices);if(!selected.length)throw new Error('Complete validation rows required');argument=table(selected);validationCount=validationRows.length;
  }else if(mode==='holdout'){if(!(Number(opts.holdout)>0&&Number(opts.holdout)<1))throw new Error('Holdout fraction must be between 0 and 1');argument=String(opts.holdout);}
  else if(mode==='crossvalidation'){if(!/^\d+$/.test(String(opts.folds))||Number(opts.folds)<2)throw new Error('Folds must be at least two');argument=String(opts.folds);}
  else throw new Error('Invalid validation method');
  if(!(Number(opts.threshold)>0&&Number(opts.threshold)<1&&Number(opts.level)>0&&Number(opts.level)<1))throw new Error('Threshold and confidence level must be between 0 and 1');
  if(!/^\d+$/.test(String(opts.resamples))||!/^\d+$/.test(String(opts.seed)))throw new Error('Resamples and seed must be nonnegative integers');
  return {expression:`logisticcompare(${table(train)},${plan.base.length},${mode},${argument},${opts.threshold},${opts.level},${opts.resamples},${opts.seed},[${rows.length},${validationCount}])`,labels:logisticComparisonLabels(rows,opts,names)};
}
