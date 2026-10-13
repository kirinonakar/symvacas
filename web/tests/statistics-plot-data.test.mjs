import test from 'node:test';
import assert from 'node:assert/strict';
import {statisticsHeatMapData,statisticsCorrelationHeatMap,statisticsFrequencyData,statisticsNamedBarData,statisticsHistogramData,histogramDensityNumber,beeswarmLayout,heatMapColor} from '../statistics-plot-data.js';
import {readFileSync} from 'node:fs';
import {statisticsDataRows,statisticsColumnCount,numericStatisticsRows,statisticsDateLabel} from '../workspace-commands.js';
import {statisticsScatterData,statisticsScatterColumns} from '../statistics-plot-data.js';

test('scatter uses selected axes, categorical groups and complete row pairs identically on both platforms',()=>{
  const {cases}=JSON.parse(readFileSync(new URL('../../tests/fixtures/statistics_scatter.json',import.meta.url),'utf8'));
  for(const item of cases){
    const data=statisticsScatterData(item.rows,{...item,columnCount:statisticsColumnCount(item.kind)});
    assert.deepEqual([data.groupColumn,data.xColumn,data.yColumn],item.columns);
    assert.deepEqual(data.series,item.series);
  }
  assert.deepEqual(statisticsScatterColumns(3,'column:1',0,0),{groupColumn:1,xColumn:0,yColumn:2});
  assert.deepEqual(statisticsScatterColumns(2,'column:9',8,8),{groupColumn:-1,xColumn:0,yColumn:1});
  const rows=[['A','2024/2/28','1'],['B','2024-02-29','2'],['A','2024.3.2','3'],['A','2024-02-30','4'],['B','','5']];
  const dates=statisticsScatterData(rows,{columnCount:3,grouping:'first',xColumn:1,yColumn:2});
  assert.deepEqual(dates.series,[{label:'A',points:[[1,1],[4,3]]},{label:'B',points:[[2,2]]}]);
  assert.equal(statisticsDateLabel(dates.dateAxis.origin,2),'2024-02-29');
  assert.equal(statisticsDateLabel(dates.dateAxis.origin,4),'2024-03-02');
  assert.deepEqual(numericStatisticsRows(rows.map(row=>row.slice(1))),[['1','1'],['2','2'],['4','3'],['','4'],['','5']]);
  assert.equal(statisticsScatterData([['1','2'],['2','3'],['2024-02-29','4']]).dateAxis,undefined,'a numeric majority retains the numeric X axis');
});

test('density histograms have unit area per series and match independent Gaussian Scott KDE reference points',()=>{
  const {reference,cases}=JSON.parse(readFileSync(new URL('../../tests/fixtures/statistics_histogram_kde.json',import.meta.url),'utf8'));
  const data=statisticsHistogramData(reference.series,true);
  assert.equal(data.bins,reference.bins);assert.deepEqual(data.counts,reference.counts);
  data.heights.forEach((row,i)=>row.forEach((height,j)=>assert.ok(Math.abs(Number(histogramDensityNumber(height,data))-reference.densities[i][j])<1e-12)));
  // Reference evaluated at original coordinates with sd=1 and h=3^(-1/5).
  for(const [index,x,density] of reference.gaussian_scott_points){
    const [position,height]=data.curves[0][index];
    assert.ok(Math.abs((data.minimum+position*data.span)*data.scale-x)<1e-12);
    assert.ok(Math.abs(Number(histogramDensityNumber(height,data))-density)<1e-12);
  }
  const integral=data.curves[0].slice(1).reduce((area,point,i)=>area+(point[0]-data.curves[0][i][0])*(point[1]+data.curves[0][i][1])/2,0);
  assert.ok(integral>.997&&integral<1.001);
  for(const example of cases){
    const series=example.series.map(row=>row.map(Number)),plot=statisticsHistogramData(series,true);
    assert.deepEqual(plot.unavailable,example.unavailable);
    plot.heights.forEach((row,i)=>assert.ok(Math.abs(row.reduce((sum,value)=>sum+value/plot.bins,0)-(series[i].some(Number.isFinite)?1:0))<1e-12));
    assert.ok(Number.isFinite(plot.peak)&&plot.peak>0);
    assert.ok(Number.isFinite(plot.viewMinimum)&&Number.isFinite(plot.viewMaximum));
    plot.curves.flat().forEach(point=>assert.ok(point.every(Number.isFinite)));
    assert.doesNotMatch(String(histogramDensityNumber(plot.peak,plot)),/Infinity|NaN/);
    const counts=statisticsHistogramData(series);
    assert.deepEqual(counts.heights,counts.counts);assert.ok(counts.curves.every(curve=>!curve.length));
  }
  const grouped=statisticsHistogramData([[0,0,1,1],[0,1]],true);assert.deepEqual(grouped.heights[0],grouped.heights[1]);
});

