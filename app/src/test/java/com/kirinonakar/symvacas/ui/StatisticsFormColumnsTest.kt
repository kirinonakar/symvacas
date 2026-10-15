package com.kirinonakar.symvacas.ui

import java.io.File
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Test

class StatisticsFormColumnsTest {
    @Test fun posthocCommandsPreserveUnequalSamplesAndSelectedControl() {
        val rows=listOf(listOf("1","3","6"),listOf("2","4","8"),listOf("","5","9"))
        val opts=mapOf("grouping" to "columns","columns" to "2,0,1","control" to "2","adjustment" to "holm")
        for(id in listOf("scheffe","dunnett","conover")) {
            val suffix=when(id){"dunnett"->",2";"conover"->",holm";else->""}
            val plan=socialStatisticsPlan(id,rows,opts,listOf("Placebo","Low","High"))
            assertEquals("$id([[6,8,9],[1,2],[3,4,5]]$suffix)",plan.expression)
            assertEquals(mapOf("sample:1" to "High","sample:2" to "Placebo","sample:3" to "Low"),plan.labels)
        }
    }
    private val schema=JSONArray(File("src/main/assets/advanced_statistics.json").readText())
    private fun definition(id:String)=(0 until schema.length()).map {schema.getJSONObject(it)}.first {it.getString("id")==id}

    @Test fun huberPredictorFormOnlyReservesTheResponseWithoutLookingUpSubject() {
        val d=definition("robustreg")
        assertEquals(setOf(2),advancedStatisticsReservedColumns(d,JSONObject(),"predictors",3))
        assertEquals(setOf(0),advancedStatisticsReservedColumns(d,JSONObject().put("response","0"),"predictors",3))
    }

    @Test fun moderatorAndSurvivalFormsReserveTheirActualInputRoles() {
        val meta=definition("metaregression")
        assertEquals(setOf(0,1),advancedStatisticsReservedColumns(meta,JSONObject(),"predictors",3))
        assertEquals(setOf(0,1,2,3),advancedStatisticsReservedColumns(meta,JSONObject().put("layout","binary"),"predictors",5))
        assertEquals((0..5).toSet(),advancedStatisticsReservedColumns(meta,JSONObject().put("layout","continuous"),"predictors",7))
        for(id in listOf("parametricsurvival","cox")) {
            assertEquals(setOf(0,1),advancedStatisticsReservedColumns(definition(id),JSONObject(),"predictors",4))
            assertEquals(setOf(0,1,2),advancedStatisticsReservedColumns(definition(id),JSONObject().put("truncation","entry").put("entry","2"),"predictors",4))
        }
    }

    @Test fun everyCheckboxFormAcceptsItsSchemaDefaultsWhenOpening() {
        for(i in 0 until schema.length()) {
            val d=schema.getJSONObject(i);val fields=d.optJSONArray("controls") ?: continue
            for(j in 0 until fields.length()) {
                val field=fields.getJSONObject(j)
                if(field.getString("type")=="columns")advancedStatisticsReservedColumns(d,JSONObject(),field.getString("key"),8)
            }
        }
    }
}
