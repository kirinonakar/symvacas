package com.kirinonakar.symvacas.math

import org.junit.Assert.*
import org.junit.Test

class ParserTest {
    private fun p(s: String) = Parser(s).parse()
    @Test fun adjacentCoordinatesAreProductsAndOtherIdentifiersStayWhole() {
        fun shape(tree:Expr):String = "${tree.kind}:${tree.value}[${tree.args.joinToString(",") {shape(it)}}]"
        for(source in listOf("xy","xz","yz","xyz","yx","zx","zy","zyx","xx","yy","zz","xxyzz")) {
            assertEquals(shape(p(source.toList().joinToString("*"))),shape(p(source)))
            for((offset,factor) in p(source).nodes().filter {it.kind=="symbol"}.withIndex()) {
                assertEquals(source[offset].toString(),factor.value)
                assertEquals(offset,factor.start)
                assertEquals(offset+1,factor.end)
            }
        }
        for((source,explicit) in listOf("2xyz^2" to "2*x*y*z^2","xy(x+1)" to "x*y*(x+1)",
            "1/xy" to "1/x*y","(xyz)^2" to "(x*y*z)^2","diff(xyz,x)" to "diff(x*y*z,x)",
            "solve(xy=6,x)" to "solve(x*y=6,x)","z=xy" to "z=x*y",
            "ax" to "a*x","bx" to "b*x","cx" to "c*x","ay" to "a*y","az" to "a*z",
            "axy" to "a*x*y","xTE+TRy" to "x*TE+TR*y","xyfoo" to "x*y*foo","abxyzcd" to "ab*x*y*z*cd",
            "xπ" to "x*pi","yθ" to "y*theta"))
            assertEquals(source,shape(p(explicit)),shape(p(source)))
        for(name in listOf("TE","TR","ab","abc","xy1","x_value","xy_z","XYZ","theta","xi","zeta","exp",
            "byte","day","henry","Hz","kHz","MHz","oz","yd","complex","polynomial","exponential","binary","tukey"))
            assertEquals(name,Expr("symbol",name,start=0,end=name.length),p(name))
        assertEquals("exp",p("exp(xy)").value)
        assertEquals("TR",p("TR(xy)").value)
        assertEquals("myfunc",p("myfunc(xy)").value)
    }
    @Test fun solvesetDomainConstantsPreserveArgumentAndSourceBoundaries() {
        for(name in listOf("Reals","Complexes","Integers","Rationals","Naturals","Naturals0")) {
            val source="solveset(sin(x) + 3*cos(x), x, domain=S.$name)"
            val tree=p(source)
            assertEquals("solveset",tree.value)
            val keyword=tree.args[2]
            assertEquals("=",keyword.value)
            assertEquals("domain",keyword.args[0].value)
            val domain=keyword.args[1]
            assertEquals("S.$name",domain.value)
            assertEquals(domain.value,source.substring(domain.start,domain.end))
            assertTrue(requiresExplicitEvaluation(tree))
        }
        for(source in listOf("S.Unknown","S.Realsx","S.Reals.__class__","x.y"))
            assertThrows(SyntaxException::class.java){p(source)}
        val source="solveset(x,x,domain=S.Reals)"
        val cursor=source.indexOf(",x")
        assertEquals("solveset(x=0,x,domain=S.Reals)",Editor(source,cursor).insert("=0").source)
    }
    @Test fun precedence() { assertEquals("*",p("2+3*4").args[1].value); assertEquals("unary",p("-2^2").kind); assertEquals("^",p("2^3^2").args[1].value) }
    @Test fun spatialCurveRestrictionsKeepCommaConditionsAndParameterLists() {
        val source="[(1-2*t)*cos(k*pi/2+a),(1-2*t)*sin(k*pi/2+a),k*pi/8]"
        val tree=p("$source {0<t<1, k=[0,0.1,0.2,0.3,0.4,0.5]}")
        assertEquals("restriction",tree.value)
        val (body,guard)=tree.args.single().args
        assertEquals(3,body.args.size)
        assertEquals("list",guard.kind)
        assertEquals(listOf("<","="),guard.args.map {it.value})
        assertEquals(6,guard.args[1].args[1].args.size)
        assertEquals("restriction",p("$source {0<t<1} {k=[0,0.5]}").args.single().args[0].value)
        for(suffix in listOf("{0<t<1,}","{,k=[0,1]}","{0<t<1,,k=[0,1]}"))
            assertThrows(SyntaxException::class.java){p(source+suffix)}
    }
    @Test fun desmosPiecewiseAndRestrictionsPreserveWholeExpressionScope() {
        val piece=p("f(x)={x<0:x^2,x>=0:2*x}").args[1]
        assertEquals("piecewise",piece.kind)
        assertEquals(listOf("^","*"),piece.args.map {it.args[0].value})
        assertEquals(listOf("<",">="),piece.args.map {it.args[1].value})
        for(source in listOf("y=(1-e^(-x/900)){0<=x<=3000}","y=1-e^(-x/900) {0<=x<=3000}")) {
            val rhs=p(source).args[1];assertEquals("restriction",rhs.value)
            assertEquals("<=",rhs.args[0].args[1].value)
            assertEquals("<=",rhs.args[0].args[1].args[0].value)
            assertEquals("3000",rhs.args[0].args[1].args[1].value)
        }
        assertEquals("*",p("y=(1-e^(-3000/900))*e^(-(x-3000)/80){x>3000}").args[1].args[0].args[0].value)
        assertEquals("-",p("y=1-e^(-x/900) {0<=x<=3000}").args[1].args[0].args[0].value)
        assertEquals("true",p("{x<0:x^2,2*x}").args.last().args[1].value)
        assertEquals("set",p("{1,2}").kind)
        for(source in listOf("{x<0:}","{x<0:1,2,x>0:3}","x{}"))assertThrows(SyntaxException::class.java){p(source)}
    }

