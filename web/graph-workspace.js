import {positiveYRange,fitYRange,yAtFraction} from './graph-y-scale.js';
import {graphRangeAxes,graphInputTree,planarTreeKind,graphSources,isGraphShading,graphVisibilityKeys,hasImplicitSurface,graphExpressions,appendGraphSource,removeGraphSource,createGraphInputHistory,graphSelectedCurveIndex,graphAnalysisTarget,graphAnalysisCurves} from './graph-input.js';

import {createGraphRangeControls} from './graph-ranges.js';
import {createGraphPresentation} from './graph-presentation.js';
import {createGraphParameterControls} from './graph-parameters.js';
import {createGraphComputation} from './graph-computation.js';

import {bindMathPaste} from './math-input.js';

import {plotGraph as plot} from './graph-canvas.js';
import {defaultGraphColors} from './graph-colors.js';
import {mathDisplay} from './math-display.js';

import {displayNumber} from './display-format.js';
import {bindGraphGestures,transformBounds,nearestPoint,curvePointAtX} from './graph-view.js';
import {surfaceZRange,surfaceSampleCount} from './surface-geometry.js';
import {graphSamplingInterval} from './graph-sampling.js';
import {t,setText} from './i18n.js';
import {graphSvg,graphPng} from './graph-export.js';
import {downloadFile} from './storage.js';

// Keep historical source-helper imports available through this entry point.
export {graphInputTree,implicitFormula,cartesianFormula,graphExpressionTarget,isImplicitSurface,surfaceFormula,splitTopLevel,graphCurveLimit,graphSourceLimit,hasImplicitSurface,graphSources,isGraphShading,graphShadingBody,graphExpressions,appendGraphSource,removeGraphSource,removeGraphInputLine,createGraphInputHistory,graphSelectedCurveIndex,graphAnalysisTarget,graphAnalysisCurves} from './graph-input.js';
export {graphShadings} from './graph-shading.js';

