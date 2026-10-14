package com.kirinonakar.symvacas.math

import org.junit.Assert.*
import org.junit.Test

class LatexOutputTest {
    @Test fun matchesWebFixturesAndKeepsExpressionStructure() {
        javaClass.getResourceAsStream("/latex-output.tsv")!!.bufferedReader().useLines {lines->lines.forEach {line->
            val (source,expected)=line.split('\t')
            assertEquals(source,expected,LatexOutput.convert(source))
        }}
        assertEquals("x = \\frac{1}{2}\n\ny = \\sqrt{2}",LatexOutput.convert("x=1/2\n\ny=sqrt(2)"))
        assertEquals("x+",LatexOutput.convert("x+"))
        val power=Expr("power",args=listOf(Expr("power",args=listOf(Expr("symbol","x"),Expr("number","2"))),Expr("number","3")))
        assertEquals("\\left(x^{2}\\right)^{3}",LatexOutput.render(power))
        for(source in listOf("f(x)+Ans","x_1+theta","{1,2}","[[1,2],[3,4]]","sqrt(x)","integrate(x^2,x,0,1)")) {
            val copied=LatexOutput.convert(source)
            assertNotNull(copied,LatexInput.convert(copied))
        }
    }
}
