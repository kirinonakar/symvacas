package com.kirinonakar.symvacas.ui

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import org.json.JSONArray
import org.json.JSONObject
import java.io.File

class StatisticsResearchTest {
    @Test fun generalStatisticsCatalogAndCorrelationMenuShareAllThreeWorkingTemplates() {
        val ids=listOf("pearson","spearman","kendall")
        val templates=ids.map {"$it([],[],both)"}
        assertEquals(templates,Catalog.getValue("General statistics").filter {it.substringBefore("(") in ids})
        for(template in templates)assertEquals(1,Catalog.values.flatten().count {it==template})
        for(id in ids) {
            val d=definition(id)
            assertEquals("Correlation",d.getString("group"))
            assertEquals(d.getString("example"),guidedStatisticsCommand(d,advancedStatisticsExampleRows(d)))
            val rows=listOf(listOf("99","1","2"),listOf("98","3","4"),listOf("97","5","6"))
            val opts=JSONObject().put("first","1").put("second","2").put("tail","right")
            assertEquals("$id([1,3,5],[2,4,6],right)",guidedStatisticsCommand(d,rows,opts))
        }
    }
    @Test fun binaryPatientCountsAndAgreementExamplesUseSharedSelectedRoles() {
        val d=definition("metaanalysis");val rows=advancedStatisticsExampleRows(d,JSONObject().put("layout","binary"))
        assertEquals(4,rows[0].size)
        val settings=JSONObject().put("layout","binary").put("measure","riskratio")
        assertTrue(guidedStatisticsCommand(d,rows,settings).endsWith(",riskratio,0.5)"))
        val named=listOf(listOf("Trial A","12","100","20","100"),listOf("Trial B","8","80","15","90"))
        val opts=JSONObject().put("layout","binary").put("eventsA","1").put("totalA","2").put("eventsB","3").put("totalB","4").put("studyLabels","column").put("study","0")
        assertEquals("metaanalysis([[12,100,20,100],[8,80,15,90]],pm,0.95,z,1,oddsratio,0.5)",guidedStatisticsCommand(d,named,opts))
        val kappa=definition("cohenkappa")
        assertEquals("Reliability & agreement",kappa.getString("group"));assertEquals(kappa.getString("example"),guidedStatisticsCommand(kappa,advancedStatisticsExampleRows(kappa)))
        assertTrue(definition("phi").getBoolean("hidden"));assertEquals("Effect Size",definition("cramerv").getString("group"))
    }
    @Test fun continuousMeanSdAndSampleSizeInputSupportsMdAndHedgesG() {
        val d=definition("metaanalysis");val settings=JSONObject().put("layout","continuous").put("continuousMeasure","smd")
        val rows=advancedStatisticsExampleRows(d,settings);assertEquals(6,rows[0].size)
        assertTrue(guidedStatisticsCommand(d,rows,settings).endsWith(",smd)"))
        settings.put("continuousMeasure","md");assertTrue(guidedStatisticsCommand(d,rows,settings).endsWith(",md)"))
    }
    @Test fun forestPagingBoundsTheCanvasWithoutDroppingStudiesOrThePooledInterval() {
        val rows=JSONArray();for(i in 0 until 105)rows.put(JSONArray().put("Study ${i+1}").put(i).put(i-1).put(i+1))
        rows.put(JSONArray().put("Pooled effect").put(1).put(0).put(2))
        val weights=JSONArray();for(i in 0 until 105)weights.put(i+1)
        val plot=JSONObject().put("rows",rows).put("summaryIndex",105).put("weights",weights)
        val collected=mutableListOf<String>()
        for(i in 0 until 3) {
            val page=statisticsIntervalPage(plot,i);val selected=page.getJSONArray("rows")
            assertTrue(selected.length()<=41);assertEquals("Pooled effect",selected.getJSONArray(selected.length()-1).getString(0))
            assertEquals((i*40+1).toDouble(),page.getJSONArray("weights").getDouble(0),0.0)
            for(j in 0 until selected.length()-1)collected.add(selected.getJSONArray(j).getString(0))
        }
        assertEquals((1..105).map {"Study $it"},collected);assertEquals(106,rows.length())
    }
    private fun definition(id:String):JSONObject {
        val array=JSONArray(File("src/main/assets/advanced_statistics.json").readText())
        return (0 until array.length()).map {array.getJSONObject(it)}.first {it.getString("id")==id}
    }
    @Test fun sharedResearchExamplesBuildTheSameExpressions() {
        for(id in listOf("metaanalysis","icc","blandaltman","tost","tost2","tostpaired")) {
            val d=definition(id)
            assertEquals(d.getString("example"),guidedStatisticsCommand(d,advancedStatisticsExampleRows(d)))
        }
    }
    @Test fun selectedMetaRolesKeepStudyNamesOutOfNumericDataAndFixedInference() {
        val rows=listOf(listOf("Study A","0.2","0.1"),listOf("Study B","0.3","0.2"))
        val opts=JSONObject().put("effect","1").put("se","2").put("studyLabels","column").put("study","0").put("method","fixed").put("inference","hksj")
        assertEquals("metaanalysis([[0.2,0.1],[0.3,0.2]],fixed,0.95,z,1)",guidedStatisticsCommand(definition("metaanalysis"),rows,opts))
        assertEquals("Study A",advancedStatisticsTermLabels(definition("metaanalysis"),rows,opts,emptyList())["study:1"])
        assertTrue(runCatching {guidedStatisticsCommand(definition("metaanalysis"),rows,JSONObject(opts.toString()).put("se","1"))}.isFailure)
    }
    @Test fun pairedEquivalenceMatchesSubjectIDsAndIndependentSamplesOmitSeparately() {
        val independent=listOf(listOf("1","4"),listOf("2",""),listOf("","5"))
        assertEquals("tost2([1,2],[4,5],-0.5,0.5,welch,0.05)",guidedStatisticsCommand(definition("tost2"),independent))
        assertTrue(runCatching {guidedStatisticsCommand(definition("tostpaired"),independent)}.isFailure)
        val rows=listOf(listOf("s1","A","1"),listOf("s2","B","5"),listOf("s2","A","2"),listOf("s1","B","4"))
        val opts=JSONObject().put("grouping","groups").put("group","1").put("value","2").put("firstGroup","A").put("secondGroup","B").put("matching","subject").put("subject","0")
        assertEquals("tostpaired([1,2],[4,5],-0.5,0.5,0.05)",guidedStatisticsCommand(definition("tostpaired"),rows,opts))
    }
    @Test fun agreementSelectedColumnsAndFunnelBoundsKeepTheStatisticalMeaning() {
        val rows=listOf(listOf("11","","10"),listOf("9","","8"),listOf("7","","7"))
        assertEquals("blandaltman([[10,11],[8,9],[7,7]],0.95,log)",guidedStatisticsCommand(definition("blandaltman"),rows,JSONObject().put("first","2").put("second","0").put("mode","log")))
        val bounds=researchPlotBounds(listOf(.2 to .1,.3 to .2),listOf(listOf(.25 to 0.0,-.25 to .4),listOf(.25 to 0.0,.75 to .4)),emptyList(),true)
        assertEquals(0.0,bounds.ymin,0.0);assertTrue(bounds.ymax>.4);assertTrue(bounds.xmin<-.25);assertTrue(bounds.xmax>.75)
    }
}
