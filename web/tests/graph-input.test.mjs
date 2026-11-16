import test from 'node:test';
import assert from 'node:assert/strict';
import {graphInputTree,planarTreeKind,cartesianFormula,graphRangeAxes,isImplicitSurface,surfaceFormula} from '../graph-input.js';
import {createGraphRangeControls} from '../graph-ranges.js';

test('analysis and viewport range fields read constant expressions without replacing the draft',()=>{
  const fields=new Map(['graph-analysis-a','graph-min'].map(id=>[id,{id,value:'pi/3+1',dataset:{},hasAttribute:()=>false}]));
  const {fieldRange,numeric,editField}=createGraphRangeControls({$:id=>fields.get(id),options:()=>({displayDigits:4})});
  for(const [id,field] of fields){
    assert.equal(numeric(id),Math.PI/3+1);
    assert.equal(fieldRange(field).tree.kind,'binary');
    editField(field);field.onblur();
    assert.equal(field.value,'pi/3+1');
    for(const [source,expected] of [['−2π',-2*Math.PI],['(sqrt(4)+1)^2',9],['log(100)',2]]){
      field.value=source;
      assert.equal(numeric(id),expected);
    }
    for(const source of ['', 'x+1', 'pi/', '1/0', 'sqrt(-1)', 'log(10,0)', '(1,2)']){
      field.value=source;
      assert.ok(Number.isNaN(numeric(id)),source);
    }
    field.value='1.234567890123';field.onblur();
    assert.equal(field.value,'1.2346');
    assert.equal(numeric(id),1.234567890123);
  }
});

test('surface coordinate triples and local height definitions retain their own axes and captions',()=>{
  for(const source of ['[cos(u)*cos(v),sin(u)*cos(v),sin(v)]','[R=2+.35*sin(6*u-3*t),x=(R+cos(v))*cos(u),y=(R+cos(v))*sin(u),z=sin(v)]','S(u,v)=(u,v,sin(u+v))']){
    assert.deepEqual([...graphRangeAxes(source,'surface')],['u','v']);
    assert.equal(isImplicitSurface(source),false);
    assert.doesNotThrow(()=>graphInputTree(surfaceFormula(source),'surface'));
    assert.ok(!surfaceFormula(source).startsWith('z='));
  }
  const helpers='[r1=sqrt((x-2)^2+y^2),r2=sqrt((x+2)^2+y^2),z=sin(4*r1-5*t)/(1+.2*r1)+sin(4*r2-5*t)/(1+.2*r2)]';
  assert.deepEqual([...graphRangeAxes(helpers,'surface')],[]);
  assert.equal(isImplicitSurface(helpers),false);
  assert.equal(surfaceFormula(helpers),helpers);
  assert.equal(isImplicitSurface('x^2+y^2+z^2=9'),true);
});

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
