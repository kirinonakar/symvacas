import {surfaceLightingGradient} from './surface-geometry.js';

// Low z is violet, high z is red. Keep these stops aligned with SurfaceColors.
export const surfaceRainbowStops=[[128,0,255],[0,0,255],[0,255,255],[0,255,0],[255,255,0],[255,0,0]];
export function surfaceRainbowRgb(height){
  const at=Math.max(0,Math.min(1,height))*5,index=Math.min(4,Math.floor(at)),t=at-index;
  return surfaceRainbowStops[index].map((v,i)=>Math.round(v+(surfaceRainbowStops[index+1][i]-v)*t));
}
export function surfaceGradientValue(gradient,point,fallback){
  if(!gradient)return fallback;
  const dx=gradient.end[0]-gradient.start[0],dy=gradient.end[1]-gradient.start[1];
  return gradient.min+(gradient.max-gradient.min)*((point[0]-gradient.start[0])*dx+(point[1]-gradient.start[1])*dy)/(dx*dx+dy*dy);
}
// The height plane, rather than screen y, anchors colors during camera rotation.
export function rainbowSurfaceFill(ctx,face,project,zmin,zmax){
  const source=face.source.map(project),heights=face.source.map(p=>(p[2]-zmin)/(zmax-zmin));
  const height=surfaceLightingGradient(source,heights),lighting=face.levels?surfaceLightingGradient(source,face.levels):null;
  const fallback=face.levels?face.levels.reduce((s,v)=>s+v,0)/3:(.65+.35*face.height)*face.light;
  const color=(value,point)=>`rgb(${surfaceRainbowRgb(value).map(v=>Math.round(v*Math.max(0,Math.min(1,surfaceGradientValue(lighting,point,fallback))))).join(',')})`;
  if(!height){
    if(!lighting)return color(heights[0],source[0]);
    const fill=ctx.createLinearGradient(...lighting.start,...lighting.end);
    fill.addColorStop(0,color(heights[0],lighting.start));fill.addColorStop(1,color(heights[0],lighting.end));return fill;
  }
  const fill=ctx.createLinearGradient(...height.start,...height.end),span=height.max-height.min;
  const stops=[height.min,...[0,.2,.4,.6,.8,1].filter(v=>v>height.min&&v<height.max),height.max];
  for(const value of stops){
    const t=(value-height.min)/span,point=height.start.map((v,i)=>v+(height.end[i]-v)*t);
    fill.addColorStop(t,color(value,point));
  }
  return fill;
}
