import {plot,dataBounds} from './plot.js';
import {numericStatisticsRows,statisticsColumnNames,statisticsDateLabel} from './workspace-commands.js';
import {displayNumber} from './display-format.js';
import {t} from './i18n.js';
import {statisticsPlotGroupingColumn,statisticsPlotNumber,statisticsFrequencyData,statisticsHistogramData,histogramDensityNumber,violinDensity,beeswarmLayout,statisticsHeatMapData,statisticsCorrelationHeatMap,heatMapColor} from './statistics-plot-data.js';
import {clusteredHeatMap} from './statistics-cluster.js';
import {appendPlotExportButtons} from './svg-export.js';
import {statisticsScatterData} from './statistics-plot-data.js';
import {defaultGraphColors} from './graph-colors.js';
import {raincloudSummary} from './statistics-plot-data.js';
export function statisticsPlotSeries(rows,{grouping='columns',columnCount=rows[0]?.length||1,columnNames=statisticsColumnNames(columnCount)}={}){
  const names=columnNames;
  const number=statisticsPlotNumber;
  if(statisticsPlotGroupingColumn(grouping,columnCount)<0){
    const numeric=numericStatisticsRows(rows);
    return names.map((label,i)=>({label,values:numeric.map(row=>number(row[i])).filter(n=>n!==null)}));
  }
  const groupColumn=statisticsPlotGroupingColumn(grouping,columnCount),groups=new Map();
  for(const row of rows){
    const group=String(row[groupColumn]??'').trim();if(!group)continue;
    if(!groups.has(group))groups.set(group,names.map(()=>[]));
    row.slice(0,columnCount).forEach((cell,i)=>{const n=number(cell);if(i!==groupColumn&&n!==null)groups.get(group)[i].push(n);});
  }
  return [...groups].flatMap(([group,samples])=>names.flatMap((name,i)=>i===groupColumn?[]:[{label:columnCount===2?group:`${group} · ${name}`,values:samples[i]}]));
}

export function statisticsPlotPanels(rows,{grouping='columns',columnCount=rows[0]?.length||1,columnNames=statisticsColumnNames(columnCount)}={}){
  if(statisticsPlotGroupingColumn(grouping,columnCount)<0)return [{label:'',series:statisticsPlotSeries(rows,{columnCount,columnNames})}];
  const groupColumn=statisticsPlotGroupingColumn(grouping,columnCount);
  return columnNames.flatMap((label,column)=>column===groupColumn||!rows.some(row=>statisticsPlotNumber(row[column])!==null)?[]:[{
    label,series:statisticsPlotSeries(rows.map(row=>[row[groupColumn]||'',row[column]||'']),{grouping:'first',columnCount:2})
  }]);
}

export function statisticsPlot(container,rows,options={}){
  drawStatisticsPlot(container,rows,options);
  const svg=container.querySelector('svg');if(!svg)return;
  const actions=appendPlotExportButtons(svg,'symvacas-statistics-'+(options.type||'scatter'),()=>{
  const captions=[];
  const legend=container.querySelector('.statistics-plot-legend');
  if(legend){
    const entries=[...legend.children];
    if(entries.length)entries.forEach(entry=>captions.push({text:entry.textContent,color:container.ownerDocument.defaultView.getComputedStyle(entry).color}));
    else captions.push({text:legend.textContent});
  }
  const bar=container.querySelector('.statistics-heatmap-legend'),scale=bar?{low:bar.firstElementChild.textContent,high:bar.lastElementChild.textContent}:null;
  if(scale&&scale.low===scale.high)scale.color=container.ownerDocument.defaultView.getComputedStyle(bar.querySelector('.statistics-heatmap-scale')).backgroundColor;
  return {captions,scale};
  });
  if(svg.parentNode!==container)container.append(actions);
}

