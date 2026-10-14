import {element,control} from './app-ui.js';
import {t,setText} from './i18n.js';
import {appendPlotExportButtons} from './svg-export.js';
import {semDiagramSvg} from './statistics-sem-diagram.js';
import {logisticComparisonPlot} from './logistic-comparison-plot.js';

const ns='http://www.w3.org/2000/svg';
const activeCharts=new Map();
globalThis.addEventListener?.('resize',()=>{for(const [view,draw] of activeCharts){if(view.isConnected)draw();else activeCharts.delete(view);}});
const number=value=>Number(value).toLocaleString(undefined,{maximumSignificantDigits:4});
const pc=(plot,index)=>plot.axisLabels?.[index]?.replace(/^(Component|Factor) (\d+)$/,(_,label,n)=>`${t(label)} ${n}`)||(['clusters','interaction'].includes(plot.kind)?(plot.features?.[index]||`Feature ${index+1}`).replace(/^Feature (\d+)$/,`${t('Feature')} $1`):`PC${index+1} (${number(100*plot.ratios[index])}%)`);

// Keep large forest canvases bounded while retaining every study and the pooled row.
export function statisticsIntervalPage(plot,page=0,pageSize=40){
  if(!Number.isInteger(plot.summaryIndex)||plot.rows.length<=pageSize+1)return plot;
  const studies=plot.rows.map((_,i)=>i).filter(i=>i!==plot.summaryIndex);
  const at=Math.max(0,Math.min(Math.floor(page),Math.ceil(studies.length/pageSize)-1));
  const indices=[...studies.slice(at*pageSize,(at+1)*pageSize),plot.summaryIndex];
  return {...plot,rows:indices.map(i=>plot.rows[i]),weights:indices.map(i=>plot.weights?.[i]??0),summaryIndex:indices.length-1};
}

