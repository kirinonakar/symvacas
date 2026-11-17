package com.kirinonakar.symvacas.math

import org.junit.Assert.*
import org.junit.Test

class StatisticsRequestTest {
    @Test fun largeModelComparisonKeepsNestedParameterOptionsAsFormulaAst() {
        val data=(0 until 1200).joinToString(","){"[$it,1.25,2.5]"}
        val request=statisticsRequest("modelcompare([$data],0,cfa,fit,0,0.95,0,0,[[factors,[1,1,1]],[addedresidual,[[2,3]]]],0)")
        assertEquals(1200,request.datasets.getValue(request.tree.args[0].value).size)
        assertEquals("list",request.tree.args[8].kind)
        assertEquals("factors",request.tree.args[8].args[0].args[0].value)
        assertEquals(3,request.tree.args[8].args[0].args[1].args.size)
    }
    @Test fun largeTablesUseDecimalDatasetReferences() {
        val source="mixedmodel(["+(0 until 5000).joinToString(",") {"[${it%20},-1.25e-3,$it]"}+"],0)"
        assertThrows(IllegalArgumentException::class.java) {Parser(source).parse()}
        val request=statisticsRequest(source)
        val name=request.tree.args[0].value
        assertEquals("symbol",request.tree.args[0].kind)
        assertEquals(5000,request.datasets[name]!!.size)
        assertEquals(listOf("0","-1.25e-3","0"),request.datasets[name]!![0])
        assertTrue(request.tree.json().length<500)
    }
    @Test fun largeMixedTablesKeepCellExpressionsAndTheirParserGuards() {
        val source="impute(["+(0 until 5000).joinToString(",") {"[$it,${if(it==2)"NA" else if(it==3)"sqrt(4)" else "1/2"}]"}+"],mean)"
        val request=statisticsRequest(source);val rows=request.datasets.getValue(request.tree.args[0].value)
        assertEquals(5000,rows.size)
        assertEquals("NA",((rows[2] as List<*>)[1] as Map<*,*>)["value"])
        assertEquals("call",((rows[3] as List<*>)[1] as Map<*,*>)["kind"])
        assertEquals("/",((rows[0] as List<*>)[1] as Map<*,*>)["value"])
        assertTrue(request.tree.json().length<600)
        assertThrows(IllegalArgumentException::class.java) {statisticsRequest("mean(["+"1+".repeat(5000)+"1])")}
    }
}
