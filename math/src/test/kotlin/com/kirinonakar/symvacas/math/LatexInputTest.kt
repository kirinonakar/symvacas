package com.kirinonakar.symvacas.math

import org.junit.Assert.*
import org.junit.Test

class LatexInputTest {

    @Test fun escapedMathFencesAndConsecutiveBlocksPasteAsSeparateExpressions() {
        val implicit="""\\[ (x^2+y^2)^4= \left[ (x^3-3xy^2)\cos t+ (3x^2y-y^3)\sin t \right]^2 \\]"""
        val polar="""\\[ \boxed{r=|\cos(3\theta-t)|} \\]"""
        val first="(x^2+y^2)^4=((x^3-3x*y^2)cos(t)+(3x^2y-y^3)sin(t))^2"
        val second="r=abs(cos(3theta-t))"
        assertEquals(first,LatexInput.convert(implicit))
        assertEquals(second,LatexInput.convert(polar))
        for(separator in listOf("  ","\n\n","\r\n")) {
            val pasted=implicit+separator+polar
            assertEquals("$first\n$second",LatexInput.convertPaste(pasted,multiline=true))
            assertNull(LatexInput.convert(pasted))
            val previous=Editor("x^2\nold\ny=0",7,4)
            val edit=LatexInput.convertEdit(previous,"x^2\n$pasted\ny=0",multiline=true)!!
            assertEquals("x^2\n$first\n$second\ny=0",edit.source)
            assertEquals(edit.source.length-4,edit.cursor)
        }
        assertEquals("x*y",LatexInput.convert("\\\\[xy\\\\]"))
        assertEquals("x*y",LatexInput.convert("\\\\(xy\\\\)"))
        assertEquals("x=1\ny=2",LatexInput.convertPaste("\\[\nx=1\n\\] \\[\ny=2\n\\]",multiline=true))
        val matrix="""\\[ \begin{bmatrix}1&2\\3&4\end{bmatrix} \\]"""
        assertEquals("[[1,2],[3,4]]",LatexInput.convertPaste(matrix,multiline=true))
        assertNull(LatexInput.convertPaste("Answer: $polar",multiline=true))
        assertNull(LatexInput.convertPaste("$polar \\[\\unknown{1}\\]",multiline=true))
    }

    @Test fun multilinePastePreservesLinesAndSelectionScope() {
        val source="\\frac{x+1}{2}\n\n$\\sqrt{x}$\nx=\\frac{1}{3}"
        assertEquals("(x+1)/2\n\nsqrt(x)\nx=1/3",LatexInput.convertPaste(source,multiline=true))
        val previous=Editor("x^2\n2x+3\ny=0",6,5)
        val edit=LatexInput.convertEdit(previous,"x^2\n2$\\frac{1}{5}$+3\ny=0",multiline=true)!!
        assertEquals("x^2\n2(1/5)+3\ny=0",edit.source)
        assertEquals(10,edit.cursor)
        assertNull(LatexInput.convertEdit(Editor("\\frac{1}{2}"),"\\frac{1}{2}"))
        assertNull(LatexInput.convertPaste("x+1\n\ny=2",multiline=true))
        assertEquals("(x+1)/2",LatexInput.convertPaste("$$\n\\frac{x+1}{2}\n$$",multiline=true))
        assertEquals("[[1,2],[3,4]]",LatexInput.convertPaste("\\begin{bmatrix}1&2\\\\\n3&4\\end{bmatrix}",multiline=true))
        val boxed="\\[\n\\boxed{r=|\\cos(3\\theta-t)|}\n\\]"
        assertEquals("r=abs(cos(3theta-t))",LatexInput.convertPaste(boxed,multiline=true))
        val implicit="\\[\n(x^2+y^2)^4=\n\\left[\n(x^3-3xy^2)\\cos t+\n(3x^2y-y^3)\\sin t\n\\right]^2\n\\]"
        assertEquals("(x^2+y^2)^4=((x^3-3x*y^2)cos(t)+(3x^2y-y^3)sin(t))^2",LatexInput.convertPaste(implicit,multiline=true))
        val boxedEdit=LatexInput.convertEdit(Editor("2x+3",2,1),"2\\boxed{x+1}+3")!!
        assertEquals("2(x+1)+3",boxedEdit.source)
        assertEquals(6,boxedEdit.cursor)
        assertNull(LatexInput.convert("xy"))
    }

