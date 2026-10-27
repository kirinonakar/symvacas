package com.kirinonakar.symvacas.calculator

import java.io.File
import org.json.JSONArray
import org.junit.Assert.assertEquals
import org.junit.Test

class ExecutionBudgetTest {
    @Test fun sharedAndroidWebPythonBudgetCases() {
        val file=listOf(File("tests/fixtures/execution_budget.json"),File("../tests/fixtures/execution_budget.json")).first {it.isFile}
        val cases=JSONArray(file.readText())
        for(i in 0 until cases.length()) {
            val case=cases.getJSONObject(i)
            assertEquals(case.getString("name"),case.getLong("timeoutMillis"),executionTimeoutMillis(case.getJSONObject("request")))
        }
    }
}
