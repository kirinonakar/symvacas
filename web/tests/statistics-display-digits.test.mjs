import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {JSDOM} from 'jsdom';
import {roundNumber,displayText} from '../display-format.js';
import {resultText} from '../result-display.js';
import {statisticsResultMarkdown,regressionEquationCopyText,statisticsFormattedCopyCell} from '../statistics-markdown.js';
import {renderStatisticsReport} from '../statistics-report.js';
import {renderRegressionReport} from '../regression-report.js';
import {renderFormulas} from '../formula-preview.js';
import {regressionGraphSource} from '../statistics-workspace.js';

const cases=JSON.parse(readFileSync(new URL('../../tests/fixtures/statistics_display_digits.json',import.meta.url),'utf8'));
const cell=value=>({exact:value,decimal:value,decimalTree:{kind:'number',value}});

test('statistics underflow expands to two significant digits with identical displayed and copied values',()=>{
  for(const {value,digits,expected} of cases){
    assert.equal(roundNumber(value,digits,true),expected,value);
    assert.equal(displayText(value,digits,{preserveSmallValues:true,grouping:true}),expected,value);
    assert.equal(resultText(cell(value),{decimal:true,digits,preserveSmallValues:true}),expected,value);
    assert.equal(statisticsFormattedCopyCell(cell(value),{digits}),expected,value);
  }
  assert.equal(roundNumber('0.0000123',3),'0');
  assert.equal(roundNumber('0.0000103',3),'0');
  assert.equal(roundNumber('1.23456',3,true),'1.235');
  assert.equal(displayText('1.23456e-90',3,{preserveSmallValues:true}),'1.235×10^-90');
});

test('statistics report, regression inference and equation rendering retain tiny results without changing engine values',context=>{
  const previous=globalThis.document,dom=new JSDOM('<!doctype html><html><body></body></html>');
  globalThis.document=dom.window.document;
  context.after(()=>{globalThis.document=previous;dom.window.close();});
  const report={title:'Mean',highlights:[{label:'mean',value:cell('0.0000123')}],sections:[{title:'Summary',columns:['Metric','Value'],rows:[['mean',cell('0.0000123')],['p-value',cell('0.0000103')]]}],plots:[]};
  const regression={n:10,df:8,rSquared:0.5,rmse:0.0000126,likelihoodP:0.0000103,coefficients:[],residuals:[]};
  const result={decimal:'0.0000123*x+0.0000103',regression,statisticsCopyReport:{title:'Regression',sections:[{title:'coefficients',columns:['Parameter','Estimate','p'],rows:[['b1',cell('0.0000123'),'0.0000103']]}]}};
  const original=JSON.stringify({report,result}),container=document.createElement('div');
  renderStatisticsReport(container,report,{digits:3});
  assert.ok(container.textContent.includes('0.000012'));
  assert.ok(container.textContent.includes('0.000010'));
  assert.ok(statisticsResultMarkdown({statisticsReport:report},{digits:3}).includes('| p-value | 0.000010 |'));
  renderRegressionReport(container,regression,3);
  assert.ok(container.textContent.includes('0.000013'));
  assert.ok(container.textContent.includes('0.000010'));
  renderFormulas(container,[result.decimal],{digits:3,preserveSmallValues:true});
  assert.deepEqual([...container.querySelectorAll('mn')].map(node=>node.textContent),['0.000012','0.000010']);
  assert.equal(regressionEquationCopyText(result,{digits:3}),'y = 0.000012*x+0.000010');
  assert.ok(statisticsResultMarkdown(result,{digits:3}).includes('| b1 | 0.000012 | 0.000010 |'));
  assert.ok(regressionGraphSource(result.decimal,3).includes('0.000012'));
  assert.equal(JSON.stringify({report,result}),original);
});
