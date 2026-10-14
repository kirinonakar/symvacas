package com.kirinonakar.symvacas.math

import org.junit.Test
import org.junit.Assert.*

class GraphYScaleTest {
    @Test fun logarithmicCoordinatesTicksAndPanKeepActualValues() {
        val scale=GraphYScale(true)
        assertEquals(0.0,scale.fraction(1.0,1.0,100.0),1e-12)
        assertEquals(.5,scale.fraction(10.0,1.0,100.0),1e-12)
        assertEquals(1.0,scale.fraction(100.0,1.0,100.0),1e-12)
        assertEquals(10.0,scale.atFraction(.5,1.0,100.0),1e-10)
        assertEquals(listOf(1.0,10.0,100.0),scale.ticks(1.0,100.0))
        val zoom=scale.view(1.0,100.0,.5,.5,2.0)
        assertEquals(kotlin.math.sqrt(10.0),zoom.first,1e-12);assertEquals(10.0,scale.atFraction(.5,zoom.first,zoom.second),1e-10)
        val pan=scale.view(1.0,100.0,.5,.6,1.0)
        assertEquals(100.0,pan.second/pan.first,1e-10)
        assertTrue(scale.coordinate(0.0).isNaN());assertTrue(scale.coordinate(-1.0).isNaN())
    }
    @Test fun clippingFillingAndFittingExcludeNonpositiveData() {
        val scale=GraphYScale(true)
        val line=scale.segment(0.0 to .001,6.0 to 1000.0,0.0,6.0,.01,100.0)!!
        assertEquals(1.0,line.first.first,1e-10);assertEquals(5.0,line.second.first,1e-10)
        val polygon=scale.polygon(listOf(-1.0 to -1.0,2.0 to -1.0,2.0 to 10.0,-1.0 to 10.0),0.0,1.0,.1,100.0)
        assertEquals(4,polygon.size);assertTrue(polygon.all {it.first in 0.0..1.0&&it.second>0})
        val fit=scale.fit(listOf(-100.0,0.0,1.0,100.0))!!
        assertTrue(fit.first>0&&fit.first<1&&fit.second>100)
        assertNull(scale.fit(listOf(-1.0,0.0)))
    }
}
