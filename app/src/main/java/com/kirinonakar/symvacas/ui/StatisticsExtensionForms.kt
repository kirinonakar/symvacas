package com.kirinonakar.symvacas.ui

internal val extensionAnalysisIds=setOf("omega","bayesttest","bayesanova","metaregression","metasubgroup","designpower","designsize","yuen","trimmedanova","winsorcor","robustreg","parametricsurvival")

internal data class ExtensionStatisticsPlan(val expression:String,val labels:Map<String,String>)

/** Keep role selection, missing-row rules and group encoding equal to the Web plan. */
internal fun extensionStatisticsPlan(id:String,rows:List<List<String>>,opts:Map<String,String>,columnLabels:List<String>):ExtensionStatisticsPlan {
    val n=rows.maxOfOrNull {it.size} ?: 0;val labels=mutableMapOf<String,String>()
    fun col(key:String):Int {val raw=opts.getValue(key).toIntOrNull();val at=if(raw==-1)n-1 else raw;require(at!=null&&at in 0 until n){"Choose valid data columns"};return at}
    fun multi(key:String,excluded:List<Int> = emptyList()):List<Int> {
        val raw=opts.getValue(key);val indices=if(raw=="auto")(0 until n).filter {it !in excluded} else raw.split(',').filter(String::isNotBlank).map {it.toIntOrNull() ?: -1}
        require(indices.isNotEmpty()&&indices.distinct().size==indices.size&&indices.all {it in 0 until n&&it !in excluded}){"Choose distinct analysis columns"};return indices
    }
    fun complete(indices:List<Int>):List<List<String>> {
        require(indices.distinct().size==indices.size){"Roles must use different columns"}
        return rows.map {row->indices.map {row.getOrElse(it){""}.trim()}}.also {selected->require(selected.all {row->row.all(String::isNotBlank)}){"Complete selected rows required"}}
    }
    fun vector(values:List<String>)=values.joinToString(",","[","]")
    fun table(values:List<List<String>>)=values.joinToString(",","[","]",transform=::vector)
    fun featureLabels(indices:List<Int>) {indices.forEachIndexed {i,at->labels["feature:${i+1}"]=columnLabels.getOrElse(at){"Feature ${i+1}"}}}
    fun groupPlan(all:Boolean=false,paired:Boolean=false):StatisticsComparisonData {
        val plan=statisticsComparisonData(rows,opts,all=all,paired=paired,strict=true)
        plan.labels.forEachIndexed {i,at->labels["sample:${i+1}"]=if(opts["grouping"]=="groups")at else columnLabels.getOrElse(at.toInt()){"Sample ${i+1}"}}
        return plan
    }
    val expression=when(id) {
        "omega"->{val indices=multi("columns");featureLabels(indices);"omega(${table(complete(indices))},${opts["mode"]})"}
        "designpower","designsize"->{
            require(listOf("effect","size","alpha").all {opts[it].orEmpty().isNotBlank()}){"Enter all study design parameters"}
            "$id(${opts["design"]},${opts["effect"]},${opts["size"]},${opts["alpha"]},${opts["tail"]},${if(opts["design"] in listOf("proportion","proportion2"))opts["baseline"] else "0.5"})"
        }
        "bayesttest"->{
            val samples=if(opts["design"]=="onesample") {
                labels["sample:1"]=columnLabels.getOrElse(col("column")){"Sample 1"}
                listOf(rows.map {it.getOrElse(col("column")){""}.trim()}.filter(String::isNotBlank),emptyList())
            }else groupPlan(paired=opts["design"]=="paired").samples
            "bayesttest(${samples.joinToString(",",transform=::vector)},${opts["design"]},${opts["null"]},${opts["r"]},${opts["level"]},${opts["samples"]},${opts["seed"]},${opts["sequential"]})"
        }
        "bayesanova","trimmedanova"->{
            val groups=groupPlan(all=true).samples
            val suffix=if(id=="bayesanova")"${opts["r"]},${opts["level"]},${opts["samples"]},${opts["seed"]},${opts["sequential"]}" else "${opts["trim"]},${opts["level"]}"
            "$id(${table(groups)},$suffix)"
        }
        "yuen"->"yuen(${groupPlan().samples.joinToString(",",transform=::vector)},${opts["trim"]},${opts["level"]})"
        "winsorcor"->{val pairs=complete(listOf(col("first"),col("second")));"winsorcor(${vector(pairs.map {it[0]})},${vector(pairs.map {it[1]})},${opts["trim"]})"}
        "robustreg"->{val response=col("response");val predictors=multi("predictors",listOf(response));featureLabels(predictors);"robustreg(${table(complete(predictors+response))},${opts["tuning"]})"}
        "metaregression","metasubgroup"->{
            val reserved=when(opts["layout"]){"binary"->listOf("eventsA","totalA","eventsB","totalB").map(::col);"continuous"->listOf("meanA","sdA","nA","meanB","sdB","nB").map(::col);else->listOf(col("effect"),col("se"))}
            val data=if(id=="metaregression") {
                val predictors=multi("predictors",reserved);featureLabels(predictors);complete(reserved+predictors)
            }else {
                val selected=complete(reserved+col("group"));val groups=selected.map {it[reserved.size]}.distinct()
                groups.forEachIndexed {i,group->labels["group:${i+1}"]=group}
                selected.map {row->row.take(reserved.size)+(groups.indexOf(row[reserved.size])+1).toString()}
            }
            val effect=when(opts["layout"]){"binary"->",${opts["measure"]},${opts["correction"]}";"continuous"->",${opts["continuousMeasure"]}";else->""}
            "$id(${table(data)},${opts["method"]},${opts["level"]},${if(opts["method"]=="fixed")"z" else opts["inference"]}$effect)"
        }
        "parametricsurvival"->{
            val reserved=listOf(col("time"),col("event"))+if(opts["truncation"]=="entry")listOf(col("entry")) else emptyList()
            val predictors=if(opts["covariates"]=="selected")multi("predictors",reserved) else emptyList();featureLabels(predictors)
            val selected=complete(reserved+predictors);val states=selected.map {it[1]}.distinct();val eventValue=opts.getValue("eventValue")
            require(eventValue.isNotBlank()){"Enter the event value"}
            require(states.size<=2&&(states.size<=1||eventValue in states)){"Event column must have at most two values and contain the event value"}
            val encoded=selected.map {row->listOf(row[0],if(row[1]==eventValue)"1" else "0")+row.drop(2)}
            "parametricsurvival(${table(encoded)},${opts["family"]},${opts["level"]},${if(opts["truncation"]=="entry")2 else -1},${opts["horizon"]})"
        }
        else->error("Unknown analysis form")
    }
    return ExtensionStatisticsPlan(expression,labels)
}
