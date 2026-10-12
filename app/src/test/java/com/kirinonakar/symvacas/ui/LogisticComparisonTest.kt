package com.kirinonakar.symvacas.ui

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class LogisticComparisonTest {
    @Test fun trainingDatasetCanAlsoSupplyValidationRows() {
        val opts=mapOf("response" to "2","basePredictors" to "0","addedPredictors" to "1","validation" to "external","threshold" to "0.5","level" to "0.95","resamples" to "200","seed" to "0")
        val rows=listOf(listOf("1","2","0"),listOf("3","4","1"));val names=listOf("age (x)","MRI (y)","event (z)")
        assertEquals("logisticcompare([[1,2,0],[3,4,1]],1,external,[[1,2,0],[3,4,1]],0.5,0.95,200,0,[2,2])",logisticComparisonPlan(rows,opts,names,rows,names))
    }
    @Test fun externalColumnsAlignByUniqueHeadersAndUseCommonCompleteRows() {
        val opts=mapOf("response" to "0","basePredictors" to "3","addedPredictors" to "1","validation" to "external","threshold" to "0.5","level" to "0.95","resamples" to "200","seed" to "0")
        val rows=listOf(listOf("0","1,234","","4"),listOf("1","","ignore","5"),listOf("0","2","","6"))
        val other=listOf(listOf("8","1","9",""),listOf("10","0","11",""),listOf("","1","3",""))
        assertEquals("logisticcompare([[4,1234,0],[6,2,0]],1,external,[[8,9,1],[10,11,0]],0.5,0.95,200,0,[3,3])",logisticComparisonPlan(rows,opts,listOf("event (x)","MRI (y)","unused (z)","age (x4)"),other,listOf("age (x)","event (y)","MRI (z)","unused (x4)")))
        assertTrue(runCatching {logisticComparisonPlan(rows,opts,listOf("a","a","b","c"),other,listOf("a","b","c","d"))}.isFailure)
        assertTrue(runCatching {logisticComparisonPlan(rows,opts+mapOf("addedPredictors" to "3"))}.isFailure)
    }
}
