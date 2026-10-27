package com.kirinonakar.symvacas.ui

import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class StatisticsHistogramDataTest {
    @Test fun emptyMismatchedAndNonNumericBinsAreRejectedBeforeDrawing() {
        for(data in listOf(
            """{"edges":[],"counts":[]}""",
            """{"edges":[0,1],"counts":[2,3]}""",
            """{"edges":[0,"bad"],"counts":[2]}""",
            """{"edges":[1,0],"counts":[2]}""",
            """{"edges":[0,1],"counts":[-1]}"""
        ))assertNull(readStatisticsHistogramData(JSONObject(data).put("kind","distribution")))
    }

    @Test fun credibleBoundsAndEstimateExtendHistogramRange() {
        val plot=JSONObject("""{"kind":"histogram","edges":[0,1,2],"counts":[3,4],"interval":[-1,3],"estimate":0.5,"level":0.95}""")
        val data=readStatisticsHistogramData(plot)!!
        assertEquals(-1.0,data.low,0.0);assertEquals(3.0,data.high,0.0)
        assertEquals(listOf(-1.0,3.0,0.5),data.markers)
        plot.put("interval",org.json.JSONArray())
        assertNull(readStatisticsHistogramData(plot))
    }

    @Test fun distributionWithoutCredibleBoundsIsValid() {
        val data=readStatisticsHistogramData(JSONObject("""{"kind":"distribution","edges":[0,1],"counts":[3]}"""))!!
        assertTrue(data.markers.isEmpty());assertEquals(0.0,data.low,0.0);assertEquals(1.0,data.high,0.0)
    }
}
