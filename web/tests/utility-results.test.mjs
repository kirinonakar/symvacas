import test from 'node:test';
import assert from 'node:assert/strict';
import {layoutFixture} from './layout-fixture.mjs';
import {createUtilityResults,utilityModes} from '../utility-results.js';

const number=value=>({kind:'number',value:String(value)});
const fraction=(numerator,denominator)=>({kind:'fraction',args:[number(numerator),number(denominator)]});
const divided={exact:'1/3',decimal:'0.33333333333',tree:fraction(1,3),decimalTree:number('0.33333333333')};

test('utility cards copy the displayed precision and clear independently',()=>{
  const {doc,root}=layoutFixture(),nodes={};
  for(const id of ['mode',...utilityModes.map(mode=>`${mode}-result`)]){
    const node=doc.createElement('div');node.id=id;nodes[id]=node;root.append(node);
  }
  nodes.mode.value='functions';
  const previousDocument=globalThis.document;globalThis.document=doc;
  try{
    const copied=[];
    const cards=createUtilityResults({state:{digits:4,resultDisplayMode:'off'},clipboard:text=>copied.push(text)});
    const {['units-result']:units,['tip-result']:tip,['currency-result']:currency,['functions-result']:functions}=nodes;
    const click=(target,label)=>{
      const descendants=node=>[node,...node.children.flatMap(descendants)];
      const button=descendants(target).find(node=>node.tagName==='BUTTON'&&node.textContent===label);
      assert.ok(button,label);button.dispatchEvent({type:'click'});
    };
    cards.set('units',{amount:'1/300',from:'m',to:'cm',result:divided});
    cards.set('currency',{amount:'1',from:'USD',to:'EUR',rate:'1/3',result:divided});
    cards.set('functions',{source:'f(3)',result:divided});
    cards.set('tip',{people:3,result:{tree:{args:[number(15),number(0),fraction(11501,100),fraction(3833,100),fraction(1917,50),number(2),number(15)]}}});

    assert.equal(units.querySelector('mfrac'),null);
    assert.equal(currency.querySelector('mfrac'),null);
    assert.ok(functions.querySelector('mfrac'));
    click(units,'Copy');click(currency,'Copy');click(functions,'Copy');click(tip,'Copy');
    assert.deepEqual(copied,['0.3333 cm','0.3333 EUR','1/3',
      'Total 115.01\nPer person 38.33 · 38.34\nTip amount 15.00 (15.00%)\nTax 0.00\n1 × 38.33 + 2 × 38.34']);

    click(functions,'Decimal');click(functions,'Copy');
    assert.equal(functions.querySelector('mfrac'),null);
    assert.equal(copied.at(-1),'0.3333');
    click(functions,'Clear');
    assert.equal(functions.hidden,true);
    assert.equal(units.hidden,false);
    assert.equal(currency.hidden,false);
    assert.equal(tip.hidden,false);
  }finally{globalThis.document=previousDocument;}
});
