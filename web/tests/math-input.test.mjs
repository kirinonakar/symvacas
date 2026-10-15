import test from 'node:test';
import assert from 'node:assert/strict';
import {latexInput,parse} from '../parser.js';
import {latexPaste} from '../math-input.js';

const implicit=String.raw`\\[ (x^2+y^2)^4= \left[ (x^3-3xy^2)\cos t+ (3x^2y-y^3)\sin t \right]^2 \\]`;
const polar=String.raw`\\[ \boxed{r=|\cos(3\theta-t)|} \\]`;
const first='(x^2+y^2)^4=((x^3-3x*y^2)cos(t)+(3x^2y-y^3)sin(t))^2',second='r=abs(cos(3theta-t))';

test('single escaped math blocks convert without changing commands or matrix row separators',()=>{
  assert.equal(latexInput(implicit),first);
  assert.equal(latexInput(polar),second);
  assert.equal(latexInput(String.raw`\\[xy\\]`),'x*y');
  assert.equal(latexInput(String.raw`\\(xy\\)`),'x*y');
  assert.equal(latexPaste(String.raw`\\[ \begin{bmatrix}1&2\\3&4\end{bmatrix} \\]`,{multiline:true}),'[[1,2],[3,4]]');
});

test('consecutive display blocks remain separate expressions regardless of physical line breaks',()=>{
  for(const separator of ['  ','\n\n','\r\n']){
    const source=implicit+separator+polar;
    const converted=latexPaste(source,{multiline:true,prefix:'x^2\n',suffix:'\ny=0'});
    assert.equal(converted,`${first}\n${second}`);
    assert.deepEqual(converted.split('\n').map(line=>parse(line).kind),['relation','relation']);
    assert.throws(()=>latexInput(source),SyntaxError);
  }
  assert.equal(latexPaste('\\[\nx=1\n\\] \\[\ny=2\n\\]',{multiline:true}),'x=1\ny=2');
  assert.equal(latexPaste('$$x=1$$ $y=2$',{multiline:true}),'x=1\ny=2');
  assert.equal(latexPaste(String.raw`\\[\boxed{x+1}\\] \\[y=2\\]`,{multiline:true,prefix:'2'}),'(x+1)\ny=2');
});

test('block recognition never drops prose or partially accepts an unsupported block',()=>{
  assert.throws(()=>latexPaste(`Answer: ${polar}`,{multiline:true}),SyntaxError);
  assert.throws(()=>latexPaste(polar+String.raw` \[\unknown{1}\]`,{multiline:true}),SyntaxError);
  assert.equal(latexPaste('x+1\n\ny=2',{multiline:true}),'x+1\n\ny=2');
});