function drawStatisticsPlot(container,rows,{type='scatter',digits=10,curve=[],xAxisLabel='x',yAxisLabel='y',scatterData,series=statisticsPlotSeries(rows),namedBars,histogramKde=false,heatMap,heatMapFit=false,orientation='horizontal'}={}){
  if(['heatmap','correlationheatmap','clusteredheatmap'].includes(type)){drawHeatMap(container,heatMap||(type==='correlationheatmap'?statisticsCorrelationHeatMap(rows):type==='clusteredheatmap'?clusteredHeatMap(statisticsHeatMapData(rows)):statisticsHeatMapData(rows)),digits,heatMapFit);return;}
  if(['violin','box','raincloud'].includes(type)){drawDistribution(container,series,digits,type,orientation);return;}
  if(type==='bar'){if(namedBars)drawNamedBars(container,namedBars,digits);else drawFrequencyBars(container,series,digits);return;}
  if(type==='scatter'){
    const data=scatterData||statisticsScatterData(rows),points=data.series.flatMap(entry=>entry.points);
    if(!points.length){container.replaceChildren();return;}
    const colors=data.series.map((_,i)=>data.groupColumn<0?'var(--accent)':defaultGraphColors[i%defaultGraphColors.length]);
    const bounds=dataBounds([...points,...curve]);
    const dateTicks=data.dateAxis?[...new Set(Array.from({length:5},(_,i)=>Math.round(Math.ceil(bounds.xmin)+(Math.floor(bounds.xmax)-Math.ceil(bounds.xmin))*i/4)))]:null;
    plot(container,{curves:[...data.series.map(entry=>entry.points),...(curve.length?[curve]:[])]},bounds,{scatterCurves:data.series.map((_,i)=>i),colors:[...colors,'var(--danger)'],digits,xAxisLabel,yAxisLabel,xTickValues:dateTicks,xTickLabel:data.dateAxis?value=>statisticsDateLabel(data.dateAxis.origin,value):null});
    if(data.groupColumn>=0){
      const legend=document.createElement('div');legend.className='statistics-plot-legend';
      data.series.forEach((entry,i)=>{const label=document.createElement('span');label.textContent=`${entry.label} (n=${entry.points.length})`;label.style.color=colors[i];legend.append(label);});
      container.prepend(legend);
    }
    return;
  }
  drawHistogram(container,series,digits,histogramKde);
}

function svgChart(label,width,height){
  const NS='http://www.w3.org/2000/svg',svg=document.createElementNS(NS,'svg');
  svg.setAttribute('viewBox',`0 0 ${width} ${height}`);svg.setAttribute('role','img');svg.setAttribute('aria-label',t(label));
  const node=(tag,attrs,text='',parent=svg)=>{const el=document.createElementNS(NS,tag);for(const [key,value] of Object.entries(attrs))el.setAttribute(key,String(value));el.textContent=text;parent.append(el);return el;};
  return {svg,node};
}

