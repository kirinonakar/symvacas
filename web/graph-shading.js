// Convert shading source lines into engine constraints.
import {parse} from './parser.js';
import {graphSources,isGraphShading,graphShadingBody,splitTopLevel,graphInputTree} from './graph-input.js';

export function graphShadings(source,kind){
  return graphSources(source,kind).filter(isGraphShading).slice(0,4).map(line=>{
    if(kind!=='cartesian')throw new Error('Shading requires a Cartesian graph');
    const [body,legacyRange]=graphShadingBody(line).split(';'),parts=splitTopLevel(body),expressions=[],intervals=[];
    for(const part of parts){if(part.includes('..'))intervals.push(part);else expressions.push(part);}
    if(legacyRange)intervals.push(legacyRange.trim());
    if(!expressions.length||intervals.length>1)throw new Error('Enter shading inequalities or one or two functions');
    const trees=expressions.map(s=>graphInputTree(s)),relation=trees[0];
    let item={mode:'band',trees};
    if(trees.length===1&&relation.kind==='relation'&&relation.args.every(node=>node.kind!=='relation')&&relation.args.some(node=>node.kind==='symbol'&&node.value==='y')){
      const [left,right]=relation.args,isLeft=left.kind==='symbol'&&left.value==='y',isRight=right.kind==='symbol'&&right.value==='y';
      if(!['<','<=','>','>='].includes(relation.value)||!isLeft&&!isRight)throw new Error('Enter y < f(x) or y > f(x)');
      const boundary=isLeft?right:left;
      if((function hasY(node){return node.kind==='symbol'&&node.value==='y'||(node.args||[]).some(hasY);})(boundary))throw new Error('Shading boundaries cannot depend on y');
      item={mode:'halfplane',side:(isLeft?relation.value.startsWith('<'):relation.value.startsWith('>'))?'below':'above',trees:[isLeft?right:left]};
    }else if(trees.some(tree=>tree.kind==='relation')){
      const boundaries=[],constraints=[];
      const has=(node,name)=>node.kind==='symbol'&&node.value===name||(node.args||[]).some(child=>has(child,name));
      function flatten(node){
        if(node.kind!=='relation')return [node];
        if(!['<','<=','>','>='].includes(node.value))throw new Error('Enter x or y inequalities for shading');
        const left=flatten(node.args[0]),right=flatten(node.args[1]),a=left.at(-1),b=right[0];
        const axis=node=>node.kind==='symbol'&&['x','y'].includes(node.value)?node.value:null;
        const onLeft=!!axis(a),name=axis(a)||axis(b),boundary=onLeft?b:a;
        if(!name||has(boundary,'y')||name==='x'&&has(boundary,'x'))throw new Error('Enter x bounds or y < f(x) inequalities');
        constraints.push({axis:name,side:(onLeft?node.value.startsWith('<'):node.value.startsWith('>'))?'upper':'lower'});
        boundaries.push(boundary);
        return [...left,...right];
      }
      for(const tree of trees.filter(tree=>tree.kind==='relation'))flatten(tree);
      const functions=trees.filter(tree=>tree.kind!=='relation');
      if(functions.length){
        if(functions.length>2)throw new Error('Use one or two shading functions with x and y bounds');
        const bounds=axis=>constraints.flatMap((constraint,index)=>constraint.axis===axis?[{side:constraint.side,tree:boundaries[index]}]:[]);
        item={mode:'band',trees:functions,xBounds:bounds('x'),yBounds:bounds('y')};
      }else item={mode:'region',trees:boundaries,constraints};
    }else if(trees.length>2){
      throw new Error('Enter one or two shading functions');
    }
    if(intervals.length){const [a,b]=intervals[0].split('..');if(!a||!b)throw new Error('Enter a..b for the shading interval');item.a=parse(a);item.b=parse(b);}
    return item;
  });
}
