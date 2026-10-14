import test from 'node:test';
import assert from 'node:assert/strict';
import {JSDOM} from 'jsdom';
import {advancedStatisticsSchema as schema} from '../advanced-statistics-schema.js';
import {guidedStatisticsCommand,advancedStatisticsTermLabels,advancedStatisticsExampleRows,createAdvancedStatistics} from '../advanced-statistics.js';
import {statisticsPlotModel,renderStatisticsVisualizations,statisticsIntervalPage} from '../statistics-visualization.js';
import {statisticsRequest} from '../statistics-request.js';
import {fork} from 'node:child_process';
import {readFileSync} from 'node:fs';

const definition=id=>schema.find(item=>item.id===id);

test('continuous mean/SD/n examples select MD or Hedges g and exclude study label columns',()=>{
  const d=definition('metaanalysis'),settings={layout:'continuous',continuousMeasure:'smd'};
  const rows=advancedStatisticsExampleRows(d,settings);assert.equal(rows[0].length,6);
  assert.equal(guidedStatisticsCommand(d,rows,settings),`metaanalysis([${rows.map(row=>`[${row.join(',')}]`).join(',')}],pm,0.95,z,1,smd)`);
  const named=rows.map((row,i)=>[`Study ${i+1}`,...row]);
  const opts={layout:'continuous',meanA:'1',sdA:'2',nA:'3',meanB:'4',sdB:'5',nB:'6',studyLabels:'column',study:'0'};
  assert.ok(guidedStatisticsCommand(d,named,opts).endsWith(',md)'));
  assert.throws(()=>guidedStatisticsCommand(d,named,{...opts,nB:'5'}),/different columns/);
});

test('binary events/patients examples and named selected columns produce OR/RR commands',()=>{
  const d=definition('metaanalysis'),settings={layout:'binary',measure:'riskratio'};
  const rows=advancedStatisticsExampleRows(d,settings);
  assert.equal(rows[0].length,4);
  assert.equal(guidedStatisticsCommand(d,rows,settings),`metaanalysis([${rows.map(row=>`[${row.join(',')}]`).join(',')}],pm,0.95,z,1,riskratio,0.5)`);
  const named=[['Trial A','12','100','20','100'],['Trial B','8','80','15','90']];
  const opts={layout:'binary',eventsA:'1',totalA:'2',eventsB:'3',totalB:'4',studyLabels:'column',study:'0'};
  assert.equal(guidedStatisticsCommand(d,named,opts),'metaanalysis([[12,100,20,100],[8,80,15,90]],pm,0.95,z,1,oddsratio,0.5)');
  assert.throws(()=>guidedStatisticsCommand(d,named,{...opts,totalB:'3'}),/different columns/);
  assert.equal(guidedStatisticsCommand(definition('cohenkappa'),definition('cohenkappa').exampleRows),definition('cohenkappa').example);
});

test('reliability/agreement confidence graphs retain raw values while displaying exactly 0–1',context=>{
  const dom=new JSDOM('<div id="result"></div>');const previous=globalThis.document;globalThis.document=dom.window.document;
  context.after(()=>{dom.window.close();globalThis.document=previous;});
  const plot={kind:'intervals',title:'Intraclass correlation (ICC)',rows:[['ICC',-.2,-.8,.15]],domain:[0,1]};
  const model=statisticsPlotModel(plot);assert.equal(model.xmin,0);assert.equal(model.xmax,1);assert.equal(model.intervals[0].estimate,-.2);
  const panel=document.getElementById('result');renderStatisticsVisualizations(panel,[plot]);
  assert.equal(panel.querySelectorAll('[data-outside-range="true"]').length,1);
  assert.ok(panel.querySelector('title').textContent.includes('-0.2'));assert.equal(panel.querySelectorAll('circle').length,0);
  const trend={kind:'research-scatter',title:'Bland–Altman plot',points:[[1,2],[2,3]],trend:[[1,1.9],[2,3.1]],horizontal:[2.5],xlabel:'Mean measurement',ylabel:'Difference (A − B)'};
  panel.replaceChildren();renderStatisticsVisualizations(panel,[trend]);assert.ok(panel.querySelector('[data-proportional-bias="true"]'));
});

test('production menus contain Reliability & agreement and one combined Phi/V Effect Size option',context=>{
  const dom=new JSDOM(readFileSync(new URL('../index.html',import.meta.url),'utf8'));const previous=globalThis.document;globalThis.document=dom.window.document;
  context.after(()=>{dom.window.close();globalThis.document=previous;});
  for(const section of ['general','tests'])createAdvancedStatistics({state:{fields:{},datasets:{}},persist:()=>{},data:()=>'',columnLimit:()=>4,section});
  const general=document.getElementById('statistics-general-kind'),tests=document.getElementById('statistics-tests-kind');
  assert.equal(general.querySelector('option[value="cohenkappa"]').parentElement.dataset.group,'Reliability & agreement');
  assert.equal(tests.querySelector('option[value="cramerv"]').parentElement.dataset.group,'Effect Size');
  assert.equal(tests.querySelector('option[value="phi"]'),null);assert.equal(general.querySelector('option[value="cramerv"]'),null);
});

