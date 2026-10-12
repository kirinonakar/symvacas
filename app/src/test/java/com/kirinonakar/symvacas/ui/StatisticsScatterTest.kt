package com.kirinonakar.symvacas.ui

import java.io.File
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class StatisticsScatterTest {
    @Test fun selectedAxesPreserveCompleteRowsAndCategoricalGroups() {
        val cases=JSONObject(File("../tests/fixtures/statistics_scatter.json").readText()).getJSONArray("cases")
        for(index in 0 until cases.length()) {
            val item=cases.getJSONObject(index);val raw=item.getJSONArray("rows")
            val rows=List(raw.length()){i->val row=raw.getJSONArray(i);List(row.length()){row.getString(it)}}
            val data=statisticsScatterData(rows,item.getString("kind"),item.getString("grouping"),item.getInt("xColumn"),item.getInt("yColumn"))
            val columns=item.getJSONArray("columns")
            assertEquals(StatisticsScatterColumns(columns.getInt(0),columns.getInt(1),columns.getInt(2)),data.columns)
            val expected=item.getJSONArray("series")
            assertEquals(expected.length(),data.series.size)
            for(i in 0 until expected.length()) {
                val series=expected.getJSONObject(i);val points=series.getJSONArray("points")
                assertEquals(series.getString("label"),data.series[i].label)
                assertEquals(List(points.length()){j->points.getJSONArray(j).let {it.getDouble(0) to it.getDouble(1)}},data.series[i].points)
            }
        }
        assertEquals(StatisticsScatterColumns(1,0,2),statisticsScatterColumns(3,"column:1",0,0))
        assertEquals(StatisticsScatterColumns(-1,0,1),statisticsScatterColumns(2,"column:9",8,8))
    }
}
