package com.kirinonakar.symvacas.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.kirinonakar.symvacas.calculator.CalculatorModel
import com.kirinonakar.symvacas.ui.theme.LocalInstrument
import org.json.JSONObject

internal data class StatisticsGroupedColumn(val csv:String,val kind:String,val labels:List<String>,val ranges:List<String>,val counts:List<Int>,val omitted:Int)
private val groupingNumber=Regex("^[+-]?(?:[0-9]+(?:\\.[0-9]*)?|\\.[0-9]+)(?:[eE][+-]?[0-9]+)?$")
internal fun defaultStatisticsGroupValues(cuts:String):String=(0..cuts.trim().split(Regex("[,;\\s]+")).count(String::isNotBlank).coerceAtLeast(1)).joinToString(",")
internal fun statisticsGroupedColumn(source:String,kind:String,column:Int,cutPoints:String,header:String,groupValues:String=""):StatisticsGroupedColumn {
    val names=statisticsColumnNames(kind)
    require(column in names.indices) {"Choose valid data columns"}
    val cutText=cutPoints.trim().split(Regex("[,;\\s]+")).filter(String::isNotBlank)
    val cuts=cutText.map {text->text.takeIf {groupingNumber.matches(it)}?.toDoubleOrNull()?.takeIf(Double::isFinite)}
    require(cuts.isNotEmpty()&&cuts.all {it!=null}) {"Enter finite numeric cut points"}
    val boundaries=cuts.filterNotNull()
    require(boundaries.zipWithNext().all {(a,b)->a<b}) {"Cut points must be strictly increasing"}
    val name=header.trim()
    require(name.isNotBlank()) {"Enter a new column header"}
    val raw=statisticsCsvRows(source)
    val width=maxOf(names.size,raw.maxOfOrNull {it.size} ?: 0)
    require(width<100) {"Column count must be between 1 and 100"}
    val hasHeader=statisticsHasHeader(raw)
    val oldNames=if(hasHeader)List(width){raw.first().getOrElse(it){""}.ifBlank {statisticsColumnNames(statisticsKindForColumns(width))[it]}} else statisticsColumnNames(statisticsKindForColumns(width))
    require(oldNames.none {it.equals(name,ignoreCase=true)}) {"New column header already exists"}
    val ranges=listOf("< ${cutText.first()}")+cutText.zipWithNext().map {(a,b)->"$a ≤ x < $b"}+"≥ ${cutText.last()}"
    val labels=if(groupValues.isBlank())ranges.indices.map(Int::toString) else groupValues.split(Regex("[,;\\r\\n]")).map(String::trim)
    require(labels.size==ranges.size&&labels.all(String::isNotBlank)) {"Enter one group value per interval"}
    require(labels.distinct().size==labels.size) {"Group values must be distinct"}
    val counts=MutableList(labels.size){0};var omitted=0
    val rows=(if(hasHeader)raw.drop(1) else raw).map {row->
        val text=row.getOrNull(column)?.statisticsNumericCell().orEmpty()
        val value=text.takeIf {groupingNumber.matches(it)}?.toDoubleOrNull()?.takeIf(Double::isFinite)
        val label=if(value==null){omitted++;""} else {
            var lo=0;var hi=boundaries.size
            while(lo<hi){val mid=(lo+hi)/2;if(value<boundaries[mid])hi=mid else lo=mid+1}
            val index=lo
            counts[index]++;labels[index]
        }
        List(width){row.getOrElse(it){""}}+label
    }
    require(counts.sum()>0) {"No finite numeric values in selected column"}
    val updated=listOf(oldNames+name)+rows
    require(statisticsHasHeader(listOf(listOf(name),listOf("1")))) {"Use a text column header"}
    return StatisticsGroupedColumn(updated.joinToString("\n",transform=::statisticsCsvLine),statisticsKindForColumns(width+1),labels,ranges,counts,omitted)
}

