package com.kirinonakar.symvacas.calculator

import com.kirinonakar.symvacas.math.SyntaxException
import org.json.JSONArray
import org.json.JSONObject

// Owned by one calculator. Only the latest source is retained; slider values,
// viewport bounds and derivatives remain fresh in each request. Consumers must
// treat the cached JSON arrays as read-only.
internal class GraphSourceCache {
    internal data class Program(val trees:JSONArray,val shadings:JSONArray)
    private data class Key(val source:String,val kind:String,val unlimited:Boolean)
    private var key:Key?=null
    private var program:Program?=null

    fun get(source:String,kind:String,removeComputationLimit:Boolean):Program {
        val next=Key(source,kind,removeComputationLimit)
        if(next==key)return program!!
        val trees=JSONArray();val shadings=JSONArray()
        source.lineSequence().filter(String::isNotBlank).take(graphSourceLimit(kind)).forEach {raw->
            val line=raw.trim()
            if(isGraphShading(line)) {
                if(kind!="cartesian")throw SyntaxException("Shading is available on Cartesian graphs",0)
                if(shadings.length()<4)shadings.put(graphShadeEntry(graphShadingBody(line),removeComputationLimit))
            } else if(trees.length()<graphCurveLimit(kind)) {
                trees.put(JSONObject(graphInputTree(line,kind,removeComputationLimit).json()))
            }
        }
        val parsed=Program(trees,shadings)
        key=next;program=parsed
        return parsed
    }
}
