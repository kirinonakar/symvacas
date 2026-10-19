// Keep geometry on the GPU between camera frames. The depth buffer resolves
// visibility per pixel rather than approximating it by triangle centers.
const renderers=new WeakMap();
// Build each vertex once; camera-only frames retain these GPU buffers. Edges
// and their string keys are unnecessary work for the ordinary surface mode.
export function surfaceGpuGeometry(prepared,includeEdges=false){
  const vertices=new Float32Array(prepared.faces.reduce((n,f)=>n+(f.points.length-2)*15,0)),lines=[],seen=new Set(),cache=new Map();
  const normalize=p=>{
    if(!cache.has(p))cache.set(p,p.map((v,i)=>2*(v-prepared.limits[i][0])/(prepared.limits[i][1]-prepared.limits[i][0])-1));
    return cache.get(p);
  };
  let offset=0;
  for(const face of prepared.faces){
    const source=face.source.map(normalize),levels=face.levels;
    let coefficients;
    const light=p=>{
      if(!levels)return (.65+.35*face.height)*face.light;
      const index=face.source.indexOf(p);if(index>=0)return levels[index];
      // Only clipped vertices require barycentric interpolation.
      if(!coefficients){
        const [a,b,c]=source,u=b.map((n,i)=>n-a[i]),v=c.map((n,i)=>n-a[i]);
        const dot=(x,y)=>x.reduce((s,n,i)=>s+n*y[i],0),uu=dot(u,u),uv=dot(u,v),vv=dot(v,v);
        coefficients={a,u,v,uu,uv,vv,d:uu*vv-uv*uv,dot};
      }
      const {a,u,v,uu,uv,vv,d,dot}=coefficients;if(!d)return levels.reduce((s,n)=>s+n,0)/3;
      const q=normalize(p).map((n,i)=>n-a[i]),qu=dot(q,u),qv=dot(q,v);
      return levels[0]+(vv*qu-uv*qv)/d*(levels[1]-levels[0])+(uu*qv-uv*qu)/d*(levels[2]-levels[0]);
    };
    const polygon=face.points.map(p=>[...normalize(p),light(p),face.group||0]);
    for(let i=1;i<polygon.length-1;i++)for(const point of [polygon[0],polygon[i],polygon[i+1]]){vertices.set(point,offset);offset+=5;}
    if(includeEdges)for(let i=0;i<polygon.length;i++){
      const a=polygon[i],b=polygon[(i+1)%polygon.length],ka=a.slice(0,3).join(','),kb=b.slice(0,3).join(','),key=(face.group||0)+':'+(ka<kb?ka+'|'+kb:kb+'|'+ka);
      if(!seen.has(key)){seen.add(key);lines.push(...a,...b);}
    }
  }
  return {vertices,edges:new Float32Array(lines)};
}
export function surfaceCameraMatrix(rotation,elevation,scale,width,height){
  const t=rotation*Math.PI/180,e=elevation*Math.PI/180,c=Math.cos(t),s=Math.sin(t),ce=Math.cos(e),se=Math.sin(e);
  const x=2*scale/width,y=2*scale/height;
  return new Float32Array([c*x,s*se*y,s*ce/4,0,-s*x,c*se*y,c*ce/4,0,0,ce*y,-se/4,0,0,0,0,1]);
}
function createRenderer(canvas){
  const layer=canvas.ownerDocument.createElement('canvas');
  const gl=layer.getContext('webgl',{alpha:true,antialias:true,premultipliedAlpha:true,preserveDrawingBuffer:true});
  if(!gl)return null;
  const shader=(type,source)=>{
    const value=gl.createShader(type);gl.shaderSource(value,source);gl.compileShader(value);
    if(!gl.getShaderParameter(value,gl.COMPILE_STATUS)){gl.deleteShader(value);throw new Error('Surface shader compilation failed');}
    return value;
  };
  const vertex=shader(gl.VERTEX_SHADER,'attribute vec3 position;attribute float brightness;attribute float group;uniform mat4 camera;uniform vec3 palette[5];varying mediump float light;varying mediump float height;varying mediump vec3 tint;void main(){gl_Position=camera*vec4(position,1.0);height=(position.z+1.0)*0.5;light=brightness;tint=group<0.5?palette[0]:group<1.5?palette[1]:group<2.5?palette[2]:group<3.5?palette[3]:palette[4];}');
  const fragment=shader(gl.FRAGMENT_SHADER,'precision mediump float;varying mediump float light;varying mediump float height;varying mediump vec3 tint;uniform vec3 color;uniform float wire;uniform float shaded;uniform float rainbow;vec3 ramp(float h){float p=clamp(h,0.0,1.0)*5.0;return p<1.0?mix(vec3(128.0/255.0,0,1),vec3(0,0,1),p):p<2.0?vec3(0,p-1.0,1):p<3.0?vec3(0,1,3.0-p):p<4.0?vec3(p-3.0,1,0):vec3(1,5.0-p,0);}void main(){gl_FragColor=vec4(mix(mix(tint,ramp(height),rainbow),color,wire)*mix(1.0,light,shaded),1.0);}');
  const program=gl.createProgram();gl.attachShader(program,vertex);gl.attachShader(program,fragment);gl.linkProgram(program);
  gl.deleteShader(vertex);gl.deleteShader(fragment);
  if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw new Error('Surface shader linking failed');
  gl.useProgram(program);
  const position=gl.getAttribLocation(program,'position'),brightness=gl.getAttribLocation(program,'brightness'),group=gl.getAttribLocation(program,'group');
  const camera=gl.getUniformLocation(program,'camera'),color=gl.getUniformLocation(program,'color'),shaded=gl.getUniformLocation(program,'shaded'),wire=gl.getUniformLocation(program,'wire'),palette=gl.getUniformLocation(program,'palette[0]');
  const rainbow=gl.getUniformLocation(program,'rainbow'),triangles=gl.createBuffer(),edges=gl.createBuffer();
  let geometry=null,count=0,edgeCount=0,hasEdges=false;
  layer.addEventListener('webglcontextlost',event=>{event.preventDefault();renderers.delete(canvas);});
  const bind=buffer=>{
    gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.enableVertexAttribArray(position);gl.vertexAttribPointer(position,3,gl.FLOAT,false,20,0);
    gl.enableVertexAttribArray(brightness);gl.vertexAttribPointer(brightness,1,gl.FLOAT,false,20,12);
    gl.enableVertexAttribArray(group);gl.vertexAttribPointer(group,1,gl.FLOAT,false,20,16);
  };
  return {draw(prepared,options){
    if(gl.isContextLost())return null;
    if(geometry!==prepared||options.renderMode!=='surface'&&!hasEdges){
      hasEdges=options.renderMode!=='surface';
      const buffers=surfaceGpuGeometry(prepared,hasEdges);
      gl.bindBuffer(gl.ARRAY_BUFFER,triangles);gl.bufferData(gl.ARRAY_BUFFER,buffers.vertices,gl.DYNAMIC_DRAW);
      gl.bindBuffer(gl.ARRAY_BUFFER,edges);gl.bufferData(gl.ARRAY_BUFFER,buffers.edges,gl.DYNAMIC_DRAW);
      count=buffers.vertices.length/5;edgeCount=buffers.edges.length/5;geometry=prepared;
    }
    const maximum=gl.getParameter(gl.MAX_RENDERBUFFER_SIZE),ratio=Math.min(1,maximum/options.pixelWidth,maximum/options.pixelHeight);
    const pixelWidth=Math.max(1,Math.floor(options.pixelWidth*ratio)),pixelHeight=Math.max(1,Math.floor(options.pixelHeight*ratio));
    if(layer.width!==pixelWidth||layer.height!==pixelHeight){layer.width=pixelWidth;layer.height=pixelHeight;}
    if(!gl.drawingBufferWidth||!gl.drawingBufferHeight)return null;
    gl.viewport(0,0,layer.width,layer.height);gl.clearColor(0,0,0,0);gl.clearDepth(1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
    gl.uniformMatrix4fv(camera,false,surfaceCameraMatrix(options.rotation,options.elevation,options.scale,options.width,options.height));
    const rgb=hex=>[1,3,5].map(i=>parseInt(hex.slice(i,i+2),16)/255);
    gl.uniform3fv(palette,Array.from({length:5},(_,i)=>rgb(options.palette?.[i]||options.color)).flat());
    gl.uniform1f(wire,0);
    gl.uniform1f(rainbow,options.colorMode==='rainbow'?1:0);
    gl.enable(gl.DEPTH_TEST);gl.depthFunc(gl.LEQUAL);gl.disable(gl.BLEND);
    if(prepared.closed){gl.enable(gl.CULL_FACE);gl.cullFace(gl.BACK);gl.frontFace(gl.CCW);}else gl.disable(gl.CULL_FACE);
    if(options.renderMode!=='wireframe'){
      if(options.renderMode==='surface-wireframe'){gl.enable(gl.POLYGON_OFFSET_FILL);gl.polygonOffset(1,1);}
      gl.uniform3fv(color,rgb(options.color));gl.uniform1f(shaded,1);bind(triangles);gl.drawArrays(gl.TRIANGLES,0,count);gl.disable(gl.POLYGON_OFFSET_FILL);
    }
    if(options.renderMode!=='surface'){
      if(options.renderMode==='wireframe')gl.disable(gl.DEPTH_TEST);
      gl.uniform3fv(color,rgb(options.wireColor));gl.uniform1f(wire,options.renderMode==='wireframe'?0:1);gl.uniform1f(shaded,0);bind(edges);gl.drawArrays(gl.LINES,0,edgeCount);
    }
    return layer;
  }};
}
export function renderSurfaceGpu(canvas,prepared,options){
  try{
    if(!renderers.has(canvas))renderers.set(canvas,createRenderer(canvas));
    return renderers.get(canvas)?.draw(prepared,options)||null;
  }catch{renderers.set(canvas,null);return null;}
}
