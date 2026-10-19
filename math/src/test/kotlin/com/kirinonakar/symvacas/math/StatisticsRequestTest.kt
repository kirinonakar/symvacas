package com.kirinonakar.symvacas.math

import org.junit.Assert.*
import org.junit.Test

class StatisticsRequestTest {
    @Test fun bayesianRegressionModesRemainLiteralWithAnalyticAndNutsOptions() {
        for(mode in listOf("bayeslinear","bayeslogistic")) {
            val prior=if(mode=="bayeslinear")"2.5,0.95,2,1" else "2.5,0.95"
            for(sampler in listOf("",",[nuts,100,50,4,7,2]")) {
                val source="regression([[1,0],[2,0],[3,1],[4,1]],$mode,[$prior$sampler])"
                for(tree in listOf(Parser(source).parse(),statisticsRequest(source).tree)) {
                    assertEquals("symbol",tree.args[1].kind)
                    assertEquals(mode,tree.args[1].value)
                }
            }
        }
    }
    @Test fun modelComparisonMetadataRemainsLiteralThroughRequestParsing() {
        val request=statisticsRequest("modelcompare([[1,1,2,3]],1,cox,external,[[2,1,3,4]],0.95,0,0,[[excludedrows,1],[excludedvalidation,2],[responsefamily,gaussian]],0)")
        assertEquals("symbol",request.tree.args[2].kind)
        assertEquals("cox",request.tree.args[2].value)
        val pairs=request.tree.args[8].args
        assertEquals(listOf("excludedrows","excludedvalidation","responsefamily"),pairs.map {it.args[0].value})
        assertTrue(pairs.all {it.args[0].kind=="symbol"})
    }
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
    @Test fun formulaListsAndExistingNamesKeepTheirMeaning() {
        val request=statisticsRequest("regression([[1,2],[3,4]],custom,SymvaStatisticsData0*x,x,[1])")
        assertEquals("SymvaStatisticsData0Data",request.tree.args[0].value)
        assertEquals(Parser("mean([1/2,2+3])").parse(),statisticsRequest("mean([1/2,2+3])").tree)
        assertThrows(IllegalArgumentException::class.java) {statisticsRequest("mean([1,,2])")}
    }
    @Test fun computationLimitsCanBeRemovedWithoutAllowingInvalidSyntax() {
        val literal="1"+"0".repeat(8192)
        val list="["+List(2100){"1"}.joinToString(",")+"]"
        assertThrows(IllegalArgumentException::class.java) {Parser(literal).parse()}
        assertThrows(IllegalArgumentException::class.java) {Parser(list).parse()}
        assertEquals(literal,Parser(literal,removeComputationLimit=true).parse().value)
        assertEquals(2100,Parser(list,removeComputationLimit=true).parse().args.size)
        assertThrows(IllegalArgumentException::class.java) {Parser("1+*2",removeComputationLimit=true).parse()}
        assertThrows(IllegalArgumentException::class.java) {Parser(literal).parse()}
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
