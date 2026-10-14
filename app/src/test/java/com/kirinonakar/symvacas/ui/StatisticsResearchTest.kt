package com.kirinonakar.symvacas.ui

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import org.json.JSONArray
import org.json.JSONObject
import java.io.File

class StatisticsResearchTest {
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
