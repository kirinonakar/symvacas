package com.kirinonakar.symvacas.ui

import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class StatisticsDetailsTest {
    @Test fun descriptionsAssumptionsAndNotesShareOneDeduplicatedPresentation() {
        val report=JSONObject("""{"title":"MANCOVA","sections":[],"details":[
            {"label":"Method","text":"Common slopes."},{"label":"Method","text":"Common slopes."},
            {"label":"Reason","text":"Unavailable.","context":[{"label":"Sample","value":"A"}]},
            {"label":"Reason","text":"Unavailable.","context":[{"label":"Sample","value":"B"}]}],
            "assumptions":["Common  slopes.","Independent subjects.","Independent subjects."],
            "notes":["Independent subjects.","Pointwise intervals."]}""")
        val snapshot=report.toString()
        assertEquals(listOf("Method: Common slopes.","Sample: A · Reason: Unavailable.","Sample: B · Reason: Unavailable.","Independent subjects.","Pointwise intervals."),statisticsModelDetails(report,"Pointwise intervals."){it})
        assertEquals(snapshot,report.toString())
        val result=JSONObject().put("statisticsReport",report).put("note","Pointwise intervals.")
        val markdown=statisticsResultMarkdown(result,{it.optString("decimal")}){it}
        assertEquals(1,markdown.split("### Model details").size-1)
        assertFalse(markdown.contains("### Assumptions"))
        assertEquals(1,markdown.split("Independent subjects.").size-1)
        assertEquals(1,markdown.split("Pointwise intervals.").size-1)
    }
}
