package com.kirinonakar.symvacas.ui

import org.json.JSONArray

private val explicitStatisticsHeaders=linkedSetOf<String>()
private fun statisticsHeaderKey(rows:List<List<String>>):String {
    var a=2166136261L.toInt();var b=3335557771L.toInt();var count=0
    fun feed(value:Int){a=(a xor value)*16777619;b=(b xor value)*2246822519L.toInt()}
    rows.forEach {raw->
        val row=raw.map(String::trim).dropLastWhile(String::isBlank)
        if(row.isNotEmpty()){count++;feed(row.size);row.forEach {cell->feed(cell.length);cell.forEach {feed(it.code)}}}
    }
    return "${a.toUInt()}:${b.toUInt()}:$count"
}
internal fun hasExplicitStatisticsHeader(rows:List<List<String>>):Boolean=synchronized(explicitStatisticsHeaders){explicitStatisticsHeaders.isNotEmpty()&&statisticsHeaderKey(rows) in explicitStatisticsHeaders}
internal fun registerStatisticsHeader(rows:List<List<String>>) {
    val first=rows.firstOrNull().orEmpty()
    if(first.any(String::isNotBlank)&&first.none {it.statisticsNumericCell().toDoubleOrNull()?.isFinite()==true})synchronized(explicitStatisticsHeaders){explicitStatisticsHeaders.add(statisticsHeaderKey(rows))}
}
internal fun statisticsHeaderKeys():String=synchronized(explicitStatisticsHeaders){JSONArray(explicitStatisticsHeaders.toList()).toString()}
internal fun restoreStatisticsHeaderKeys(saved:String) {
    explicitStatisticsHeaders.clear()
    runCatching {JSONArray(saved)}.getOrNull()?.let {array->(0 until array.length()).forEach {index->array.optString(index).takeIf {it.matches(Regex("[0-9]+:[0-9]+:[0-9]+"))}?.let(explicitStatisticsHeaders::add)}}
}
