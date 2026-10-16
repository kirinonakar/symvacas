package com.kirinonakar.symvacas.calculator

import com.kirinonakar.symvacas.math.SyntaxException
import com.kirinonakar.symvacas.ui.graphEquationTree
import org.junit.Assert.*
import org.junit.Test

class GraphInputTest {
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
