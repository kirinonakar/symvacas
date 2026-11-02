package com.kirinonakar.symvacas.ui

import java.math.BigInteger

internal data class StratifiedStatisticsData(val tables:List<List<String>>,val labels:Map<String,String>)

/** Same grouping and strict count/binary validation as statistics-stratified-data.js. */
internal fun stratifiedStatisticsData(rows:List<List<String>>,opts:Map<String,String>,columnLabels:List<String>):StratifiedStatisticsData {
    val layout=opts["layout"] ?: "tables";val width=rows.maxOfOrNull {it.size} ?: 0
    fun col(key:String):Int {val i=opts[key]?.toIntOrNull();require(i!=null&&i in 0 until width){"Choose valid data columns"};return i}
    val groupA=opts.getOrDefault("groupA","A").trim();val groupB=opts.getOrDefault("groupB","B").trim()
    require(groupA.isNotEmpty()&&groupB.isNotEmpty()&&groupA!=groupB){"Enter two different treatment/group values"}
    fun count(value:String):BigInteger {require(Regex("\\+?\\d+(?:\\.0+)?").matches(value)){"Enter nonnegative integer counts"};return value.replace(Regex("\\.0+$"),"").toBigInteger()}
    val labels=mutableMapOf("group:1" to groupA,"group:2" to groupB)
    var event="Event";var nonEvent="No event"
    val tables=if(layout=="tables") {
        val indices=listOf("a","b","c","d").map(::col)
        require(indices.distinct().size==4){"Roles must use different columns"}
        rows.map {row->indices.map {i->val value=row.getOrElse(i){""}.trim();require(value.isNotEmpty()){"Complete selected rows required"};count(value).toString()}}
    }else {
        require(layout in listOf("counts","observations")){"Invalid analysis option"}
        val raw=layout=="observations"
        val keys=if(raw)listOf("patientStratum","patientGroup","outcome") else listOf("stratum","group","events",if(opts["countType"]=="total")"total" else "nonEvents")
        val indices=keys.map(::col)
        require(indices.distinct().size==indices.size){"Roles must use different columns"}
        val eventValue=opts.getOrDefault("eventValue","1").trim();val nonEventValue=opts.getOrDefault("nonEventValue","0").trim()
        require(!raw||eventValue.isNotEmpty()&&nonEventValue.isNotEmpty()&&eventValue!=nonEventValue){"Enter two different outcome values"}
        fun name(key:String,fallback:String)=columnLabels.getOrElse(col(key)){fallback}.ifBlank {fallback}
        event=if(raw)"${name("outcome","Outcome")} = $eventValue" else name("events","Event")
        nonEvent=if(raw)"${name("outcome","Outcome")} = $nonEventValue" else if(opts["countType"]=="total")"No event" else name("nonEvents","No event")
        val strata=linkedMapOf<String,MutableList<BigInteger>>()
        for(row in rows) {
            val selected=indices.map {row.getOrElse(it){""}.trim()}
            require(selected.all(String::isNotEmpty)){"Complete selected rows required"}
            val stratum=selected[0];val group=selected[1]
            require(group==groupA||group==groupB){"Treatment/group column must contain only the two selected groups"}
            val totals=strata.getOrPut(stratum){MutableList(4){BigInteger.ZERO}};val offset=if(group==groupA)0 else 2
            if(raw) {
                require(selected[2] in listOf(eventValue,nonEventValue)){"Outcome column must contain only the two selected outcome values"}
                val at=offset+if(selected[2]==eventValue)0 else 1;totals[at]+=BigInteger.ONE
            }else {
                val events=count(selected[2]);val other=count(selected[3])
                require(opts["countType"]!="total"||other>=events){"Total count must be at least the event count"}
                totals[offset]+=events;totals[offset+1]+=if(opts["countType"]=="total")other-events else other
            }
        }
        strata.keys.forEachIndexed {i,name->labels["stratum:${i+1}"]=name}
        strata.values.map {row->row.map(BigInteger::toString)}
    }
    labels["count:1"]="$groupA · $event";labels["count:2"]="$groupA · $nonEvent"
    labels["count:3"]="$groupB · $event";labels["count:4"]="$groupB · $nonEvent"
    labels["outcome:event"]=event;labels["outcome:nonevent"]=nonEvent
    return StratifiedStatisticsData(tables,labels)
}
