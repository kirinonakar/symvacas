package com.kirinonakar.symvacas.ui

import com.kirinonakar.symvacas.calculator.ResultDisplayMode
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import java.io.File

class StatisticsDisplayDigitsTest {
    @Test fun tinyValuesKeepTwoSignificantDigitsAndCopyMatchesTheDisplay() {
        val fixture=sequenceOf(File("../tests/fixtures/statistics_display_digits.json"),File("tests/fixtures/statistics_display_digits.json")).first {it.isFile}
        val cases=JSONArray(fixture.readText())
        repeat(cases.length()) {index->
            val case=cases.getJSONObject(index)
            val value=case.getString("value");val digits=case.getInt("digits");val expected=case.getString("expected")
            val cell=JSONObject().put("exact",value).put("decimal",value).put("decimalTree",JSONObject().put("kind","number").put("value",value))
            assertEquals(value,expected,ResultDisplayFormat.formatText(value,ResultDisplayMode.OFF,true,maxFractionDigits=digits,preserveSmallValues=true))
            assertEquals(value,expected,ResultDisplayFormat.formatTree(cell.getJSONObject("decimalTree"),ResultDisplayMode.OFF,false,maxFractionDigits=digits,preserveSmallValues=true).getString("value"))
            assertEquals(value,expected,statisticsFormattedCopyCell(cell,digits))
            assertEquals(value,expected,ResultDisplayFormat.resultText(cell,true,false,ResultDisplayMode.OFF,false,false,0,false,false,digits,preserveSmallValues=true))
            assertEquals(value,cell.getString("decimal"))
        }
        assertEquals("0",ResultDisplayFormat.formatText("0.0000123",ResultDisplayMode.OFF,false,maxFractionDigits=3))
        assertEquals("1.235×10^-90",ResultDisplayFormat.formatText("1.23456e-90",ResultDisplayMode.OFF,false,maxFractionDigits=3,preserveSmallValues=true))
    }

    @Test fun tinyRegressionCoefficientsSurviveEquationsCopyAndGraphTransfer() {
        val source="0.0000123*x+0.0000103"
        val tree=regressionFormulaDisplayTree(source,3)!!
        val shown=equationFormulaText(tree)
        assertTrue(shown.contains("0.000012"));assertTrue(shown.contains("0.000010"))
        val result=JSONObject().put("exact",source).put("decimal",source).put("regression",JSONObject().put("fitScale","y"))
        assertEquals("y = $shown",regressionEquationCopyText(result,3))
        val graph=regressionFormulaGraphSource(source,3)!!
        assertTrue(graph.contains("0.000012"));assertTrue(graph.contains("0.000010"))
        assertEquals(source,result.getString("exact"))
        for((fraction,expected) in listOf("123*x/10000000" to "0.000012","103*x/10000000" to "0.000010","4999*x/10000000" to "0.00050")) {
            assertTrue(equationFormulaText(regressionFormulaDisplayTree(fraction,3)!!).contains(expected))
            assertTrue(regressionFormulaGraphSource(fraction,3)!!.contains(expected))
        }
    }
}
