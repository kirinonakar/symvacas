package com.kirinonakar.symvacas

import com.kirinonakar.symvacas.calculator.DataTransfer
import com.kirinonakar.symvacas.calculator.FunctionTransfer
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import java.io.File

class DataTransferTest {
    @Test fun androidAndWebAcceptTheSamePortableFixture() {
        val data=DataTransfer.decode(File("../tests/fixtures/data_transfer.json").readText(Charsets.UTF_8))
        val exported=DataTransfer.encode(data.getJSONObject("variables"),data.getJSONObject("functions"),data.getJSONObject("datasets"),data.getJSONObject("assumptions"))
        val restored=DataTransfer.decode(exported)
        assertEquals("점수,그룹\n1,A\n2,B",restored.getJSONObject("datasets").getJSONObject("D1").getString("csv"))
        assertEquals("snapshot_symbol",restored.getJSONObject("functions").getJSONObject("f").getJSONObject("body").getJSONArray("args").getJSONObject(0).getString("kind"))
    }
    @Test fun portableRoundtripKeepsGuardedBodiesCategoricalDataAndAssumptions() {
        val variables=JSONObject("""{"Ans":{"kind":"number","value":"9"},"a":{"kind":"number","value":"1"}}""")
        val function=FunctionTransfer.definition("f","x","x+1").json()
        val guarded=JSONObject("""{"kind":"restricted","args":[{"kind":"symbol","value":"x"},{"kind":"relation","value":"!=","args":[{"kind":"symbol","value":"x"},{"kind":"number","value":"0"}]}]}""")
        function.put("body",guarded).put("answerSource",variables.getJSONObject("Ans"))
        val functions=JSONObject().put("f",function)
        val datasets=JSONObject().put("D1",JSONObject().put("csv","x,group\n1,A\n2,B").put("kind","columns:2"))
        val assumptions=JSONObject("""{"a":["positive"]}""")
        val encoded=DataTransfer.encode(variables,functions,datasets,assumptions)
        val imported=DataTransfer.decode("\uFEFF"+encoded)
        assertEquals(guarded.toString(),imported.getJSONObject("functions").getJSONObject("f").getJSONObject("body").toString())
        assertEquals(datasets.toString(),imported.getJSONObject("datasets").toString())
        assertEquals(assumptions.toString(),imported.getJSONObject("assumptions").toString())
        assertEquals(2,DataTransfer.merge(JSONObject().put("other",1),imported.getJSONObject("datasets")).length())
    }
    @Test fun settingsResetPreservesOnlyUserDataRegardlessOfPreferenceKey() {
        val prefs=mapOf("variables" to "{\"a\":1}","functions" to "{\"f\":1}","dataSets" to "{\"D1\":1}","assumptions" to "{}", "history" to "[1]","expression" to "old", "statisticsSectionExpansion" to "{\"summary\":false}","unknownFutureSetting" to true)
        val reset=DataTransfer.settingsResetData(prefs)
        assertEquals(setOf("variables","functions","dataSets","assumptions"),reset.keys)
        assertEquals(prefs["dataSets"],reset["dataSets"])
        assertEquals("{}",DataTransfer.settingsResetData(emptyMap<String,Any>())["variables"])
    }
    @Test fun malformedImportsFailAndEmptyLibrariesAreValid() {
        val source=DataTransfer.encode(JSONObject(),JSONObject(),JSONObject(),JSONObject())
        assertEquals(0,DataTransfer.decode(source).getJSONObject("functions").length())
        for(text in listOf(source.replace("\"version\": 1","\"version\": 2"),source.replace("\"variables\": {}","\"variables\": {\"a\": {\"kind\": 1}}"))) {
            assertThrows(Exception::class.java){DataTransfer.decode(text)}
        }
        assertTrue(DataTransfer.validDatasetKind("columns:100"));assertFalse(DataTransfer.validDatasetKind("columns:101"))
        for(name in listOf("mode","skewness","kurtosis"))assertThrows(Exception::class.java){FunctionTransfer.definition(name,"x","x")}
    }
}