function drawHistogram(container,series,digits,kde){
  if(!series.some(entry=>entry.values.some(Number.isFinite))){container.replaceChildren();return;}
  const data=statisticsHistogramData(series.map(entry=>entry.values),kde),{svg,node}=svgChart('Histogram',800,400);
  svg.setAttribute('data-y-axis',kde?'density':'count');
  const colors=['var(--accent)','#a04c75','#3b70bd'],left=kde?95:70,width=730-left,baseline=340,height=290,peak=data.peak*(kde?1.08:1);
  const px=value=>left+(value-data.viewMinimum)/(data.viewMaximum-data.viewMinimum)*width,py=value=>baseline-height*value/peak;
  for(let i=0;i<=4;i++){
    const value=peak*i/4,y=py(value);
    node('line',{x1:left,x2:left+width,y1:y,y2:y,stroke:'var(--grid)'});
    const raw=String(kde?histogramDensityNumber(value,data):value),parts=raw.split(/e/i);
    const label=kde?String(Number(Number(parts[0]).toPrecision(4)))+(parts.length>1?'e'+parts[1]:''):displayNumber(value,digits);
    node('text',{x:left-8,y:y+5,fill:'var(--muted)','text-anchor':'end','font-size':12},label);
    const position=data.viewMinimum+(data.viewMaximum-data.viewMinimum)*i/4,x=(data.minimum+position*data.span)*data.scale;
    node('text',{x:px(position),y:365,fill:'var(--muted)','text-anchor':'middle','font-size':13},displayNumber(x,digits));
  }
  node('line',{x1:left,x2:left,y1:50,y2:baseline,stroke:'var(--muted)'});
  node('line',{x1:left,x2:left+width,y1:baseline,y2:baseline,stroke:'var(--muted)'});
  node('text',{x:left,y:22,fill:'var(--muted)','font-size':14},t(kde?'Density':'Count'));
  data.heights.forEach((heights,seriesIndex)=>heights.forEach((value,index)=>{
    const start=px(index/data.bins),end=px((index+1)/data.bins),binWidth=end-start,lane=binWidth/series.length;
    const x=kde?start:start+lane*seriesIndex,w=kde?binWidth:Math.max(1,lane-2),h=baseline-py(value);
    const shown=kde?histogramDensityNumber(value,data):value;
    const bar=node('rect',{x,y:py(value),width:w,height:h,fill:colors[seriesIndex%colors.length],opacity:kde?.25:.7,'data-bin':index,'data-series':series[seriesIndex].label,'data-count':data.counts[seriesIndex][index],...(kde?{'data-density':shown}:{})});
    node('title',{},`${series[seriesIndex].label}: ${displayNumber(shown,digits)}`,bar);
    if(!kde)node('text',{x:x+w/2,y:py(value)-5,fill:'var(--ink)','text-anchor':'middle','font-size':11},String(value));
  }));
  data.curves.forEach((curve,index)=>{
    if(!curve.length)return;
    node('path',{d:curve.map(([at,density],i)=>`${i?'L':'M'}${px(at)},${py(density)}`).join(' '),fill:'none',stroke:colors[index%colors.length],'stroke-width':2.5,'data-kde-series':series[index].label});
  });
  const legend=document.createElement('div');legend.className='statistics-plot-legend';
  series.forEach((entry,index)=>{
    const label=document.createElement('span');label.textContent=`${entry.label} (n=${entry.values.filter(Number.isFinite).length})${kde?' · KDE':''}${data.unavailable.includes(index)?' · '+t('KDE unavailable for this series'):''}`;label.style.color=colors[index%colors.length];legend.append(label);
  });
  container.replaceChildren(legend,svg);
}

function drawFrequencyBars(container,series,digits){
  const data=statisticsFrequencyData(series.map(entry=>entry.values));
  if(!data.values.length){container.replaceChildren();return;}
  const {svg,node}=svgChart('Bar',800,400),colors=['var(--accent)','#a04c75','#3b70bd'];
  const left=60,baseline=340,width=680,height=300;
  const step=Math.max(1,Math.ceil(data.peak/4)),ticks=new Set([0,data.peak]);
  for(let count=0;count<=data.peak;count+=step)ticks.add(count);
  for(const count of [...ticks].sort((a,b)=>a-b)){
    const y=baseline-height*count/data.peak;
    node('line',{x1:left,x2:left+width,y1:y,y2:y,stroke:'var(--grid)'});
    node('text',{x:left-8,y:y+5,fill:'var(--muted)','text-anchor':'end','font-size':13},String(count));
  }
  node('line',{x1:left,x2:left,y1:40,y2:baseline,stroke:'var(--muted)'});
  node('line',{x1:left,x2:left+width,y1:baseline,y2:baseline,stroke:'var(--muted)'});
  node('text',{x:left,y:20,fill:'var(--muted)','font-size':14},t('Count'));
  node('text',{x:left+width,y:390,fill:'var(--muted)','text-anchor':'end','font-size':14},t('Value'));
  const groupWidth=Math.max(width*data.barWidth,series.length*.75),lane=groupWidth/series.length;
  data.values.forEach((value,index)=>{
    const center=left+width*data.positions[index];
    if(data.values.length<=10||index===0||index===data.values.length-1||index%Math.ceil(data.values.length/8)===0)
      node('text',{x:center,y:365,fill:'var(--muted)','text-anchor':'middle','font-size':13},displayNumber(value,digits));
    data.counts.forEach((counts,seriesIndex)=>{
      const count=counts[index];if(!count)return;
      const h=height*count/data.peak,x=center-groupWidth/2+seriesIndex*lane;
      const bar=node('rect',{x:x+lane*.05,y:baseline-h,width:lane*.9,height:h,fill:colors[seriesIndex%colors.length],opacity:.78,'data-value':value,'data-count':count,'data-series':series[seriesIndex].label});
      node('title',{},`${series[seriesIndex].label} · ${displayNumber(value,digits)}: ${count}`,bar);
      node('text',{x:x+lane/2,y:baseline-h-5,fill:'var(--ink)','text-anchor':'middle','font-size':12},String(count));
    });
  });
  const legend=document.createElement('div');legend.className='statistics-plot-legend';
  series.forEach((entry,index)=>{const label=document.createElement('span');label.textContent=`${entry.label} (n=${entry.values.length})`;label.style.color=colors[index%colors.length];legend.append(label);});
  container.replaceChildren(legend,svg);
}

