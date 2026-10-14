package com.kirinonakar.symvacas.ui

import com.kirinonakar.symvacas.calculator.ResultDisplayMode
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class MathClipboardTest {
    @Test fun copiesEngineTextLeavesAsMathAndKeepsDisabledCopiesUnchanged() {
        val tree=JSONObject("""{"kind":"fraction","args":[{"kind":"text","value":"1"},{"kind":"text","value":"2"}]}""")
        assertEquals("\\frac{1}{2}",latexTree(tree))
        assertEquals("1/2",mathCopyText("1/2",false))
        assertEquals("\\frac{1}{2}",mathCopyText("1/2",true))
        val decimal=JSONObject("""{"kind":"number","value":"0.123456"}""")
        assertEquals("0.123",latexTree(ResultDisplayFormat.formatTree(decimal,ResultDisplayMode.OFF,false,maxFractionDigits=3)))
        val report=JSONObject("""{"steps":[{"title":"Result","explanation":"Keep this explanation.","tree":$tree}]}""")
        val copied=solutionStepsCopyText(report,3,true){it}
        assertTrue(copied.contains("Keep this explanation."));assertTrue(copied.contains("\\frac{1}{2}"))
        assertFalse(solutionStepsCopyText(report,3){it}.contains("\\frac"))
    }
}