test('named and grouped bars preserve raw heights, category order, missingness and negative baselines on both platforms',()=>{
  const {cases}=JSON.parse(readFileSync(new URL('../../tests/fixtures/statistics_named_bar.json',import.meta.url),'utf8'));
  for(const example of cases){
    const data=statisticsNamedBarData(example.rows,{columnCount:statisticsColumnCount(example.kind),grouping:example.grouping,columnNames:example.columnNames});
    assert.deepEqual(data.labels,example.labels);assert.deepEqual(data.series,example.series);
    assert.equal(data.minimum,example.minimum);assert.equal(data.maximum,example.maximum);assert.ok(Math.abs(data.baseline-example.baseline)<1e-12);
    data.positions.forEach((row,i)=>row.forEach((position,j)=>assert.ok(position===null?example.positions[i][j]===null:Math.abs(position-example.positions[i][j])<1e-12)));
  }
  const csv='name,value\nA,5\nB,8\nC,3';
  assert.deepEqual(statisticsNamedBarData(statisticsDataRows(csv,'xy')).series,[{label:'y',values:[5,8,3]}]);
});

test('frequency bars count each distinct value and retain numeric spacing across Android and Web',()=>{
  const {cases}=JSON.parse(readFileSync(new URL('../../tests/fixtures/statistics_frequency.json',import.meta.url),'utf8'));
  for(const example of cases){
    const data=statisticsFrequencyData(example.series.map(row=>row.map(Number)));
    assert.deepEqual(data.values,example.values);assert.deepEqual(data.counts,example.counts);assert.equal(data.peak,example.peak);
    data.positions.forEach((position,i)=>assert.ok(Math.abs(position-example.positions[i])<1e-12));
    assert.ok(Number.isFinite(data.barWidth)&&data.barWidth>0);
  }
});

test('heat map retains row order, zero, missing cells and categorical labels without compacting columns',()=>{
  const rows=[['A','0','1,234'],['B','','-2'],['A','NaN','Infinity']];
  assert.deepEqual(statisticsHeatMapData(rows,{columnCount:3,grouping:'first'}),{columns:['y','z'],rows:[
    {label:'A',values:[0,1234]},{label:'B',values:[null,-2]},{label:'A',values:[null,null]}
  ]});
  assert.deepEqual(statisticsHeatMapData([['1','','A'],['2','3','B']],{columnCount:3,grouping:'last'}).rows.map(row=>row.values),[[1,null],[2,3]]);
  assert.equal(heatMapColor(0,0,0),'rgb(241,241,235)');assert.equal(heatMapColor(null,-1,1),null);
  assert.equal(heatMapColor(-1e308,-1e308,1e308),'rgb(59,112,189)');assert.equal(heatMapColor(1e308,-1e308,1e308),'rgb(180,55,72)');
});

test('Pearson matrix uses complete pairs, omits categorical columns and marks constant/insufficient pairs undefined',()=>{
  const data=statisticsCorrelationHeatMap([
    ['1','2','-1','.1','A'],['2','4','-2','.1','B'],['3','8','','.1','C'],['','10','-4','.1','D'],['5','','-5','.1','E'],['','','','.1','F']
  ],{columnCount:5});
  assert.deepEqual(data.columns,['x','y','z','x4']);assert.deepEqual(data.range,[-1,1]);
  assert.ok(Math.abs(data.rows[0].values[1]-.9819805060619657)<1e-12);
  assert.ok(Math.abs(data.rows[0].values[2]+1)<1e-12);assert.equal(data.rows[0].counts[1],3);assert.equal(data.rows[0].counts[2],3);
  assert.deepEqual(data.rows[3].values,[null,null,null,null]);
  data.rows.forEach((row,i)=>row.values.forEach((value,j)=>assert.equal(value,data.rows[j].values[i])));
  assert.equal(statisticsCorrelationHeatMap([['1',''],['','2']],{columnCount:2}).rows[0].values[1],null);
  const large=statisticsCorrelationHeatMap([['-1e308','1e308'],['0','0'],['1e308','-1e308']],{columnCount:2});
  assert.ok(Math.abs(large.rows[0].values[1]+1)<1e-12);
});
