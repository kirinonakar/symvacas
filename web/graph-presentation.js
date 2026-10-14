// Input gutter, selectable formula rows, value table, and analysis result rendering.
import {cartesianFormula,graphShadingBody,graphSources,isGraphShading,parametricFormula,removeGraphInputLine,surfaceFormula} from './graph-input.js';
import {displayNumber} from './display-format.js';
import {graphCurveColor} from './graph-canvas.js';
import {mathDisplay} from './math-display.js';
import {renderFormulas} from './formula-preview.js';
import {t} from './i18n.js';

export function createGraphPresentation({
  $,
  analysisCurveKey,
  analysisCurveLabel,
  clearPlot,
  expressions,
  getColors,
  kind,
  options,
  persist,
  queue,
  rememberInput,
  removeSource,
  render,
  selectDerivative,
  selectTrace,
  selected,
  state,
  surface,
  value
}){
  let formulaSignature='',tableResult=null,tableDigits=null,tableLanguage=null;

  function syncInputLineScroll(){
    $('graph-line-numbers').style.transform=`translateY(${-$('graph-source').scrollTop}px)`;
  }

  function inputLineControls(){
    const gutter=$('graph-line-numbers');gutter.replaceChildren();
    value('graph-source').split(/\r?\n/).forEach((_,index)=>{
      const row=document.createElement('div'),number=document.createElement('span'),remove=document.createElement('button');
      row.className='graph-input-line';number.textContent=String(index+1);
      remove.type='button';remove.textContent='×';remove.title=`${t('Delete line')} ${index+1}`;remove.setAttribute('aria-label',remove.title);
      remove.onclick=()=>{
        const field=$('graph-source');field.value=removeGraphInputLine(field.value,index);field.oninput();persist();
      };
      row.append(remove,number);gutter.append(row);
    });
    syncInputLineScroll();
  }

  function formulas(){
    const next=JSON.stringify([value('graph-source'),kind(),state.derivative,state.secondDerivative,state.result?.derivativeExpression,state.result?.secondDerivativeExpression,selected(),state.selectedDerivativeOrder,options().displayDigits,document.documentElement.lang,getColors(),surface.color]);if(next===formulaSignature)return;formulaSignature=next;
    $('graph-derivative-label').textContent=`f${(state.derivative??selected())+1}′`;
    $('graph-second-derivative-label').textContent=`f${(state.secondDerivative??selected())+1}″`;
    const variable=kind()==='sequence'?'n':['parametric','polar','space','differential'].includes(kind())?'t':'x',labels=expressions().map((s,i)=>kind()==='cartesian'?cartesianFormula(s,i):['parametric','space'].includes(kind())?parametricFormula(s,i,kind()==='space'):kind()==='surface'?surfaceFormula(s):kind()==='differential'?`diff(y,t)=${s}`:kind()==='polar'?`r${i+1}(t)=${s}`:`f${i+1}(${variable})=${s}`);
    if(state.derivative!==null&&kind()==='cartesian'&&expressions()[state.derivative])labels.push(`diff(f${state.derivative+1}(x),x)`+(state.result?.derivativeSelected===state.derivative&&state.result?.derivativeExpression?`=${state.result.derivativeExpression}`:''));
    if(state.secondDerivative!==null&&kind()==='cartesian'&&expressions()[state.secondDerivative])labels.push(`diff(f${state.secondDerivative+1}(x),x,2)`+(state.result?.secondDerivativeSelected===state.secondDerivative&&state.result?.secondDerivativeExpression?`=${state.result.secondDerivativeExpression}`:''));
    for(const line of graphSources(value('graph-source'),kind()).filter(isGraphShading))labels.push(graphShadingBody(line).split(';')[0].trim());
    renderFormulas($('graph-formulas'),labels,{digits:options().displayDigits});
    const lines=[...$('graph-formulas').children],count=expressions().length;
    function removeButton(line,label,remove){
      const button=document.createElement('button');button.type='button';button.className='graph-formula-remove';button.textContent='×';button.setAttribute('aria-label',label);button.title=label;button.onclick=remove;line.append(button);
    }
    function selectButton(line,active,label,pick,color){
      line.classList.toggle('selected-curve',active);line.style.setProperty('--curve-color',color);
      const button=document.createElement('button');button.type='button';button.className='graph-formula-select';button.setAttribute('aria-label',label);button.setAttribute('aria-pressed',String(active));button.append(...line.childNodes);line.append(button);button.onclick=pick;
    }
    lines.slice(0,count).forEach((line,i)=>{
      const pick=()=>{$('graph-selected').value=String(i);$('graph-selected').onchange();};
      selectButton(line,state.selectedDerivativeOrder===0&&i===selected(),`f${i+1}`,pick,['surface','space'].includes(kind())&&count===1?surface.color:graphCurveColor(i,getColors()));
      removeButton(line,`${t('Delete graph')}: f${i+1}`,()=>removeSource(i));
    });
    const hasDerivative=state.derivative!==null&&kind()==='cartesian'&&expressions()[state.derivative];
    if(hasDerivative){
      selectButton(lines[count],state.selectedDerivativeOrder===1,`f${state.derivative+1}′`,()=>selectDerivative(1),graphCurveColor(count,getColors()));
      removeButton(lines[count],t('Delete derivative curve'),()=>{rememberInput();state.derivative=null;if(state.selectedDerivativeOrder===1)state.selectedDerivativeOrder=0;$('graph-derivative').checked=false;clearPlot();formulas();queue();persist();});
    }
    const hasSecondDerivative=state.secondDerivative!==null&&kind()==='cartesian'&&expressions()[state.secondDerivative];
    if(hasSecondDerivative){
      const index=count+(hasDerivative?1:0);
      selectButton(lines[index],state.selectedDerivativeOrder===2,`f${state.secondDerivative+1}″`,()=>selectDerivative(2),graphCurveColor(index,getColors()));
      removeButton(lines[index],`${t('Delete derivative curve')}: f${state.secondDerivative+1}″`,()=>{rememberInput();state.secondDerivative=null;if(state.selectedDerivativeOrder===2)state.selectedDerivativeOrder=0;$('graph-second-derivative').checked=false;clearPlot();formulas();queue();persist();});
    }
    lines.slice(count+(hasDerivative?1:0)+(hasSecondDerivative?1:0)).forEach((line,i)=>removeButton(line,`${t('Delete shading')}: ${i+1}`,()=>removeSource(i,true)));
  }

  function table(){
    if(tableResult===state.result&&tableDigits===options().displayDigits&&tableLanguage===document.documentElement.lang)return;tableResult=state.result;tableDigits=options().displayDigits;tableLanguage=document.documentElement.lang;
    const table=document.createElement('table'),head=document.createElement('thead'),header=document.createElement('tr');
    for(const name of ['Curve','x / n','y',...(state.result.spaceCurves?['z','t']:state.result.curveParameters?['t']:state.result.surface?['z']:[])]){const th=document.createElement('th');th.textContent=t(name);header.append(th);}head.append(header);table.append(head);const body=document.createElement('tbody');
    const curves=state.result.surfaces?.map(surface=>surface.surfaceVertices||surface.surface.flat())||state.result.spaceCurves||state.result.curves||state.result.surface||[];
    curves.forEach((curve,i)=>curve.forEach((point,index)=>{if(!point||index%Math.max(1,Math.floor(curve.length/60))!==0)return;const row=document.createElement('tr');for(const number of [i+1,...point,...(state.result.curveParameters?[state.result.curveParameters[i]?.[index]]:[])]){const td=document.createElement('td');td.textContent=displayNumber(number,options().displayDigits);row.append(td);}if(!state.result.surface){row.tabIndex=0;const pick=()=>{if(i===state.result.derivativeCurveIndex&&state.derivative!==null)selectDerivative(1);else if(i===state.result.secondDerivativeCurveIndex&&state.secondDerivative!==null)selectDerivative(2);else if(i<expressions().length){$('graph-selected').value=String(i);$('graph-selected').onchange();}selectTrace(point,state.result.curveParameters?.[i]?.[index]??point[0]);};row.onclick=pick;row.onkeydown=e=>{if(['Enter',' '].includes(e.key)){e.preventDefault();pick();}};}body.append(row);}));table.append(body);$('graph-table').replaceChildren(table);
  }

  function renderAnalysis(){
    const container=$('graph-analysis-result');container.replaceChildren();if(!state.analysis)return;
    const title=document.createElement('div');title.textContent=`${t($('graph-analysis-action').selectedOptions[0]?.textContent||'Analyze')} · ${analysisCurveLabel(analysisCurveKey())}`+(['intersection','intersectionangle'].includes(state.analysis.analysis)?` × ${analysisCurveLabel(Number(value('graph-other')))}`:'');container.append(title);
    const angleText=angle=>`${displayNumber(angle.value,options().displayDigits)}° (${displayNumber(angle.radians,options().displayDigits)} rad)`;
    if(state.analysis.unit==='deg'){
      const note=document.createElement('div');note.textContent=t(state.analysis.analysis==='tangentangle'?'Tangent angle: inclination from the positive x axis (0° ≤ θ < 180°).':'Intersection angle: smaller angle between tangents (0°–90°).');container.append(note);
    }
    if(state.analysis.value!==undefined){if(state.analysis.unit==='deg'){const value=document.createElement('div');value.textContent=angleText(state.analysis);container.append(value);}else container.append(mathDisplay({kind:'number',value:String(state.analysis.value)},options().displayDigits,true));}
    if(state.analysis.vertical){const note=document.createElement('div');note.textContent=t('Vertical tangent');container.append(note);}
    for(const item of state.analysis.asymptotes||[])container.append(mathDisplay(item.tree,options().displayDigits));
    if(state.analysis.note){const note=document.createElement('div');note.textContent=state.analysis.note;container.append(note);}
    for(const [index,point] of (state.analysis.points||[]).entries()){const button=document.createElement('button');button.className='analysis-point';button.append(mathDisplay({kind:'tuple',args:point.map(n=>({kind:'number',value:String(n)}))},options().displayDigits,true));const angle=state.analysis.angles?.[index];if(angle)button.append(document.createTextNode(` · ${angle.value===null?t('Tangent is undefined at this point'):angleText(angle)}`));button.onclick=()=>{if(kind()==='cartesian')selectTrace(point);else{state.trace=point;render();}};container.append(button);}
    if(state.analysis.truncated){const note=document.createElement('div');note.textContent=t('First 80 points shown');container.append(note);}
    if(!state.analysis.points?.length&&!state.analysis.asymptotes?.length&&state.analysis.value===undefined&&!state.analysis.vertical){const note=document.createElement('div');note.textContent=t('No points found in this interval');container.append(note);}
  }
  return {syncInputLineScroll,inputLineControls,formulas,table,renderAnalysis};
}
