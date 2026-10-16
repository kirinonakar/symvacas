package com.kirinonakar.symvacas.calculator

import com.kirinonakar.symvacas.math.Parser
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Test

class StatisticsBindingsTest {
    private fun tree(source:String)=JSONObject(Parser(source).parse().json())
    private fun data(csv:String,kind:String="list")=JSONObject().put("csv",csv).put("kind",kind)

    @Test fun namedDatasetsKeepExactCellsShapesAndCurrentValues() {
        val saved=JSONObject().put("D1",data("value\n0.1\n\n0.2\n1/2")).put("D2",data("x,y\n1,2\n3,4","xy"))
        fun bindings(source:String)=savedStatisticsDatasets(tree(source),saved,JSONObject(),JSONObject())
        val vector=bindings("sumdata(D1)").getJSONArray("D1")
        assertEquals("0.1",vector.getJSONObject(0).getString("value"))
        assertEquals("/",vector.getJSONObject(2).getString("value"))
        assertEquals("[[\"1\",\"2\"],[\"3\",\"4\"]]",bindings("regression(D2,linear)").getJSONArray("D2").toString())
        saved.put("D1",data((1..5000).joinToString("\n")))
        assertEquals(5000,bindings("mean(D1)").getJSONArray("D1").length())
        assertEquals(0,bindings("2+3").length())
    }

    @Test fun storedFormulasAndFunctionsResolveOnlyReferencedDatasets() {
        val saved=JSONObject().put("D1",data("1\n2\n3")).put("Unused",data("bad("))
        val variables=JSONObject().put("A",tree("mean(D1)"))
        val functions=JSONObject().put("f",JSONObject().put("parameters",org.json.JSONArray().put("x")).put("body",tree("sumdata(D1)+x")))
        val result=savedStatisticsDatasets(tree("A+f(1)"),saved,variables,functions)
        assertEquals("[\"1\",\"2\",\"3\"]",result.getJSONArray("D1").toString())
        assertEquals(1,result.length())
    }
}