    @Test fun latexConversionMatchesSharedFixturesAndRejectsInvalidInput() {
        run { // extendedLatexMatchesSharedWebFixtures
            val cases=javaClass.getResourceAsStream("/latex-input.tsv")!!.bufferedReader().readLines()
            for(line in cases) {
                val (source,expected)=line.split('\t')
                for(wrapped in listOf(source,"$${source}$","$$${source}$$","\\[$source\\]","\\($source\\)")) {
                    assertEquals(wrapped,expected,LatexInput.convert(wrapped))
                    assertNotNull(Parser(expected).parse())
                }
            }
            for(name in LatexInput.symbolLabels.keys)assertEquals(name,LatexInput.convert("\\$name"))
            for(source in listOf("\\sum k","\\sum_{k}^{3} k","\\prod_{k=1} k","\\int_0 x dx","\\int_0^1 x","\\int x dxfoo","\\begin{pmatrix}1&2\\\\3\\end{pmatrix}","\\begin{matrix}1&\\end{matrix}","\\begin{matrix}1","\\begin{cases}x\\end{cases}","\\binom{5}"))assertNull(source,LatexInput.convert(source))
            val paste="\\sum_{k=1}^{5} k^2"
            val edit=LatexInput.convertEdit(Editor("1+x+3",3,2),"1+$${paste}$+3")!!
            assertEquals("1+sum(k^2,k,1,5)+3",edit.source)
            assertEquals(edit.source.length-2,edit.cursor)
        }
        run { // incompleteOrUnsupportedLatexDoesNotConvert
            for(source in listOf("\\boxed", "\\boxed{}", "\\boxed{x", "\\boxed{|x}", "\\sqrt[3{5}","\\sqrt[]{5}","\\sqrt[3]{}","\\sqrt[3]{5", "\\sqrt[3]", "\\frac{1}","$$\\unknown{1}$$","$$\\sqrt{5}$")) {
                assertNull(source,LatexInput.convert(source))
            }
            assertNull(LatexInput.convert("1/3+1/6"))
        }
    }
    @Test fun calculusPastePreservesBoundsVariableScopeAndWhitespace() {
        run { // limitPastePreservesApproachFunctionPowerAndScope
            val body="\\lim_{x \\to 0} \\frac{3x^2}{\\sin^2 x}"
            val expected="limit(3x^2/sin(x)^2,x,0)"
            for(source in listOf(body,"$$${body}$$","$${body}$","\\[$body\\]","\\($body\\)")) {
                assertEquals(expected,LatexInput.convert(source))
                val tree=Parser(LatexInput.convert(source)!!).parse()
                assertEquals("limit",tree.value)
                assertEquals(listOf("x","0"),tree.args.drop(1).map {it.value})
                assertEquals("sin",tree.args[0].args[1].args[0].value)
            }
            for((source,converted) in listOf(
                "\\lim _ {x \\rightarrow \\infty} \\frac{1}{x}" to "limit(1/x,x,oo)",
                "\\lim_{x \\to 0^+} 1/x" to "limit(1/x,x,0,right)",
                "\\lim_{x \\to 0^{-}} 1/x" to "limit(1/x,x,0,left)",
                "\\lim_{\\theta \\to \\pi} \\cos\\theta" to "limit(cos(theta),theta,pi)",
                "(\\lim_{x \\to 0} x)+2" to "limit(x,x,0)+2",
                "\\left(\\lim_{x \\to 0} x\\right)+2" to "limit(x,x,0)+2",
                "\\lim_{x \\to 0} x=0" to "limit(x,x,0)=0",
                "\\lim_{x \\to 0} (x+1)" to "limit(x+1,x,0)",
                "\\lim_{x \\to 0} \\frac{3x^2+1}{\\sin^2 x+2}" to "limit((3x^2+1)/(sin(x)^2+2),x,0)",
                "\\lim_{x \\to 0} \\frac{x}{2}^2" to "limit((x/2)^2,x,0)",
                "\\lim_{x \\to 0} x^{\\frac{1}{2}}" to "limit(x^(1/2),x,0)",
                "\\lim_{x \\to 0} \\frac{1}{x(x+1)}" to "limit(1/x(x+1),x,0)",
                "\\lim_{x \\to 0} \\frac{1}{2x}" to "limit(1/(2x),x,0)",
                "\\lim_{x \\to 0} (x)(x+1)" to "limit((x)(x+1),x,0)",
                "\\lim_{x \\to 0} (x^2)^3" to "limit((x^2)^3,x,0)",
                "\\frac{\\lim_{x \\to 0} x+1}{2}" to "limit(x+1,x,0)/2"
            ))assertEquals(source,converted,LatexInput.convert(source))
            for(source in listOf("\\lim","\\lim_x x","\\lim_{x 0} x","\\lim_{x+1 \\to 0} x","\\lim_{x \\to} x","\\lim_{x \\to 0}"))assertNull(source,LatexInput.convert(source))
            val edit=LatexInput.convertEdit(Editor("1+2+3",3,2),"1+$$${body}$$+3")!!
            assertEquals("1+$expected+3",edit.source)
            assertEquals(2+expected.length,edit.cursor)
        }
        run { // integralEquationsAllowWhitespaceAroundBoundsAndDifferentials
            for(body in listOf(
                "\\int _{-2}^{a} f(x) dx = \\int _{-2}^{0} f(x) dx",
                "\\int_{-2}^{a} f(x) dx = \\int_{-2}^{0} f(x) dx",
                "\\int _ {-2} ^ {a} f(x) \\, d x = \\int _ {-2} ^ {0} f(x) \\, d x"
            ))for(source in listOf(body,"$$${body}$$","$${body}$","\\[$body\\]","\\($body\\)")) {
                val converted=LatexInput.convert(source)
                assertEquals(source,"integrate(f(x),x,-2,a)=integrate(f(x),x,-2,0)",converted)
                val tree=Parser(converted!!).parse()
                assertEquals("relation",tree.kind)
                assertEquals(listOf("integrate","integrate"),tree.args.map {it.value})
                assertEquals(listOf("a","0"),tree.args.map {it.args[3].value})
            }
            for(source in listOf("\\int _{-2} f(x) dx","\\int _{-2}^{a} f(x)","\\int _{}^{a} f(x) dx")) {
                assertNull(source,LatexInput.convert(source))
            }
        }
    }

}
