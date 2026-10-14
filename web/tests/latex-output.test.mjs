import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {JSDOM} from 'jsdom';
import {latexTree,mathCopyText,bindMathCopy} from '../latex-output.js';
import {latexInput} from '../parser.js';
import {mathDisplay} from '../math-display.js';
import {latexResult} from '../result-display.js';
import {createAppState} from '../app-state.js';
import {solutionStepsCopyText} from '../equation-steps.js';

test('LaTeX copy matches Android fixtures, preserves precedence and permits paste back',()=>{
  const fixtures=readFileSync(new URL('../../math/src/test/resources/latex-output.tsv',import.meta.url),'utf8').trim().split(/\r?\n/);
  for(const line of fixtures){const [source,expected]=line.split('\t');assert.equal(mathCopyText(source,true),expected,source);assert.equal(mathCopyText(source,false),source);}
  for(const source of ['f(x)+Ans','x_1+theta','{1,2}','[[1,2],[3,4]]','sqrt(x)','integrate(x^2,x,0,1)'])assert.doesNotThrow(()=>latexInput(mathCopyText(source,true)),source);
  assert.equal(mathCopyText('x=1/2\n\ny=sqrt(2)',true),'x = \\frac{1}{2}\n\ny = \\sqrt{2}');
  assert.equal(mathCopyText('x+',true),'x+');
  assert.equal(latexTree({kind:'power',args:[{kind:'power',args:[{kind:'symbol',value:'x'},{kind:'number',value:'2'}]},{kind:'number',value:'3'}]}),'\\left(x^{2}\\right)^{3}');
});

test('native Copy and Cut obey the current option for all three math workspaces',()=>{
  const dom=new JSDOM('<textarea id="expression"></textarea><textarea id="graph-source"></textarea><textarea id="equation-source"></textarea><textarea id="python-source"></textarea>'),{document}=dom.window;
  let enabled=false;const dispose=bindMathCopy(document,()=>enabled);
  const copy=(field,type='copy')=>{let text;const event=new dom.window.Event(type,{bubbles:true,cancelable:true});Object.defineProperty(event,'clipboardData',{value:{setData:(_,value)=>{text=value;}}});field.dispatchEvent(event);return {text,event};};
  try{
    for(const id of ['expression','graph-source','equation-source']){
      const field=document.getElementById(id);field.value='2+1/3';field.setSelectionRange(2,5);
      enabled=false;assert.equal(copy(field).event.defaultPrevented,false);
      enabled=true;assert.equal(copy(field).text,'\\frac{1}{3}');assert.equal(field.value,'2+1/3');
    }
    const field=document.getElementById('graph-source');assert.equal(copy(field,'cut').text,'\\frac{1}{3}');assert.equal(field.value,'2+');
    const python=document.getElementById('python-source');python.value='1/2';python.select();assert.equal(copy(python).event.defaultPrevented,false);
  }finally{dispose();dom.window.close();}
});

test('rendered fractions copy their structure and results retain displayed precision',()=>{
  const dom=new JSDOM('<main></main>'),old=globalThis.document;globalThis.document=dom.window.document;
  const document=dom.window.document,dispose=bindMathCopy(document,()=>true);
  try{
    const tree={kind:'fraction',args:[{kind:'text',value:'1'},{kind:'text',value:'2'}]},math=mathDisplay(tree);
    document.querySelector('main').append(math);
    const range=document.createRange();range.selectNodeContents(math);const selection=dom.window.getSelection();selection.removeAllRanges();selection.addRange(range);
    let text;const event=new dom.window.Event('copy',{bubbles:true,cancelable:true});Object.defineProperty(event,'clipboardData',{value:{setData:(_,value)=>{text=value;}}});math.dispatchEvent(event);
    assert.equal(text,'\\frac{1}{2}');
    assert.equal(latexResult({exact:'1/2',tree,decimalTree:{kind:'number',value:'0.500000'}},{decimal:true,digits:3}),'0.5');
    assert.equal(latexResult({exact:'1/2',tree},{digits:3}),'\\frac{1}{2}');
  }finally{dispose();dom.window.close();globalThis.document=old;}
});

test('copy preference defaults off, restores true and changes only formulas in full solutions',()=>{
  assert.equal(createAppState().copyAsLatex,false);assert.equal(createAppState({copyAsLatex:true}).copyAsLatex,true);assert.equal(createAppState({copyAsLatex:'true'}).copyAsLatex,false);
  const report={steps:[{title:'Result',explanation:'Keep this explanation.',tree:{kind:'fraction',args:[{kind:'number',value:'1'},{kind:'number',value:'2'}]}}]};
  assert.match(solutionStepsCopyText(report,10,true),/Keep this explanation\./);assert.match(solutionStepsCopyText(report,10,true),/\\frac\{1\}\{2\}/);
  assert.doesNotMatch(solutionStepsCopyText(report,10,false),/\\frac/);
});
