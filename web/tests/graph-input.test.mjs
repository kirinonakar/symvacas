import test from 'node:test';
import assert from 'node:assert/strict';
import {graphInputTree,planarTreeKind,cartesianFormula} from '../graph-input.js';

test('comma conditions are a single inequality region without changing nested commas',()=>{
  for(const source of ['-1<x<1, -1<y<x','x^2+y^2<4, y>=0','y>max(x,0), x<1','(x<1), (y>0)']){
    assert.equal(planarTreeKind(graphInputTree(source)),'inequality',source);
    assert.doesNotThrow(()=>graphInputTree(cartesianFormula(source)));
  }
  for(const [source,kind] of [['(cos(t),sin(t))','parametric'],['[cos(t),sin(t)]','parametric'],
    ['y=max(x,0)','cartesian'],['f(x)={x<0:x^2,3}','cartesian']]){
    assert.equal(planarTreeKind(graphInputTree(source)),kind,source);
  }
  assert.equal(cartesianFormula('f(x)=x^2'),'f(x)=x^2');
  assert.equal(cartesianFormula('(y<1)'),'(y<1)');
  for(const source of ['x<1,',',x<1','x<1,,y>0','x<1,y','x,y'])assert.throws(()=>graphInputTree(source),SyntaxError);
  assert.throws(()=>graphInputTree('x<1,y>0','parametric'),SyntaxError);
});