// Raw engine arrays retain every observation and all component coordinates.
export function statisticsPlotModel(plot,xAxis=0,yAxis=1){
  if(plot.kind==='research-scatter'){
    const points=plot.points.map(([x,y],i)=>({x,y,label:plot.labels?.[i]||`${t('Observation')} ${i+1}`}));
    if(!points.length)return null;
    const lines=plot.lines||[],horizontal=plot.horizontal||[],all=[...plot.points,...lines.flat(),...(plot.trend||[])];
    const xs=all.map(p=>p[0]),ys=[...all.map(p=>p[1]),...horizontal];
    const lo=Math.min(...xs),hi=Math.max(...xs),low=Math.min(...ys),high=Math.max(...ys);
    const dx=(hi-lo||1)*.1,dy=(high-low||1)*.1;
    return {xmin:lo-dx,xmax:hi+dx,ymin:plot.invertY?0:low-dy,ymax:high+dy,points,lines,horizontal,invertY:!!plot.invertY,
      trend:plot.trend||[],xlabel:t(plot.xlabel),ylabel:t(plot.ylabel)};
  }
  if(plot.kind==='timeseries'){
    const all=[...plot.observed,...plot.fitted,...plot.forecast,...plot.interval.flatMap(([x,lo,hi])=>[[x,lo],[x,hi]])];
    if(!all.length)return null;
    const xs=all.map(row=>row[0]),ys=all.map(row=>row[1]);if(Number.isFinite(plot.reference))ys.push(plot.reference);
    const lo=ys.reduce((a,b)=>Math.min(a,b)),hi=ys.reduce((a,b)=>Math.max(a,b)),pad=(hi-lo||1)*.1;
    return {xmin:xs.reduce((a,b)=>Math.min(a,b)),xmax:xs.reduce((a,b)=>Math.max(a,b))+.5,ymin:lo-pad,ymax:hi+pad,
      series:[plot.observed,plot.fitted,plot.forecast],band:plot.interval,boundary:plot.boundary,reference:plot.reference,
      timeLabels:plot.timeLabels,tickLabels:plot.timeTickLabels||plot.timeLabels,
      xlabel:t(plot.timeLabels?'Date':'Time index'),ylabel:t('Value')};
  }
  if(plot.kind==='acf')return {xmin:.5,xmax:plot.values.length+.5,ymin:Math.min(-1,-plot.bound*1.1),ymax:Math.max(1,plot.bound*1.1),
    stems:plot.values.map((y,i)=>[i+1,y]),bounds:[-plot.bound,plot.bound],xlabel:t('Lag'),ylabel:t('Autocorrelation')};
  if(plot.kind==='intervals'){
    const rows=plot.rows.filter(row=>row.slice(1).every(Number.isFinite));
    if(!rows.length)return null;
    const bounds=[...rows.flatMap(row=>row.slice(1)),...(plot.thresholds||[])];if(Number.isFinite(plot.reference))bounds.push(plot.reference);
    const lo=plot.domain?.[0]??Math.min(...bounds),hi=plot.domain?.[1]??Math.max(...bounds),pad=plot.domain?0:(hi-lo||1)*.1;
    return {xmin:lo-pad,xmax:hi+pad,ymin:0,ymax:rows.length+1,intervals:rows.map(([label,estimate,lower,upper],i)=>({label,estimate,lower,upper,y:rows.length-i,summary:i===plot.summaryIndex,weight:plot.weights?.[i]})),reference:plot.reference,thresholds:plot.thresholds||[],xlabel:t(plot.xlabel||'Estimate & interval'),ylabel:''};
  }
  if(plot.kind==='bars')return {xmin:.5,xmax:plot.values.length+.5,ymin:0,ymax:plot.maximum||Math.max(1e-12,...plot.values,...(plot.secondary||[]))*1.15,
    bars:plot.values.map((value,i)=>({x:i+1,y:value,label:`${plot.labels[i]}: ${number(value)}`})),secondary:plot.secondary,reference:plot.reference,xlabel:t('Observation / fold'),ylabel:t(plot.ylabel)};
  if(plot.kind==='scree'){
    let cumulative=0;
    return {xmin:.5,xmax:plot.ratios.length+.5,ymin:0,ymax:100,
      bars:plot.ratios.map((value,i)=>({x:i+1,y:100*value,label:`PC${i+1}: ${number(100*value)}% · λ=${number(plot.eigenvalues[i])}`})),
      line:plot.ratios.map((value,i)=>[i+1,100*(cumulative+=value)]),xlabel:t('Component'),ylabel:'%'};
  }
  if(['histogram','distribution'].includes(plot.kind)){
    const markers=plot.kind==='histogram'?[...plot.interval,plot.estimate]:[];
    const low=Math.min(plot.edges[0],...markers),high=Math.max(plot.edges.at(-1),...markers),padding=(high-low||1)*.025;
    return {xmin:low-padding,xmax:high+padding,ymin:0,ymax:Math.max(1,...plot.counts)*1.1,
      bars:plot.counts.map((value,i)=>({x:(plot.edges[i]+plot.edges[i+1])/2,y:value,width:plot.edges[i+1]-plot.edges[i],label:`${number(plot.edges[i])} – ${number(plot.edges[i+1])}: ${value}`})),
      markers,zero:!!plot.groupLabels&&low-padding<=0&&high+padding>=0,xlabel:t(plot.statistic||'Value'),ylabel:t(plot.kind==='distribution'?'Count':'Draws')};
  }
  const width=plot.points[0]?.length||0;
  if(!width)return null;
  xAxis=Math.min(Math.max(0,xAxis),width-1);yAxis=width>1?Math.min(Math.max(0,yAxis),width-1):-1;
  const points=plot.points.map((row,i)=>({x:row[xAxis],y:yAxis<0?0:row[yAxis],group:plot.assignments?.[i],label:plot.labels?.[i]||`${t('Observation')} ${i+1}`}));
  let xmin=Math.min(0,...points.map(p=>p.x)),xmax=Math.max(0,...points.map(p=>p.x));
  let ymin=Math.min(0,...points.map(p=>p.y)),ymax=Math.max(0,...points.map(p=>p.y));
  const dx=(xmax-xmin||1)*.14,dy=(ymax-ymin||1)*.14;
  if(plot.kind==='loadings'){const limit=Math.max(1.2,1.1*Math.max(...points.flatMap(point=>[Math.abs(point.x),Math.abs(point.y)])));xmin=ymin=-limit;xmax=ymax=limit;}
  else{xmin-=dx;xmax+=dx;ymin-=dy;ymax+=dy;}
  const centroids=plot.centroids?.map((row,i)=>({x:row[xAxis],y:yAxis<0?0:row[yAxis],group:i+1}));
  return {xmin,xmax,ymin,ymax,points,centroids,referenceLine:plot.referenceLine,vectors:plot.kind==='loadings',xlabel:plot.kind==='qq'?t('Theoretical normal quantiles'):pc(plot,xAxis),ylabel:plot.kind==='qq'?t('Ordered sample values'):yAxis<0?'':pc(plot,yAxis)};
}

