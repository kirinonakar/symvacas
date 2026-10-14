import {yCoordinate,yValue,yFraction,yAtFraction} from './graph-y-scale.js';
const clamp=(value,low,high)=>Math.max(low,Math.min(high,value));
export function transformBounds(bounds,previous,current,zx=1,zy=zx,yLog=false){
  const width=bounds.xmax-bounds.xmin,height=yCoordinate(bounds.ymax,yLog)-yCoordinate(bounds.ymin,yLog);
  const anchorX=bounds.xmin+width*previous.x,anchorY=yCoordinate(bounds.ymax,yLog)-height*previous.y;
  const nextWidth=clamp(width/zx,2e-7,2e8),nextHeight=clamp(height/zy,2e-7,yLog?600:2e8);
  const xmin=anchorX-nextWidth*current.x,ymax=anchorY+nextHeight*current.y;
  return {xmin,xmax:xmin+nextWidth,ymin:yValue(yLog?clamp(ymax-nextHeight,-300,300-nextHeight):ymax-nextHeight,yLog),ymax:yValue(yLog?clamp(ymax,nextHeight-300,300):ymax,yLog)};
}
export function pinchFactors(old,next,axis=null){
  axis=axis||(Math.abs(old.x)>2*Math.abs(old.y)?'x':Math.abs(old.y)>2*Math.abs(old.x)?'y':'xy');
  const ratio=(a,b)=>Math.abs(a)<4?1:clamp(Math.abs(b/a),.5,2);
  const z=ratio(Math.hypot(old.x,old.y),Math.hypot(next.x,next.y));
  return {axis,zx:axis==='x'?ratio(old.x,next.x):axis==='y'?1:z,zy:axis==='y'?ratio(old.y,next.y):axis==='x'?1:z};
}
export function nearestPoint(result,bounds,position,selected=0,yLog=false){
  let best=null,distance=Infinity;
  for(const [index,point] of (result?.curves?.[selected]||[]).entries()){
    if(!point||!point.every(Number.isFinite)||yLog&&point[1]<=0)continue;
    const dx=(point[0]-bounds.xmin)/(bounds.xmax-bounds.xmin)-position.x,dy=1-yFraction(point[1],bounds.ymin,bounds.ymax,yLog)-position.y;
    if(dx*dx+dy*dy<distance){distance=dx*dx+dy*dy;best={point,index,parameter:result.curveParameters?.[selected]?.[index]??point[0]};}
  }
  return best;
}
export function curvePointAtX(curve,x,referenceY=null,{fallbackToNearest=true,yLog=false}={}){
  if(!Number.isFinite(x))return null;
  const finite=point=>point?.length>=2&&point.every(Number.isFinite)&&(!yLog||point[1]>0);
  let best=null,score=Infinity,nearest=null,distance=Infinity;
  const consider=point=>{
    if(!finite(point))return;
    const nextScore=Number.isFinite(referenceY)?Math.abs(yCoordinate(point[1],yLog)-yCoordinate(referenceY,yLog)):-point[1];
    if(!best||nextScore<score){best=point;score=nextScore;}
  };
  for(let i=0;i<curve.length;i++){
    const point=curve[i];if(!finite(point))continue;
    const dx=Math.abs(point[0]-x);
    if(!nearest||dx<distance||(dx===distance&&point[1]>nearest[1])){nearest=point;distance=dx;}
    if(point[0]===x)consider([x,point[1]]);
    const previous=curve[i-1];if(!finite(previous))continue;
    if(previous[0]===point[0]){
      if(point[0]===x)consider([x,Number.isFinite(referenceY)?clamp(referenceY,Math.min(previous[1],point[1]),Math.max(previous[1],point[1])):Math.max(previous[1],point[1])]);
      continue;
    }
    const at=(x-previous[0])/(point[0]-previous[0]),epsilon=16*Number.EPSILON;
    if(!Number.isFinite(at)||at<-epsilon||at>1+epsilon)continue;
    const fraction=clamp(at,0,1);
    consider([x,yAtFraction(fraction,previous[1],point[1],yLog)]);
  }
  return best||(fallbackToNearest?nearest:null);
}
// Bind to the container: the SVG can be redrawn without losing pointer capture.
export function bindGraphGestures(container,{getBounds,onView,onTrace,isSurface=()=>false,onSurface=()=>{},getYLog=()=>false}){
  const pointers=new Map();let moved=false,axis=null,start=null;
  function position(event){const rect=container.getBoundingClientRect();return {x:(event.clientX-rect.left)/rect.width,y:(event.clientY-rect.top)/rect.height};}
  function frame(){const values=[...pointers.values()],center=values.reduce((sum,p)=>({x:sum.x+p.x/values.length,y:sum.y+p.y/values.length}),{x:0,y:0});return {center,span:values.length>1?{x:values[1].x-values[0].x,y:values[1].y-values[0].y}:null};}
  function viewport(p){const canvas=container.querySelector('canvas'),height=Number(canvas?.dataset.plotHeight)||460,left=Number(canvas?.dataset.plotLeft)||42,width=Number(canvas?.dataset.plotWidth)||716;return {x:(p.x*800-left)/width,y:(p.y*height-42)/(height-84)};}
  const down=event=>{if(event.button>0||!getBounds())return;container.setPointerCapture?.(event.pointerId);pointers.set(event.pointerId,position(event));if(pointers.size===1){moved=false;start=position(event);}else moved=true;axis=null;};
  const move=event=>{
    if(!pointers.has(event.pointerId))return;
    const before=frame(),old=pointers.get(event.pointerId),next=position(event);pointers.set(event.pointerId,next);const after=frame();
    if(!moved&&Math.hypot(next.x-start.x,next.y-start.y)<.006)return;
    moved=true;event.preventDefault();
    const rect=container.getBoundingClientRect(),factors=before.span&&after.span?pinchFactors({x:before.span.x*rect.width,y:before.span.y*rect.height},{x:after.span.x*rect.width,y:after.span.y*rect.height},axis):{zx:1,zy:1,axis:null};axis=factors.axis;
    if(isSurface())onSurface((after.center.x-before.center.x)*rect.width,(after.center.y-before.center.y)*rect.height,Math.sqrt(factors.zx*factors.zy));
    else onView(transformBounds(getBounds(),viewport(before.center),viewport(after.center),factors.zx,factors.zy,getYLog()),false);
  };
  const up=event=>{if(!pointers.has(event.pointerId))return;const at=position(event);pointers.delete(event.pointerId);axis=null;if(!pointers.size){if(moved){if(!isSurface())onView(getBounds(),true);}else if(event.type==='pointerup'&&!isSurface())onTrace(viewport(at));}moved=true;};
  const wheel=event=>{if(!getBounds())return;event.preventDefault();const z=Math.exp(clamp(-event.deltaY*.002,-.4,.4));if(isSurface())onSurface(0,0,z);else{const at=viewport(position(event));onView(transformBounds(getBounds(),at,at,event.shiftKey?1:z,event.altKey?1:z,getYLog()),true);}};
  const key=event=>{if(!getBounds()||isSurface())return;const movement={ArrowLeft:[.1,0],ArrowRight:[-.1,0],ArrowUp:[0,.1],ArrowDown:[0,-.1]}[event.key];if(movement){event.preventDefault();onView(transformBounds(getBounds(),{x:.5,y:.5},{x:.5+movement[0],y:.5+movement[1]},1,1,getYLog()),true);}else if(['+','=','-'].includes(event.key)){event.preventDefault();onView(transformBounds(getBounds(),{x:.5,y:.5},{x:.5,y:.5},event.key==='-'?.5:2,event.key==='-'?.5:2,getYLog()),true);}};
  const listeners={pointerdown:down,pointermove:move,pointerup:up,pointercancel:up,lostpointercapture:up,wheel,keydown:key};
  for(const [name,handler] of Object.entries(listeners))container.addEventListener(name,handler,{passive:false});
  return ()=>{for(const [name,handler] of Object.entries(listeners))container.removeEventListener(name,handler);pointers.clear();};
}
