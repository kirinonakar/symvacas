package com.kirinonakar.symvacas.ui

import java.io.File
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class StatisticsSummaryTest {
    @Test fun sharedPlansPreserveNumericDataAndLiteralCategories() {
        val cases=JSONObject(File("../tests/fixtures/statistics_summary.json").readText()).getJSONArray("cases")
        for(index in 0 until cases.length()) {
            val item=cases.getJSONObject(index)
            val plan=statisticsSummaryPlan(item.getString("source"),item.getString("kind"),item.getInt("column"))
            val labels=item.getJSONObject("labels").let {objectValue->objectValue.keys().asSequence().associateWith {objectValue.getString(it)}}
            assertEquals(item.getString("command"),plan.source);assertEquals(labels,plan.termLabels)
        }
        assertEquals("Enter at least one data value",runCatching {statisticsSummaryPlan("\"\"\n\"\"","list")}.exceptionOrNull()?.message)
    }
}