export function createGraphWorkspace({execute,options,onError:reportError,onClearError=()=>{},persist,isBusy,isReady=()=>true,saved={},getColors=()=>defaultGraphColors}){
  const $=id=>document.getElementById(id),value=id=>$(id).value,kind=()=>value('graph-kind');
  // One session state object is shared by controllers, including replacement maps on Undo.
  const graphState={
    hiddenKeys:new Set(saved.hiddenKeys||[]),
    result:null,
    bounds:null,
    analysis:null,
    trace:null,
    integral:null,
    parameters:{...(saved.parameters||{})},
    parameterRanges:{...(saved.parameterRanges||{})},
    derivative:null,
    secondDerivative:null,
    radianAxis:!!saved.radianAxis,
    yLog:!!saved.yLog,
    active:false,
    pending:false,
    timer:null,
    animation:null,
    revision:0,
    analysisRevision:0,
    signature:'',
    animationEnabled:{...(saved.animationEnabled||{})},
    heightScale:[1,.5,2].includes(saved.heightScale)?saved.heightScale:saved.halfHeight?.5:1,
    running:false,
    frame:null,
    parametersOpen:saved.parametersOpen!==false,
    pendingAnalysis:null,
    viewDragging:false,
    parameterDragging:false,
    parameterUpdatePending:false,
    exporting:false,
    selectedDerivativeOrder:0
  };
  const onError=message=>{setText($('graph-status'),message);$('graph-status').classList.add('error');reportError(message);};

  const viewSampler=graphSamplingInterval(()=>{if(graphState.pending&&graphState.active&&!graphState.running&&!isBusy()&&isReady())run();});
  const window=$('graph-plot').ownerDocument.defaultView;

  function exportControls(){for(const format of ['svg','png'])$('graph-save-'+format).disabled=graphState.exporting||!graphState.result||!graphState.bounds;}
  for(const format of ['svg','png'])$('graph-save-'+format).onclick=async()=>{
    if(!graphState.result||!graphState.bounds||graphState.exporting)return;
    graphState.exporting=true;exportControls();
    try{
      let range=graphState.result.surface?zRange():null;
      const shown=range?{...graphState.result,zMin:range[0],zMax:range[1]}:graphState.result;
      const settings={colors:getColors(),digits:options().displayDigits,dots:kind()==='sequence',analysis:graphState.analysis,trace:graphState.trace,integral:graphState.integral,selected:selectedPlotIndex(),radianAxis:graphState.radianAxis,yLog:yLog(),heightScale:graphState.heightScale,surfaceView:surface,...visibilitySettings()};
      // Render synchronously to snapshot the current view before async encoding.
      if(format==='svg')downloadFile('symvacas-graph.svg',graphSvg($('graph-plot'),shown,graphState.bounds,settings),'image/svg+xml');
      else {draw();downloadFile('symvacas-graph.png',await graphPng($('graph-plot').querySelector('canvas')),'image/png');}
    }catch(error){onError(error.message||'Could not export the graph');}
    finally{graphState.exporting=false;exportControls();}
  };
  const requestFrame=callback=>window.requestAnimationFrame?window.requestAnimationFrame(callback):window.setTimeout(callback,16);
  const cancelFrame=id=>window.cancelAnimationFrame?window.cancelAnimationFrame(id):window.clearTimeout(id);
  function draw(){if(graphState.result&&graphState.bounds){let range;try{range=graphState.result.surface?zRange():null;}catch{return;}plot($('graph-plot'),range?{...graphState.result,zMin:range[0],zMax:range[1]}:graphState.result,graphState.bounds,{colors:getColors(),digits:options().displayDigits,dots:kind()==='sequence',analysis:graphState.analysis,trace:graphState.trace,integral:graphState.integral,selected:selectedPlotIndex(),radianAxis:graphState.radianAxis,yLog:yLog(),heightScale:graphState.heightScale,surfaceView:surface,...visibilitySettings()});}}
  function queueDraw(){if(graphState.frame!==null)return;graphState.frame=requestFrame(()=>{graphState.frame=null;draw();});}
  const resizeObserver=window.ResizeObserver?new window.ResizeObserver(queueDraw):null;
  resizeObserver?.observe($('graph-plot'));
  const surface={opacity:1,sliceEnabled:false,sliceAxis:'z',slicePosition:0,rotation:35,elevation:32,zoom:1,renderMode:'surface',color:'#007b68',samples:26,autoDensity:true,autoZ:!['graph-zmin','graph-zmax'].every(id=>Number.isFinite(saved.ranges?.[id])),...saved.surface};
  surface.opacity=Number.isFinite(surface.opacity)?Math.max(.1,Math.min(1,surface.opacity)):1;
  surface.sliceAxis=['x','y','z'].includes(surface.sliceAxis)?surface.sliceAxis:'z';
  const storedSection=saved.surface?.slicePosition??saved.surface?.sliceZ??0;
  surface.slicePosition=Number.isFinite(storedSection)?storedSection:0;
  delete surface.sliceZ;
  surface.elevation=Number.isFinite(surface.elevation)?Math.max(-90,Math.min(90,surface.elevation)):32;
  if(!['wireframe','surface','surface-wireframe'].includes(surface.renderMode))surface.renderMode='surface';
  if(!/^#[0-9a-f]{6}$/i.test(surface.color))surface.color='#007b68';
  surface.samples=Number.isFinite(surface.samples)?Math.max(12,Math.min(96,Math.round(surface.samples))):26;
  const sourceDrafts={implicit:'x^2+y^2=1',cartesian:'sin(x)\ncos(x)',parametric:'[cos(t),sin(t)]',space:'C(t)=4*(sin(t),cos(t),0.6*sin(2*t))',polar:'2*cos(3*t)',sequence:'n\nu(n-1)+u(n-2)',surface:'sin(sqrt(x^2+y^2))',differential:'y-t',...saved.sources};
  let sourceKind=kind();sourceDrafts[sourceKind]=value('graph-source');
  const inputHistory=createGraphInputHistory();
  function undoControls(){$('graph-undo').disabled=!inputHistory.canUndo(kind());}
  function rememberInput(){
    inputHistory.remember(kind(),{source:sourceDrafts[kind()],derivative:graphState.derivative,secondDerivative:graphState.secondDerivative,hiddenKeys:[...graphState.hiddenKeys],parameters:graphState.parameters,parameterRanges:graphState.parameterRanges,animationEnabled:graphState.animationEnabled,selected:selected(),selectedDerivativeOrder:graphState.selectedDerivativeOrder,other:Number(value('graph-other'))});
    undoControls();
  }
  const {syncInputLineScroll,inputLineControls,formulas,table,renderAnalysis}=createGraphPresentation({
    $,
    analysisCurveKey:(...args)=>analysisCurveKey(...args),
    analysisCurveLabel:(...args)=>analysisCurveLabel(...args),
    clearPlot,
    expressions:(...args)=>expressions(...args),
    getColors,
    kind,
    options,
    persist,
    queue:(...args)=>queue(...args),
    rememberInput,
    removeSource,
    render,
    selectDerivative,
    selectTrace,
    selected:(...args)=>selected(...args),
    state:graphState,
    surface,
    visibilityKey,
    toggleVisibility,
    value
  });

  const formulaStrip=$('graph-formulas');
  function scrollFormulas(event){
    if(event.ctrlKey||event.shiftKey||Math.abs(event.deltaX)>Math.abs(event.deltaY))return;
    const maximum=formulaStrip.scrollWidth-formulaStrip.clientWidth;
    if(maximum<=0)return;
    const delta=event.deltaY*(event.deltaMode===1?16:event.deltaMode===2?formulaStrip.clientWidth:1);
    const position=Math.max(0,Math.min(maximum,formulaStrip.scrollLeft+delta));
    if(position===formulaStrip.scrollLeft)return;
    formulaStrip.scrollLeft=position;event.preventDefault();
  }
  formulaStrip.addEventListener('wheel',scrollFormulas,{passive:false});
  $('graph-source').addEventListener('scroll',syncInputLineScroll);
  const {fieldNumber,numeric,displayField,editField,analysisRange,syncRangePair,resetRangeDomain,showNumber,renderRangeNumbers,bindRangeTrackClick,rangeIds,sliderIds,rangePairs,pairedSliders,initializeRanges}=createGraphRangeControls({
    $,
    analysisControls,
    currentBounds,
    getAnalysisSliders:()=>analysisSliders,
    options,
    persist,
    queue:(...args)=>queue(...args),
    render,
    state:graphState,
    value
  });

  const displayOptions=()=>({digits:options().displayDigits,notation:'off'});
  const selected=()=>Number(value('graph-selected'))||0;

  const analysisCurveKey=()=>graphState.selectedDerivativeOrder?-graphState.selectedDerivativeOrder:selected();
  const analysisTarget=()=>graphAnalysisTarget(analysisCurveKey(),graphState.derivative,graphState.secondDerivative);
  const otherTarget=()=>graphAnalysisTarget(Number(value('graph-other')),graphState.derivative,graphState.secondDerivative);
  const analysisCurveLabel=key=>graphAnalysisCurves(expressions().length,graphState.derivative,graphState.secondDerivative).find(curve=>curve.key===key)?.label||'';
  let otherChoicesSignature='';
  function otherChoices(){
    const choices=graphAnalysisCurves(expressions().length,graphState.derivative,graphState.secondDerivative).filter(curve=>curve.key!==analysisCurveKey()),signature=JSON.stringify(choices);
    if(signature===otherChoicesSignature)return;otherChoicesSignature=signature;
    const previous=value('graph-other');$('graph-other').replaceChildren(...choices.map(curve=>{const option=document.createElement('option');option.value=String(curve.key);option.textContent=curve.label;return option;}));
    $('graph-other').value=choices.some(curve=>String(curve.key)===previous)?previous:String(choices[0]?.key??'');
  }
  const selectedPlotIndex=()=>graphSelectedCurveIndex(selected(),graphState.selectedDerivativeOrder,
    graphState.derivative!==null&&graphState.result?.derivativeSelected===graphState.derivative?graphState.result.derivativeCurveIndex:-1,
    graphState.secondDerivative!==null&&graphState.result?.secondDerivativeSelected===graphState.secondDerivative?graphState.result.secondDerivativeCurveIndex:-1);
  function selectDerivative(order){
    graphState.selectedDerivativeOrder=order;graphState.pendingAnalysis=null;graphState.analysisRevision++;graphState.analysis=null;graphState.trace=null;graphState.integral=null;
    render();persist();
  }
  const expressions=()=>graphExpressions(value('graph-source'),kind());
  function visibilityKey(index,role='curve'){
    const sources=role==='shade'?graphSources(value('graph-source'),kind()).filter(isGraphShading):expressions();
    return graphVisibilityKeys(sources,kind(),role)[index];
  }
  function toggleVisibility(key){
    if(graphState.hiddenKeys.has(key))graphState.hiddenKeys.delete(key);else graphState.hiddenKeys.add(key);
    graphState.analysis=null;graphState.trace=null;graphState.integral=null;graphState.analysisRevision++;
    render();persist();
  }
  function visibilitySettings(){
    const hiddenCurves=expressions().flatMap((_,i)=>graphState.hiddenKeys.has(visibilityKey(i))?[i]:[]);
    for(const [role,prefix] of [['derivative','derivative'],['secondDerivative','secondDerivative']]){
      const source=graphState[role],index=graphState.result?.[prefix+'CurveIndex'];
      if(source!==null&&Number.isInteger(index)&&graphState.hiddenKeys.has(visibilityKey(source,role)))hiddenCurves.push(index);
    }
    const hiddenShadings=(graphState.result?.shadings||[]).flatMap((shade,i)=>
      (shade.sourceIndex!==undefined?hiddenCurves.includes(shade.sourceIndex):graphState.hiddenKeys.has(visibilityKey(shade.shadeIndex??i,'shade')))?[i]:[]);
    return {hiddenCurves,hiddenShadings};
  }
  const yLog=()=>graphState.yLog&&!['surface','space'].includes(kind());
  const transformView=(bounds,previous,current,zx=1,zy=zx)=>transformBounds(bounds,previous,current,zx,zy,yLog());
  function ensurePositiveY(){if(yLog()){const view=currentBounds(),[min,max]=positiveYRange(view.ymin,view.ymax);showNumber('graph-ymin',min);showNumber('graph-ymax',max);}}
  function yScaleControls(){const button=$('graph-y-scale');button.hidden=['surface','space'].includes(kind());setText(button,yLog()?'y: log10':'y: linear');button.setAttribute('aria-pressed',String(yLog()));}
  function currentBounds(){return {xmin:numeric(['cartesian','implicit','surface'].includes(kind())?'graph-min':'graph-xmin'),xmax:numeric(['cartesian','implicit','surface'].includes(kind())?'graph-max':'graph-xmax'),ymin:numeric('graph-ymin'),ymax:numeric('graph-ymax')};}
  function writeBounds(next){showNumber(['cartesian','implicit','surface'].includes(kind())?'graph-min':'graph-xmin',next.xmin);showNumber(['cartesian','implicit','surface'].includes(kind())?'graph-max':'graph-xmax',next.xmax);showNumber('graph-ymin',next.ymin);showNumber('graph-ymax',next.ymax);for(const pair of new Set(pairedSliders.values()))resetRangeDomain(pair);analysisControls();}
  function zControls(){for(const id of ['graph-zmin','graph-zmax']){$(id).disabled=surface.autoZ;const slider=$(id+'-slider');if(slider)slider.disabled=surface.autoZ;}}
  function zRange(){
    if(surface.autoZ)return surfaceZRange(graphState.result?.zMin??-1,graphState.result?.zMax??1);
    const min=numeric('graph-zmin'),max=numeric('graph-zmax');
    if(!Number.isFinite(max-min)||max<=min)throw new Error('Enter finite values with minimum < maximum');
    return [min,max];
  }
  const {makeRequest,queue,requestParameters,flush,run,analyze}=createGraphComputation({
    $,
    analysisControls,
    analysisTarget,
    clearPlot,
    currentBounds,
    densityControls,
    execute,
    expressions,
    isBusy,
    isReady,
    kind,
    numeric,
    onError,
    options,
    otherTarget,
    parameterControls:(...args)=>parameterControls(...args),
    persist,
    queueDraw,
    render,
    selectedPlotIndex,
    selections,
    sourceDrafts,
    state:graphState,
    surface,
    value,
    viewSampler,
    zRange
  });
  function densityControls(){const implicit=hasImplicitSurface(value('graph-source'));$('graph-surface-samples').max=implicit?'32':'96';const count=surfaceSampleCount(currentBounds(),surface.samples,surface.autoDensity,surface.zoom,hasImplicitSurface(value('graph-source')));$('graph-auto-density').checked=surface.autoDensity;$('graph-surface-samples').disabled=surface.autoDensity;$('graph-surface-samples').value=String(count);$('graph-surface-samples-value').textContent=implicit?`${count} × ${count} × ${count}`:`${count} × ${count}`;}

  function selections(){
    if(graphState.selectedDerivativeOrder===1&&graphState.derivative===null||graphState.selectedDerivativeOrder===2&&graphState.secondDerivative===null)graphState.selectedDerivativeOrder=0;
    const count=expressions().length;
    const before=selected();$('graph-selected').replaceChildren(...Array.from({length:count},(_,i)=>{const option=document.createElement('option');option.value=String(i);option.textContent=`f${i+1}`;return option;}));$('graph-selected').value=String(Math.min(before,Math.max(0,count-1)));otherChoices();
  }

  function clearPlot(){
    graphState.parameterDragging=false;graphState.parameterUpdatePending=false;
    viewSampler.cancel();graphState.viewDragging=false;
    graphState.result=null;graphState.analysis=null;graphState.trace=null;graphState.integral=null;graphState.pendingAnalysis=null;graphState.revision++;graphState.analysisRevision++;
    for(const id of ['graph-plot','graph-table','graph-trace','graph-analysis-result'])$(id).replaceChildren();
    $('graph-status').textContent='';$('graph-status').classList.remove('error');
    exportControls();
  }
  function removeSource(index,shading=false){
    const next=removeGraphSource(value('graph-source'),index,kind(),shading),before=selected(),other=Number(value('graph-other'));
    if(next===value('graph-source'))return;
    rememberInput();
    stopAnimation(false);clearPlot();$('graph-source').value=next;
    const count=expressions().length,adjust=i=>Math.max(0,Math.min(i>index?i-1:i,count-1));
    selections();
    if(!shading){$('graph-selected').value=String(adjust(before));$('graph-other').value=String(adjust(other));}
    if(count>1&&value('graph-other')===value('graph-selected'))$('graph-other').value=String((selected()+1)%count);
    $('graph-source').oninput();persist();
  }
  function render(){
    exportControls();heightControls();densityControls();parameterVisibility();formulas();renderRangeNumbers();analysisControls();syncParameterControls();if(!graphState.result||!graphState.bounds)return;
    for(const [id,number,suffix] of [['graph-rotation',surface.rotation,'°'],['graph-elevation',surface.elevation,'°'],['graph-surface-zoom',surface.zoom*100,'%']]){let output=$(id+'-value');if(!output){output=document.createElement('output');output.id=id+'-value';$(id).insertAdjacentElement('afterend',output);}output.textContent=displayNumber(number,options().displayDigits)+suffix;}
    let shown=graphState.result;
    if(graphState.result.surface){
      surfaceSectionControls();
      let range;try{range=zRange();}catch{return;}
      const [zMin,zMax]=range;shown={...graphState.result,zMin,zMax};
      if(surface.autoZ){showNumber('graph-zmin',zMin);showNumber('graph-zmax',zMax);resetRangeDomain(pairedSliders.get('graph-zmin'));}
    }
    plot($('graph-plot'),shown,graphState.bounds,{colors:getColors(),digits:options().displayDigits,dots:kind()==='sequence',analysis:graphState.analysis,trace:graphState.trace,integral:graphState.integral,selected:selectedPlotIndex(),radianAxis:graphState.radianAxis,yLog:yLog(),heightScale:graphState.heightScale,surfaceView:surface,...visibilitySettings()});
    table();renderAnalysis();
    $('graph-trace').replaceChildren();if(graphState.trace)$('graph-trace').append(mathDisplay({kind:'relation',value:'≈',args:[{kind:'symbol',value:'Trace'},{kind:'tuple',args:graphState.trace.map(n=>({kind:'number',value:String(n)}))}]},options().displayDigits,true));
  }

  const {parameterVisibility,syncParameterControls,parameterControls,parameterPhase}=createGraphParameterControls({
    $,
    bindRangeTrackClick,
    displayField,
    editField,
    fieldNumber,
    onError,
    options,
    parameterChanged,
    persist,
    state:graphState
  });

  for(const [id,preference] of [['graph-ranges','rangesOpen'],['graph-surface-rendering','renderingOpen'],['graph-help','helpOpen']]){
    $(id).open=id==='graph-help'?saved[preference]===true:saved[preference]!==false;
    $(id).addEventListener('toggle',persist);
  }
  function parameterChanged(preview=false){graphState.analysisRevision++;graphState.analysis=null;graphState.trace=null;graphState.integral=null;queueDraw();requestParameters(preview);}

  function changeView(next,commit=true){
    if(yLog()&&next.ymin<=0){const [ymin,ymax]=positiveYRange(next.ymin,next.ymax);next={...next,ymin,ymax};}
    if(!Object.values(next).every(Number.isFinite)||next.xmin>=next.xmax||next.ymin>=next.ymax){onError('Enter finite values with minimum < maximum');return;}
    graphState.viewDragging=!commit;graphState.bounds=next;writeBounds(next);queueDraw();
    if(commit){
      viewSampler.cancel();render();persist();
      if(['cartesian','implicit','surface','differential'].includes(kind())){clearTimeout(graphState.timer);graphState.timer=null;graphState.pending=true;run();}
    }else if(['cartesian','implicit','differential'].includes(kind())){graphState.pending=true;viewSampler.schedule();}
  }
  function surfaceChange(dx,dy,zoom){const previousCount=surfaceSampleCount(currentBounds(),surface.samples,surface.autoDensity,surface.zoom,hasImplicitSurface(value('graph-source')));surface.rotation=((surface.rotation+dx*.7)%360+360)%360;surface.elevation=Math.max(-90,Math.min(90,surface.elevation+dy*.5));surface.zoom=Math.max(.4,Math.min(3,surface.zoom*zoom));$('graph-rotation').value=String(surface.rotation);$('graph-elevation').value=String(surface.elevation);$('graph-surface-zoom').value=String(surface.zoom);queueDraw();persist();if(surface.autoDensity&&previousCount!==surfaceSampleCount(currentBounds(),surface.samples,true,surface.zoom,hasImplicitSurface(value('graph-source'))))queue();}
  function selectTrace(point,parameter=point[0]){
    if(visibilitySettings().hiddenCurves.includes(selectedPlotIndex()))return;
    graphState.trace=point;
    const action=value('graph-analysis-action');
    if(['derivative','tangent','tangentangle'].includes(action)){showNumber('graph-analysis-a',parameter);$('graph-tangent-slider').value=String(parameter);}
    render();
    if(['tangent','tangentangle'].includes(action))analyze(action,parameter);
  }
  const disposeGestures=bindGraphGestures($('graph-plot'),{getBounds:()=>graphState.bounds,onView:changeView,onTrace:position=>{
    if(['cartesian','implicit'].includes(kind())&&!['parametric','polar'].includes(graphState.result?.curveKinds?.[selectedPlotIndex()])){
      const x=graphState.bounds.xmin+(graphState.bounds.xmax-graphState.bounds.xmin)*position.x,y=yAtFraction(1-position.y,graphState.bounds.ymin,graphState.bounds.ymax,yLog());
      const point=curvePointAtX(visibilitySettings().hiddenCurves.includes(selectedPlotIndex())?[]:graphState.result?.curves?.[selectedPlotIndex()]||[],x,y,{fallbackToNearest:false,yLog:yLog()});
      if(point)selectTrace(point);else{graphState.trace=null;render();}
    }else{
      const closest=nearestPoint({...graphState.result,curves:(graphState.result?.curves||[]).map((curve,i)=>visibilitySettings().hiddenCurves.includes(i)?[]:curve)},graphState.bounds,position,selectedPlotIndex(),yLog());if(closest)selectTrace(closest.point,closest.parameter);
    }
  },isSurface:()=>['surface','space'].includes(kind()),onSurface:surfaceChange,getYLog:yLog});
  const zoom=z=>{if(['surface','space'].includes(kind())){surfaceChange(0,0,z);return;}const at={x:.5,y:.5};changeView(transformView(graphState.bounds||currentBounds(),at,at,z));};
  $('graph-zoom-in').onclick=()=>zoom(2);$('graph-zoom-out').onclick=()=>zoom(.5);
  function heightControls(){const button=$('graph-height-toggle'),label=graphState.heightScale===1?'Half height':graphState.heightScale===.5?'Double height':'Full height';button.dataset.heightScale=String(graphState.heightScale);button.setAttribute('aria-pressed',String(graphState.heightScale!==1));button.setAttribute('aria-label',t(label));button.title=t(label);button.textContent=graphState.heightScale===1?'½':graphState.heightScale===.5?'2×':'1×';}
  $('graph-height-toggle').onclick=()=>{graphState.heightScale=graphState.heightScale===1?.5:graphState.heightScale===.5?2:1;heightControls();render();persist();};heightControls();
  $('graph-reset-ranges').onclick=()=>{surface.autoZ=true;$('graph-auto-z').checked=true;zControls();changeView({xmin:-3,xmax:3,ymin:-3,ymax:3});for(const pair of new Set(pairedSliders.values()))resetRangeDomain(pair);};
  $('graph-fit').onclick=()=>{if(['surface','space'].includes(kind())){surface.autoZ=true;$('graph-auto-z').checked=true;zControls();render();if(hasImplicitSurface(value('graph-source')))queue();persist();return;}const view=graphState.bounds||currentBounds(),curves=(graphState.result?.curves||[]).slice(0,expressions().length).filter((_,i)=>!visibilitySettings().hiddenCurves.includes(i)),ys=curves.flat().filter(p=>p&&p.every(Number.isFinite)&&p[0]>=view.xmin&&p[0]<=view.xmax).map(p=>p[1]),range=fitYRange(ys,yLog());if(range)changeView({...view,ymin:range[0],ymax:range[1]});};
  $('graph-reset').onclick=()=>{graphState.analysis=null;graphState.trace=null;graphState.integral=null;surface.rotation=35;surface.elevation=32;surface.zoom=1;$('graph-rotation').value='35';$('graph-elevation').value='32';$('graph-surface-zoom').value='1';if(kind()==='sequence'){showNumber('graph-min',0);showNumber('graph-max',20);changeView({xmin:0,xmax:20,ymin:-2,ymax:20});queue();}else if(kind()==='differential'){showNumber('graph-min',-5);showNumber('graph-max',5);changeView({xmin:-5,xmax:5,ymin:-3,ymax:5});}else if(kind()==='implicit'){changeView({xmin:-3,xmax:3,ymin:-3,ymax:3});}else if(['surface','space'].includes(kind())){surface.autoZ=true;$('graph-auto-z').checked=true;zControls();const extent=kind()==='space'?5:3;changeView({xmin:-extent,xmax:extent,ymin:-extent,ymax:extent});}else changeView({xmin:-10,xmax:10,ymin:-5,ymax:5});};
  $('graph-y-scale').onclick=()=>{graphState.yLog=!graphState.yLog;ensurePositiveY();resetRangeDomain(pairedSliders.get('graph-ymin'));yScaleControls();graphState.trace=null;graphState.analysis=null;graphState.integral=null;graphState.analysisRevision++;changeView(currentBounds());queue();persist();};
  $('graph-axis').onclick=()=>{graphState.radianAxis=!graphState.radianAxis;setText($('graph-axis'),graphState.radianAxis?'x: π rad':'x: decimal');render();persist();};
  $('graph-selected').onchange=()=>{
    graphState.selectedDerivativeOrder=0;graphState.pendingAnalysis=null;graphState.analysisRevision++;graphState.analysis=null;graphState.trace=null;graphState.integral=null;
    if(graphState.derivative!==null&&graphState.derivative!==selected()||graphState.secondDerivative!==null&&graphState.secondDerivative!==selected())rememberInput();
    if($('graph-derivative').checked&&selectedRowKind()==='cartesian')graphState.derivative=selected();
    if($('graph-second-derivative').checked&&selectedRowKind()==='cartesian')graphState.secondDerivative=selected();
    if(graphState.derivative!==null||graphState.secondDerivative!==null)queue();render();persist();
  };
  $('graph-derivative').onchange=()=>{rememberInput();graphState.pendingAnalysis=null;graphState.analysisRevision++;graphState.analysis=null;graphState.trace=null;graphState.integral=null;if(graphState.selectedDerivativeOrder===1)graphState.selectedDerivativeOrder=0;graphState.derivative=$('graph-derivative').checked?selected():null;queue();render();persist();};
  $('graph-second-derivative').onchange=()=>{rememberInput();graphState.pendingAnalysis=null;graphState.analysisRevision++;graphState.analysis=null;graphState.trace=null;graphState.integral=null;if(graphState.selectedDerivativeOrder===2)graphState.selectedDerivativeOrder=0;graphState.secondDerivative=$('graph-second-derivative').checked?selected():null;queue();render();persist();};
  $('graph-undo').onclick=()=>{
    const previous=inputHistory.undo(kind());if(!previous)return;
    stopAnimation(false);clearPlot();graphState.hiddenKeys=new Set(previous.hiddenKeys||[]);
    $('graph-source').value=previous.source;sourceDrafts[kind()]=previous.source;
    graphState.parameters=previous.parameters;graphState.parameterRanges=previous.parameterRanges;graphState.animationEnabled=previous.animationEnabled;
    graphState.selectedDerivativeOrder=previous.selectedDerivativeOrder??0;graphState.derivative=previous.derivative;graphState.secondDerivative=previous.secondDerivative??null;$('graph-derivative').checked=graphState.derivative!==null;$('graph-second-derivative').checked=graphState.secondDerivative!==null;
    selections();$('graph-selected').value=String(previous.selected);$('graph-other').value=String(previous.other);
    parameterControls(Object.keys(graphState.parameters),true);undoControls();inputLineControls();formulas();render();queue();persist();
  };
  $('graph-analysis-run').onclick=()=>analyze();$('graph-analysis-clear').onclick=()=>{graphState.pendingAnalysis=null;graphState.analysisRevision++;graphState.analysis=null;graphState.trace=null;graphState.integral=null;$('graph-status').textContent='';$('graph-status').classList.remove('error');onClearError();render();};
  $('graph-analysis-visible-range').onclick=()=>{
    const [low,high]=analysisRange();
    showNumber('graph-analysis-a',low);showNumber('graph-analysis-b',high);analysisControls();
    $('graph-tangent-slider').value=String(low);persist();
  };
  function selectedRowKind(){
    if(kind()!=='cartesian'||graphState.selectedDerivativeOrder)return kind();
    try{return planarTreeKind(graphInputTree(expressions()[selected()]||'0'));}catch{return 'cartesian';}
  }
  function analysisControls(){
    otherChoices();
    const cartesian=selectedRowKind()==='cartesian';
    $('graph-derivative').disabled=!cartesian;$('graph-second-derivative').disabled=!cartesian;
    setText($('graph-analysis-visible-range'),cartesian?'Use visible x range':'Use visible t range');
    for(const action of ['intersection','intersectionangle','asymptotes'])$('graph-analysis-action').querySelector(`[value="${action}"]`).disabled=!cartesian;
    const action=value('graph-analysis-action'),fixedIntercept=action==='yintercept'&&selectedRowKind()==='cartesian',point=['derivative','tangent','tangentangle'].includes(action),tangent=['tangent','tangentangle'].includes(action);
    $('graph-other').closest('label').hidden=!['intersection','intersectionangle'].includes(action);$('graph-analysis-b').closest('label').hidden=point||fixedIntercept;
    $('graph-analysis-a').closest('label').hidden=fixedIntercept;$('graph-analysis-visible-range').hidden=fixedIntercept;
    $('graph-tangent-position').hidden=!tangent;$('graph-analysis-a-slider').hidden=tangent||fixedIntercept;$('graph-analysis-b-slider').hidden=point||fixedIntercept;
    const pair=pairedSliders.get('graph-analysis-a');if(pair){pair.track.hidden=tangent||fixedIntercept;syncRangePair(pair);}
    const [low,high]=analysisRange(),position=numeric('graph-analysis-a');
    if(Number.isFinite(high-low)&&high>low){$('graph-tangent-slider').min=String(low);$('graph-tangent-slider').max=String(high);if(Number.isFinite(position))$('graph-tangent-slider').value=String(Math.max(low,Math.min(high,position)));}
  }
  $('graph-analysis-action').onchange=()=>{graphState.pendingAnalysis=null;graphState.analysisRevision++;graphState.analysis=null;graphState.integral=null;analysisControls();render();};$('graph-tangent-slider').oninput=()=>{showNumber('graph-analysis-a',Number(value('graph-tangent-slider')));};$('graph-tangent-slider').onchange=()=>analyze(value('graph-analysis-action'));
  $('graph-other').onchange=()=>{graphState.pendingAnalysis=null;graphState.analysisRevision++;graphState.analysis=null;graphState.trace=null;graphState.integral=null;render();persist();};

  const tangentTrack=document.createElement('div');tangentTrack.className='graph-range-slider graph-axis-slider';
  $('graph-tangent-slider').before(tangentTrack);tangentTrack.append($('graph-tangent-slider'));
  bindRangeTrackClick(tangentTrack);
  const analysisSliders=document.createElement('div');analysisSliders.id='graph-analysis-sliders';
  $('graph-analysis').querySelector('summary').after(analysisSliders);analysisSliders.append($('graph-tangent-position'));
  for(const id of ['graph-rotation','graph-elevation','graph-surface-zoom'])$(id).oninput=()=>{const previousCount=surfaceSampleCount(currentBounds(),surface.samples,surface.autoDensity,surface.zoom,hasImplicitSurface(value('graph-source')));surface.rotation=Number(value('graph-rotation'));surface.elevation=Number(value('graph-elevation'));surface.zoom=Number(value('graph-surface-zoom'));render();persist();if(surface.autoDensity&&previousCount!==surfaceSampleCount(currentBounds(),surface.samples,true,surface.zoom,hasImplicitSurface(value('graph-source'))))queue();};
  $('graph-surface-opacity').oninput=()=>{surface.opacity=Number(value('graph-surface-opacity'));render();persist();};
  $('graph-slice-enabled').onchange=()=>{surface.sliceEnabled=$('graph-slice-enabled').checked;surfaceSectionControls();render();persist();};
  $('graph-slice-axis').onchange=()=>{surface.sliceAxis=value('graph-slice-axis');surfaceSectionControls();render();persist();};
  $('graph-slice-z').oninput=()=>{surface.slicePosition=Number(value('graph-slice-z'));render();persist();};
  function surfaceSectionControls(){
    $('graph-surface-opacity').value=String(surface.opacity);
    $('graph-surface-opacity-value').textContent=displayNumber(surface.opacity*100,options().displayDigits)+'%';
    const view=currentBounds(),[min,max]=surface.sliceAxis==='x'?[view.xmin,view.xmax]:surface.sliceAxis==='y'?[view.ymin,view.ymax]:zRange(),position=Math.max(min,Math.min(max,surface.slicePosition));
    if(surface.sliceAxis!=='z'||!surface.autoZ||graphState.result?.surface)surface.slicePosition=position;
    $('graph-slice-enabled').checked=surface.sliceEnabled;$('graph-slice-axis').value=surface.sliceAxis;
    const slider=$('graph-slice-z');slider.min=String(min);slider.max=String(max);slider.value=String(position);slider.disabled=!surface.sliceEnabled;
    $('graph-slice-z-value').textContent=surface.sliceAxis+' = '+displayNumber(position,options().displayDigits);
  }
  $('graph-surface-render').onchange=()=>{surface.renderMode=value('graph-surface-render');render();persist();};
  $('graph-surface-color').oninput=()=>{surface.color=value('graph-surface-color');render();persist();};
  $('graph-surface-samples').oninput=()=>{surface.samples=Number(value('graph-surface-samples'));$('graph-surface-samples-value').textContent=`${surface.samples} × ${surface.samples}`;queue();};
  $('graph-surface-samples').onchange=()=>{persist();queue();};
  $('graph-auto-density').onchange=()=>{surface.autoDensity=$('graph-auto-density').checked;densityControls();persist();queue();};
  $('graph-auto-z').onchange=()=>{surface.autoZ=$('graph-auto-z').checked;zControls();if(!surface.autoZ&&(!Number.isFinite(numeric('graph-zmax')-numeric('graph-zmin'))||numeric('graph-zmax')<=numeric('graph-zmin'))){const [min,max]=surfaceZRange(graphState.result?.zMin??-1,graphState.result?.zMax??1);showNumber('graph-zmin',min);showNumber('graph-zmax',max);}render();if(hasImplicitSurface(value('graph-source')))queue();persist();};
  for(const id of ['graph-zmin','graph-zmax'])$(id).onchange=()=>{try{zRange();render();if(hasImplicitSurface(value('graph-source')))queue();$('graph-status').textContent='';persist();}catch(error){onError(error.message);}};

  function updateButtons(){
    exportControls();
    const animateButton=$('graph-animate'),animateLabel=graphState.animation?'Stop':'Animate';
    animateButton.setAttribute('aria-pressed',String(!!graphState.animation));
    for(const attribute of ['aria-label','title'])animateButton.setAttribute(attribute,t(animateLabel));
    animateButton.dataset.i18narialabel=animateButton.dataset.i18ntitle=animateLabel;
    $('graph-analysis-run').disabled=!!graphState.animation||isBusy()||!isReady();
    undoControls();
  }
  function stopAnimation(refine=true){graphState.parameterDragging=false;graphState.parameterUpdatePending=false;if(!graphState.animation)return;if(graphState.animation.frame!==null)cancelFrame(graphState.animation.frame);graphState.animation=null;if(refine){render();persist();run();}updateButtons();}
  function animateFrame(timestamp){
    const state=graphState.animation;if(!state)return;state.frame=null;
    const now=Number.isFinite(timestamp)?timestamp:window.performance.now();
    state.phase+=state.previous===null?0:Math.max(0,Math.min(.1,(now-state.previous)/1000));state.previous=now;
    if(now-state.updated>=1000/60-1e-6){
      state.updated=now;let changed=false;
      for(const name of Object.keys(graphState.parameters)){if(graphState.animationEnabled[name]===false)continue;const [a,b]=graphState.parameterRanges[name]||[-5,5];state.phases[name]??=parameterPhase(name)-state.phase;graphState.parameters[name]=a+(b-a)*(Math.sin(state.phase+state.phases[name])+1)/2;changed=true;}
      if(changed){graphState.pending=true;if(!graphState.running&&!isBusy()&&isReady())run();}
    }
    state.frame=requestFrame(animateFrame);
  }
  $('graph-animate').onclick=()=>{if(graphState.animation){stopAnimation();return;}clearTimeout(graphState.timer);graphState.timer=null;graphState.analysis=null;graphState.trace=null;graphState.integral=null;render();graphState.animation={frame:null,previous:null,updated:-Infinity,phase:0,phases:Object.fromEntries(Object.keys(graphState.parameters).map(name=>[name,parameterPhase(name)]))};updateButtons();graphState.animation.frame=requestFrame(animateFrame);};
  function parameterRangeVisibility(){
    const axes=graphRangeAxes(value('graph-source'),kind());
    $('graph-mixed-ranges').hidden=!axes.has('t')&&!axes.has('theta')||kind()==='differential';
    $('graph-t-ranges').hidden=!axes.has('t');$('graph-theta-ranges').hidden=!axes.has('theta');
    const primary=pairedSliders.get('graph-min');if(primary)primary.track.closest('.graph-range-pair').hidden=['parametric','polar','space'].includes(kind());
  }
  function typeControls(){
    for(const section of $('graph-help').querySelectorAll('[data-graph-help-kind]'))section.hidden=section.dataset.graphHelpKind!==kind();
    ensurePositiveY();yScaleControls();const yPair=pairedSliders.get('graph-ymin');if(yPair)resetRangeDomain(yPair);parameterRangeVisibility();$('graph-reset-ranges').hidden=kind()!=='surface';$('graph-viewport-ranges').hidden=['cartesian','implicit','surface'].includes(kind());for(const id of ['graph-surface-z-range','graph-surface-rendering'])$(id).hidden=!['surface','space'].includes(kind());$('graph-surface-samples').closest('.graph-surface-density').hidden=kind()==='space';$('graph-surface-render').closest('label').hidden=kind()==='space';$('graph-surface-section-controls').hidden=kind()==='space';setText($('graph-fit'),['surface','space'].includes(kind())?'Fit Z':'Fit Y');setText($('graph-analysis-visible-range'),kind()==='cartesian'?'Use visible x range':'Use visible t range');$('graph-analysis').hidden=!['cartesian','parametric','polar'].includes(kind());$('graph-derivative-controls').hidden=kind()!=='cartesian';$('graph-initial').closest('label').hidden=!['sequence','differential'].includes(kind());$('graph-t0').closest('label').hidden=kind()!=='differential';for(const action of ['intersection','intersectionangle','asymptotes'])$('graph-analysis-action').querySelector(`[value="${action}"]`).disabled=kind()!=='cartesian';analysisControls();}
  $('graph-kind').onchange=()=>{
    graphState.pendingAnalysis=null;
    sourceDrafts[sourceKind]=value('graph-source');sourceKind=kind();$('graph-source').value=sourceDrafts[sourceKind];inputLineControls();
    stopAnimation(false);
    const view=kind()==='space'?[-5,5,-5,5]:kind()==='sequence'?[0,20,-2,20]:kind()==='differential'?[-5,5,-3,5]:kind()==='cartesian'?[-10,10,-5,5]:[-3,3,-3,3];
    writeBounds({xmin:view[0],xmax:view[1],ymin:view[2],ymax:view[3]});
    if(['parametric','polar','space'].includes(kind())){showNumber('graph-min',0);showNumber('graph-max',2*Math.PI);}
    if(['sequence','differential'].includes(kind())){showNumber('graph-min',view[0]);showNumber('graph-max',view[1]);$('graph-initial').value=kind()==='sequence'?'0,1':'1';}
    graphState.parameters={};graphState.parameterRanges={};parameterControls([],true);graphState.selectedDerivativeOrder=0;graphState.derivative=null;graphState.secondDerivative=null;$('graph-derivative').checked=false;$('graph-second-derivative').checked=false;graphState.result=null;graphState.bounds=null;graphState.analysis=null;graphState.trace=null;graphState.integral=null;graphState.revision++;graphState.analysisRevision++;$('graph-plot').replaceChildren();$('graph-table').replaceChildren();selections();formulas();typeControls();undoControls();queue();persist();
  };
  $('graph-source').oninput=()=>{if(value('graph-source')!==sourceDrafts[kind()])rememberInput();sourceDrafts[kind()]=value('graph-source');inputLineControls();graphState.pendingAnalysis=null;graphState.selectedDerivativeOrder=0;graphState.derivative=null;graphState.secondDerivative=null;$('graph-derivative').checked=false;$('graph-second-derivative').checked=false;graphState.analysis=null;graphState.trace=null;graphState.integral=null;graphState.revision++;graphState.analysisRevision++;selections();formulas();parameterRangeVisibility();queue();};
  bindMathPaste($('graph-source'),{multiline:true,onError});
  for(const id of ['graph-parameter-min','graph-parameter-max','graph-theta-min','graph-theta-max','graph-min','graph-max','graph-ymin','graph-ymax','graph-xmin','graph-xmax','graph-initial','graph-t0'])$(id).onchange=()=>{analysisControls();queue();};
  initializeRanges();
  for(const [id,number] of Object.entries(saved.ranges||{}))if(rangeIds.includes(id))showNumber(id,number);
  for(const suffix of ['min','max']){
    const theta='graph-theta-'+suffix,t='graph-parameter-'+suffix,legacy='graph-'+suffix;
    if(saved.ranges?.[theta]===undefined){const previous=saved.ranges?.[t]??(kind()==='polar'?saved.ranges?.[legacy]:undefined);if(Number.isFinite(previous))showNumber(theta,previous);}
    if(saved.ranges?.[t]===undefined&&['parametric','space'].includes(kind())&&Number.isFinite(saved.ranges?.[legacy]))showNumber(t,saved.ranges[legacy]);
  }
  for(const pair of new Set(pairedSliders.values()))resetRangeDomain(pair);
  selections();formulas();typeControls();setText($('graph-axis'),graphState.radianAxis?'x: π rad':'x: decimal');for(const [id,name] of [['graph-rotation','rotation'],['graph-elevation','elevation'],['graph-surface-zoom','zoom']])$(id).value=String(surface[name]);
  $('graph-surface-render').value=surface.renderMode;$('graph-auto-z').checked=surface.autoZ;zControls();
  $('graph-surface-color').value=surface.color;densityControls();surfaceSectionControls();
  renderRangeNumbers();parameterControls([],true);inputLineControls();
  function addExpression(source,graphKind){
    const next=appendGraphSource(kind()===graphKind?value('graph-source'):sourceDrafts[graphKind]||'',source,graphKind);
    if(kind()!==graphKind){$('graph-kind').value=graphKind;$('graph-kind').onchange();}
    $('graph-source').value=next;$('graph-source').oninput();persist();
  }
  return {addExpression,run,render,flush,snapshot:()=>({sources:{...sourceDrafts,[kind()]:value('graph-source')},parameters:{...graphState.parameters},parameterRanges:graphState.parameterRanges,parametersOpen:graphState.parametersOpen,rangesOpen:$('graph-ranges').open,renderingOpen:$('graph-surface-rendering').open,helpOpen:$('graph-help').open,animationEnabled:{...graphState.animationEnabled},heightScale:graphState.heightScale,halfHeight:graphState.heightScale===.5,radianAxis:graphState.radianAxis,yLog:graphState.yLog,surface:{...surface},hiddenKeys:[...graphState.hiddenKeys],ranges:Object.fromEntries(rangeIds.filter(id=>!(surface.autoZ&&id.startsWith('graph-z'))&&value(id)!==''&&Number.isFinite(numeric(id))).map(id=>[id,numeric(id)]))}),updateButtons,activate(value){graphState.active=value;if(graphState.active&&(!graphState.result||graphState.pending))queue();if(!graphState.active){viewSampler.cancel();graphState.viewDragging=false;graphState.pendingAnalysis=null;clearTimeout(graphState.timer);graphState.timer=null;stopAnimation(false);}},dispose(){formulaStrip.removeEventListener('wheel',scrollFormulas);viewSampler.cancel();graphState.viewDragging=false;graphState.pendingAnalysis=null;graphState.active=false;disposeGestures();resizeObserver?.disconnect();if(graphState.frame!==null)cancelFrame(graphState.frame);clearTimeout(graphState.timer);stopAnimation(false);graphState.revision++;graphState.analysisRevision++;}};
}
