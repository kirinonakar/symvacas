package com.kirinonakar.symvacas.ui

import java.io.File
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class StatisticsExtensionFormsTest {
    private val schema=JSONArray(File("src/main/assets/advanced_statistics.json").readText())
    private fun definition(id:String)=(0 until schema.length()).map {schema.getJSONObject(it)}.first {it.getString("id")==id}

    @Test fun everyPriorityPresetBuildsThePublicExpressionAndBelongsToItsCatalog() {
        for(id in extensionAnalysisIds) {
            val d=definition(id)
            assertEquals(id,d.getString("example"),guidedStatisticsCommand(d,advancedStatisticsExampleRows(d)))
            val category=if(d.getString("section")=="advanced")"Advanced statistics" else "General statistics"
            assertTrue(id,Catalog.getValue(category).any {it.startsWith("$id(")})
        }
    }
    @Test fun pairedBayesianDataMatchesSubjectIDsAndOneSampleIgnoresHiddenColumns() {
        val rows=listOf(listOf("s1","A","1"),listOf("s2","B","5"),listOf("s2","A","2"),listOf("s1","B","4"))
        val opts=JSONObject().put("design","paired").put("grouping","groups").put("group","1").put("value","2").put("firstGroup","A").put("secondGroup","B").put("matching","subject").put("subject","0")
        assertTrue(guidedStatisticsCommand(definition("bayesttest"),rows,opts).startsWith("bayesttest([1,2],[4,5],paired,"))
        assertTrue(guidedStatisticsCommand(definition("bayesttest"),listOf(listOf("1"),listOf("2"),listOf("4")),JSONObject().put("design","onesample")).startsWith("bayesttest([1,2,4],[],onesample,"))
        assertTrue(runCatching {guidedStatisticsCommand(definition("bayesttest"),listOf(listOf("1","2"),listOf("3","")),JSONObject().put("design","paired"))}.isFailure)
    }
    @Test fun metaRolesEncodeNamedGroupsAndExcludeNonModeratorColumns() {
        val rows=listOf(listOf("US",".2",".1"),listOf("KR",".4",".15"),listOf("US",".3",".2"),listOf("KR",".5",".2"))
        val opts=JSONObject().put("effect","1").put("se","2").put("group","0").put("method","fixed")
        assertEquals("metasubgroup([[.2,.1,1],[.4,.15,2],[.3,.2,1],[.5,.2,2]],fixed,0.95,z)",guidedStatisticsCommand(definition("metasubgroup"),rows,opts))
        assertEquals(mapOf("group:1" to "US","group:2" to "KR"),advancedStatisticsTermLabels(definition("metasubgroup"),rows,opts,emptyList()))
        assertTrue(runCatching {guidedStatisticsCommand(definition("metaregression"),rows,JSONObject().put("effect","1").put("se","2").put("predictors","1"))}.isFailure)
    }
    @Test fun aftEventEncodingAndDelayedEntryPreserveSelectedPredictorLabels() {
        val rows=listOf(listOf("dead","40",".2","1"),listOf("alive","50",".3","2"),listOf("dead","60",".4","3"),listOf("dead","70",".1","4"))
        val opts=JSONObject().put("time","3").put("event","0").put("eventValue","dead").put("truncation","entry").put("entry","2").put("predictors","1")
        assertEquals("parametricsurvival([[1,1,.2,40],[2,0,.3,50],[3,1,.4,60],[4,1,.1,70]],weibull,0.95,2,6)",guidedStatisticsCommand(definition("parametricsurvival"),rows,opts))
        assertEquals(mapOf("feature:1" to "age"),advancedStatisticsTermLabels(definition("parametricsurvival"),rows,opts,listOf("event","age","entry","time")))
        assertTrue(runCatching {guidedStatisticsCommand(definition("parametricsurvival"),rows,JSONObject(opts.toString()).put("predictors","2"))}.isFailure)
        assertEquals("parametricsurvival([[1,1],[2,0]],weibull,0.95,-1,6)",guidedStatisticsCommand(definition("parametricsurvival"),listOf(listOf("1","1"),listOf("2","0")),JSONObject().put("covariates","none")))
    }
    @Test fun moderatorsAndSubgroupsAcceptRawIndependentArmSummaries() {
        for(id in listOf("metaregression","metasubgroup"))for(layout in listOf("binary","continuous")) {
            val d=definition(id);val settings=JSONObject().put("layout",layout);val rows=advancedStatisticsExampleRows(d,settings)
            assertEquals(if(layout=="binary")5 else 7,rows.first().size)
            assertTrue(guidedStatisticsCommand(d,rows,settings).endsWith(if(layout=="binary")",oddsratio,0.5)" else ",md)"))
        }
        val binary=listOf(listOf("12","100","20","100","2010"),listOf("8","80","15","90","2012"))
        assertEquals("metaregression([[12,100,20,100,2010],[8,80,15,90,2012]],pm,0.95,hksj,oddsratio,0.5)",guidedStatisticsCommand(definition("metaregression"),binary,JSONObject().put("layout","binary").put("predictors","4")))
        val continuous=listOf(listOf("12","3","50","10","2.5","48","US"),listOf("15","4","60","12","3.5","55","KR"))
        assertEquals("metasubgroup([[12,3,50,10,2.5,48,1],[15,4,60,12,3.5,55,2]],pm,0.95,hksj,md)",guidedStatisticsCommand(definition("metasubgroup"),continuous,JSONObject().put("layout","continuous").put("group","6")))
    }
}
