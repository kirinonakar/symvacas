package com.kirinonakar.symvacas

import com.kirinonakar.symvacas.calculator.graphRangeAxes
import com.kirinonakar.symvacas.calculator.loadGraphColors
import com.kirinonakar.symvacas.calculator.normalizeGraphColors
import com.kirinonakar.symvacas.ui.graphTracePointAtX
import com.kirinonakar.symvacas.calculator.graphAnalysisTarget
import com.kirinonakar.symvacas.calculator.GraphAnalysisTarget
import org.json.JSONArray
import org.junit.Assert.*
import org.junit.Assert.assertEquals
import org.junit.Test

class GraphFormulaTest {
    @Test fun parameterRangesAppearOnlyForCorrespondingCurveKinds() {
        assertEquals(emptySet<String>(),graphRangeAxes("y=x^2\nx^2+y^2=9","cartesian"))
        assertEquals(setOf("t"),graphRangeAxes("(cos(t),sin(t))","cartesian"))
        assertEquals(setOf("theta"),graphRangeAxes("r=2cos(3θ)","cartesian"))
        assertEquals(setOf("t","theta"),graphRangeAxes("(cos(t),sin(t))\nr=2cos(3θ)","cartesian"))
        assertEquals(emptySet<String>(),graphRangeAxes("","polar"))
        assertEquals(setOf("theta"),graphRangeAxes("2cos(3θ)","polar"))
        assertEquals(setOf("t"),graphRangeAxes("(cos(t),sin(t))","parametric"))
    }
    @Test fun analysisTargetsDistinguishDerivativesFromTheirSourceForIntersections() {
        val original=graphAnalysisTarget(0,0,0)
        val first=graphAnalysisTarget(-1,0,0)
        val second=graphAnalysisTarget(-2,0,0)
        assertEquals(GraphAnalysisTarget(0,0),original);assertEquals(GraphAnalysisTarget(0,1),first);assertEquals(GraphAnalysisTarget(0,2),second)
        assertNotEquals(original,first);assertNotEquals(first,second)
        assertEquals(GraphAnalysisTarget(2,1),graphAnalysisTarget(-1,2,1))
        assertNull(graphAnalysisTarget(-1,null,0));assertNull(graphAnalysisTarget(-2,0,null))
    }

}

class GraphTraceTest {
    @Test fun implicitCurvesChooseTheBranchNearTheTouchedY() {
        run { // implicitCurvesChooseTheBranchNearTheTouchedY
            val curve=listOf(-2.0 to 2.0,2.0 to 2.0,null,2.0 to -2.0,-2.0 to -2.0)
            assertEquals(0.5 to 2.0,graphTracePointAtX(curve,0.5,1.0))
            assertEquals(0.5 to -2.0,graphTracePointAtX(curve,0.5,-1.0))
            assertEquals(0.0 to 0.5,graphTracePointAtX(listOf(0.0 to -2.0,0.0 to 2.0),0.0,0.5))
        }
        run { // missingAndNonFiniteSamplesDoNotConnectUnrelatedCurveSegments
            for(gap in listOf(null,0.0 to Double.NaN,Double.POSITIVE_INFINITY to 0.0)) {
                assertNull(graphTracePointAtX(listOf(-1.0 to -1.0,gap,1.0 to 1.0),0.0,0.0))
            }
            assertNull(graphTracePointAtX(emptyList(),0.0,0.0))
            assertNull(graphTracePointAtX(listOf(0.0 to 0.0,1.0 to 1.0),2.0,0.0))
            assertNull(graphTracePointAtX(listOf(0.0 to 0.0),Double.NaN,0.0))
            assertEquals(1.0 to 1.0,graphTracePointAtX(listOf(1.0 to 1.0),1.0,0.0))
        }
    }

}

class GraphColorsTest {
    @Test fun sixIndependentOverridesAndIndividualResetsSurviveStorage() {
        val colors=listOf("#123456","#abcdef","#000000","#ffffff","#ff0000","#00ff00")
        assertEquals(colors,loadGraphColors(JSONArray(colors).toString()))
        val reset=normalizeGraphColors(colors.mapIndexed {i,color->if(i==3)null else color})
        assertEquals(colors.take(3)+listOf(null)+colors.drop(4),loadGraphColors(JSONArray(reset).toString()))
        assertEquals(colors,normalizeGraphColors(colors+"#112233"))
    }
}
