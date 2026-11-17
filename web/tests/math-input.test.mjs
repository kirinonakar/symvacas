import test from 'node:test';
import assert from 'node:assert/strict';
import {latexPaste} from '../math-input.js';
import {readFileSync} from 'node:fs';
import {graphInputTree} from '../graph-input.js';

const implicit=String.raw`\\[ (x^2+y^2)^4= \left[ (x^3-3xy^2)\cos t+ (3x^2y-y^3)\sin t \right]^2 \\]`;
const polar=String.raw`\\[ \boxed{r=|\cos(3\theta-t)|} \\]`;
const first='(x^2+y^2)^4=((x^3-3x*y^2)cos(t)+(3x^2y-y^3)sin(t))^2',second='r=abs(cos(3theta-t))';

test('block recognition never drops prose or partially accepts an unsupported block',()=>{
  assert.throws(()=>latexPaste(`Answer: ${polar}`,{multiline:true}),SyntaxError);
  assert.throws(()=>latexPaste(polar+String.raw` \[\unknown{1}\]`,{multiline:true}),SyntaxError);
  assert.equal(latexPaste('x+1\n\ny=2',{multiline:true}),'x+1\n\ny=2');
});

test('multiline LaTeX cases paste as one graph with intact parameter names and conditions',()=>{
  const [source,expected]=readFileSync(new URL('../../math/src/test/resources/latex-input.tsv',import.meta.url),'utf8')
    .split(/\r?\n/).find(line=>line.startsWith(String.raw`\operatorname{f}\left(x\right) = \begin{cases}`)).split('\t');
  const multiline=source.replace(String.raw`\\ `,'\\\\\n');
  for(const text of [source,multiline,`\\[\n${multiline}\n\\]`]){
    assert.equal(latexPaste(text,{multiline:true}),expected);
    const tree=graphInputTree(text);
    assert.equal(tree.kind,'piecewise');assert.equal(tree.args.length,2);
    const symbols=new Set();
    function collect(node){if(node.kind==='symbol')symbols.add(node.value);node.args.forEach(collect);}
    collect(tree);assert.deepEqual([...symbols].sort(),['T1','T2','TE','TR','e','x']);
    for(const branch of tree.args){
      assert.equal(branch.args[1].kind,'relation');
      assert.equal(branch.args[1].args[0].kind,'relation');
    }
  }
});