function drawNamedBars(container,data,digits){
  if(!data.labels.length){container.replaceChildren();return;}
  const width=Math.max(800,data.labels.length*72+120),left=70,right=width-40,top=40,height=300,baseline=top+height*data.baseline;
  const {svg,node}=svgChart('Bar',width,420),colors=['var(--accent)','#a04c75','#3b70bd'];
  const scale=Math.max(Math.abs(data.minimum),Math.abs(data.maximum))||1;
  for(let i=0;i<=(data.minimum===data.maximum?0:4);i++){
    const fraction=data.minimum===data.maximum?1:i/4,value=(data.maximum/scale*(1-fraction)+data.minimum/scale*fraction)*scale,y=top+height*fraction;
    node('line',{x1:left,x2:right,y1:y,y2:y,stroke:'var(--grid)'});
    node('text',{x:left-8,y:y+5,fill:'var(--muted)','text-anchor':'end','font-size':13},displayNumber(value,digits));
  }
  node('line',{x1:left,x2:right,y1:baseline,y2:baseline,stroke:'var(--muted)'});
  node('line',{x1:left,x2:left,y1:top,y2:top+height,stroke:'var(--muted)'});
  node('text',{x:left,y:20,fill:'var(--muted)','font-size':14},t(data.valueLabel));
  node('text',{x:right,y:410,fill:'var(--muted)','text-anchor':'end','font-size':14},t(data.categoryLabel));
  const slotWidth=(right-left)/data.labels.length,groupWidth=slotWidth*.75,lane=groupWidth/data.series.length;
  data.labels.forEach((label,index)=>{
    const center=left+(index+.5)*slotWidth;
    const labelNode=node('text',{x:center,y:382,fill:'var(--muted)','text-anchor':'middle','font-size':13},label.length>18?label.slice(0,17)+'…':label);node('title',{},label,labelNode);
    data.series.forEach((entry,seriesIndex)=>{
      const value=entry.values[index],position=data.positions[seriesIndex][index];if(value===null)return;
      const y=top+height*position,x=center-groupWidth/2+seriesIndex*lane,h=Math.abs(y-baseline);
      const bar=node('rect',{x:x+lane*.05,y:Math.min(y,baseline),width:lane*.9,height:h,fill:colors[seriesIndex%colors.length],opacity:.78,'data-name':label,'data-value':value,'data-series':entry.label});
      node('title',{},`${entry.label} · ${label}: ${displayNumber(value,digits)}`,bar);
      node('text',{x:x+lane/2,y:y+(value<0?16:-5),fill:'var(--ink)','text-anchor':'middle','font-size':12},displayNumber(value,digits));
    });
  });
  const legend=document.createElement('div');legend.className='statistics-plot-legend';
  data.series.forEach((entry,index)=>{const label=document.createElement('span');label.textContent=entry.label;label.style.color=colors[index%colors.length];legend.append(label);});
  container.replaceChildren(legend,svg);
}

