import test from 'node:test';
import assert from 'node:assert/strict';
import {JSDOM} from 'jsdom';
import {bindMathPaste,latexPaste} from '../math-input.js';

test('multiline LaTeX paste retains curve/equation boundaries and nested expression scope',()=>{
  assert.equal(latexPaste('\\frac{x+1}{2}\n\n$\\sqrt{x}$\nx=\\frac{1}{3}',{multiline:true}),'(x+1)/2\n\nsqrt(x)\nx=1/3');
  assert.equal(latexPaste('x+1\n\ny=2',{multiline:true}),'x+1\n\ny=2');
  assert.equal(latexPaste('$$\n\\frac{x+1}{2}\n$$',{multiline:true}),'(x+1)/2');
  assert.equal(latexPaste('\\begin{bmatrix}1&2\\\\\n3&4\\end{bmatrix}',{multiline:true}),'[[1,2],[3,4]]');
  assert.equal(latexPaste('$\\frac{1}{5}$',{prefix:'x^2\n2',suffix:'+3\ny=0',multiline:true}),'(1/5)');
});

test('paste replaces native selection and emits one input update, preserving invalid input',()=>{
  const dom=new JSDOM('<textarea></textarea>'),field=dom.window.document.querySelector('textarea'),errors=[];
  try {
    let updates=0;field.addEventListener('input',()=>updates++);
    bindMathPaste(field,{multiline:true,onError:message=>errors.push(message)});
    const paste=text=>{const event=new dom.window.Event('paste',{cancelable:true,bubbles:true});Object.defineProperty(event,'clipboardData',{value:{getData:()=>text}});field.dispatchEvent(event);return event;};
    field.value='x^2\n2x+3\ny=0';field.setSelectionRange(5,6);
    assert.equal(paste('$\\frac{1}{5}$').defaultPrevented,true);
    assert.equal(field.value,'x^2\n2(1/5)+3\ny=0');assert.equal(field.selectionStart,10);assert.equal(field.selectionEnd,10);assert.equal(updates,1);
    assert.equal(paste('\\frac{1}').defaultPrevented,true);assert.equal(errors.length,1);assert.equal(updates,1);
    assert.equal(paste('x+1').defaultPrevented,false);assert.equal(updates,1);
  }finally{dom.window.close();}
});