function chart(plot,xAxis,yAxis,displayWidth){
  if(plot.kind==='sem-diagram')return semDiagramSvg(plot);
  const model=statisticsPlotModel(plot,xAxis,yAxis);
  const height=model?.intervals?Math.max(240,model.intervals.length*32+90):340,width=Math.max(320,Math.min(620,displayWidth||(globalThis.innerWidth||720)-56));
  const svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox',`0 0 ${width} ${height}`);svg.setAttribute('role','img');
  svg.setAttribute('aria-label',t(plot.title));svg.style.cssText='width:100%;height:auto;min-width:260px;display:block;background:var(--number);border-radius:8px';
  if(!model)return svg;
  const {xmin,xmax,ymin,ymax}=model,left=model.intervals?(width<400?128:170):64,top=22,w=width-left-30,h=height-82;
  const px=x=>left+w*(x-xmin)/(xmax-xmin),py=y=>top+(model.invertY?0:h)+(model.invertY?1:-1)*h*(y-ymin)/(ymax-ymin);
  function shape(tag,attrs,text=''){
    const node=document.createElementNS(ns,tag);for(const [key,value]of Object.entries(attrs))node.setAttribute(key,String(value));node.textContent=text;svg.append(node);return node;
  }
  const text=(x,y,label,anchor='middle')=>shape('text',{x,y,fill:'var(--muted)','font-size':12,'text-anchor':anchor},label);
  for(let i=0;i<=4;i++){
    const y=ymin+(ymax-ymin)*i/4;
    shape('line',{x1:left,x2:left+w,y1:py(y),y2:py(y),stroke:'var(--line)'});if(!model.intervals)text(left-8,py(y)+4,number(y),'end');
    if(!model.timeLabels&&!['scree','bars','interaction'].includes(plot.kind)){const x=xmin+(xmax-xmin)*i/4;text(px(x),top+h+20,number(x));}
  }
  if(model.timeLabels){
    const count=width<460?2:4;
    const indices=[...new Set(Array.from({length:count+1},(_,i)=>Math.round(xmin+(Math.floor(xmax)-xmin)*i/count)))];
    for(const x of indices)text(px(x),top+h+20,model.tickLabels[x-1]||String(x));
  }
  const barWidth=['scree','bars'].includes(plot.kind) ? .65 : (model.bars?.[0]?.width||0);
  for(const bar of model.bars||[]){
    const node=shape('rect',{x:px(bar.x-(bar.width||barWidth)/2),y:py(bar.y),width:Math.max(.5,w*(bar.width||barWidth)/(xmax-xmin)-1),height:py(0)-py(bar.y),fill:'var(--accent)',opacity:.72});
    const title=document.createElementNS(ns,'title');title.textContent=bar.label;node.append(title);
    if(plot.kind==='scree')text(px(bar.x),top+h+20,`PC${bar.x}`);
    if(plot.kind==='bars'){
      text(px(bar.x),top+h+20,plot.labels[bar.x-1]);
      if(model.secondary){const node=shape('circle',{cx:px(bar.x),cy:py(model.secondary[bar.x-1]),r:4,fill:'var(--gold)'});const title=document.createElementNS(ns,'title');title.textContent=`${t('Raw p')}: ${number(model.secondary[bar.x-1])}`;node.append(title);}
    }
  }
  if(Number.isFinite(model.reference)){
    const vertical=!!model.intervals;shape('line',vertical?{x1:px(model.reference),x2:px(model.reference),y1:top,y2:top+h,stroke:'var(--muted)','stroke-dasharray':'5 4'}:{x1:left,x2:left+w,y1:py(model.reference),y2:py(model.reference),stroke:'var(--muted)','stroke-dasharray':'5 4'});
  }
  for(const row of model.intervals||[]){
    text(left-10,py(row.y)+4,row.label.length>21?row.label.slice(0,20)+'…':row.label,'end');
    const clip=value=>Math.max(xmin,Math.min(xmax,value));
    if(row.upper>=xmin&&row.lower<=xmax)shape('line',{x1:px(clip(row.lower)),x2:px(clip(row.upper)),y1:py(row.y),y2:py(row.y),stroke:'var(--accent)','stroke-width':3});
    for(const end of [row.lower,row.upper].filter(value=>value>=xmin&&value<=xmax))shape('line',{x1:px(end),x2:px(end),y1:py(row.y)-5,y2:py(row.y)+5,stroke:'var(--accent)','stroke-width':2});
    const side=Number.isFinite(row.weight)?Math.max(4,Math.min(18,2*Math.sqrt(row.weight))):8;
    const outside=row.estimate<xmin||row.estimate>xmax,tip=px(clip(row.estimate)),tail=tip+(row.estimate<xmin?8:-8);
    const node=outside?shape('polygon',{points:`${tip},${py(row.y)} ${tail},${py(row.y)-5} ${tail},${py(row.y)+5}`,fill:'var(--gold)','data-outside-range':'true'}):row.summary?shape('polygon',{points:[[row.lower,row.y],[row.estimate,row.y+.22],[row.upper,row.y],[row.estimate,row.y-.22]].map(([x,y])=>`${px(x)},${py(y)}`).join(' '),fill:'var(--gold)'}):Number.isFinite(row.weight)?shape('rect',{x:px(row.estimate)-side/2,y:py(row.y)-side/2,width:side,height:side,fill:'var(--accent)'}):shape('circle',{cx:px(row.estimate),cy:py(row.y),r:4,fill:'var(--gold)'});
    const title=document.createElementNS(ns,'title');title.textContent=`${row.label}: ${number(row.estimate)} [${number(row.lower)}, ${number(row.upper)}]${Number.isFinite(row.weight)?` · ${number(row.weight)}%`:''}`;node.append(title);
  }
  for(const value of model.thresholds||[])shape('line',{x1:px(value),x2:px(value),y1:top,y2:top+h,stroke:'var(--danger)','stroke-width':2,'stroke-dasharray':'6 4'});
  for(const line of model.lines||[])shape('polyline',{points:line.map(([x,y])=>`${px(x)},${py(y)}`).join(' '),fill:'none',stroke:'var(--muted)','stroke-width':1.6,'stroke-dasharray':'5 4'});
  for(const [index,value] of (model.horizontal||[]).entries())shape('line',{x1:left,x2:left+w,y1:py(value),y2:py(value),stroke:index===0?'var(--gold)':'var(--muted)','stroke-width':1.8,...(index?{'stroke-dasharray':'5 4'}:{})});
  if(model.trend?.length)shape('polyline',{points:model.trend.map(([x,y])=>`${px(x)},${py(y)}`).join(' '),fill:'none',stroke:'var(--accent)','stroke-width':2.5,'data-proportional-bias':'true'});
  if(plot.kind==='interaction'){
    plot.xLabels.forEach((label,i)=>text(px(i+1),top+h+20,label));
    plot.lineGroups.forEach((line,i)=>shape('polyline',{points:line.map(([x,y])=>`${px(x)},${py(y)}`).join(' '),fill:'none',stroke:['var(--accent)','var(--gold)','#9466b8','#437db0','#bd5c67','#598e85'][i%6],'stroke-width':2.5}));
  }
  if(model.band?.length){
    const points=[...model.band.map(([x,lo,hi])=>[x,hi]),...model.band.slice().reverse().map(([x,lo])=>[x,lo])];
    shape('polygon',{points:points.map(([x,y])=>`${px(x)},${py(y)}`).join(' '),fill:'var(--gold)',opacity:.18});
    if(model.band.length===1){const [x,lo,hi]=model.band[0];shape('line',{x1:px(x),x2:px(x),y1:py(lo),y2:py(hi),stroke:'var(--gold)','stroke-width':3});}
  }
  if(Number.isFinite(model.boundary))shape('line',{x1:px(model.boundary),x2:px(model.boundary),y1:top,y2:top+h,stroke:'var(--muted)','stroke-dasharray':'5 4'});
  for(const [i,series] of (model.series||[]).entries()){
    const color=['var(--accent)','var(--muted)','var(--gold)'][i];
    shape('polyline',{points:series.map(([x,y])=>`${px(x)},${py(y)}`).join(' '),fill:'none',stroke:color,'stroke-width':i===1?1.5:2.5,...(i===1?{'stroke-dasharray':'4 3'}:{})});
    series.forEach(([x,y])=>{const node=shape('circle',{cx:px(x),cy:py(y),r:2,fill:color}),title=document.createElementNS(ns,'title');title.textContent=`${model.timeLabels?.[x-1]||number(x)} · ${t(['Observed','Fitted','Forecast'][i])}: ${number(y)}`;node.append(title);});
  }
  for(const bound of model.bounds||[])shape('line',{x1:left,x2:left+w,y1:py(bound),y2:py(bound),stroke:'var(--muted)','stroke-dasharray':'5 4'});
  for(const [x,y] of model.stems||[])shape('line',{x1:px(x),x2:px(x),y1:py(0),y2:py(y),stroke:'var(--accent)','stroke-width':2});
  if(model.stems)shape('line',{x1:left,x2:left+w,y1:py(0),y2:py(0),stroke:'var(--muted)'});
  if(model.line)shape('polyline',{points:model.line.map(([x,y])=>`${px(x)},${py(y)}`).join(' '),fill:'none',stroke:'var(--gold)','stroke-width':2.5});
  if(model.points){
    if(plot.kind!=='research-scatter'){
      shape('line',{x1:px(0),x2:px(0),y1:top,y2:top+h,stroke:'var(--line)'});
      shape('line',{x1:left,x2:left+w,y1:py(0),y2:py(0),stroke:'var(--line)'});
    }
    model.points.forEach((point,i)=>{
      const palette=['var(--accent)','var(--gold)','#9466b8','#437db0','#bd5c67','#598e85'];
      const color=model.vectors?palette[i%palette.length]:point.group?palette[(point.group-1)%palette.length]:'var(--accent)';
      if(model.vectors){
        shape('line',{x1:px(0),y1:py(0),x2:px(point.x),y2:py(point.y),stroke:color,'stroke-width':2});
        const angle=Math.atan2(py(point.y)-py(0),px(point.x)-px(0));
        const tip=[px(point.x),py(point.y)],a=[tip[0]-8*Math.cos(angle-.45),tip[1]-8*Math.sin(angle-.45)],b=[tip[0]-8*Math.cos(angle+.45),tip[1]-8*Math.sin(angle+.45)];
        shape('polygon',{points:[tip,a,b].map(p=>p.join(',')).join(' '),fill:color});
        text(px(point.x)+5,py(point.y)-7,String(i+1),'start');
      }
      const node=shape('circle',{cx:px(point.x),cy:py(point.y),r:model.vectors?2:3,fill:color,opacity:.8});
      const title=document.createElementNS(ns,'title');title.textContent=`${point.label}${point.group?` · ${t('Cluster')} ${point.group}`:''}: ${number(point.x)}, ${number(point.y)}`;node.append(title);
    });
  }
  for(const point of model.centroids||[])shape('path',{d:`M${px(point.x)-6},${py(point.y)} L${px(point.x)+6},${py(point.y)} M${px(point.x)},${py(point.y)-6} L${px(point.x)},${py(point.y)+6}`,stroke:'var(--ink)','stroke-width':3});
  if(model.referenceLine)shape('polyline',{points:model.referenceLine.map(([x,y])=>`${px(x)},${py(y)}`).join(' '),fill:'none',stroke:'var(--gold)','stroke-width':2});
  for(const [i,value]of (model.markers||[]).entries())shape('line',{x1:px(value),x2:px(value),y1:top,y2:top+h,stroke:i===2?'var(--gold)':'var(--ink)','stroke-width':1.8,'stroke-dasharray':i===2?'3 3':'6 4'});
  if(model.zero)shape('line',{x1:px(0),x2:px(0),y1:top,y2:top+h,stroke:'var(--muted)','stroke-width':1.4});
  text(left+w/2,height-14,model.xlabel);text(left,14,model.ylabel,'start');
  return svg;
}

