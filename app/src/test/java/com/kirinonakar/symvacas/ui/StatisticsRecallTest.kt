package com.kirinonakar.symvacas.ui

import com.kirinonakar.symvacas.math.Editor
import org.junit.Assert.assertEquals
import org.junit.Test

class StatisticsRecallTest {
    private fun recall(source:String,csv:String="1\n2\n3",kind:String="list",committed:Boolean=false):String {
        val caret=source.indexOf('|')
        val editor=Editor(source.replace("|",""),caret)
        return editor.insert(statisticsRecallSource(editor,csv,kind,committed)).source
    }

    @Test fun recalledListsFillCatalogArgumentsWithoutNesting() {
        for(name in listOf("sumdata","mean","median","variance","stdev","mode","skewness","kurtosis","quartiles","stats"))
            assertEquals("$name([1,2,3])",recall("$name([|])"))
        assertEquals("variance([1,2,3],0)",recall("variance([|],0)"))
        assertEquals("correlation([4,5,6],[1,2,3])",recall("correlation([4,5,6],[|])"))
        assertEquals("mean([ 1,2,3 ])",recall("mean([ | ])"))
        assertEquals("mean([])",recall("mean([|])",""))
    }

    @Test fun tablesKeepRowsAndWholeListInsertionsKeepTheirBrackets() {
        assertEquals("regression([[1,2],[3,4]],linear)",recall("regression([|],linear)","1,2\n3,4","xy"))
        assertEquals("regression([[1,2,3],[4,5,6]],multiple)",recall("regression([|],multiple)","1,2,3\n4,5,6","xyz"))
        assertEquals("mean([1,2,3])",recall("mean(|)"))
        assertEquals("[1,2,3]",recall("|"))
        assertEquals("mean([4,[1,2,3]])",recall("mean([4,|])"))
        val selected=Editor("mean([])",7,5)
        assertEquals("[1,2,3]",statisticsRecallSource(selected,"1\n2\n3","list"))
        assertEquals("[1,2,3]",statisticsRecallSource(Editor("mean([])",6),"1\n2\n3","list",true))
    }
}
