package com.kirinonakar.symvacas.ui

import org.json.JSONArray
import org.json.JSONException
import org.json.JSONObject

internal data class StatisticsReportHistogram(val edges:List<Double>,val counts:List<Double>,val markers:List<Double>) {
    val low=(edges+markers).minOrNull() ?: 0.0
    val high=(edges+markers).maxOrNull() ?: 1.0
}

/** Validate engine arrays before composition and the deferred Canvas draw callback. */
internal fun readStatisticsHistogramData(plot:JSONObject):StatisticsReportHistogram? = try {
    fun numbers(array:JSONArray)=List(array.length()){array.getDouble(it)}.also {values->require(values.all(Double::isFinite))}
    val edges=numbers(plot.getJSONArray("edges"));val counts=numbers(plot.getJSONArray("counts"))
    require(counts.isNotEmpty()&&edges.size==counts.size+1&&counts.all {it>=0})
    require(edges.zipWithNext().all {(a,b)->a<b})
    val markers=if(plot.optString("kind")=="histogram") {
        val interval=numbers(plot.getJSONArray("interval"));val estimate=plot.getDouble("estimate");val level=plot.getDouble("level")
        require(interval.size==2&&interval[0]<=interval[1]&&estimate.isFinite()&&level>0&&level<1)
        interval+estimate
    } else emptyList()
    StatisticsReportHistogram(edges,counts,markers)
} catch(_:JSONException) {null} catch(_:IllegalArgumentException) {null}
