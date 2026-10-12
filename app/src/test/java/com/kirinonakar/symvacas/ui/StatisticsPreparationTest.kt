package com.kirinonakar.symvacas.ui

import java.io.File
import org.json.JSONObject
import org.json.JSONArray
import org.junit.Assert.*
import org.junit.Test
import kotlin.math.abs
import kotlin.math.max
import com.kirinonakar.symvacas.calculator.DataTransfer

class StatisticsPreparationTest {
    @Test fun filteredDatasetNamesAllowCustomNamesAndRejectOverwrites() {
        val names=listOf("D1","D3","Cohort_18")
        assertEquals("D4",newStatisticsDatasetName("",names,"D1"))
        assertEquals("Subset_2",newStatisticsDatasetName(" Subset_2 ",names,"D1"))
        assertEquals("Dataset name already exists; choose another name",runCatching {newStatisticsDatasetName("Cohort_18",names,"D1")}.exceptionOrNull()?.message)
        assertEquals("Use a letter followed by letters, digits or underscores for the dataset name",runCatching {newStatisticsDatasetName("1invalid",names,"D1")}.exceptionOrNull()?.message)
    }
    @Test fun rowFiltersPreserveCellsOrderAndNumericTextMissingAndCombinationSemantics() {
        val fixture=JSONObject(File("../tests/fixtures/statistics_row_filter.json").readText())
        val cases=fixture.getJSONArray("cases")
        for(i in 0 until cases.length()) {
            val item=cases.getJSONObject(i);val source=fixture.getString(item.getString("source"));val kind=if(item.getString("source")=="multi")"xyz" else "xy"
            val input=preparationDataset(source,kind)
            val result=preparationTransform(source,kind,"filter",mapOf("match" to item.getString("match"),"conditions" to item.getJSONArray("conditions").toString()))
            val indices=item.getJSONArray("rows");val expected=List(indices.length()){input.rows[indices.getInt(it)]}
            assertEquals(input.headers,result.headers);assertEquals(expected,result.rows);assertEquals(input.rows.size-expected.size,result.changed);assertEquals(0,result.omitted)
            if(result.rows.isNotEmpty())assertEquals(StatisticsPreparationDataset(result.headers,result.rows),preparationDataset(result.csv,result.kind))
        }
        val invalid=fixture.getJSONArray("invalid")
        for(i in 0 until invalid.length()) {
            val item=invalid.getJSONObject(i);val result=runCatching {preparationTransform(fixture.getString("numeric"),"xy","filter",mapOf("match" to item.getString("match"),"conditions" to item.getString("conditions")))}
            assertEquals(item.getString("error"),result.exceptionOrNull()?.message)
        }
    }
    private val fixture=JSONObject(File("../tests/fixtures/statistics_preparation.json").readText())
    private fun settings(item:JSONObject)=item.getJSONObject("settings").let {value->value.keys().asSequence().associateWith {value.getString(it)}}
    private fun strings(array:JSONArray)=List(array.length()){array.getString(it)}
    @Test fun preparationRowsHeadersPrecisionAndMissingnessMatchSharedReferences() {
        val cases=fixture.getJSONArray("cases")
        for(index in 0 until cases.length()) {
            val item=cases.getJSONObject(index);val result=preparationTransform(item.getString("source"),item.getString("kind"),item.getString("id"),settings(item))
            assertEquals(strings(item.getJSONArray("headers")),result.headers);assertEquals(item.getInt("changed"),result.changed);assertEquals(item.getInt("omitted"),result.omitted)
            val rows=item.getJSONArray("rows");assertEquals(rows.length(),result.rows.size)
            val numeric=item.optJSONArray("numericColumns")?.let {array->List(array.length()){array.getInt(it)}}.orEmpty()
            for(i in 0 until rows.length())for(j in result.headers.indices) {
                val expected=rows.getJSONArray(i).getString(j)
                if(j in numeric&&expected.isNotEmpty())assertEquals(expected.toDouble(),result.rows[i][j].toDouble(),1e-12*max(1.0,abs(expected.toDouble())))
                else assertEquals(expected,result.rows[i][j])
            }
            assertEquals(result.headers,preparationDataset(result.csv,result.kind).headers)
            assertEquals(result.rows,preparationDataset(result.csv,result.kind).rows)
        }
    }
    @Test fun invalidMappingsRolesDuplicatesAndFormulaOperationsRejectTheTransformation() {
        val cases=fixture.getJSONArray("invalid")
        for(index in 0 until cases.length()) {
            val item=cases.getJSONObject(index);val result=runCatching {preparationTransform(item.getString("source"),item.getString("kind"),item.getString("id"),settings(item))}
            assertTrue(result.isFailure);assertEquals(item.getString("error"),result.exceptionOrNull()?.message)
        }
    }
    @Test fun reshapingRoundtripKeepsQuotedIDsPrecisionAndMissingMeasurements() {
        val source="ID,before,after\n\"A,B\",1.2000,\nC,2,4"
        val long=preparationTransform(source,"xyz","wideToLong")
        assertEquals(source,preparationTransform(long.csv,long.kind,"longToWide").csv)
    }
    @Test fun explicitAllTextHeadersSurvivePersistence() {
        val result=preparationTransform("Gender\n1\n2","list","recode",mapOf("rules" to "1, male\n2, female","output" to "replace","header" to "Sex"))
        val saved=statisticsHeaderKeys();restoreStatisticsHeaderKeys("[]")
        assertFalse(statisticsHasHeader(statisticsCsvRows(result.csv)))
        restoreStatisticsHeaderKeys(saved);assertEquals(listOf(listOf("male"),listOf("female")),statisticsRows(result.csv))
        assertTrue(saved.contains("4021414396:2881141766:3"))
        val exported=DataTransfer.encode(JSONObject(),JSONObject(),JSONObject().put("D1",JSONObject().put("csv",result.csv).put("kind","list")),JSONObject())
        val imported=DataTransfer.decode(exported);restoreStatisticsHeaderKeys(imported.getJSONArray("statisticsHeaders").toString())
        assertEquals(listOf(listOf("male"),listOf("female")),statisticsRows(result.csv))
        assertEquals(saved,DataTransfer.settingsResetData(mapOf("statisticsHeaderKeys" to saved))["statisticsHeaderKeys"])
    }
}
