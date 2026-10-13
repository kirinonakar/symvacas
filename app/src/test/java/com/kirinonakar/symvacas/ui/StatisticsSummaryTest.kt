package com.kirinonakar.symvacas.ui

import java.io.File
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class StatisticsSummaryTest {
    @Test fun sharedPlansPreserveNumericDataAndLiteralCategories() {
        val cases=JSONObject(File("../tests/fixtures/statistics_summary.json").readText()).getJSONArray("cases")
        for(index in 0 until cases.length()) {
            val item=cases.getJSONObject(index)
            val plan=statisticsSummaryPlan(item.getString("source"),item.getString("kind"),item.getInt("column"))
            val labels=item.getJSONObject("labels").let {objectValue->objectValue.keys().asSequence().associateWith {objectValue.getString(it)}}
            assertEquals(item.getString("command"),plan.source);assertEquals(labels,plan.termLabels)
        }
        assertEquals("Enter at least one data value",runCatching {statisticsSummaryPlan("\"\"\n\"\"","list")}.exceptionOrNull()?.message)
    }
    @Test fun overallPlansKeepIndependentColumnValuesAndLabels() {
        val cases=JSONObject(File("../tests/fixtures/statistics_summary.json").readText()).getJSONArray("overallCases")
        for(index in 0 until cases.length()) {
            val item=cases.getJSONObject(index)
            val plan=statisticsOverallPlan(item.getString("source"),item.getString("kind"))
            val labels=item.getJSONObject("labels").let {value->value.keys().asSequence().associateWith {value.getString(it)}}
            assertEquals(item.getString("command"),plan.source);assertEquals(labels,plan.termLabels)
        }
        assertEquals("Enter at least one data value",runCatching {statisticsOverallPlan("\"\"\n\"\"","list")}.exceptionOrNull()?.message)
    }
    @Test fun groupedTPlansMatchWebIndependentAndPairedColumnSamples() {
        val cases=JSONObject(File("../tests/fixtures/statistics_t_columns.json").readText()).getJSONArray("cases")
        for(index in 0 until cases.length()) {
            val item=cases.getJSONObject(index);val settings=item.getJSONObject("settings")
            val plan=statisticsGroupedTTestPlan(statisticsRows(item.getString("source")),settings.getString("kind"),statisticsColumnLabels(item.getString("source"),settings.getString("kind")),
                settings.getString("valueColumns"),settings.getInt("groupColumn"),settings.getInt("valueColumn"),settings.getString("firstGroup"),settings.getString("secondGroup"),settings.getString("op")=="ttestpaired",
                settings.optString("matching","order"),settings.optInt("subjectColumn",0),settings.optString("extra","0"),when(settings.optString("tail")){"right"->"Right";"left"->"Left";else->"Two-sided"},settings.optString("independentMethod","welch"))
            val labels=item.getJSONObject("labels").let {value->value.keys().asSequence().associateWith {value.getString(it)}}
            assertEquals(item.getString("command"),plan.source);assertEquals(labels,plan.termLabels)
        }
    }
    @Test fun groupedRankCategoricalAnovaAndZPlansMatchWeb() {
        val cases=JSONObject(File("../tests/fixtures/statistics_grouped_columns.json").readText()).getJSONArray("cases")
        for(index in 0 until cases.length()) {
            val item=cases.getJSONObject(index);val settings=item.getJSONObject("settings");val kind=settings.getString("kind")
            val procedure=when(settings.getString("op")){"ztest2"->"z test";"chi2independence"->"χ² test";"fisherexact"->"Fisher exact";"wilcoxon"->"Wilcoxon";"mannwhitney"->"Mann–Whitney";"kruskal"->"Kruskal–Wallis";else->"ANOVA"}
            val plan=statisticsGroupedTestPlan(statisticsRows(item.getString("source")),kind,statisticsColumnLabels(item.getString("source"),kind),settings.getString("valueColumns"),procedure,
                settings.optInt("groupColumn",0),settings.optInt("valueColumn",1),settings.optString("firstGroup"),settings.optString("secondGroup"),
                matching=settings.optString("matching","order"),subjectColumn=settings.optInt("subjectColumn",0),mu0=settings.optString("extra","0"),sigma=settings.optString("sigma","1"),sigmaY=settings.optString("sigmaY","1"),
                anovaMethod=if(settings.getString("op")=="welchanova")"welch" else settings.optString("anovaMethod","welch"))
            val labels=item.getJSONObject("labels").let {value->value.keys().asSequence().associateWith {value.getString(it)}}
            assertEquals(item.getString("command"),plan.source);assertEquals(labels,plan.termLabels)
        }
    }
}
