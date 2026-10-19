package com.kirinonakar.symvacas.calculator

import com.kirinonakar.symvacas.math.SyntaxException
import com.kirinonakar.symvacas.ui.graphEquationTree
import org.junit.Assert.*
import org.junit.Test

class GraphInputTest {
    @Test fun surfaceCoordinatesAndLocalHelpersKeepDomainsAndFormulaCaptions() {
        for(source in listOf("[cos(u)*cos(v),sin(u)*cos(v),sin(v)]","[R=2+.35*sin(6*u-3*t),x=(R+cos(v))*cos(u),y=(R+cos(v))*sin(u),z=sin(v)]","S(u,v)=(u,v,sin(u+v))")) {
            assertEquals(setOf("u","v"),graphRangeAxes(source,"surface"))
            assertFalse(isImplicitSurface(source))
            val caption=graphEquationTree("surface",source,0)!!
            assertTrue(caption.getString("kind") in listOf("relation","list"))
        }
        val helpers="[r1=sqrt((x-2)^2+y^2),r2=sqrt((x+2)^2+y^2),z=sin(4*r1-5*t)/(1+.2*r1)+sin(4*r2-5*t)/(1+.2*r2)]"
        assertTrue(graphRangeAxes(helpers,"surface").isEmpty())
        assertFalse(isImplicitSurface(helpers))
        assertEquals("list",graphEquationTree("surface",helpers,0)!!.getString("kind"))
        assertTrue(isImplicitSurface("x^2+y^2+z^2=9"))
    }
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
