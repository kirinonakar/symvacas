package com.kirinonakar.symvacas.ui

import java.io.File
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class StatisticsStratifiedDataTest {
    private val schema=JSONArray(File("src/main/assets/advanced_statistics.json").readText())
    private val definition=(0 until schema.length()).map {schema.getJSONObject(it)}.first {it.getString("id")=="mantelhaenszel"}
    private val opts=definition.getJSONArray("controls").let {fields->(0 until fields.length()).associate {fields.getJSONObject(it).let {f->f.getString("key") to f.get("default").toString()}}}
    private val counts="""severity,treatment,improved,not_improved,total
        |mild,A,16,2,18
        |mild,B,144,36,180
        |moderate,A,40,20,60
        |moderate,B,30,30,60
        |severe,A,60,120,180
        |severe,B,4,16,20""".trimMargin()
    private val expected=listOf(listOf("16","2","144","36"),listOf("40","20","30","30"),listOf("60","120","4","16"))

    @Test fun groupedCountsAndExpandedPatientsProduceIdenticalTables() {
        val rows=advancedStatisticsRows(counts,5)
        val plan=stratifiedStatisticsData(rows,opts,listOf("severity","treatment","improved","not_improved","total"))
        assertEquals(expected,plan.tables)
        assertEquals("mild",plan.labels["stratum:1"]);assertEquals("A · improved",plan.labels["count:1"])
        assertEquals(expected,stratifiedStatisticsData(rows,opts+("countType" to "total"),emptyList()).tables)
        val patients=advancedStatisticsExampleRows(definition,JSONObject().put("layout","observations"))
        assertEquals(518,patients.size)
        assertEquals(expected,stratifiedStatisticsData(patients,opts+("layout" to "observations"),emptyList()).tables)
        val repeated=rows.drop(1)+listOf(listOf("mild","A","10","1","11"),listOf("mild","A","6","1","7"))
        assertEquals(expected,stratifiedStatisticsData(repeated,opts,emptyList()).tables)
        assertEquals(expected.map {it.drop(2)+it.take(2)},stratifiedStatisticsData(rows,opts+mapOf("groupA" to "B","groupB" to "A"),emptyList()).tables)
    }

    @Test fun individualRecordsIgnorePatientIdAndKeepStratumNames() {
        val source="""patient_id,severity,treatment,improved
            |1,moderate,A,1
            |2,severe,A,1
            |3,severe,A,0
            |4,mild,B,1
            |5,moderate,B,0
            |6,mild,B,1""".trimMargin()
        val plan=stratifiedStatisticsData(advancedStatisticsRows(source,4),opts+("layout" to "observations"),emptyList())
        assertEquals(listOf(listOf("1","0","0","1"),listOf("1","1","0","0"),listOf("0","0","2","0")),plan.tables)
        assertEquals(listOf("moderate","severe","mild"),(1..3).map {plan.labels["stratum:$it"]})
    }

    @Test fun invalidGroupsOutcomesCountsAndTotalsAreRejected() {
        val rows=advancedStatisticsRows(counts,5)
        assertTrue(runCatching {stratifiedStatisticsData(rows,opts+("groupB" to "A"),emptyList())}.isFailure)
        assertTrue(runCatching {stratifiedStatisticsData(rows+listOf(listOf("mild","C","1","2","3")),opts,emptyList())}.isFailure)
        assertTrue(runCatching {stratifiedStatisticsData(listOf(listOf("mild","A","4","1","3")),opts+("countType" to "total"),emptyList())}.isFailure)
        assertTrue(runCatching {stratifiedStatisticsData(listOf(listOf("mild","A","1.5","2","3")),opts,emptyList())}.isFailure)
        assertTrue(runCatching {stratifiedStatisticsData(listOf(listOf("1","mild","A","unknown")),opts+("layout" to "observations"),emptyList())}.isFailure)
        assertTrue(runCatching {stratifiedStatisticsData(rows,opts+("group" to "0"),emptyList())}.isFailure)
    }
}
