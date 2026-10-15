import {element} from './app-ui.js';
import {t} from './i18n.js';
import {roundNumber} from './display-format.js';
import {appendPlotExportButtons} from './svg-export.js';

export function svmDecisionPlot(plot,digits=10,parameterLabels={}){
  if(!plot)return null;
  const title=t('SVM decision boundary and margins'),figure=element('figure');
  figure.append(element('figcaption',title));
  const name=index=>parameterLabels[`b${index+1}`]||`x${index+1}`;
  const number=value=>roundNumber(String(value),digits,true);
  const legend=t('Blue: class 0; orange: class 1; rings: support vectors. Solid: f = 0; dashed: f = -1 and +1.');
  figure.append(element('p',legend));
  const fixed=plot.fixedFeatures||[];
  const slice=fixed.length?t('First two predictors shown; other predictors fixed at training means. Points are projections.')+' '+fixed.map(item=>`${name(item.index)}=${number(item.value)}`).join(', '):'';
  if(slice)figure.append(element('p',slice));
  const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');
  svg.setAttribute('viewBox','0 0 640 470');svg.setAttribute('role','img');svg.setAttribute('aria-label',title);svg.setAttribute('data-svm-decision-plot','true');svg.style.width='100%';
  const draw=(tag,attributes,text='')=>{const node=document.createElementNS(svg.namespaceURI,tag);for(const [key,value] of Object.entries(attributes))node.setAttribute(key,String(value));node.textContent=text;svg.append(node);return node;};
  const [xmin,xmax]=plot.xlim,[ymin,ymax]=plot.ylim;
  const x=v=>72+540*(v-xmin)/(xmax-xmin),y=v=>410-380*(v-ymin)/(ymax-ymin);
  draw('rect',{x:72,y:30,width:540,height:380,fill:'var(--number)',stroke:'var(--muted)'});
  for(let i=0;i<=4;i++){
    const vx=xmin+(xmax-xmin)*i/4,vy=ymin+(ymax-ymin)*i/4;
    draw('line',{x1:x(vx),x2:x(vx),y1:30,y2:410,stroke:'var(--muted)','stroke-opacity':.2});
    draw('line',{x1:72,x2:612,y1:y(vy),y2:y(vy),stroke:'var(--muted)','stroke-opacity':.2});
    draw('text',{x:x(vx),y:429,fill:'var(--ink)','font-size':11,'text-anchor':'middle'},number(vx));
    draw('text',{x:65,y:y(vy)+4,fill:'var(--ink)','font-size':11,'text-anchor':'end'},number(vy));
  }
  for(const contour of plot.contours||[]){
    const path=(contour.segments||[]).map(([a,b])=>`M${x(a[0])},${y(a[1])}L${x(b[0])},${y(b[1])}`).join('');
    if(path)draw('path',{d:path,fill:'none',stroke:'var(--ink)','stroke-width':contour.level===0?2:1.3,
      'stroke-dasharray':contour.level===0?'none':'6 4','data-svm-level':contour.level});
  }
  if(plot.curve?.length)draw('path',{d:plot.curve.map(([a,b],i)=>`${i?'L':'M'}${x(a)},${y(b)}`).join(''),fill:'none',stroke:'var(--accent)','stroke-width':2,'data-svm-score-curve':'true'});
  for(const point of plot.points||[]){
    const dot=draw('circle',{cx:x(point.x),cy:y(point.y),r:3.5,fill:point.class?'#cf7820':'#397bb5','data-svm-observation':point.row});
    const tooltip=document.createElementNS(svg.namespaceURI,'title');tooltip.textContent=`${t('Observation')} ${point.row} · ${t('Observed class')}=${point.class}${point.support?' · '+t('Support vector'):''}`;dot.append(tooltip);
    if(point.support)draw('circle',{cx:x(point.x),cy:y(point.y),r:6.5,fill:'none',stroke:'var(--ink)','stroke-width':1.4,'data-svm-support':point.row});
  }
  draw('text',{x:342,y:458,fill:'var(--ink)','font-size':13,'text-anchor':'middle'},name(0));
  draw('text',{transform:'translate(15 220) rotate(-90)',fill:'var(--ink)','font-size':13,'text-anchor':'middle'},plot.kind==='score'?t('Decision score'):name(1));
  const wrap=text=>Array.from(text).reduce((lines,char)=>{if(lines.at(-1).length>=68)lines.push('');lines[lines.length-1]+=char;return lines;},['']);
  figure.append(svg);appendPlotExportButtons(svg,'symvacas-svm',{captions:[title,legend,...(slice?[slice]:[])].flatMap(text=>wrap(text).map(text=>({text})))});
  return figure;
}
