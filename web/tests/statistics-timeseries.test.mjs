import test from 'node:test';
import assert from 'node:assert/strict';
import {statisticsPlotModel} from '../statistics-visualization.js';

test('forecast plot includes future interval bounds and original time indices in its axes',()=>{
  const plot={kind:'timeseries',observed:[[1,12],[2,14],[3,13]],fitted:[[2,13],[3,13.5]],forecast:[[3,13],[4,15],[5,16]],interval:[[4,10,20],[5,8,24]],boundary:3};
  const model=statisticsPlotModel(plot);
  assert.equal(model.xmin,1);assert.ok(model.xmax>5);
  assert.ok(model.ymin<8);assert.ok(model.ymax>24);
  assert.equal(model.boundary,3);assert.deepEqual(model.band,plot.interval);
  assert.deepEqual(model.series,[plot.observed,plot.fitted,plot.forecast]);
  const labels=['2014-01-01','2015-01-01','2016-01-01','2017-01-01','2018-01-01'];
  const dated=statisticsPlotModel({...plot,timeLabels:labels,timeTickLabels:labels.map(label=>label.slice(0,4))});
  assert.equal(dated.xlabel,'Date');assert.deepEqual(dated.timeLabels,labels);
  assert.deepEqual(dated.tickLabels,['2014','2015','2016','2017','2018']);
  const residual=statisticsPlotModel({...plot,observed:[[2,2],[3,4]],fitted:[],forecast:[],interval:[],boundary:null,reference:0});
  assert.ok(residual.ymin<0);assert.equal(residual.reference,0);
  const acf=statisticsPlotModel({kind:'acf',values:[-.4,.2,0],bound:.5});
  assert.deepEqual(acf.stems,[[1,-.4],[2,.2],[3,0]]);assert.deepEqual(acf.bounds,[-.5,.5]);
  assert.ok(acf.ymin<=-1&&acf.ymax>=1);
});
