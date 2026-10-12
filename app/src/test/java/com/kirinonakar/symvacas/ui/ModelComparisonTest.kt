package com.kirinonakar.symvacas.ui

import java.io.File
import org.json.JSONArray
import org.junit.Assert.*
import org.junit.Test

class ModelComparisonTest {
    private fun defaults():Map<String,String> {
        val schema=JSONArray(File("src/main/assets/advanced_statistics.json").readText())
        val definition=(0 until schema.length()).map {schema.getJSONObject(it)}.first {it.getString("id")=="modelcompare"}
        val fields=definition.getJSONArray("controls")
        return (0 until fields.length()).associate {i->val field=fields.getJSONObject(i);field.getString("key") to field.get("default").toString()}
    }
    @Test fun commonCompleteUnionAlignedValidationAndCandidateLabelsMatchWeb() {
        val rows=listOf(listOf("1","2","0"),listOf("3","","1"),listOf("4","5","1"))
        val opts=defaults()+mapOf("candidates" to "1","validation" to "external","resamples" to "0")
        val plan=modelComparisonPlan(rows,opts,listOf("age (x)","biomarker (y)","event (z)"),listOf(listOf("0","6","7"),listOf("1","8","9")),listOf("event (x)","biomarker (y)","age (z)"))
        assertEquals("modelcompare([[1,2,0],[4,5,1]],1,linear,external,[[7,6,0],[9,8,1]],0.95,0,0,[[excludedrows,1],[excludedvalidation,0]],1)",plan.expression)
        assertEquals("biomarker (y)",plan.labels["candidate:1"])
    }
    @Test fun sameDatasetRemainsSelectableAndReservedRolesCannotBecomePredictors() {
        val rows=listOf(listOf("1","2","0"),listOf("3","4","1"));val opts=defaults()+mapOf("validation" to "external","resamples" to "0")
        assertTrue(modelComparisonPlan(rows,opts,validationRows=rows).expression.contains(",external,[[1,2,0],[3,4,1]],"))
        assertTrue(runCatching {modelComparisonPlan(rows,opts+mapOf("addedPredictors" to "0"),validationRows=rows)}.isFailure)
    }
}
