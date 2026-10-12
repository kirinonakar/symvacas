import test from 'node:test';
import assert from 'node:assert/strict';
import {editableTable} from '../editable-table.js';

// DOM construction/focus contract, without claiming real browser performance QA.
class Node {
  constructor(tag,doc){this.tag=tag;this.ownerDocument=doc;this.children=[];this.attrs={};this.dataset={};this.style={};this.events={};this.classList={add:()=>{}};}
  get firstElementChild(){return this.children[0];}
  setAttribute(key,value){this.attrs[key]=String(value);}
  append(...nodes){for(const n of nodes){n.parentNode=this;this.children.push(n);}}
  addEventListener(key,fn){this.events[key]=fn;}
  removeEventListener(key,fn){if(this.events[key]===fn)delete this.events[key];}
  remove(){this.parentNode.children.splice(this.parentNode.children.indexOf(this),1);this.parentNode=null;}
  insertBefore(node,next){if(node.parentNode)node.remove();const at=next?this.children.indexOf(next):this.children.length;this.children.splice(at,0,node);node.parentNode=this;}
  contains(node){return node===this||this.children.some(n=>n.contains(node));}
  querySelectorAll(tag){return this.children.flatMap(n=>[...(n.tag===tag?[n]:[]),...n.querySelectorAll(tag)]);}
  querySelector(selector){const [,row,column]=/data-row="(\d+)".*data-column="(\d+)"/.exec(selector);return this.querySelectorAll('input').find(n=>n.dataset.row===row&&n.dataset.column===column);}
  focus(){this.ownerDocument.activeElement=this;}
  select(){}
}

test('ten thousand rows mount only a viewport window and retain edited cells and keyboard navigation',context=>{
  const saved={document:globalThis.document,requestAnimationFrame:globalThis.requestAnimationFrame,cancelAnimationFrame:globalThis.cancelAnimationFrame};
  context.after(()=>Object.assign(globalThis,saved));let frame;
  const doc={createElement:tag=>new Node(tag,doc),activeElement:null};globalThis.document=doc;
  globalThis.requestAnimationFrame=fn=>{frame=fn;return 1;};globalThis.cancelAnimationFrame=()=>{frame=null;};
  const viewport=new Node('div',doc);viewport.scrollTop=0;viewport.clientHeight=300;
  const edits=new Map(),table=editableTable({rows:10000,columns:['age','group'],label:'Stats data',viewport,value:(row,col)=>edits.get(`${row}:${col}`)??String(row),onInput:(row,col,value)=>edits.set(`${row}:${col}`,value)});viewport.append(table);
  assert.ok(table.querySelectorAll('input').length<70);
  assert.equal(table.attrs['aria-rowcount'],'10001');
  const first=table.querySelector('input[data-row="0"][data-column="0"]');first.focus();first.value='한글';first.oninput();
  viewport.scrollTop=160060;viewport.events.scroll();frame();
  assert.equal(doc.activeElement,first);assert.ok(table.contains(first));
  assert.equal(table.querySelector('input[data-row="4000"][data-column="0"]').value,'4000');
  assert.ok(table.querySelectorAll('input').length<70);
  const inputs=table.querySelectorAll('input'),tail=inputs.filter(n=>n.dataset.column==='0').at(-1);tail.focus();
  tail.onkeydown({key:'ArrowDown',preventDefault(){},stopPropagation(){}});
  assert.equal(Number(doc.activeElement.dataset.row),Number(tail.dataset.row)+1);
  doc.activeElement=null;viewport.scrollTop=0;viewport.events.scroll();frame();
  assert.equal(table.querySelector('input[data-row="0"][data-column="0"]').value,'한글');
  table.disposeEditableTable();assert.equal(viewport.events.scroll,undefined);
});
