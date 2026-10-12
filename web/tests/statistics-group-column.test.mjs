import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {statisticsGroupedColumn,defaultStatisticsGroupValues} from '../statistics-group-column.js';
import {statisticsRenameColumn,csvRows,statisticsCsvHasHeader,statisticsDataRows,statisticsColumnLabels} from '../workspace-commands.js';
import {editableTable} from '../editable-table.js';

const fixture=JSON.parse(readFileSync(new URL('../../tests/fixtures/statistics_group_column.json',import.meta.url),'utf8'));
test('group columns include exact boundaries in the upper interval and preserve original text and missing rows',()=>{
  for(const item of fixture.cases){
    const result=statisticsGroupedColumn(item.source,item.kind,item.column,item.cuts,item.header,item.values);
    assert.deepEqual(result,{csv:item.csv,kind:item.resultKind,labels:item.labels,ranges:item.ranges,counts:item.counts,omitted:item.omitted});
    assert.ok(statisticsCsvHasHeader(csvRows(result.csv,{skipHeader:false,preserveEmptyRows:true})));
  }
  assert.equal(defaultStatisticsGroupValues(''),'0,1');assert.equal(defaultStatisticsGroupValues('10,20'),'0,1,2');
});
test('invalid grouping options cannot produce a transformed dataset',()=>{
  for(const item of fixture.invalid)assert.throws(()=>statisticsGroupedColumn('9\n10','list',0,item.cuts,item.header,item.values),error=>error.message===item.error);
  assert.throws(()=>statisticsGroupedColumn('NA\nInfinity','list',0,'10','group'),/No finite numeric/);
  assert.throws(()=>statisticsGroupedColumn('9','list',1,'10','group'),/valid data columns/);
  assert.throws(()=>statisticsGroupedColumn('9','columns:100',0,'10','group'),/Column count/);
});
test('header editing creates or updates only the header and preserves quoted and hidden columns',()=>{
  for(const item of fixture.headers){
    const updated=statisticsRenameColumn(item.source,item.columns,item.column,item.header);assert.equal(updated,item.csv);
    assert.ok(statisticsCsvHasHeader(csvRows(updated+'\n',{skipHeader:false,preserveEmptyRows:true})));
    if(item.source.trim())assert.deepEqual(statisticsDataRows(updated,`columns:${item.columns}`),statisticsDataRows(item.source,`columns:${item.columns}`));
  }
  assert.throws(()=>statisticsRenameColumn('1,2',2,0,'y'),/already exists/);
  assert.throws(()=>statisticsRenameColumn('1',1,0,''),/header/);
  const empty=statisticsRenameColumn('',1,0,'Measurement');
  assert.deepEqual(statisticsColumnLabels(empty,'list'),['Measurement (x)']);
  assert.deepEqual(statisticsDataRows(empty,'list'),[['']]);
});

test('statistics column names are keyboard-accessible buttons that open the selected header editor',context=>{
  class Node {
    constructor(tag){this.tag=tag;this.children=[];this.attrs={};this.dataset={};this.style={};this.events={};}
    append(...nodes){this.children.push(...nodes);}
    setAttribute(name,value){this.attrs[name]=String(value);}
    addEventListener(name,callback){this.events[name]=callback;}
    querySelectorAll(tag){return this.children.flatMap(node=>[...(node.tag===tag?[node]:[]),...node.querySelectorAll(tag)]);}
  }
  const previous=globalThis.document;context.after(()=>globalThis.document=previous);globalThis.document={createElement:tag=>new Node(tag)};
  let selected=-1;
  const table=editableTable({rows:0,columns:['Age (x)','Weight (y)'],label:'Stats data',onRenameColumn:column=>selected=column});
  const buttons=table.querySelectorAll('button');assert.equal(buttons.length,2);
  buttons[1].events.click();assert.equal(selected,1);assert.equal(buttons[1].attrs['aria-label'],'Edit column header: Weight (y)');
  assert.equal(buttons[1].type,'button');
  const matrix=editableTable({rows:0,columns:['1','2'],label:'Matrix'});assert.equal(matrix.querySelectorAll('button').length,0);
});
