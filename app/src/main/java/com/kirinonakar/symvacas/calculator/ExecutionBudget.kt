package com.kirinonakar.symvacas.calculator

import org.json.JSONObject

internal fun executionTimeoutMillis(request:JSONObject):Long {
    val variables=request.optJSONObject("variables")
    fun number(node:JSONObject?,depth:Int=0):Double {
        if(node==null||depth>8)return 0.0
        return when(node.optString("kind")) {
            "number"->node.optString("value").toDoubleOrNull() ?: 0.0
            "symbol"->number(variables?.optJSONObject(node.optString("value")),depth+1)
            "unary"->(if(node.optString("value")=="-")-1 else 1)*number(node.optJSONArray("args")?.optJSONObject(0),depth+1)
            else->0.0
        }
    }
    fun work(node:JSONObject?):Long {
        if(node==null)return 0
        val args=node.optJSONArray("args");var seconds=0L
        if(node.optString("kind")=="call"&&node.optString("value")=="sem"&&(args?.length() ?: 0)>10) {
            val samples=number(args!!.optJSONObject(10))
            if(samples.isFinite()&&samples>=20&&samples==kotlin.math.floor(samples)) {
                val count=samples.coerceAtMost(10000.0).toLong();val p=args.optJSONObject(1)?.optJSONArray("args")?.length()?.takeIf {it>0} ?: 6
                seconds=count*maxOf(10L,p.toLong()*p)*(if(args.optJSONObject(7)?.optString("value")=="wlsmv")4 else 1)
            }
        }
        for(index in 0 until (args?.length() ?: 0))seconds+=work(args!!.optJSONObject(index))
        return seconds
    }
    return (60+work(request.optJSONObject("tree")))*1000
}