test('research presets produce public numeric commands from the same example rows',()=>{
  for(const id of ['metaanalysis','icc','blandaltman','tost','tost2','tostpaired']){
    const d=definition(id),expression=guidedStatisticsCommand(d,d.exampleRows);
    assert.equal(statisticsRequest(expression).tree.value,id);
    assert.equal(expression,d.example);
  }
});

test('meta selected roles exclude study names, preserve their labels and reset hidden random inference',()=>{
  const rows=[['Study A','0.2','0.1'],['Study B','0.3','0.2']];
  const opts={effect:'1',se:'2',studyLabels:'column',study:'0',method:'fixed',inference:'hksj'};
  assert.equal(guidedStatisticsCommand(definition('metaanalysis'),rows,opts),'metaanalysis([[0.2,0.1],[0.3,0.2]],fixed,0.95,z,1)');
  assert.deepEqual(advancedStatisticsTermLabels(definition('metaanalysis'),rows,opts),{'study:1':'Study A','study:2':'Study B'});
  assert.throws(()=>guidedStatisticsCommand(definition('metaanalysis'),rows,{...opts,se:'1'}),/different columns/);
  assert.throws(()=>guidedStatisticsCommand(definition('metaanalysis'),[['Study A','.2','']],opts),/Complete/);
});

test('agreement columns are complete, in chosen order, and may omit unselected cells',()=>{
  const rows=[['11','','10'],['9','','8'],['7','','7']];
  assert.equal(guidedStatisticsCommand(definition('blandaltman'),rows,{first:'2',second:'0',mode:'log'}),'blandaltman([[10,11],[8,9],[7,7]],0.95,log)');
  assert.equal(guidedStatisticsCommand(definition('icc'),rows,{columns:'2,0',model:'mixed',unit:'average'}),'icc([[10,11],[8,9],[7,7]],mixed,average,0.95)');
  assert.throws(()=>guidedStatisticsCommand(definition('icc'),rows),/Complete/);
});

test('independent TOST omits blanks separately while paired TOST matches subject IDs',()=>{
  assert.equal(guidedStatisticsCommand(definition('tost2'),[['1','4'],['2',''],['','5']],{lower:'-2',upper:'3'}),'tost2([1,2],[4,5],-2,3,welch,0.05)');
  assert.throws(()=>guidedStatisticsCommand(definition('tostpaired'),[['1','4'],['2','']]),/Complete/);
  const rows=[['s1','A','1'],['s2','B','5'],['s2','A','2'],['s1','B','4']];
  const opts={grouping:'groups',group:'1',value:'2',firstGroup:'A',secondGroup:'B',matching:'subject',subject:'0'};
  assert.equal(guidedStatisticsCommand(definition('tostpaired'),rows,opts),'tostpaired([1,2],[4,5],-0.5,0.5,0.05)');
});

test('funnel inversion, agreement limits and equivalence bounds survive graph preparation',()=>{
  const funnel={kind:'research-scatter',points:[[.2,.1],[.3,.2]],lines:[[[.25,0],[-.25,.4]],[[.25,0],[.75,.4]]],invertY:true,xlabel:'Effect estimate',ylabel:'Standard error'};
  const model=statisticsPlotModel(funnel);
  assert.equal(model.invertY,true);assert.equal(model.ymin,0);assert.ok(model.ymax>.4);assert.ok(model.xmin<-.25);assert.ok(model.xmax>.75);
  assert.deepEqual(model.points.map(p=>[p.x,p.y]),funnel.points);
  const agreement=statisticsPlotModel({kind:'research-scatter',points:[[1,.1],[2,.2]],horizontal:[.15,-2,2],xlabel:'Mean measurement',ylabel:'Difference (A − B)'});
  assert.ok(agreement.ymin<-2&&agreement.ymax>2);
  const intervals=statisticsPlotModel({kind:'intervals',rows:[['A−B',0,-.02,.02]],thresholds:[-1,2],reference:0});
  assert.ok(intervals.xmin<-1&&intervals.xmax>2);assert.deepEqual(intervals.thresholds,[-1,2]);
});

