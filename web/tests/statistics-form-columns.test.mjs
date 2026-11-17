import test from 'node:test';
import assert from 'node:assert/strict';
import {advancedStatisticsSchema as schema} from '../advanced-statistics-schema.js';
import {socialStatisticsPlan} from '../statistics-social-forms.js';
const definition=id=>schema.find(d=>d.id===id);

test('post-hoc forms preserve unequal sample sizes, control identity and group labels',()=>{
  const rows=[['1','3','6'],['2','4','8'],['','5','9']];
  const base={grouping:'columns',columns:'2,0,1',control:'2',adjustment:'holm'};
  const nested='[[6,8,9],[1,2],[3,4,5]]';
  for(const id of ['scheffe','dunnett','conover']){
    const plan=socialStatisticsPlan(id,rows,base,['Placebo','Low','High']);
    assert.equal(plan.expression,`${id}(${nested}${id==='dunnett'?',2':id==='conover'?',holm':''})`);
    assert.deepEqual(plan.labels,{'sample:1':'High','sample:2':'Placebo','sample:3':'Low'});
  }
  const long=[['Placebo','1'],['High','6'],['Placebo','2'],['High','8']];
  assert.equal(socialStatisticsPlan('dunnett',long,{grouping:'groups',group:'0',value:'1',control:'2'}).expression,'dunnett([[1,2],[6,8]],2)');
  assert.throws(()=>socialStatisticsPlan('dunnett',rows,{...base,control:'4'}),/control/);
});
