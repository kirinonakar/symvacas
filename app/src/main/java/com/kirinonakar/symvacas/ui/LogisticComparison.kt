package com.kirinonakar.symvacas.ui

internal data class LogisticComparisonSelection(val base:List<Int>,val added:List<Int>,val response:Int,val count:Int) {val indices get()=base+added+response}
internal fun logisticComparisonSelections(rows:List<List<String>>,opts:Map<String,String>):LogisticComparisonSelection {
    val n=rows.maxOfOrNull {it.size} ?: 0;val response=opts["response"]?.toIntOrNull()?.let {if(it==-1)n-1 else it} ?: -1
    require(response in 0 until n) {"Choose valid data columns"}
    fun choose(text:String?,excluded:List<Int>)=if(text=="auto")(0 until n).filter {it !in excluded} else text.orEmpty().split(',').filter(String::isNotBlank).map {it.toIntOrNull() ?: -1}
    val base=choose(opts["basePredictors"],listOf(response));val added=choose(opts["addedPredictors"],listOf(response)+base)
    require(added.isNotEmpty()&&(base+added).all {it in 0 until n&&it!=response}&&(base+added).distinct().size==base.size+added.size) {"Choose distinct baseline and added predictors"}
    return LogisticComparisonSelection(base,added,response,n)
}
internal fun logisticComparisonLabels(rows:List<List<String>>,opts:Map<String,String>,names:List<String>):Map<String,String> {
    val plan=logisticComparisonSelections(rows,opts);val labels=names.ifEmpty {statisticsColumnNames(statisticsKindForColumns(plan.count))}
    return mapOf("model:A" to plan.base.map {labels[it]}.joinToString(" + ").ifBlank {"Intercept only"},"model:B" to (plan.base+plan.added).map {labels[it]}.joinToString(" + "),"response" to labels[plan.response])
}
internal fun logisticComparisonPlan(rows:List<List<String>>,opts:Map<String,String>,names:List<String> = emptyList(),validationRows:List<List<String>> = emptyList(),validationNames:List<String> = emptyList()):String {
    val plan=logisticComparisonSelections(rows,opts)
    fun complete(data:List<List<String>>,indices:List<Int>)=data.map {row->indices.map {row.getOrElse(it){""}.trim().statisticsNumericCell()}}.filter {row->row.none {it.isBlank()||it.matches(Regex("(?i)(NA|NaN|[+-]?Infinity)"))}}
    val train=complete(rows,plan.indices);require(train.isNotEmpty()) {"Complete selected rows required"}
    fun table(data:List<List<String>>)=data.joinToString(",","[","]"){it.joinToString(",","[","]")}
    val mode=opts["validation"];var validationCount=0
    val argument=when(mode) {
        "external"->{
            require(validationRows.isNotEmpty()) {"Choose a validation dataset"}
            fun plain(label:String)=label.replace(Regex(" \\((?:x|y|z|x[0-9]+)\\)$"),"")
            val source=names.ifEmpty {statisticsColumnNames(statisticsKindForColumns(plan.count))}.map(::plain)
            val other=validationNames.ifEmpty {statisticsColumnNames(statisticsKindForColumns(validationRows.first().size))}.map(::plain)
            val indices=plan.indices.map {at->other.indices.filter {other[it]==source[at]}.also {require(it.size==1&&source.count {name->name==source[at]}==1) {"Validation dataset must have matching unique column headers"}}.first()}
            val selected=complete(validationRows,indices);require(selected.isNotEmpty()) {"Complete validation rows required"};validationCount=validationRows.size;table(selected)
        }
        "holdout"->{require(opts["holdout"]?.toDoubleOrNull()?.let {it>0&&it<1}==true) {"Holdout fraction must be between 0 and 1"};opts.getValue("holdout")}
        "crossvalidation"->{require(opts["folds"]?.toIntOrNull()?.let {it>=2}==true) {"Folds must be at least two"};opts.getValue("folds")}
        else->error("Invalid validation method")
    }
    require(listOf("threshold","level").all {opts[it]?.toDoubleOrNull()?.let {v->v>0&&v<1}==true}) {"Threshold and confidence level must be between 0 and 1"}
    require(listOf("resamples","seed").all {opts[it]?.matches(Regex("[0-9]+"))==true}) {"Resamples and seed must be nonnegative integers"}
    return "logisticcompare(${table(train)},${plan.base.size},$mode,$argument,${opts["threshold"]},${opts["level"]},${opts["resamples"]},${opts["seed"]},[${rows.size},$validationCount])"
}
