import test from 'node:test';
import assert from 'node:assert/strict';
import {createStatisticsUndoHistory} from '../statistics-undo.js';

const draft={csv:'name,value\nA,1',kind:'columns',columns:'2',auto:true};

test('dataset undo keeps structural edits separate from consecutive cell edits',()=>{
  const history=createStatisticsUndoHistory();
  const next={...draft,csv:'name,value\nA,12'},typed={...draft,csv:'name,value\nA,123'};
  const combined={...typed,csv:'name,value,extra\nA,123,4',columns:'3'};
  history.record(draft,next,'cell:0:1',100);
  history.record(next,typed,'cell:0:1',200);
  history.record(typed,combined,null,201);
  assert.deepEqual(history.undo(),typed);
  assert.deepEqual(history.undo(),draft);
  history.record(draft,next,'cell:0:1',300);
  history.record(next,draft,'cell:0:1',400);
  assert.equal(history.canUndo,false);
});

test('an action that leaves the displayed data unchanged adds no undo entry',()=>{
  const history=createStatisticsUndoHistory();
  history.record(draft,{...draft});
  assert.equal(history.canUndo,false);
  assert.equal(history.undo(),undefined);
});
