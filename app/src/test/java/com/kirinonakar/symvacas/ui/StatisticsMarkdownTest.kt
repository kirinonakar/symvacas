package com.kirinonakar.symvacas.ui

import com.kirinonakar.symvacas.calculator.ResultDisplayMode
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class StatisticsMarkdownTest {
    private fun format(cell:JSONObject)=ResultDisplayFormat.resultText(cell,true,false,ResultDisplayMode.OFF,true,false,0,false,false,3)
    @Test fun contingencyMarginsTranslateWithoutChangingCategoryNames() {
        val result=JSONObject("""{"statisticsReport":{"title":"Fisher exact test","sections":[{"title":"Row percentages (%)","columns":["Row","Category 1","Total"],"rows":[["Total","25","100"],["Total","25","100"]],"totalRow":1}]}}""")
        val copied=statisticsResultMarkdown(result,::format){translateLabel(it,"ko")}
        assertTrue(copied.contains("### 행 기준 백분율 (%)"))
        assertTrue(copied.contains("| 행 | Category 1 | 합계 |"))
        assertTrue(copied.contains("| Total | 25 | 100 |"))
        assertTrue(copied.contains("| 합계 | 25 | 100 |"))
    }
    @Test fun completeMarkdownKeepsRowsPrecisionAndLiteralLabels() {
        val result=JSONObject("""{"exact":"source should not be copied","note":"Result only","statisticsReport":{"title":"Descriptive statistics","sections":[{"title":"Summary","columns":["Metric","Value"],"rows":[["mean",{"decimal":"1.234567"}]],"copyRows":[["mean",{"decimal":"1.234567"}],["A|B\n<row>",{"decimal":"12345.6789"}]]}]}}""")
        result.getJSONObject("statisticsReport").put("assumptions",org.json.JSONArray().put("Independent rows; ordered categories."))
        result.getJSONObject("statisticsReport").put("details",org.json.JSONArray().put(JSONObject().put("section","Summary").put("label","Estimator").put("text","Normal-theory covariance ML (N divisor)")))
        val text=statisticsResultMarkdown(result,::format){it}
        assertTrue(text.contains("| Metric | Value |\n| --- | --- |\n| mean | 1.235 |"))
        assertTrue(text.contains("| A\\|B<br>&lt;row&gt; | 12,345.679 |"))
        assertTrue(text.endsWith("Result only"))
        assertTrue(text.contains("### Assumptions\n\nIndependent rows; ordered categories."))
        assertTrue(text.contains("### Model details\n\nEstimator: Normal-theory covariance ML (N divisor)"))
        assertTrue(text.indexOf("### Model details")>text.indexOf("| A\\|B"))
        assertFalse(text.contains("source should not be copied"))
        val korean=statisticsResultMarkdown(result,::format){translateLabel(it,"ko")}
        assertTrue(korean.startsWith("## "+translateLabel("Descriptive statistics","ko")))
        assertTrue(korean.contains("| "+translateLabel("Metric","ko")+" | "+translateLabel("Value","ko")+" |"))
        assertTrue(korean.contains("A\\|B"))
    }
    @Test fun fittedReportCopiesItsOwnResponseAfterTheMainResultChanges() {
        val report=JSONObject().put("model","logistic").put("n",6)
        val fitted=JSONObject().put("regression",report).put("statisticsCopyReport",JSONObject().put("title","Regression").put("sections",org.json.JSONArray()))
        assertSame(fitted,regressionResultForCopy(fitted,report))
        val current=JSONObject().put("exact","123").put("statisticsReport",JSONObject().put("title","Mean"))
        val recovered=regressionResultForCopy(JSONObject(fitted.toString()),report)!!
        assertTrue(statisticsResultMarkdown(recovered,::format){it}.startsWith("## Regression"))
        assertNull(regressionResultForCopy(current,report))
        assertNull(regressionResultForCopy(fitted,JSONObject().put("model","logistic").put("n",9)))
    }
}
