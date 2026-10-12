package com.kirinonakar.symvacas.ui

import java.io.File
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class StatisticsFrequencyTest {
    @Test fun namedAndGroupedBarsKeepRawHeightsCategoryOrderMissingnessAndNegativeBaseline() {
        val cases=JSONObject(File("../tests/fixtures/statistics_named_bar.json").readText()).getJSONArray("cases")
        for(index in 0 until cases.length()) {
            val item=cases.getJSONObject(index);val raw=item.getJSONArray("rows")
            val rows=List(raw.length()){i->val row=raw.getJSONArray(i);List(row.length()){row.getString(it)}}
            val names=item.optJSONArray("columnNames")?.let {List(it.length()){i->it.getString(i)}} ?: statisticsColumnNames(item.getString("kind"))
            val data=statisticsNamedBarData(rows,item.getString("kind"),item.optString("grouping","columns"),names)
            val labels=item.getJSONArray("labels");assertEquals(List(labels.length()){labels.getString(it)},data.labels)
            val expected=item.getJSONArray("series");assertEquals(expected.length(),data.series.size)
            for(i in 0 until expected.length()) {
                assertEquals(expected.getJSONObject(i).getString("label"),data.series[i].label)
                val values=expected.getJSONObject(i).getJSONArray("values");val positions=item.getJSONArray("positions").getJSONArray(i)
                for(j in 0 until values.length()) {
                    if(values.isNull(j)){assertNull(data.series[i].values[j]);assertNull(data.positions[i][j])}
                    else {assertEquals(values.getDouble(j),data.series[i].values[j]!!,0.0);assertEquals(positions.getDouble(j),data.positions[i][j]!!,1e-12)}
                }
            }
            assertEquals(item.getDouble("baseline"),data.baseline,1e-12)
            assertEquals(item.getDouble("minimum"),data.minimum,0.0);assertEquals(item.getDouble("maximum"),data.maximum,0.0)
        }
        val csv="name,value\nA,5\nB,8\nC,3"
        assertEquals(listOf(5.0,8.0,3.0),statisticsNamedBarData(statisticsRows(csv),"xy").series.single().values)
    }
    @Test fun observedValuesHaveTheirOwnFrequenciesAndNumericPositionsOnBothPlatforms() {
        val cases=JSONObject(File("../tests/fixtures/statistics_frequency.json").readText()).getJSONArray("cases")
        for(index in 0 until cases.length()) {
            val item=cases.getJSONObject(index);val rows=item.getJSONArray("series")
            val series=List(rows.length()) {row->val data=rows.getJSONArray(row);List(data.length()){data.getString(it).toDouble()}}
            val result=statisticsFrequencyData(series)
            val values=item.getJSONArray("values");val counts=item.getJSONArray("counts");val positions=item.getJSONArray("positions")
            assertEquals(values.length(),result.values.size)
            for(i in 0 until values.length()) {
                assertEquals(values.getDouble(i),result.values[i],0.0)
                assertEquals(positions.getDouble(i),result.positions[i],1e-12)
            }
            for(row in 0 until counts.length()) {
                val expected=counts.getJSONArray(row)
                assertEquals(List(expected.length()){expected.getInt(it)},result.counts[row])
            }
            assertEquals(item.getInt("peak"),result.peak)
            assertTrue(result.barWidth.isFinite()&&result.barWidth>0)
        }
    }
}
