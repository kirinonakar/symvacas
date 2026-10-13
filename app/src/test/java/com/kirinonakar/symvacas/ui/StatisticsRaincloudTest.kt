package com.kirinonakar.symvacas.ui

import org.junit.Assert.*
import org.junit.Test

class StatisticsRaincloudTest {
    @Test fun tukeyWhiskersExcludeOutliersWithoutChangingQuartiles() {
        assertEquals(StatisticsRaincloudSummary(0.0,1.25,2.5,3.75,4.0),raincloudSummary(listOf(0.0,1.0,2.0,3.0,4.0,100.0,Double.NaN,Double.POSITIVE_INFINITY)))
    }
    @Test fun singletonConstantEmptyAndExtremeSamplesRemainDefined() {
        assertEquals(StatisticsRaincloudSummary(8.0,8.0,8.0,8.0,8.0),raincloudSummary(listOf(8.0)))
        assertEquals(StatisticsRaincloudSummary(3.0,3.0,3.0,3.0,3.0),raincloudSummary(List(40){3.0}))
        assertNull(raincloudSummary(listOf(Double.NaN,Double.POSITIVE_INFINITY)))
        assertEquals(StatisticsRaincloudSummary(-1e308,-5e307,0.0,5e307,1e308),raincloudSummary(listOf(-1e308,0.0,1e308)))
    }
}
