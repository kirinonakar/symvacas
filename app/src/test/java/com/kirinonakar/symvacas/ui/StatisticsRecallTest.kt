package com.kirinonakar.symvacas.ui

import com.kirinonakar.symvacas.math.Editor
import org.junit.Assert.assertEquals
import org.junit.Test

class StatisticsRecallTest {
    private fun recall(source:String,name:String="D1"):String {
        val caret=source.indexOf('|')
        val editor=Editor(source.replace("|",""),caret)
        return statisticsRecallTarget(editor).insert(name).source
    }

    @Test fun referencesReplaceEmptyCatalogLists() {
        for(name in listOf("sumdata","mean","median","variance","stdev","mode","skewness","kurtosis","quartiles","stats"))
            assertEquals("$name(D1)",recall("$name([|])"))
        assertEquals("variance(D1,0)",recall("variance([|],0)"))
        assertEquals("correlation(D2,D1)",recall("correlation(D2,[|])"))
        assertEquals("mean(D1)",recall("mean([ | ])"))
    }

}
