package com.kirinonakar.symvacas.calculator

import com.kirinonakar.symvacas.math.statisticsRequest
import com.kirinonakar.symvacas.ui.statisticsDataSource
import org.json.JSONArray
import org.json.JSONObject

internal fun savedStatisticsDatasets(tree:JSONObject,dataSets:JSONObject,variables:JSONObject,functions:JSONObject,removeLimit:Boolean=false):JSONObject {
    val result=JSONObject();val visited=mutableSetOf<String>()
    fun visit(node:JSONObject,bound:Set<String> = emptySet()) {
        val name=node.optString("value");val kind=node.optString("kind")
        if(kind=="symbol"&&name !in bound&&visited.add("symbol:$name")) {
            val saved=dataSets.optJSONObject(name)
            if(saved!=null) {
                val input=statisticsRequest(statisticsDataSource(saved.optString("csv"),saved.optString("kind","list")),removeLimit)
                val packed=input.datasets[input.tree.value]
                result.put(name,if(packed!=null)JSONArray(packed) else JSONArray().apply {
                    input.tree.args.forEach {cell->put(if(cell.kind=="list")JSONArray().apply {cell.args.forEach {put(JSONObject(it.json()))}} else JSONObject(cell.json()))}
                })
            }else variables.optJSONObject(name)?.let {visit(it,bound)}
        }
        if(kind=="call"&&functions.has(name)&&visited.add("call:$name")) {
            val definition=functions.getJSONObject(name);val parameters=definition.optJSONArray("parameters")?:JSONArray()
            definition.optJSONObject("body")?.let {visit(it,(0 until parameters.length()).map {parameters.getString(it)}.toSet())}
        }
        val args=node.optJSONArray("args")?:return
        for(index in 0 until args.length())args.optJSONObject(index)?.let {visit(it,bound)}
    }
    visit(tree);return result
}
