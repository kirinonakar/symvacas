package com.kirinonakar.symvacas.ui

import java.io.File
import org.json.JSONObject
import org.json.JSONArray
import org.junit.Assert.*
import org.junit.Test

class StatisticsGroupColumnTest {
    private val fixture=JSONObject(File("../tests/fixtures/statistics_group_column.json").readText())
    private fun strings(values:JSONArray)=List(values.length()){values.getString(it)}
    @Test fun boundariesBelongToTheUpperGroupAndTextAndRowsAreRetained() {
        val cases=fixture.getJSONArray("cases")
        for(index in 0 until cases.length()) {
            val item=cases.getJSONObject(index)
            val result=statisticsGroupedColumn(item.getString("source"),item.getString("kind"),item.getInt("column"),item.getString("cuts"),item.getString("header"),item.getString("values"))
            assertEquals(item.getString("csv"),result.csv);assertEquals(item.getString("resultKind"),result.kind)
            assertEquals(strings(item.getJSONArray("labels")),result.labels);assertEquals(strings(item.getJSONArray("ranges")),result.ranges)
            val counts=item.getJSONArray("counts");assertEquals(List(counts.length()){counts.getInt(it)},result.counts)
            assertEquals(item.getInt("omitted"),result.omitted);assertTrue(statisticsHasHeader(statisticsCsvRows(result.csv)))
        }
        assertEquals("0,1",defaultStatisticsGroupValues(""));assertEquals("0,1,2",defaultStatisticsGroupValues("10,20"))
    }
    @Test fun invalidOptionsCannotProduceAGroupedColumn() {
        val cases=fixture.getJSONArray("invalid")
        for(index in 0 until cases.length()) {
            val item=cases.getJSONObject(index)
            val result=runCatching {statisticsGroupedColumn("9\n10","list",0,item.getString("cuts"),item.getString("header"),item.getString("values"))}
            assertTrue(result.isFailure);assertEquals(item.getString("error"),result.exceptionOrNull()?.message)
        }
        assertTrue(runCatching {statisticsGroupedColumn("NA\nInfinity","list",0,"10","group")}.isFailure)
        assertTrue(runCatching {statisticsGroupedColumn("9","columns:100",0,"10","group")}.isFailure)
    }
    @Test fun renamingAddsOrChangesOnlyHeadersAndPreservesEveryDataCell() {
        val cases=fixture.getJSONArray("headers")
        for(index in 0 until cases.length()) {
            val item=cases.getJSONObject(index)
            val result=statisticsRenameColumn(item.getString("source"),item.getInt("columns"),item.getInt("column"),item.getString("header"))
            assertEquals(item.getString("csv"),result);assertTrue(statisticsHasHeader(statisticsCsvRows(result)))
            if(item.getString("source").isNotBlank())assertEquals(statisticsRows(item.getString("source")),statisticsRows(result))
        }
        assertTrue(runCatching {statisticsRenameColumn("1,2",2,0,"y")}.isFailure)
    }
}
