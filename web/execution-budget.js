export function bootstrapWork(request){
  const number=(node,depth=0)=>{
    if(!node||depth>8)return 0;
    if(node.kind==='number')return Number(node.value);
    if(node.kind==='symbol')return number(request.variables?.[node.value],depth+1);
    if(node.kind==='unary')return (node.value==='-'?-1:1)*number(node.args?.[0],depth+1);
    return 0;
  };
  const visit=node=>{
    if(!node)return {samples:0,seconds:0};
    const args=node.args||[];let samples=0,seconds=0;
    if(node.kind==='call'&&node.value==='sem'&&args.length>10){
      const count=number(args[10]);
      if(Number.isInteger(count)&&count>=20){samples=Math.min(count,10000);const p=args[1].args?.length||6;seconds=samples*Math.max(10,p*p)*(args[7].value==='wlsmv'?4:1);}
    }
    for(const arg of args){const child=visit(arg);samples+=child.samples;seconds+=child.seconds;}
    return {samples,seconds};
  };
  return visit(request.tree);
}

export function executionTimeoutMillis(request){
  return request.removeComputationLimit===true?Infinity:(60+bootstrapWork(request).seconds)*1000;
}
