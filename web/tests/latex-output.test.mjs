import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {latexTree,mathCopyText} from '../latex-output.js';
import {latexInput} from '../parser.js';

test('LaTeX copy matches Android fixtures, preserves precedence and permits paste back',()=>{
  const fixtures=readFileSync(new URL('../../math/src/test/resources/latex-output.tsv',import.meta.url),'utf8').trim().split(/\r?\n/);
  for(const line of fixtures){const [source,expected]=line.split('\t');assert.equal(mathCopyText(source,true),expected,source);assert.equal(mathCopyText(source,false),source);}
  for(const source of ['f(x)+Ans','x_1+theta','{1,2}','[[1,2],[3,4]]','sqrt(x)','integrate(x^2,x,0,1)'])assert.doesNotThrow(()=>latexInput(mathCopyText(source,true)),source);
  assert.equal(mathCopyText('x=1/2\n\ny=sqrt(2)',true),'x = \\frac{1}{2}\n\ny = \\sqrt{2}');
  assert.equal(mathCopyText('x+',true),'x+');
  assert.equal(latexTree({kind:'power',args:[{kind:'power',args:[{kind:'symbol',value:'x'},{kind:'number',value:'2'}]},{kind:'number',value:'3'}]}),'\\left(x^{2}\\right)^{3}');
});
