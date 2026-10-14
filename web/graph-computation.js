// Graph requests, scheduling, analysis, and stale-response rejection.
import {curvePointAtX} from './graph-view.js';
import {planarTreeKind,graphInputTree,hasImplicitSurface,splitTopLevel} from './graph-input.js';
import {graphPreviewRequest,graphSamplingIdentity} from './graph-sampling.js';
import {graphShadings} from './graph-shading.js';
import {parse} from './parser.js';
import {surfaceSampleCount} from './surface-geometry.js';

export function createGraphComputation({
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
  parameterControls,
  persist,
  queueDraw,
  render,
  selectedPlotIndex,
  selections,
  sourceDrafts,
  state,
  surface,
  value,
  viewSampler,
  zRange
}){
  function makeRequest(){
    const trees=expressions().map(s=>graphInputTree(s,kind())),shadings=graphShadings(value('graph-source'),kind()),prefix=kind()==='polar'?'graph-theta':['parametric','space'].includes(kind())?'graph-parameter':'graph',min=numeric(prefix+'-min'),max=numeric(prefix+'-max'),view=currentBounds();
    if(!trees.length&&!shadings.length)throw new Error('Enter a function to graph');
    if(![min,max,...Object.values(view)].every(Number.isFinite)||max<=min||view.xmax<=view.xmin||view.ymax<=view.ymin)throw new Error('Enter finite values with minimum < maximum');
    const yLog=state.yLog&&!['surface','space'].includes(kind());
    if(yLog&&view.ymin<=0)throw new Error('Log y requires 0 < y min < y max');
    if(kind()==='surface')zRange();
    const request={...options(),action:'graph',angle:'RAD',yLog,graphKind:kind(),trees,shadings,min,max,xMin:view.xmin,xMax:view.xmax,yMin:view.ymin,yMax:view.ymax,surfaceYMin:view.ymin,surfaceYMax:view.ymax,parameterMin:numeric('graph-parameter-min'),parameterMax:numeric('graph-parameter-max'),thetaMin:numeric('graph-theta-min'),thetaMax:numeric('graph-theta-max'),parameters:{...state.parameters},variable:['parametric','polar','space','differential'].includes(kind())?'t':kind()==='sequence'?'n':'x',samples:state.animation?200:500};
    if(kind()==='space'){[request.surfaceZMin,request.surfaceZMax]=surface.autoZ?[-5,5]:zRange();}if(kind()==='surface'){const density=surfaceSampleCount(view,surface.samples,surface.autoDensity,surface.zoom,hasImplicitSurface(value('graph-source')));request.surfaceSamples=state.animation?Math.min(density,hasImplicitSurface(value('graph-source'))?16:32):density;[request.surfaceZMin,request.surfaceZMax]=surface.autoZ?[view.ymin,view.ymax]:zRange();}
    if(kind()==='sequence')request.initialTrees=splitTopLevel(value('graph-initial')).map(s=>parse(s));
    if(kind()==='differential'){request.initialValues=splitTopLevel(value('graph-initial')).map(Number);request.t0=numeric('graph-t0');}
    if(state.derivative!==null&&kind()==='cartesian'&&trees[state.derivative])request.derivativeSelected=state.derivative;
    if(state.secondDerivative!==null&&kind()==='cartesian'&&trees[state.secondDerivative])request.secondDerivativeSelected=state.secondDerivative;
    return request;
  }

  function queue(){state.pending=true;densityControls();clearTimeout(state.timer);state.timer=null;if(state.animation||!state.active)return;state.timer=setTimeout(()=>{state.timer=null;if(state.active&&!state.running&&!isBusy()&&isReady())run();},180);}

  function flush(){
    if(state.pendingAnalysis&&!state.running&&!isBusy()&&isReady()){const next=state.pendingAnalysis;state.pendingAnalysis=null;analyze(next.action,next.point);return;}
    if(!state.animation&&state.pending&&state.active&&!state.running&&!isBusy()&&isReady()&&state.timer===null){if(state.viewDragging)viewSampler.schedule();else queue();}
  }

  async function run(){
    if(value('graph-source')!==sourceDrafts[kind()])$('graph-source').oninput();
    clearTimeout(state.timer);state.timer=null;if(state.running||isBusy()||!isReady()){state.pending=true;return;}state.pending=false;state.running=true;
    try{
      if(!value('graph-source').trim()){clearPlot();parameterControls([],true);selections();render();persist();return;}
      const preview=state.viewDragging&&['cartesian','implicit','differential'].includes(kind()),baseRequest=makeRequest(),request=preview?graphPreviewRequest(baseRequest):baseRequest,identity=graphSamplingIdentity(baseRequest),token=++state.revision,source=value('graph-source'),graphKind=kind();
      const nextSignature=JSON.stringify([source,graphKind,state.parameters,state.derivative,state.secondDerivative]);if(nextSignature!==state.signature){state.analysis=null;state.trace=null;state.integral=null;state.analysisRevision++;state.signature=nextSignature;}
      const response=await execute(request,{background:preview||!!state.animation});if(token!==state.revision||source!==value('graph-source')||graphKind!==kind()||!state.animation&&identity!==graphSamplingIdentity(makeRequest()))return;
      if(!response.ok){onError(response.error);return;}
      state.result=response;state.bounds=currentBounds();$('graph-status').textContent='';parameterControls(response.parameters);
      if(state.animation||state.viewDragging)queueDraw();else{selections();render();persist();}
    }catch(error){onError(error.message);}finally{state.running=false;flush();}
  }

  async function analyze(action=value('graph-analysis-action'),point=null){
    if(state.running||isBusy()||!isReady()){state.pendingAnalysis={action,point};return;}
    if(state.pending&&kind()==='cartesian'&&['derivative','tangent','tangentangle'].includes(action)){state.pendingAnalysis={action,point};return run();}
    state.pendingAnalysis=null;clearTimeout(state.timer);state.timer=null;
    const token=++state.analysisRevision;
    try{
      const fixedIntercept=action==='yintercept'&&kind()==='cartesian'&&planarTreeKind(graphInputTree(expressions()[analysisTarget()?.source]||'0'))==='cartesian';
      const trees=expressions().map(s=>graphInputTree(s,kind())),a=fixedIntercept?0:point??numeric('graph-analysis-a'),b=fixedIntercept||['derivative','tangent','tangentangle'].includes(action)?a:numeric('graph-analysis-b'),view=state.bounds||currentBounds(),source=value('graph-source'),graphKind=kind();
      if(!Number.isFinite(a)||!Number.isFinite(b)||!fixedIntercept&&!['derivative','tangent','tangentangle'].includes(action)&&a>=b)throw new Error('Enter finite values with a < b');
      const currentParameters={...state.parameters};
      const target=analysisTarget(),other=otherTarget();
      if(!target||target.source>=trees.length||['intersection','intersectionangle'].includes(action)&&(!other||other.source>=trees.length||JSON.stringify(target)===JSON.stringify(other)))throw new Error('Select two different functions');
      const rowKind=graphKind==='cartesian'?planarTreeKind(trees[target.source]):graphKind;
      const tracePoint=state.trace||(graphKind==='cartesian'&&['derivative','tangent','tangentangle'].includes(action)&&(state.selectedDerivativeOrder!==0||state.result?.implicitCurves?.[selectedPlotIndex()])?curvePointAtX(state.result?.curves?.[selectedPlotIndex()]||[],a,null,{yLog:!!state.yLog}):null);
      const response=await execute({...options(),angle:'RAD',action:'graphAnalysis',graphKind,trees,analysis:action,a,b,selected:target.source,selectedDerivativeOrder:target.order,other:other?.source??0,otherDerivativeOrder:other?.order??0,variable:rowKind==='cartesian'?'x':'t',parameters:currentParameters,tracePoint,xMin:view.xmin,xMax:view.xmax,yMin:view.ymin,yMax:view.ymax});
      if(token!==state.analysisRevision||source!==value('graph-source')||graphKind!==kind()||JSON.stringify(currentParameters)!==JSON.stringify(state.parameters))return;if(!response.ok){onError(response.error);return;}
      state.analysis=response;$('graph-status').textContent='';state.integral=action==='integral'&&rowKind==='cartesian'?[a,b]:null;state.trace=response.points?.[0]||state.trace;$('graph-analysis-action').value=action;analysisControls();render();
    }catch(error){if(token===state.analysisRevision)onError(error.message);}finally{flush();}
  }
  return {makeRequest,queue,flush,run,analyze};
}