export function renderStatisticsVisualizations(container,plots=[]){
  for(const view of activeCharts.keys())if(!view.isConnected)activeCharts.delete(view);
  for(const plot of plots){
    if(['roc-comparison','calibration-comparison'].includes(plot.kind)){container.append(logisticComparisonPlot(plot));continue;}
    const block=element('section','','statistics-visualization');block.append(element('h4',t(plot.title)));
    const view=element('div');if(plot.kind==='sem-diagram')view.style.cssText='overflow-x:auto;max-width:100%';
    let x=0,y=(plot.points?.[0]?.length||0)>1?1:-1,sample=0,fitToScreen=false,page=0;
    const pages=Number.isInteger(plot.summaryIndex)?Math.ceil((plot.rows.length-1)/40):1;
    const selected=()=>pages>1?statisticsIntervalPage(plot,page):plot.series?{...plot,...plot.series[sample]}:plot;
    const draw=()=>{const svg=plot.kind==='sem-diagram'?semDiagramSvg(selected(),{fitToScreen,viewportWidth:view.clientWidth||container.clientWidth||(globalThis.innerWidth||720)-56,viewportHeight:(globalThis.innerHeight||800)*.65}):chart(selected(),x,plot.kind==='qq'?1:y,view.clientWidth);view.replaceChildren(svg);appendPlotExportButtons(svg,`symvacas-${plot.kind}`,{captions:[{text:t(plot.title)},...(plot.series?[{text:`${plot.series[sample].label} · n=${plot.series[sample].n}`}]:[])]});};
    activeCharts.set(view,draw);
    if(pages>1){
      const pager=element('div','','form-row'),label=element('span');
      const update=()=>{label.textContent=`${t('Page')} ${page+1} / ${pages}`;previous.disabled=page===0;next.disabled=page===pages-1;draw();};
      const previous=control('Previous',()=>{page--;update();}),next=control('Next',()=>{page++;update();});
      pager.append(previous,label,next);block.append(pager);update();
    }
    if(plot.kind==='sem-diagram'){
      const button=control('Fit diagram to screen',()=>{fitToScreen=!fitToScreen;setText(button,fitToScreen?'Original size':'Fit diagram to screen');button.setAttribute('aria-pressed',String(fitToScreen));draw();});
      button.setAttribute('aria-pressed','false');block.append(button);
    }
    const width=plot.points?.[0]?.length||0;
    if(plot.series){
      const label=element('label',t('Sample')),select=element('select');
      plot.series.forEach((item,i)=>{const option=element('option',`${t(item.label)} (n=${item.n})`);option.value=String(i);select.append(option);});
      select.onchange=()=>{sample=Number(select.value);draw();};label.append(select);block.append(label);
    }
    if(width>1&&!['qq','interaction','research-scatter'].includes(plot.kind)){
      const controls=element('div','','form-row');
      for(const axis of ['x','y']){
        const label=element('label',t(axis==='x'?'X axis':'Y axis')),select=element('select');
        for(let i=0;i<width;i++){const option=element('option',pc(plot,i));option.value=String(i);select.append(option);}
        select.value=String(axis==='x'?x:y);
        select.onchange=()=>{const value=Number(select.value);if(axis==='x'){if(value===y)y=x;x=value;}else{if(value===x)x=y;y=value;}controls.querySelectorAll('select')[0].value=String(x);controls.querySelectorAll('select')[1].value=String(y);draw();};
        label.append(select);controls.append(label);
      }
      block.append(controls);
    }
    draw();block.append(view);
    if(plot.kind==='sem-diagram')block.append(element('p',t('Ellipses: latent factors · rectangles: indicators · arrows: standardized coefficients [95% CI] · dashed double arrows: exogenous correlations.'),'hint'));
    if(plot.kind==='scree')block.append(element('p',t('Bars: explained variance · line: cumulative variance'),'hint'));
    if(plot.kind==='histogram')block.append(element('p',`${number(plot.level*100)}% ${t('credible interval')}: ${plot.interval.map(number).join(' – ')} · ${t('estimate')}: ${number(plot.estimate)}`,'hint'));
    if(plot.kind==='histogram')block.append(element('p',t('Dashed: credible bounds · dotted: estimate')+(statisticsPlotModel(plot).zero?' · '+t('Solid: zero difference'):''),'hint'));
    if(plot.groupLabels)block.append(element('p',`A: ${plot.groupLabels[0]} · B: ${plot.groupLabels[1]} · ${t('Difference (B − A)')}`,'hint'));
    if(plot.kind==='loadings')block.append(element('p',plot.labels.map((label,i)=>`${i+1}: ${label}`).join(' · '),'hint'));
    if(plot.caption)block.append(element('p',t(plot.caption),'hint'));
    if(plot.kind==='timeseries'&&plot.forecast.length){
      const legend=element('div','','form-row');['Observed','Fitted','Forecast'].forEach((label,i)=>{const item=element('span',`● ${t(label)}`);item.style.color=['var(--accent)','var(--muted)','var(--gold)'][i];legend.append(item);});block.append(legend,element('p',`${number(plot.level*100)}% ${t('Prediction interval')}`,'hint'));
    }
    if(plot.kind==='qq')block.append(element('p',t('Reference line passes through the first and third quartiles. Curvature or tail departures suggest non-normality; up to 200 ordered points are shown.'),'hint'));
    if(plot.kind==='clusters')block.append(element('p',t('Colors: cluster membership · crosses: centroids. Axes show original feature values.'),'hint'));
    if(plot.kind==='interaction'){
      const legend=element('div','','form-row');plot.lineLabels.forEach((label,i)=>{const item=element('span',`● ${label}`);item.style.color=['var(--accent)','var(--gold)','#9466b8','#437db0','#bd5c67','#598e85'][i%6];legend.append(item);});block.append(legend);
      block.append(element('p',t('Lines connect fitted cell means; nonparallel lines suggest interaction. Intervals are shown separately. Interpret with the interaction F test.'),'hint'));
    }
    if(plot.kind==='clusters'){
      const legend=element('div','','form-row');
      for(let i=0;i<plot.centroids.length;i++){const item=element('span',`● ${t('Cluster')} ${i+1}`);item.style.color=['var(--accent)','var(--gold)','#9466b8','#437db0','#bd5c67','#598e85'][i%6];legend.append(item);}block.append(legend);
    }
    if(plot.secondary)block.append(element('p',t('Bars: adjusted p · dots: raw p · dashed line: α'),'hint'));
    container.append(block);
    if(plot.kind==='sem-diagram')draw(); // Measure after the view enters its responsive container.
  }
}
