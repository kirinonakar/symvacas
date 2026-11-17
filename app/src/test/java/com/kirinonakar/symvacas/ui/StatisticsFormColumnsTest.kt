package com.kirinonakar.symvacas.ui

import java.io.File
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class StatisticsFormColumnsTest {
    @Test fun modelComparisonFormsKeepOptionNamesAndFamiliesIntactInRequests() {
        val d=definition("modelcompare")
        val families=d.getJSONObject("exampleRowsByFamily")
        for(family in families.keys()) {
            val settings=JSONObject().put("family",family).put("basePredictors",when(family){"cox"->"2";"lmm","glmm","gee"->"1";else->"0"})
            val rows=advancedStatisticsExampleRows(d,settings)
            val command=guidedStatisticsCommand(d,rows,settings)
            val tree=com.kirinonakar.symvacas.math.statisticsRequest(command).tree
            assertEquals(family,"symbol",tree.args[2].kind)
            assertEquals(family,family,tree.args[2].value)
            assertTrue(family,tree.args[8].args.all {it.args[0].kind=="symbol"})
            assertTrue(family,tree.args[8].args.any {it.args[0].value=="excludedrows"})
            assertTrue(family,advancedStatisticsTermLabels(d,rows,settings,statisticsColumnNames(statisticsKindForColumns(rows.first().size))).isNotEmpty())
        }
    }
    @Test fun mancovaPreservesRolesAndTextGroupLabels() {
        val d=definition("mancova")
        val rows=listOf(listOf("A","2","9","7","3"),listOf("B","4","8","6","5"),listOf("A","6","7","5","8"))
        val opts=JSONObject().put("group","0").put("covariates","4,1").put("responses","3,2").put("level","0.9").put("slopes","test")
        assertEquals("mancova([[1,3,2,7,9],[2,5,4,6,8],[1,8,6,5,7]],2,0.9,1)",guidedStatisticsCommand(d,rows,opts))
        assertEquals(mapOf("Group" to "Treatment","group:1" to "A","group:2" to "B","x1" to "Baseline","x2" to "Age","response:1" to "Score","response:2" to "Speed"),advancedStatisticsTermLabels(d,rows,opts,listOf("Treatment","Age","Speed","Score","Baseline")))
        assertEquals(setOf(0,1),advancedStatisticsReservedColumns(d,JSONObject(),"responses",4))
        assertEquals(setOf(0,4,1),advancedStatisticsReservedColumns(d,opts,"responses",5))
        assertEquals(setOf(0),advancedStatisticsReservedColumns(d,JSONObject(),"covariates",4))
        assertTrue(runCatching {guidedStatisticsCommand(d,rows,JSONObject(opts.toString()).put("responses","1,2"))}.exceptionOrNull() is IllegalArgumentException)
        assertTrue(runCatching {guidedStatisticsCommand(d,rows,JSONObject(opts.toString()).put("responses","2"))}.exceptionOrNull() is IllegalArgumentException)
    }
    @Test fun normalityOmnibusUsesSelectedColumnAndEnforcesMinimumSampleSize() {
        val d=definition("normaltest")
        val rows=(0..7).map {listOf("99",it.toString())}+listOf(listOf("100",""))
        val opts=JSONObject().put("column","1")
        assertEquals("normaltest([0,1,2,3,4,5,6,7])",guidedStatisticsCommand(d,rows,opts))
        assertEquals(mapOf("sample:1" to "Outcome"),advancedStatisticsTermLabels(d,rows,opts,listOf("ID","Outcome")))
        assertTrue(runCatching {guidedStatisticsCommand(d,rows.take(7),opts)}.exceptionOrNull() is IllegalArgumentException)
    }
    private val schema=JSONArray(File("src/main/assets/advanced_statistics.json").readText())
    private fun definition(id:String)=(0 until schema.length()).map {schema.getJSONObject(it)}.first {it.getString("id")==id}

}
