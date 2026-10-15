import {statisticsComparisonData} from './statistics-comparison-data.js';

export const extensionAnalysisIds=new Set(['omega','bayesttest','bayesanova','metaregression','metasubgroup','designpower','designsize','yuen','trimmedanova','winsorcor','robustreg','parametricsurvival']);

export function extensionStatisticsPlan(id,rows,opts,columnLabels=[]){
  const n=Math.max(0,...rows.map(row=>row.length)),labels={};
  const col=key=>{const raw=Number(opts[key]),i=raw===-1?n-1:raw;if(!Number.isInteger(i)||i<0||i>=n)throw new Error('Choose valid data columns');return i;};
  const multi=(key,excluded=[])=>{
    const selected=opts[key]==='auto'?Array.from({length:n},(_,i)=>i).filter(i=>!excluded.includes(i)):String(opts[key]??'').split(',').filter(Boolean).map(Number);
    if(!selected.length||new Set(selected).size!==selected.length||selected.some(i=>!Number.isInteger(i)||i<0||i>=n||excluded.includes(i)))throw new Error('Choose distinct analysis columns');return selected;
  };
  const complete=indices=>{
    if(new Set(indices).size!==indices.length)throw new Error('Roles must use different columns');
    const selected=rows.map(row=>indices.map(i=>String(row[i]??'').trim()));
    if(selected.some(row=>row.some(v=>!v)))throw new Error('Complete selected rows required');return selected;
  };
  const list=values=>'['+values.join(',')+']',table=values=>list(values.map(list));
  const featureLabels=indices=>indices.forEach((at,i)=>{labels[`feature:${i+1}`]=columnLabels[at]||`Feature ${i+1}`;});
  const groupPlan=(all=false,paired=false)=>{
    const plan=statisticsComparisonData(rows,opts,{all,paired,strict:true});
    plan.labels.forEach((at,i)=>{labels[`sample:${i+1}`]=opts.grouping==='groups'?at:columnLabels[Number(at)]||`Sample ${i+1}`;});return plan;
  };
  let expression;
  if(id==='omega'){
    const indices=multi('columns');featureLabels(indices);expression=`omega(${table(complete(indices))},${opts.mode})`;
  }else if(id==='designpower'||id==='designsize'){
    if(['effect','size','alpha'].some(key=>!String(opts[key]??'').trim()))throw new Error('Enter all study design parameters');
    expression=`${id}(${opts.design},${opts.effect},${opts.size},${opts.alpha},${opts.tail},${['proportion','proportion2'].includes(opts.design)?opts.baseline:'0.5'})`;
  }else if(id==='bayesttest'){
    let samples;
    if(opts.design==='onesample'){
      samples=[rows.map(row=>String(row[col('column')]??'').trim()).filter(Boolean),[]];labels['sample:1']=columnLabels[col('column')]||'Sample 1';
    }else samples=groupPlan(false,opts.design==='paired').samples;
    expression=`bayesttest(${samples.map(list).join(',')},${opts.design},${opts.null},${opts.r},${opts.level},${opts.samples},${opts.seed},${opts.sequential})`;
  }else if(id==='bayesanova'||id==='trimmedanova'){
    const groups=groupPlan(true).samples;
    expression=`${id}(${table(groups)},${id==='bayesanova'?`${opts.r},${opts.level},${opts.samples},${opts.seed},${opts.sequential}`:`${opts.trim},${opts.level}`})`;
  }else if(id==='yuen'){
    expression=`yuen(${groupPlan().samples.map(list).join(',')},${opts.trim},${opts.level})`;
  }else if(id==='winsorcor'){
    const pairs=complete([col('first'),col('second')]);expression=`winsorcor(${list(pairs.map(row=>row[0]))},${list(pairs.map(row=>row[1]))},${opts.trim})`;
  }else if(id==='robustreg'){
    const response=col('response'),predictors=multi('predictors',[response]);featureLabels(predictors);
    expression=`robustreg(${table(complete([...predictors,response]))},${opts.tuning})`;
  }else if(id==='metaregression'||id==='metasubgroup'){
    const reserved=opts.layout==='binary'?['eventsA','totalA','eventsB','totalB'].map(col):opts.layout==='continuous'?['meanA','sdA','nA','meanB','sdB','nB'].map(col):[col('effect'),col('se')];let data;
    if(id==='metaregression'){
      const predictors=multi('predictors',reserved);featureLabels(predictors);data=complete([...reserved,...predictors]);
    }else{
      data=complete([...reserved,col('group')]);const groups=[...new Set(data.map(row=>row[reserved.length]))];
      groups.forEach((group,i)=>{labels[`group:${i+1}`]=group;});data=data.map(row=>[...row.slice(0,reserved.length),String(groups.indexOf(row[reserved.length])+1)]);
    }
    expression=`${id}(${table(data)},${opts.method},${opts.level},${opts.method==='fixed'?'z':opts.inference}${opts.layout==='binary'?`,${opts.measure},${opts.correction}`:opts.layout==='continuous'?`,${opts.continuousMeasure}`:''})`;
  }else if(id==='parametricsurvival'){
    const reserved=[col('time'),col('event'),...(opts.truncation==='entry'?[col('entry')]:[])];
    const predictors=opts.covariates==='selected'?multi('predictors',reserved):[];featureLabels(predictors);
    let selected=complete([...reserved,...predictors]);const states=new Set(selected.map(row=>row[1]));
    if(!String(opts.eventValue).trim())throw new Error('Enter the event value');
    if(states.size>2||states.size>1&&!states.has(opts.eventValue))throw new Error('Event column must have at most two values and contain the event value');
    selected=selected.map(row=>[row[0],row[1]===opts.eventValue?'1':'0',...row.slice(2)]);
    expression=`parametricsurvival(${table(selected)},${opts.family},${opts.level},${opts.truncation==='entry'?2:-1},${opts.horizon})`;
  }else throw new Error('Unknown analysis form');
  return {expression,labels};
}