test('production SVG renders all observations, inverted SE, pooled diamond and export actions',context=>{
  const dom=new JSDOM('<div id="result"></div>');const previous=globalThis.document;globalThis.document=dom.window.document;
  context.after(()=>{dom.window.close();globalThis.document=previous;});
  const panel=document.getElementById('result');
  renderStatisticsVisualizations(panel,[{kind:'research-scatter',title:'Funnel plot',points:[[.2,.05],[.3,.3]],invertY:true,xlabel:'Effect estimate',ylabel:'Standard error',lines:[[[.25,0],[-.25,.4]],[[.25,0],[.75,.4]]]}]);
  const svg=panel.querySelector('svg'),circles=[...svg.querySelectorAll('circle')];
  assert.equal(circles.length,2);assert.ok(Number(circles[0].getAttribute('cy'))<Number(circles[1].getAttribute('cy')));
  assert.equal(svg.querySelectorAll('polyline').length,2);assert.equal(panel.querySelectorAll('select').length,0);
  assert.ok(svg.textContent.includes('Standard error'));assert.ok(panel.querySelector('button'));
  panel.replaceChildren();
  renderStatisticsVisualizations(panel,[{kind:'intervals',title:'Forest plot',rows:[['Study A',.1,-.1,.3],['Pooled effect',.2,.1,.3]],summaryIndex:1,weights:[100],reference:0}]);
  assert.equal(panel.querySelectorAll('polygon').length,1);assert.equal(panel.querySelectorAll('rect').length,1);
});

test('forest paging keeps every study and its weight, with the same pooled interval on each page',()=>{
  const studies=Array.from({length:105},(_,i)=>[`Study ${i+1}`,i,i-1,i+1]);
  const pooled=['Pooled effect',1,0,2],plot={kind:'intervals',rows:[...studies,pooled],weights:studies.map((_,i)=>i+1),summaryIndex:105};
  const collected=[];
  for(let i=0;i<3;i++){
    const page=statisticsIntervalPage(plot,i);assert.ok(page.rows.length<=41);
    assert.deepEqual(page.rows.at(-1),pooled);assert.equal(page.summaryIndex,page.rows.length-1);
    assert.equal(page.weights[0],i*40+1);collected.push(...page.rows.slice(0,-1));
  }
  assert.deepEqual(collected,studies);assert.equal(plot.rows.length,106);
});

test('production WASM engine computes the research presets against independent references',{timeout:60000},async context=>{
  const worker=fork(new URL('./worker-bridge.mjs',import.meta.url),[],{execArgv:['--experimental-wasm-jspi']});
  context.after(()=>worker.kill());
  const receive=predicate=>new Promise((resolve,reject)=>{
    const timeout=setTimeout(()=>finish(new Error('Research worker timed out')),30000);
    const listener=data=>{if(data.type==='fatal')finish(new Error(data.error));else if(predicate(data))finish(null,data);};
    function finish(error,data){clearTimeout(timeout);worker.off('message',listener);worker.off('error',finish);error?reject(error):resolve(data);}
    worker.on('message',listener);worker.on('error',finish);
  });
  await receive(data=>data.type==='ready');let id=0;
  const fixture=JSON.parse(readFileSync(new URL('../../tests/fixtures/research_statistics_reference.json',import.meta.url),'utf8'));
  const done=new Set();
  for(const entry of fixture.cases){
    const key=entry.function+(entry.function==='metaanalysis'&&entry.arguments.length>=6?':'+entry.arguments[5]:'');
    if(done.has(key))continue;done.add(key);
    const literal=value=>Array.isArray(value)?`[${value.map(literal).join(',')}]`:String(value);
    const expression=`${entry.function}(${entry.arguments.map(literal).join(',')})`;
    const current=++id,pending=receive(data=>data.type==='result'&&data.id===current);worker.send({id:current,request:statisticsRequest(expression)});
    const result=(await pending).result;assert.equal(result.ok,true,`${entry.function}: ${result.error}`);
    const summary=result.statisticsReport.sections.find(section=>section.title==='Summary');assert.ok(summary,entry.function);
    for(const [path,expected] of entry.expected){
      if(path.length!==1)continue;
      const row=summary.rows.find(row=>row[0]===path[0]);assert.ok(row,`${entry.function}: ${path[0]}`);
      assert.ok(Math.abs(Number(row[1].decimal)-expected)<=entry.tolerance*Math.max(1,Math.abs(expected)),`${entry.function}: ${path[0]}`);
    }
  }
  assert.equal(done.size,10);
  for(const analysis of ['chi2independence','fisherexact']){
    const current=++id,pending=receive(data=>data.type==='result'&&data.id===current);
    worker.send({id:current,request:{...statisticsRequest(`${analysis}([0,0,1,1,1],[0,1,0,1,1])`),statisticsTermLabels:{'table:row':'Treatment','table:column':'Outcome'}}});
    const result=(await pending).result;assert.equal(result.ok,true,result.error);
    const sections=result.statisticsReport.sections;
    assert.equal(sections.filter(section=>section.title==='Compared columns').length,1,analysis);
    assert.deepEqual(sections.find(section=>section.title==='Effect size').columns,['Effect size','Value','Rating']);
  }
});
