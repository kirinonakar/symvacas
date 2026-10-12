package com.kirinonakar.symvacas.calculator

import org.json.JSONObject
import org.json.JSONArray
import com.kirinonakar.symvacas.ui.statisticsHeaderKeys

/** Portable Android/Web data file. Validate the whole file before changing storage. */
object DataTransfer {
    private val identifier=Regex("[A-Za-z][A-Za-z0-9_]*")
    private fun validName(name:String)=name.matches(identifier)&&name !in setOf("__proto__","constructor","prototype")
    fun validDatasetKind(kind:String)=kind in listOf("list","xy","xyz")||Regex("columns:[0-9]+").matches(kind)&&kind.substringAfter(":").toIntOrNull() in 1..100
    private fun validateAst(node:JSONObject) {
        require(node.opt("kind") is String && (!node.has("value")||node.opt("value") is String)) {"Invalid expression data"}
        if(node.has("args")) {
            val args=node.getJSONArray("args")
            for(i in 0 until args.length())validateAst(args.getJSONObject(i))
        }
    }
    fun encode(variables:JSONObject,functions:JSONObject,datasets:JSONObject,assumptions:JSONObject):String =
        JSONObject().put("format","symvacas.data").put("version",1).put("variables",variables)
            .put("functions",functions).put("datasets",datasets).put("assumptions",assumptions).apply {JSONArray(statisticsHeaderKeys()).takeIf {it.length()>0}?.let {put("statisticsHeaders",it)}}.toString(2)

    fun decode(text:String):JSONObject {
        val root=JSONObject(text.removePrefix("\uFEFF"))
        require(root.optString("format")=="symvacas.data" && root.opt("version")==1) {"Invalid SymvaCAS data file"}
        val variables=root.getJSONObject("variables")
        variables.keys().forEach {name->require(validName(name)) {"Invalid variable name"};validateAst(variables.getJSONObject(name))}
        val functions=root.getJSONObject("functions")
        functions.keys().forEach {name->
            val entry=functions.getJSONObject(name)
            val parameters=entry.getJSONArray("parameters").let {array->(0 until array.length()).map {array.getString(it)}}
            val definition=FunctionTransfer.definition(name,parameters,FunctionTransfer.storedSource(entry))
            if(entry.has("body"))validateAst(entry.getJSONObject("body"))else entry.put("body",definition.body)
            if(entry.has("answerSource"))validateAst(entry.getJSONObject("answerSource"))
        }
        val datasets=root.getJSONObject("datasets")
        datasets.keys().forEach {name->
            val entry=datasets.getJSONObject(name)
            require(validName(name)&&entry.opt("csv") is String&&validDatasetKind(entry.optString("kind"))) {"Invalid statistics data"}
        }
        val assumptions=root.getJSONObject("assumptions")
        assumptions.keys().forEach {name->
            require(validName(name)) {"Invalid symbol assumptions"}
            val values=assumptions.getJSONArray(name)
            for(i in 0 until values.length())require(values.getString(i) in listOf("real","positive","negative","integer","nonzero")) {"Invalid symbol assumptions"}
        }
        if(root.has("statisticsHeaders")) {
            val headers=root.getJSONArray("statisticsHeaders")
            for(i in 0 until headers.length())require(headers.opt(i) is String&&headers.getString(i).matches(Regex("[0-9]+:[0-9]+:[0-9]+"))) {"Invalid statistics header metadata"}
        }
        return root
    }
    fun merge(current:JSONObject,imported:JSONObject)=JSONObject(current.toString()).apply {
        imported.keys().forEach {name->put(name,imported.get(name))}
    }
    fun settingsResetData(prefs:Map<String,*>):Map<String,String> =
        listOf("variables","functions","dataSets","assumptions").associateWith {prefs[it] as? String ?: "{}"}.toMutableMap().apply {if(prefs.containsKey("statisticsHeaderKeys"))put("statisticsHeaderKeys",prefs["statisticsHeaderKeys"] as? String ?: "[]")}
}