    @Test fun structuredParserPreservesOperatorSlotsSetsAndMatrixTemplates() {
        run { // operatorSlotBetweenOperandsParses
            assertEquals("*",Parser("2()3",true).parse().value); assertEquals("*",Parser("[[1,0],[0,1]]()[[4,5],[6,7]]",true).parse().value)
        }
        run { // directSecondPageStructures
            assertEquals(listOf("x","y"),p("{x,y}").args.map{it.value})
            assertEquals("set",p("{x,y}").kind)
            assertEquals("list",Parser("[[,],[,]]",true).parse().kind)
            assertEquals(4,Parser("[[,],[,]]",true).parse().nodes().count {it.kind=="hole"})
            assertEquals("[[1,],[,]]",Editor().insert("[[,],[,]]",2).insert("1").source)
            assertEquals(9,Parser("[[,,],[,,],[,,]]",true).parse().nodes().count {it.kind=="hole"})
            assertEquals("[[1,,],[,,],[,,]]",Editor().insert("[[,,],[,,],[,,]]",2).insert("1").source)
        }
    }

    @Test fun invalid() {
        run { // invalid
            for(s in listOf("", "1..2", "2+", "a.__class__", "f(1,)", "[1,2", "(x,,0)")) assertThrows(SyntaxException::class.java) { p(s) }
        }
        run { // complexity
            assertThrows(SyntaxException::class.java) { p("(".repeat(200)+"1"+")".repeat(200)) }
        }
    }

}

class EvaluationPolicyTest {
    @Test fun evaluationPolicySeparatesExplicitCallsFromEntryPreviews() {
        run { // multiArgumentCallsWaitForEquals
            assertTrue(requiresExplicitEvaluation(Parser("rnd()",true).parse()))
            assertTrue(requiresExplicitEvaluation(Parser("integrate(e)").parse()))
            assertTrue(requiresExplicitEvaluation(Parser("roundh(1.225,2)").parse()))
            assertTrue(requiresExplicitEvaluation(Parser("integrate(,x)",true).parse()))
            assertTrue(requiresExplicitEvaluation(Parser("integrate(exp(-x^2)*cos(2x),(x,0,oo))").parse()))
            assertTrue(requiresExplicitEvaluation(Parser("1+dot([1,2],[3,4])").parse()))
            assertTrue(requiresExplicitEvaluation(Parser("f(1)").parse(),setOf("f")))
        }
        run { // entryHelpersPreviewWhileTyping
            assertFalse(requiresExplicitEvaluation(Parser("log(100)").parse()))
            assertFalse(requiresExplicitEvaluation(Parser("log(100,10)").parse()))
            assertFalse(requiresExplicitEvaluation(Parser("nthroot(8,3)").parse()))
            assertFalse(requiresExplicitEvaluation(Parser("mixed(1,1,2)").parse()))
            assertFalse(requiresExplicitEvaluation(Parser("mod(17,5)").parse()))
            assertFalse(requiresExplicitEvaluation(Parser("divmod(17,5)").parse()))
        }
    }

}

class BracketAutoCloseTest {
}
