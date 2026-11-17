package com.kirinonakar.symvacas.calculator

import com.kirinonakar.symvacas.math.Parser
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Test

class StatisticsBindingsTest {
    private fun tree(source:String)=JSONObject(Parser(source).parse().json())
    private fun data(csv:String,kind:String="list")=JSONObject().put("csv",csv).put("kind",kind)

    @Test fun storedFormulasAndFunctionsResolveOnlyReferencedDatasets() {
        val saved=JSONObject().put("D1",data("1\n2\n3")).put("Unused",data("bad("))
        val variables=JSONObject().put("A",tree("mean(D1)"))
        val functions=JSONObject().put("f",JSONObject().put("parameters",org.json.JSONArray().put("x")).put("body",tree("sumdata(D1)+x")))
        val result=savedStatisticsDatasets(tree("A+f(1)"),saved,variables,functions)
        assertEquals("[\"1\",\"2\",\"3\"]",result.getJSONArray("D1").toString())
        assertEquals(1,result.length())
    }
}
