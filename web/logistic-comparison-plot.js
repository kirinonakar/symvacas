import {element} from './app-ui.js';
import {t} from './i18n.js';
import {appendPlotExportButtons} from './svg-export.js';
import {displayNumber} from './display-format.js';

export function logisticComparisonPlot(plot,digits=6){
  const calibration=plot.kind==='calibration-comparison',figure=element('figure'),ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');
  const colors=['var(--accent)','#a04c75'],title=t(plot.title),xLabel=t(calibration?'Predicted probability':'False positive rate (FPR)'),yLabel=t(calibration?'Observed event proportion':'Sensitivity (TPR)');
  svg.setAttribute('viewBox','0 0 520 440');svg.setAttribute('role','img');svg.setAttribute('aria-label',title);svg.style.width='100%';svg.style.maxWidth='520px';
  const node=(tag,attrs,text='',parent=svg)=>{const value=document.createElementNS(ns,tag);for(const [key,item] of Object.entries(attrs))value.setAttribute(key,String(item));value.textContent=text;parent.append(value);return value;};
  const x=v=>58+428*v,y=v=>378-326*v;
  for(const value of [0,.25,.5,.75,1]){
    node('line',{x1:x(value),x2:x(value),y1:y(0),y2:y(1),stroke:'var(--line)','stroke-width':1,'data-grid':'x'});node('line',{x1:x(0),x2:x(1),y1:y(value),y2:y(value),stroke:'var(--line)','stroke-width':1,'data-grid':'y'});
    node('line',{x1:x(value),x2:x(value),y1:y(0),y2:y(0)+5,stroke:'var(--muted)'});node('line',{x1:x(0)-5,x2:x(0),y1:y(value),y2:y(value),stroke:'var(--muted)'});
    node('text',{x:x(value),y:396,'text-anchor':'middle','font-size':12,fill:'var(--muted)','data-axis-tick':'x'},String(value));node('text',{x:48,y:y(value)+4,'text-anchor':'end','font-size':12,fill:'var(--muted)','data-axis-tick':'y'},String(value));
  }
  node('line',{x1:x(0),x2:x(1),y1:y(0),y2:y(0),stroke:'var(--muted)','stroke-width':1.25,'data-axis':'x'});
  node('line',{x1:x(0),x2:x(0),y1:y(0),y2:y(1),stroke:'var(--muted)','stroke-width':1.25,'data-axis':'y'});
  node('line',{x1:x(0),y1:y(0),x2:x(1),y2:y(1),stroke:'var(--muted)','stroke-dasharray':'5 5','data-reference':calibration?'ideal':'chance'});
  const captions=[];
  plot.series.forEach((series,index)=>{
    const color=colors[index],points=series.points.filter(point=>point.slice(0,2).every(value=>Number.isFinite(value)&&value>=0&&value<=1));
    node('path',{d:points.map((point,i)=>`${i?'L':'M'}${x(point[0])},${y(point[1])}`).join(' '),fill:'none',stroke:color,'stroke-width':2.5,'data-model':series.label});
    if(calibration)points.forEach(point=>{const dot=node('circle',{cx:x(point[0]),cy:y(point[1]),r:4,fill:color,'data-model':series.label});node('title',{},`${series.label}: n=${point[2]}, p=${displayNumber(point[0],digits)}, observed=${displayNumber(point[1],digits)}`,dot);});
    const caption=`${series.label}${calibration?'':` · AUC=${displayNumber(series.auc,digits)}${series.interval?` · CI [${series.interval.map(value=>displayNumber(value,digits)).join(', ')}]`:''}`}`;
    node('text',{x:58,y:20+index*18,fill:color,'font-size':12,'data-model-legend':series.label},caption);captions.push({text:caption,color});
  });
  node('text',{x:270,y:432,'text-anchor':'middle','font-size':12,fill:'var(--ink)','data-axis-label':'x'},xLabel);
  node('text',{x:0,y:0,transform:'translate(16 215) rotate(-90)','text-anchor':'middle','font-size':12,fill:'var(--ink)','data-axis-label':'y'},yLabel);
  figure.append(element('figcaption',title),element('p',t(plot.evaluation==='crossvalidation'?'Out-of-fold predictions; refitted bootstrap confidence intervals.':plot.evaluation==='apparent'?'Training-data predictions; apparent performance.':plot.evaluation==='holdout'?'Held-out predictions; models fitted on the training split only.':'Validation dataset predictions; conditional on the fitted training models.'),'hint'),svg);
  appendPlotExportButtons(svg,`symvacas-${plot.kind}`,{captions});return figure;
}
