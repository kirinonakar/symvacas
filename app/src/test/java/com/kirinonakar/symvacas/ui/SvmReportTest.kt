package com.kirinonakar.symvacas.ui

import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class SvmReportTest {
    @Test fun decisionEquationsUseTheSvmSourceAndClassificationPrefix() {
        for(source in listOf("0+(0.8)*x","-0.1+(0.9)*exp(-(0.5)*(((x1-(-2))/(1.3))^2+((x2-(3))/(2))^2))")) {
            val equation=JSONObject().put("expression",source)
            val report=JSONObject().put("model","svm").put("task","classification").put("decisionEquation",equation)
            val result=JSONObject().put("exact","SVC").put("regression",report)
            val copied=regressionEquationCopyText(result,6)
            assertNotNull(copied);assertTrue(copied!!.startsWith("f(x) = "))
            assertFalse(copied.contains("SVC"));assertTrue(copied.contains("x"))
            report.put("task","regression");assertNull(regressionEquationCopyText(result,6))
            report.put("predictionEquation",equation)
            assertTrue(regressionEquationCopyText(result,6)!!.startsWith("ŷ = "))
        }
    }

    @Test fun largeRbfModelsKeepTheirIndexedEquationAndCopyItOnce() {
        val formula="f(x) = b + Σᵢ aᵢ exp(−γ Σⱼ ((xⱼ − vᵢⱼ)/sⱼ)²)"
        val report=JSONObject().put("model","svm").put("task","classification").put("decisionEquation",JSONObject().put("formula",formula))
        val section=JSONObject().put("title","Summary").put("columns",JSONArray(listOf("Metric","Value")))
            .put("rows",JSONArray().put(JSONArray(listOf("Model","SVC"))).put(JSONArray(listOf("Decision function",formula))))
        val result=JSONObject().put("regression",report).put("statisticsCopyReport",JSONObject().put("title","SVM classification").put("sections",JSONArray().put(section)))
        assertEquals(formula,regressionEquationCopyText(result,6))
        val markdown=statisticsResultMarkdown(result,{it.optString("decimal")},formula){it}
        assertTrue(markdown.contains("### Decision function"));assertFalse(markdown.contains("Regression equation"))
        assertEquals(1,markdown.windowed(formula.length).count {it==formula})
    }
}
