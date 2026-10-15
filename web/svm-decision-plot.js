import {element} from './app-ui.js';
import {t} from './i18n.js';
import {roundNumber} from './display-format.js';
import {appendPlotExportButtons} from './svg-export.js';

export function svmDecisionPlot(plot,digits=10,parameterLabels={}){
  if(!plot)return null;
  const regression=['observedPredicted','predictionError','regressionFit'].includes(plot.kind);
  const plotTitles={observedPredicted:'Observed vs predicted',predictionError:'Prediction error vs predicted',regressionFit:'SVR fit and epsilon tube'};
  const title=t(plotTitles[plot.kind]||'SVM decision boundary and margins')+(regression?' · '+t('Training data evaluation'):''),figure=element('figure');
  figure.append(element('figcaption',title));
  const name=index=>parameterLabels[`b${index+1}`]||`x${index+1}`;
  const number=value=>roundNumber(String(value),digits,true);
  const legends={observedPredicted:'Dots: observations; rings: support vectors. Dashed: perfect predictions (y = x).',predictionError:'Dots: observations; rings: support vectors. Solid: zero prediction error.',regressionFit:'Solid: prediction function; dashed: f(x) ± epsilon; rings: support vectors.'};
  const legend=t(legends[plot.kind]||'Blue: class 0; orange: class 1; rings: support vectors. Solid: f = 0; dashed: f = -1 and +1.')+(plot.kind==='regressionFit'?' · ε='+number(plot.epsilon):'');
  figure.append(element('p',legend));
  const fixed=plot.fixedFeatures||[];
  const slice=fixed.length?t('First two predictors shown; other predictors fixed at training means. Points are projections.')+' '+fixed.map(item=>`${name(item.index)}=${number(item.value)}`).join(', '):'';
  if(slice)figure.append(element('p',slice));
  const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');
  const width=plot.kind==='observedPredicted'?380:540;
  svg.setAttribute('viewBox',`0 0 ${width+100} 470`);svg.setAttribute('data-svm-plot-kind',plot.kind);svg.setAttribute('role','img');svg.setAttribute('aria-label',title);svg.setAttribute('data-svm-decision-plot','true');svg.style.width='100%';
  const draw=(tag,attributes,text='')=>{const node=document.createElementNS(svg.namespaceURI,tag);for(const [key,value] of Object.entries(attributes))node.setAttribute(key,String(value));node.textContent=text;svg.append(node);return node;};
  const [xmin,xmax]=plot.xlim,[ymin,ymax]=plot.ylim;
  const x=v=>72+width*(v-xmin)/(xmax-xmin),y=v=>410-380*(v-ymin)/(ymax-ymin);
  draw('rect',{x:72,y:30,width,height:380,fill:'var(--number)',stroke:'var(--muted)'});
  for(let i=0;i<=4;i++){
    const vx=xmin+(xmax-xmin)*i/4,vy=ymin+(ymax-ymin)*i/4;
    draw('line',{x1:x(vx),x2:x(vx),y1:30,y2:410,stroke:'var(--muted)','stroke-opacity':.2});
    draw('line',{x1:72,x2:72+width,y1:y(vy),y2:y(vy),stroke:'var(--muted)','stroke-opacity':.2});
    draw('text',{x:x(vx),y:429,fill:'var(--ink)','font-size':11,'text-anchor':'middle'},number(vx));
    draw('text',{x:65,y:y(vy)+4,fill:'var(--ink)','font-size':11,'text-anchor':'end'},number(vy));
  }
  for(const contour of plot.contours||[]){
    const path=(contour.segments||[]).map(([a,b])=>`M${x(a[0])},${y(a[1])}L${x(b[0])},${y(b[1])}`).join('');
    if(path)draw('path',{d:path,fill:'none',stroke:'var(--ink)','stroke-width':contour.level===0?2:1.3,
      'stroke-dasharray':(contour.dashed??contour.level!==0)?'6 4':'none','data-svm-level':contour.level});
  }
  if(plot.curve?.length)draw('path',{d:plot.curve.map(([a,b],i)=>`${i?'L':'M'}${x(a)},${y(b)}`).join(''),fill:'none',stroke:'var(--accent)','stroke-width':2,'data-svm-score-curve':'true'});
  for(const point of plot.points||[]){
    const dot=draw('circle',{cx:x(point.x),cy:y(point.y),r:3.5,fill:regression?'#397bb5':point.class?'#cf7820':'#397bb5','data-svm-observation':point.row});
    const tooltip=document.createElementNS(svg.namespaceURI,'title');tooltip.textContent=`${t('Observation')} ${point.row} · ${regression?number(point.x)+', '+number(point.y):t('Observed class')+'='+point.class}${point.support?' · '+t('Support vector'):''}`;dot.append(tooltip);
    if(point.support)draw('circle',{cx:x(point.x),cy:y(point.y),r:6.5,fill:'none',stroke:'var(--ink)','stroke-width':1.4,'data-svm-support':point.row});
  }
  const xlabel=plot.kind==='observedPredicted'?t('Observed value'):plot.kind==='predictionError'?t('Predicted value'):name(0);
  const ylabel=plot.kind==='observedPredicted'?t('Predicted value'):plot.kind==='predictionError'?t('Prediction error'):plot.kind==='regressionFit'?t('Observed value'):plot.kind==='score'?t('Decision score'):name(1);
  draw('text',{x:72+width/2,y:458,fill:'var(--ink)','font-size':13,'text-anchor':'middle'},xlabel);
  draw('text',{transform:'translate(15 220) rotate(-90)',fill:'var(--ink)','font-size':13,'text-anchor':'middle'},ylabel);
  const wrap=text=>Array.from(text).reduce((lines,char)=>{if(lines.at(-1).length>=68)lines.push('');lines[lines.length-1]+=char;return lines;},['']);
  figure.append(svg);appendPlotExportButtons(svg,'symvacas-'+(regression?'svr-'+plot.kind:'svm'),{captions:[title,legend,...(slice?[slice]:[])].flatMap(text=>wrap(text).map(text=>({text})))});
  return figure;
}