@Composable internal fun StatisticsGroupColumn(m:CalculatorModel,data:String,kind:String,onAdd:(StatisticsGroupedColumn)->Unit) {
    val draft=remember {m.advancedStatisticsDraft.optJSONObject("groupColumn") ?: JSONObject()}
    var column by rememberSaveable {mutableStateOf(draft.optInt("column",0))}
    var cuts by rememberSaveable {mutableStateOf(draft.optString("cuts",""))}
    var header by rememberSaveable {mutableStateOf(draft.optString("header","group"))}
    var groups by rememberSaveable {mutableStateOf(draft.optString("groups",defaultStatisticsGroupValues(cuts)))}
    var added by remember {mutableStateOf<Pair<String,List<String>>?>(null)}
    var addedResult by remember {mutableStateOf<StatisticsGroupedColumn?>(null)}
    val names=statisticsColumnLabels(data,kind)
    val selected=column.coerceIn(names.indices)
    val expanded=m.statisticsSectionExpanded("group-column")
    LaunchedEffect(column,cuts,header,groups) {
        m.updateAdvancedStatisticsDraft(JSONObject(m.advancedStatisticsDraft.toString()).put("groupColumn",JSONObject().put("column",column).put("cuts",cuts).put("header",header).put("groups",groups)))
    }
    StatisticsSectionToggle("Add group column",expanded,"statistics-group-column-toggle",depth=2) {m.setStatisticsSectionExpanded("group-column",!expanded)}
    if(expanded)Column(Modifier.fillMaxWidth().padding(start=14.dp),verticalArrangement=Arrangement.spacedBy(4.dp)) {
        StatisticsSelectionTitle("Source column")
        Choices(names,names[selected],{column=names.indexOf(it)},translate=false)
        Field(cuts,"Numeric cut points",Modifier.fillMaxWidth().testTag("statistics-group-column-cuts")){if(groups==defaultStatisticsGroupValues(cuts))groups=defaultStatisticsGroupValues(it);cuts=it}
        Field(groups,"Group values (comma-separated)",Modifier.fillMaxWidth().testTag("statistics-group-column-values")){groups=it}
        Field(header,"New column header",Modifier.fillMaxWidth().testTag("statistics-group-column-header")){header=it}
        StatisticsExplanation("Usage notes",tr("Separate cut points with commas in increasing order. Groups use < and ≥; boundary values belong to the upper group. Missing or nonnumeric values remain blank."),"statistics-group-column-help")
        val options=listOf(selected.toString(),cuts,header,groups)
        val alreadyAdded=added==(data to options)
        val preview=remember(data,kind,selected,cuts,header,groups) {runCatching {statisticsGroupedColumn(data,kind,selected,cuts,header,groups)}}
        (if(alreadyAdded)addedResult else preview.getOrNull())?.let {result->
            result.labels.forEachIndexed {index,label->Text("${result.ranges[index]} → $label  (n=${result.counts[index]})",fontSize=12.sp)}
            if(result.omitted>0)Text("${tr("Ungrouped rows")}: ${result.omitted}",fontSize=11.sp,color=LocalInstrument.current.muted)
        }
        if(alreadyAdded)Text(tr("Group column added"),fontSize=11.sp,color=LocalInstrument.current.accent)
        else if(cuts.isNotBlank()&&header.isNotBlank()&&preview.isFailure)Text(tr(preview.exceptionOrNull()?.message.orEmpty()),fontSize=11.sp,color=LocalInstrument.current.danger)
        OutlinedButton(onClick={preview.getOrNull()?.let {result->added=result.csv to options;addedResult=result;onAdd(result)}},enabled=!alreadyAdded&&preview.isSuccess&&!m.busy&&!m.regressionBusy,modifier=Modifier.testTag("statistics-group-column-add")){Text(tr("Add group column"))}
    }
    HorizontalDivider()
}
