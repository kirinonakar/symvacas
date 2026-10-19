package com.kirinonakar.symvacas.calculator

import com.kirinonakar.symvacas.math.SyntaxException
import com.kirinonakar.symvacas.ui.graphEquationTree
import org.junit.Assert.*
import org.junit.Test

class GraphInputTest {
    @Test fun calculatorTransferKeepsTheSelectedGraphCategory() {
        for((kind,source) in listOf("cartesian" to "z=x+y","parametric" to "(cos(t),sin(t))","polar" to "r=2cos(3theta)","space" to "(t,t^2,t^3)","sequence" to "n^2","differential" to "t-y")) {
            assertEquals(kind to source,graphExpressionTarget(source,kind))
        }
        assertEquals("cartesian" to "(t,t^2,t^3)",graphExpressionTarget("(t,t^2,t^3)","cartesian"))
        assertEquals("surface" to "x^2+y^2",graphExpressionTarget("z=x^2+y^2","surface"))
        assertEquals("surface" to "x^2+y^2+z^2=1",graphExpressionTarget("x^2+y^2+z^2=1","surface"))
    }
    @Test fun radialSquareRootSurfaceParsesAdjacentAxisFactors() {
        val tree=graphInputTree("sin(sqrt(ax^2+ay^2))","surface")
        assertEquals("sin",tree.value);assertEquals("sqrt",tree.args.single().value)
        assertEquals(setOf("a","x","y"),tree.nodes().filter {it.kind=="symbol"}.map {it.value}.toSet())
        assertFalse(isImplicitSurface("sin(sqrt(ax^2+ay^2))"))
    }
    @Test fun commaSeparatedInequalitiesRemainOneVisibleGraphRow() {
        val source="-1<x<1, -1<y<x"
        val program=GraphSourceCache().get("$source\ny=x", "cartesian", false)
        assertEquals(2,program.trees.length())
        assertEquals(0,program.shadings.length())
        assertEquals("inequality",graphPlanarKind(graphInputTree(source)))
        assertTrue(graphRangeAxes(source,"cartesian").isEmpty())
        val caption=graphEquationTree("cartesian",source,0)!!
        assertEquals("list",caption.getString("kind"))
        assertEquals(2,caption.getJSONArray("args").length())
        assertEquals("inequality",graphPlanarKind(graphInputTree("x^2+y^2<4, y>=0")))
    }

    @Test fun nestedCommasKeepTheirExistingMeaning() {
        assertEquals("parametric",graphPlanarKind(graphInputTree("(cos(t),sin(t))")))
        assertEquals("cartesian",graphPlanarKind(graphInputTree("y=max(x,0)")))
        assertEquals("cartesian",graphPlanarKind(graphInputTree("f(x)={x<0:x^2,3}")))
        assertEquals("inequality",graphPlanarKind(graphInputTree("y>max(x,0), x<1")))
    }

    @Test fun bareCommasDoNotAcceptEmptyConditionsOrOrdinaryExpressions() {
        for(source in listOf("x<1,",",x<1","x<1,,y>0","x<1,y","x,y")) {
            assertThrows(SyntaxException::class.java) {graphInputTree(source)}
        }
        assertThrows(SyntaxException::class.java) {graphInputTree("x<1,y>0","parametric")}
    }
}
