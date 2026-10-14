import {clipGraphSegment} from './graph-geometry.js';
export const yCoordinate=(value,logarithmic=false)=>logarithmic?(value>0?Math.log10(value):NaN):value;
export const yValue=(value,logarithmic=false)=>logarithmic?10**value:value;
export const yFraction=(value,min,max,logarithmic=false)=>(yCoordinate(value,logarithmic)-yCoordinate(min,logarithmic))/(yCoordinate(max,logarithmic)-yCoordinate(min,logarithmic));
export const yAtFraction=(fraction,min,max,logarithmic=false)=>yValue(yCoordinate(min,logarithmic)+fraction*(yCoordinate(max,logarithmic)-yCoordinate(min,logarithmic)),logarithmic);
export function positiveYRange(min,max){
  if(Number.isFinite(min)&&Number.isFinite(max)&&min>0&&max>min)return [min,max];
  const high=Number.isFinite(max)&&max>0?max:10;return [high*.001,high];
}
export function fitYRange(values,logarithmic=false){
  const ys=values.filter(v=>Number.isFinite(v)&&(!logarithmic||v>0));if(!ys.length)return null;
  let low=Infinity,high=-Infinity;for(const value of ys){const at=yCoordinate(value,logarithmic);low=Math.min(low,at);high=Math.max(high,at);}
  const padding=Math.max((high-low)*.12,high===low?(logarithmic?.5:1):1e-6);
  return [yValue(Math.max(logarithmic?-300:-Infinity,low-padding),logarithmic),yValue(Math.min(logarithmic?300:Infinity,high+padding),logarithmic)];
}
export function logYTicks(min,max){
  if(!(min>0&&max>min))return [];
  const low=Math.log10(min),high=Math.log10(max),step=Math.max(1,Math.ceil((high-low)/8)),first=Math.ceil(low/step)*step,ticks=[];
  for(let exponent=first;exponent<=high+1e-12&&ticks.length<10;exponent+=step)ticks.push(10**exponent);
  return ticks.length>=2?ticks:Array.from({length:5},(_,i)=>10**(low+(high-low)*i/4));
}
export function yScaleSegment(first,last,bounds,logarithmic=false){
  if(!logarithmic)return clipGraphSegment(first,last,bounds);
  if(!first||!last)return null;
  if(first[1]<=0||last[1]<=0){const positive=clipGraphSegment(first,last,bounds);if(!positive)return null;[first,last]=positive;}
  const transformed={...bounds,ymin:Math.log10(bounds.ymin),ymax:Math.log10(bounds.ymax)};
  const line=clipGraphSegment([first[0],Math.log10(first[1])],[last[0],Math.log10(last[1])],transformed);
  return line?.map(([x,y])=>[x,10**y])??null;
}
export function clipYPolygon(points,bounds){
  if(!points.every(p=>p&&p.every(Number.isFinite)))return [];
  let polygon=points;
  for(const [axis,edge,lower] of [[0,bounds.xmin,true],[0,bounds.xmax,false],[1,bounds.ymin,true],[1,bounds.ymax,false]]){
    const output=[];let a=polygon.at(-1);if(!a)return [];
    for(const b of polygon){const inA=lower?a[axis]>=edge:a[axis]<=edge,inB=lower?b[axis]>=edge:b[axis]<=edge;
      if(inA!==inB){const t=(edge-a[axis])/(b[axis]-a[axis]);const point=a.map((v,i)=>v+t*(b[i]-v));point[axis]=edge;output.push(point);}
      if(inB)output.push(b);a=b;
    }polygon=output;
  }return polygon;
}

export function yScaleLine(first,last,bounds,logarithmic=false){
  const segment=clipGraphSegment(first,last,bounds);if(!segment)return [];
  const [a,b]=segment;if(!logarithmic||a[1]===b[1])return segment;
  return Array.from({length:65},(_,i)=>{const y=yAtFraction(i/64,a[1],b[1],true),t=(y-a[1])/(b[1]-a[1]);return [a[0]+t*(b[0]-a[0]),y];});
}
