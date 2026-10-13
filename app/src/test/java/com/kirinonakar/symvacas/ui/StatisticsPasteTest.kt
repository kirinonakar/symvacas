package com.kirinonakar.symvacas.ui

import java.io.File
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class StatisticsPasteTest {
    @Test fun sharedPasteCasesPreserveDataAndRemoveMarkdownHeadings() {
        val fixtures=JSONObject(File("../tests/fixtures/statistics_number_import.json").readText())
        val pastes=fixtures.getJSONArray("pastes")
        for(index in 0 until pastes.length()) {
            val item=pastes.getJSONObject(index)
            assertEquals(item.getString("source"),item.getString("expected"),statisticsPasteText(item.getString("source"),item.optBoolean("singleColumn")))
        }
        val cells=fixtures.getJSONArray("cells")
        for(index in 0 until cells.length()) {
            val item=cells.getJSONObject(index)
            assertEquals(item.getString("source"),item.getString("expected"),statisticsPasteCell(item.getString("source")))
        }
    }

    @Test fun selectionReplacementFiltersOnlyTheInsertedText() {
        val previous="# existing\n12\n34"
        val pasted="# note\n56\n# skipped\n78"
        assertEquals("# existing\n56\n78\n34",normalizeStatisticsPaste(previous,"# existing\n$pasted\n34",selectionStart=11,selectionEnd=13))
        assertNull(normalizeStatisticsPaste("","#",selectionStart=0,selectionEnd=0))
        assertEquals("12",normalizeStatisticsPaste("12","12# comment",selectionStart=2,selectionEnd=2))
        assertEquals("before\nx,y\n1,2\nafter",normalizeStatisticsPaste("before\nold\nafter","before\nx\ty\n1\t2\nafter",selectionStart=7,selectionEnd=10))
    }
}
