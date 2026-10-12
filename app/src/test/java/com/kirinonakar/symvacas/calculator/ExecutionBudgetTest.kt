package com.kirinonakar.symvacas.calculator

import org.json.JSONArray
import org.junit.Assert.assertEquals
import org.junit.Test
import java.io.File

class ExecutionBudgetTest {
    @Test fun sharedBootstrapBudgetsMatchWorkerAndPython() {
        val cases=JSONArray(File("../tests/fixtures/execution_budget.json").readText())
        for(index in 0 until cases.length()) {
            val item=cases.getJSONObject(index)
            assertEquals(item.getString("name"),item.getLong("timeoutMillis"),executionTimeoutMillis(item.getJSONObject("request")))
        }
    }
}
