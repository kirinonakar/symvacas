package com.kirinonakar.symvacas.math

import org.junit.Assert.*
import org.junit.Test

class LatexInputTest {

    @Test fun multilineCasesPreserveBranchesParametersAndPasteSelection() {
        val (source,expected)=javaClass.getResourceAsStream("/latex-input.tsv")!!.bufferedReader().readLines()
            .first {it.startsWith("""\operatorname{f}\left(x\right) = \begin{cases}""")}.split('\t')
        val multiline=source.replace("\\\\ ","\\\\\n")
        for(text in listOf(source,multiline,"\\[\n$multiline\n\\]")) {
            assertEquals(expected,LatexInput.convertPaste(text,multiline=true))
            val definition=Parser(LatexInput.convert(text)!!).parse()
            assertEquals("f",definition.args[0].value)
            val tree=definition.args[1]
            assertEquals("piecewise",tree.kind)
            assertEquals(2,tree.args.size)
            assertEquals(setOf("T1","T2","TR","TE","e","x"),tree.nodes().filter {it.kind=="symbol"}.map {it.value}.toSet())
            assertTrue(tree.args.all {it.args[1].kind=="relation" && it.args[1].args[0].kind=="relation"})
            val edit=LatexInput.convertEdit(Editor("x^2\nold\ny=0",7,4),"x^2\n$text\ny=0",multiline=true)!!
            assertEquals("x^2\n$expected\ny=0",edit.source)
            assertEquals(4+expected.length,edit.cursor)
        }
        for(text in listOf("""\begin{cases}x&\end{cases}""","""\begin{cases}x&x<0&1\end{cases}""","""\begin{cases}x&\text{unknown}\end{cases}""","""\begin{cases}x&x<0\end{matrix}"""))assertNull(text,LatexInput.convert(text))
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
}