function drawDistribution(container,series,digits,type,orientation){
  series=series.map(entry=>({...entry,values:entry.values.filter(Number.isFinite)})).filter(entry=>entry.values.length);
  if(!series.some(entry=>entry.values.length)){container.replaceChildren();return;}
  const raincloud=type==='raincloud';
  const vertical=orientation==='vertical',width=vertical?Math.max(800,series.length*90+130):800,height=vertical?440:Math.max(300,series.length*90+70);
  const {svg,node}=svgChart(raincloud?'Raincloud plot':type==='box'?'Box plot':'Violin + points',width,height);
  svg.dataset.orientation=vertical?'vertical':'horizontal';
  if(type==='violin'||raincloud)svg.dataset.rawLayout='beeswarm';
  const all=series.flatMap(entry=>entry.values),scale=all.reduce((a,b)=>Math.max(a,Math.abs(b)),0)||1;
  const minimum=all.reduce((a,b)=>Math.min(a,b)),maximum=all.reduce((a,b)=>Math.max(a,b)),span=maximum/scale-minimum/scale;
  const fraction=value=>span?(value/scale-minimum/scale)/span:.5;
  const axis=value=>vertical?height-80-fraction(value)*(height-120):110+fraction(value)*630;
  const lane=index=>vertical?110+(index+.5)*(width-150)/series.length:45+index*90;
  const position=(value,index,offset=0)=>vertical?[lane(index)+offset,axis(value)]:[axis(value),lane(index)+offset];
  const colors=['var(--accent)','#a04c75','#3b70bd'];
  node('line',vertical?{x1:110,x2:110,y1:40,y2:height-80,stroke:'var(--muted)'}:{x1:110,x2:740,y1:height-45,y2:height-45,stroke:'var(--muted)'});
  for(let i=0;i<=(span?4:0);i++){
    const fraction=span?i/4:.5,value=(minimum/scale*(1-fraction)+maximum/scale*fraction)*scale;
    node('text',{x:vertical?100:110+fraction*630,y:vertical?axis(value)+5:height-20,fill:'var(--muted)','text-anchor':vertical?'end':'middle','font-size':14,'data-value-tick':value},displayNumber(value,digits));
  }
  series.forEach((entry,index)=>{
    const center=lane(index),color=colors[index%colors.length],density=type==='violin'||raincloud?violinDensity(entry.values):[];
    const label=node('text',{x:vertical?center:20,y:vertical?height-52:center+5,fill:'var(--ink)','font-size':14,'text-anchor':vertical?'middle':'start'},entry.label.length>12?`${entry.label.slice(0,11)}…`:entry.label);
    node('title',{},entry.label,label);
    node('text',{x:vertical?center:20,y:vertical?height-32:center+23,fill:'var(--muted)','font-size':12,'text-anchor':vertical?'middle':'start'},`n=${entry.values.length}`);
    if((type==='box'||raincloud)&&entry.values.length){
      const values=[...entry.values].sort((a,b)=>a-b),q=p=>{const at=(values.length-1)*p,lo=Math.floor(at),hi=Math.ceil(at),f=at-lo;return values[lo]*(1-f)+values[hi]*f;};
      const {low,q1,median,q3,high}=raincloud?raincloudSummary(values):{low:values[0],q1:q(.25),median:q(.5),q3:q(.75),high:values.at(-1)};
      const boxCenter=raincloud?6:0,boxHalf=raincloud?5:20;
      const line=(value1,offset1,value2,offset2,attrs={})=>{const [x1,y1]=position(value1,index,offset1),[x2,y2]=position(value2,index,offset2);return node('line',{x1,y1,x2,y2,stroke:color,'stroke-width':2,...attrs});};
      line(low,boxCenter,high,boxCenter);
      const a=position(q1,index,boxCenter-boxHalf),b=position(q3,index,boxCenter+boxHalf);
      const box=node('rect',{x:Math.min(a[0],b[0]),y:Math.min(a[1],b[1]),width:Math.max(1,Math.abs(b[0]-a[0])),height:Math.max(1,Math.abs(b[1]-a[1])),fill:color,'fill-opacity':.3,stroke:color,'data-box':entry.label});
      node('title',{},`${entry.label}: ${raincloud?'lower whisker':'min'}=${displayNumber(low,digits)}, Q1=${displayNumber(q1,digits)}, median=${displayNumber(median,digits)}, Q3=${displayNumber(q3,digits)}, ${raincloud?'upper whisker':'max'}=${displayNumber(high,digits)}`,box);
      line(median,boxCenter-boxHalf,median,boxCenter+boxHalf,{'stroke-width':3,'data-median':median});for(const at of [low,high])line(at,boxCenter-boxHalf*.6,at,boxCenter+boxHalf*.6,{'data-whisker':at});
      if(!raincloud){const [mx,my]=position(median,index,42);node('text',{x:mx,y:my+4,fill:'var(--ink)','text-anchor':'middle','font-size':12},displayNumber(median,digits));}
    }
    if(density.length){
      const upper=density.map(([value,width])=>position(value,index,(raincloud?-4:0)-width*28).join(',')),lower=[...density].reverse().map(([value,width])=>position(value,index,raincloud?-4:width*28).join(','));
      node('path',{d:`M${upper.join(' L')} L${lower.join(' L')} Z`,fill:color,'fill-opacity':.24,stroke:color,'stroke-width':1.5,'data-violin':entry.label,...(raincloud?{'data-half-violin':'true'}:{})});
    }
    if(type==='violin'||raincloud){
      const swarm=beeswarmLayout(entry.values.map(axis),3,raincloud?10:28);
      entry.values.forEach((value,i)=>{
        const [cx,cy]=position(value,index,(raincloud?26:0)+swarm.offsets[i]),point=node('circle',{cx,cy,r:swarm.radius,fill:color,'fill-opacity':.75,'data-raw-point':entry.label,'data-value':value});
        node('title',{},`${entry.label}: ${displayNumber(value,digits)}`,point);
      });
    }
  });
  svg.classList.add('statistics-distribution');
  if(vertical&&width>800){const scroll=document.createElement('div');scroll.className='statistics-distribution-scroll';svg.style.width=`${width}px`;scroll.append(svg);container.replaceChildren(scroll);}
  else container.replaceChildren(svg);
}

