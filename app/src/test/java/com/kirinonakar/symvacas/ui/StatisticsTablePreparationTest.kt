package com.kirinonakar.symvacas.ui

import java.io.File
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class StatisticsTablePreparationTest {
    private val fixture=JSONObject(File("../tests/fixtures/statistics_table_preparation.json").readText())
    private val sources=fixture.getJSONObject("sources")

    private fun transform(item:JSONObject):StatisticsPreparationResult {
        val source=sources.getJSONObject(item.getString("source"))
        val other=sources.optJSONObject(item.optString("other"))?.let {
            StatisticsPreparationSource(it.getString("csv"),it.getString("kind"))
        }
        val options=item.getJSONObject("settings")
        val settings=options.keys().asSequence().associateWith {options.getString(it)}
        return preparationTransform(source.getString("csv"),source.getString("kind"),item.getString("id"),settings,other=other)
    }

    private fun JSONArray.strings()=List(length()) {getString(it)}

    @Test fun preservesHeadersAndRowsWhenDeletingOrCombiningData() {
        val cases=fixture.getJSONArray("cases")
        for(index in 0 until cases.length()) {
            val item=cases.getJSONObject(index)
            val result=transform(item)
            assertEquals(item.getJSONArray("headers").strings(),result.headers)
            assertEquals(item.getJSONArray("rows").let {rows->List(rows.length()){rows.getJSONArray(it).strings()}},result.rows)
            assertEquals(item.getInt("changed"),result.changed)
            assertEquals(StatisticsPreparationDataset(result.headers,result.rows),preparationDataset(result.csv,result.kind))
        }
    }

    @Test fun rejectsAmbiguousIndexesHeadersAndZeroColumnOutput() {
        val cases=fixture.getJSONArray("invalid")
        for(index in 0 until cases.length()) {
            val item=cases.getJSONObject(index)
            assertEquals(item.getString("error"),assertThrows(IllegalArgumentException::class.java){transform(item)}.message)
        }
    }
}
