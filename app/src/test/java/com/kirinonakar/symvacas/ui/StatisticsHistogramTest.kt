package com.kirinonakar.symvacas.ui

import java.io.File
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class StatisticsHistogramTest {
    @Test fun densityHistogramsHaveUnitAreaAndMatchIndependentGaussianScottReferences() {
        val fixture=JSONObject(File("../tests/fixtures/statistics_histogram_kde.json").readText())
        val reference=fixture.getJSONObject("reference");val data=statisticsHistogramData(listOf(listOf(-1.0,0.0,1.0)),true)
        assertEquals(reference.getInt("bins"),data.bins)
        assertEquals(listOf(listOf(1,1,1)),data.counts)
        data.heights.single().forEach {assertEquals(.5,histogramDensityNumber(it,data).toDouble(),1e-12)}
        val points=reference.getJSONArray("gaussian_scott_points")
        for(i in 0 until points.length()) {
            val expected=points.getJSONArray(i);val (position,height)=data.curves.single()[expected.getInt(0)]
            assertEquals(expected.getDouble(1),(data.minimum+position*data.span)*data.scale,1e-12)
            assertEquals(expected.getDouble(2),histogramDensityNumber(height,data).toDouble(),1e-12)
        }
        val integral=data.curves.single().zipWithNext().sumOf {(a,b)->(b.first-a.first)*(a.second+b.second)/2}
        assertTrue(integral>.997&&integral<1.001)
        val cases=fixture.getJSONArray("cases")
        for(i in 0 until cases.length()) {
            val example=cases.getJSONObject(i);val rows=example.getJSONArray("series")
            val series=List(rows.length()){index->val row=rows.getJSONArray(index);List(row.length()){row.getString(it).toDouble()}}
            val plot=statisticsHistogramData(series,true)
            val unavailable=example.getJSONArray("unavailable")
            assertEquals(List(unavailable.length()){unavailable.getInt(it)},plot.unavailable)
            plot.heights.forEachIndexed {index,row->assertEquals(if(series[index].any(Double::isFinite))1.0 else 0.0,row.sum()/plot.bins,1e-12)}
            assertTrue(plot.peak.isFinite()&&plot.peak>0)
            assertTrue(plot.viewMinimum.isFinite()&&plot.viewMaximum.isFinite())
            assertTrue(plot.curves.flatten().all {it.first.isFinite()&&it.second.isFinite()})
            assertFalse(histogramDensityNumber(plot.peak,plot).contains("Infinity"))
            val counts=statisticsHistogramData(series)
            assertEquals(counts.counts.map {row->row.map(Int::toDouble)},counts.heights)
            assertTrue(counts.curves.all {it.isEmpty()})
        }
        val grouped=statisticsHistogramData(listOf(listOf(0.0,0.0,1.0,1.0),listOf(0.0,1.0)),true)
        assertEquals(grouped.heights[0],grouped.heights[1])
    }
}