function drawHeatMap(container,data,digits,fitToScreen=false){
  const finite=data.rows.flatMap(row=>row.values).filter(value=>value!==null);
  if(!data.rows.length||!data.columns.length||!finite.length&&!data.correlation){container.replaceChildren();return;}
  const minimum=data.range?.[0]??finite.reduce((a,b)=>Math.min(a,b)),maximum=data.range?.[1]??finite.reduce((a,b)=>Math.max(a,b));
  const left=data.clustered?180:100,top=data.clustered?120:45,width=Math.max(600,left+20+data.columns.length*80),cellWidth=(width-left-20)/data.columns.length;
  const height=top+data.rows.length*30;
  const {svg,node}=svgChart('Heat map',width,height);
  if(fitToScreen){
    const availableWidth=container.clientWidth||width,scale=Math.min(1,availableWidth/width,420/height);
    svg.style.width=`${Math.max(1,Math.round(width*scale))}px`;svg.style.height=`${Math.max(1,Math.round(height*scale))}px`;
    svg.classList.add('statistics-heatmap','statistics-heatmap-fit');
  }else{svg.style.width=`${width}px`;svg.classList.add('statistics-heatmap');}
  if(data.clustered){
    const rowPeak=data.rowLinks.reduce((peak,link)=>Math.max(peak,link.height),0)||1,columnPeak=data.columnLinks.reduce((peak,link)=>Math.max(peak,link.height),0)||1;
    for(const link of data.rowLinks){const a=top+(link.left+.5)*30,b=top+(link.right+.5)*30,x=78-link.height/rowPeak*70;
      node('path',{d:`M${78-link.leftHeight/rowPeak*70},${a} H${x} V${b} H${78-link.rightHeight/rowPeak*70}`,fill:'none',stroke:'var(--muted)','stroke-width':1.5,'data-dendrogram':'row'});}
    for(const link of data.columnLinks){const a=left+(link.left+.5)*cellWidth,b=left+(link.right+.5)*cellWidth,y=85-link.height/columnPeak*75;
      node('path',{d:`M${a},${85-link.leftHeight/columnPeak*75} V${y} H${b} V${85-link.rightHeight/columnPeak*75}`,fill:'none',stroke:'var(--muted)','stroke-width':1.5,'data-dendrogram':'column'});}
  }
  data.columns.forEach((name,i)=>node('text',{x:left+(i+.5)*cellWidth,y:top-21,fill:'var(--ink)','text-anchor':'middle','font-size':14},name));
  data.rows.forEach((row,i)=>{
    const label=node('text',{x:left-10,y:top+i*30+19,fill:'var(--ink)','text-anchor':'end','font-size':13},row.label.length>12?`${row.label.slice(0,11)}…`:row.label);
    node('title',{},row.label,label);
    row.values.forEach((value,column)=>{
      const cell=node('rect',{x:left+column*cellWidth,y:top+i*30,width:cellWidth,height:30,fill:heatMapColor(value,minimum,maximum)||'var(--number)',stroke:'var(--line)','data-row':i,'data-column':column,'data-value':value??''});
      const displayed=value===null?'—':displayNumber(value,digits);
      node('title',{},`${row.label} · ${data.columns[column]}: ${displayed}${row.counts?` (n=${row.counts[column]})`:''}`,cell);
      node('text',{x:left+(column+.5)*cellWidth,y:top+i*30+20,fill:value===null?'var(--muted)':heatMapTextColor(value,minimum,maximum),'text-anchor':'middle','font-size':12},displayed.length>10?`${displayed.slice(0,9)}…`:displayed);
    });
  });
  const scroll=document.createElement('div');scroll.className=fitToScreen?'statistics-heatmap-scroll statistics-heatmap-fit-scroll':'statistics-heatmap-scroll';scroll.tabIndex=0;scroll.setAttribute('aria-label',t('Heat map'));scroll.append(svg);
  const legend=document.createElement('div');legend.className='statistics-heatmap-legend';
  const low=document.createElement('span'),bar=document.createElement('span'),high=document.createElement('span');
  low.textContent=displayNumber(minimum,digits);high.textContent=displayNumber(maximum,digits);bar.className='statistics-heatmap-scale';
  if(minimum===maximum)bar.style.background=heatMapColor(minimum,minimum,maximum);
  legend.append(low,bar,high);
  const caption=document.createElement('div');caption.className='statistics-plot-legend';
  const methodName={pearson:'Pearson',spearman:'Spearman',kendall:'Kendall'}[data.method]||'Pearson';
  const captionKey=data.correlation?`${methodName} correlation · pairwise complete observations`:data.mode==='zrow'?'Row z-scores · color = z-score':data.mode==='zcolumn'?'Column z-scores · color = z-score':'Raw values · rows × columns';
  caption.textContent=t(captionKey)+(data.clustered?` · ${t('Hierarchical clustering')}`:'');
  container.replaceChildren(caption,scroll,legend);
}

function heatMapTextColor(value,minimum,maximum){
  const rgb=heatMapColor(value,minimum,maximum).match(/\d+/g).map(Number);
  const linear=rgb.map(v=>{const n=v/255;return n<=.04045?n/12.92:((n+.055)/1.055)**2.4;});
  return .2126*linear[0]+.7152*linear[1]+.0722*linear[2]<.18?'#fff':'#17232c';
}
