package com.kirinonakar.symvacas.ui

internal data class ModelComparisonPlan(val expression:String,val labels:Map<String,String>)
internal fun modelComparisonRoles(opts:Map<String,String>)=when(opts["family"]){"cox"->listOf("time","event");"lmm","glmm","gee"->listOf("subject","response");else->listOf("response")}
internal fun modelComparisonPlan(rows:List<List<String>>,opts:Map<String,String>,names:List<String> = emptyList(),validationRows:List<List<String>> = emptyList(),validationNames:List<String> = emptyList()):ModelComparisonPlan {
    val width=rows.maxOfOrNull {it.size} ?: 0;val family=opts.getValue("family");val labels=names.ifEmpty {statisticsColumnNames(statisticsKindForColumns(width))}
    fun get(key:String)=opts.getValue(key)
    fun column(key:String):Int {val raw=get(key).toIntOrNull();val at=if(raw==-1)width-1 else raw;require(at!=null&&at in 0 until width){"Choose valid data columns"};return at}
    fun choose(text:String,excluded:List<Int> = emptyList()):List<Int> {
        val values=if(text=="auto")(0 until width).filter {it !in excluded} else text.split(',').filter(String::isNotBlank).map {it.trim().toIntOrNull() ?: -1}
        require(values.distinct().size==values.size&&values.all {it in 0 until width&&it !in excluded}){"Choose distinct baseline and added predictors"};return values
    }
    fun list(values:List<String>)=values.joinToString(",","[","]")
    fun table(values:List<List<String>>)=list(values.map(::list))
    fun pairs(text:String):String {
        if(text.isBlank())return "[]"
        val values=text.split(';').map {it.split(',').map(String::trim)}
        require(values.all {pair->pair.size==2&&pair.all {it.matches(Regex("[0-9]+"))&&(it.toIntOrNull() ?: 0)>0}}){"Use positive model parameter pairs separated by semicolons"}
        return table(values)
    }
    val numeric=Regex("^[+-]?(?:[0-9]+(?:\\.[0-9]*)?|\\.[0-9]+)(?:[eE][+-]?[0-9]+)?$")
    fun complete(data:List<List<String>>,indices:List<Int>)=data.map {row->indices.map {row.getOrElse(it){""}.trim().statisticsNumericCell()}}.filter {row->row.none {it.isBlank()||it.matches(Regex("(?i)(NA|NaN|[+-]?Infinity)"))}}
    var base=emptyList<Int>();var added=emptyList<Int>();val indices:List<Int>;val options=mutableListOf<List<String>>();val labelMap=mutableMapOf<String,String>()
    var mode=get("validation");var argument=when(mode){"holdout"->get("holdout");"crossvalidation"->get("folds");else->"0"};var samples=get("resamples")
    if(family in listOf("cfa","sem")) {
        indices=choose(get("indicators"));require(indices.isNotEmpty()){"Select common observed indicators"}
        val factors=get("factors").trim().removeSurrounding("[","]").split(',').map(String::trim)
        require(factors.size==indices.size&&factors.all {it.matches(Regex("[0-9]+"))&&(it.toIntOrNull() ?: 0)>0}){"Factor ID count must match selected indicators"}
        options+=listOf(listOf("factors",list(factors)),listOf("estimator",get("estimator")))
        listOf("basepaths","addedpaths","basecross","addedcross","baseresidual","addedresidual").forEach {options+=listOf(it,pairs(get(it)))}
        mode="fit";samples="0";argument="0";labelMap["model:A"]=indices.joinToString(", "){labels[it]};labelMap["model:B"]=labelMap.getValue("model:A")
    } else {
        val reserved=modelComparisonRoles(opts).map(::column);require(reserved.distinct().size==reserved.size){"Roles must use different columns"}
        base=choose(get("basePredictors"),reserved);added=choose(get("addedPredictors"),reserved+base);require(added.isNotEmpty()){"Choose at least one added predictor"}
        val leading=when(family){"cox"->reserved;"lmm","glmm","gee"->listOf(column("subject"));else->emptyList()}
        indices=leading+base+added+if(family=="cox")emptyList() else listOf(column("response"))
        labelMap["model:A"]=base.joinToString(" + "){labels[it]}.ifBlank {"Intercept only"};labelMap["model:B"]=(base+added).joinToString(" + "){labels[it]};labelMap["response"]=labels[column(if(family=="cox")"event" else "response")]
        added.forEachIndexed {i,at->labelMap["candidate:${i+1}"]=labels[at]}
        (base+added).forEachIndexed {i,at->labelMap["x${i+1}"]=labels[at]}
        if(family in listOf("lmm","glmm","gee")){mode="fit";samples="0";argument="0"}
        if(family in listOf("logistic","mlclassification"))options+=listOf("threshold",get("threshold"))
        if(family=="cox")options+=listOf("ties",get("ties"))
        if(family in listOf("lmm","glmm")) {
            fun slope(value:String):String {require(value.matches(Regex("[0-9]+"))){"Random slope position must be a nonnegative integer"};return value}
            options+=listOf(listOf("randoma",slope(get("randomA"))),listOf("randomb",slope(if(get("randomB")=="same")get("randomA") else get("randomB"))))
        }
        if(family in listOf("glmm","gee"))options+=listOf("responsefamily",get("responsefamily"))
        if(family=="glmm")options+=listOf("points",get("points"))
        if(family=="gee")options+=listOf("correlation",get("correlation"))
        if(family in listOf("mlclassification","mlregression"))listOf("algorithm","alpha","ratio","trees","depth").forEach {options+=listOf(it,get(it))}.also {options+=listOf("forestseed",get("seed"))}
    }
    var selected=complete(rows,indices)
    if(family in listOf("lmm","glmm","gee")) {val ids=selected.map {it[0]}.distinct();selected=selected.map {listOf((ids.indexOf(it[0])+1).toString())+it.drop(1)}}
    require(selected.none {row->row.any { !numeric.matches(it)}}){"Enter finite numeric data"};require(selected.isNotEmpty()){"Complete selected rows required"}
    options+=listOf("excludedrows",(rows.size-selected.size).toString())
    if(mode=="external") {
        require(validationRows.isNotEmpty()){"Choose a validation dataset"}
        fun plain(value:String)=value.replace(Regex(" \\((?:x|y|z|x[0-9]+)\\)$"),"")
        val source=labels.map(::plain);val other=validationNames.ifEmpty {statisticsColumnNames(statisticsKindForColumns(validationRows.first().size))}.map(::plain)
        val at=indices.map {i->other.indices.filter {other[it]==source[i]}.also {require(it.size==1&&source.count {name->name==source[i]}==1){"Validation dataset must have matching unique column headers"}}.first()}
        val values=complete(validationRows,at);require(values.isNotEmpty()){"Complete validation rows required"};argument=table(values);options+=listOf("excludedvalidation",(validationRows.size-values.size).toString())
    }
    val safe=Regex("^[\\p{L}][\\p{L}\\p{N}_]*$|^[+-]?(?:[0-9]+(?:\\.[0-9]*)?|\\.[0-9]+)(?:[eE][+-]?[0-9]+)?$|^\\[[0-9,\\[\\]\\s]*\\]$")
    require((listOf(family,mode,if(argument.startsWith('['))"0" else argument,get("level"),samples,get("seed"))+options.flatten()).all(safe::matches)){"Invalid model comparison option"}
    val candidates=if(family in listOf("cfa","sem"))"0" else get("candidates");require(candidates in listOf("0","1")){"Invalid candidate comparison mode"}
    return ModelComparisonPlan("modelcompare(${table(selected)},${base.size},$family,$mode,$argument,${get("level")},$samples,${get("seed")},${table(options)},$candidates)",labelMap)
}
