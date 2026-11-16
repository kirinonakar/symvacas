package com.kirinonakar.symvacas.ui

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.kirinonakar.symvacas.calculator.CalculatorModel
import com.kirinonakar.symvacas.ui.theme.LocalInstrument
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject

@Composable internal fun StatisticsPreparationTools(m:CalculatorModel,data:String,kind:String,onSaveAsNew:(StatisticsPreparationResult,String)->Unit,onApply:(StatisticsPreparationResult)->Unit) {
    val context=LocalContext.current
    val schema=remember {context.assets.open("statistics_preparation.json").bufferedReader().use {JSONArray(it.readText())}}
    repeat(schema.length()){index->StatisticsPreparationTool(m,data,kind,schema.getJSONObject(index),onSaveAsNew,onApply)}
}

private fun preparationColumnLabels(headers:List<String>):List<String> {
    if(headers.isEmpty())return emptyList()
    val aliases=statisticsColumnNames(statisticsKindForColumns(headers.size))
    return headers.mapIndexed {index,name->if(name==aliases[index])name else "$name (${aliases[index]})"}
}

private fun preparationChoiceOptions(field:JSONObject):List<Pair<String,String>> {
    val choices=field.getJSONArray("options")
    return List(choices.length()){index->choices.getJSONArray(index).let {it.getString(0) to it.getString(1)}}
}

@Composable private fun PreparationHeaderDropdown(field:JSONObject,value:String,modifier:Modifier,onChange:(String)->Unit) {
    val options=preparationChoiceOptions(field)
    val selected=options.firstOrNull {it.first==value} ?: options.first()
    var expanded by remember {mutableStateOf(false)}
    Column(modifier) {
        StatisticsSelectionTitle(field.getString("label"))
        Box {
            OutlinedButton(
                onClick={expanded=true},
                modifier=Modifier.fillMaxWidth().testTag("statistics-preparation-merge-${field.getString("key")}"),
                contentPadding=PaddingValues(horizontal=8.dp,vertical=8.dp)
            ) {
                Text(tr(selected.second),Modifier.weight(1f),fontSize=12.sp,maxLines=1,overflow=TextOverflow.Ellipsis)
                Text("▾",Modifier.padding(start=4.dp),fontSize=12.sp)
            }
            DropdownMenu(expanded,onDismissRequest={expanded=false}) {
                options.forEach {(id,label)->
                    DropdownMenuItem(text={Text(tr(label))},onClick={expanded=false;onChange(id)})
                }
            }
        }
    }
}

@Composable private fun StatisticsPreparationTool(m:CalculatorModel,data:String,kind:String,definition:JSONObject,onSaveAsNew:(StatisticsPreparationResult,String)->Unit,onApply:(StatisticsPreparationResult)->Unit) {
    val id=definition.getString("id")
    val fields=remember(definition) {definition.getJSONArray("fields").let {array->List(array.length(),array::getJSONObject)}}
    val draft=remember {m.advancedStatisticsDraft.optJSONObject("preparationTools")?.optJSONObject(id) ?: JSONObject()}
    var formsText by rememberSaveable {mutableStateOf(draft.toString())}
    val expanded=m.statisticsSectionExpanded("preparation-$id")
    val current=JSONObject(formsText)
    val mergeColumns=id=="merge"&&current.optString("axis")=="columns"
    val leftHeader=if(mergeColumns)current.optString("leftHeader","auto") else null
    val rightHeader=if(mergeColumns)current.optString("rightHeader","auto") else null
    val input=remember(data,kind,leftHeader){runCatching {
        preparationDataset(data,kind,keepTrailingEmptyRow=leftHeader==null,headerMode=leftHeader)
    }}
    val headers=input.getOrNull()?.headers.orEmpty()
    val columnLabels=preparationColumnLabels(headers)
    val datasets=m.dataSets
    val datasetNames=remember(datasets,id){if(id=="merge")datasets.keys().asSequence().sorted().toList() else emptyList()}
    val otherName=current.optString("dataset").takeIf {it in datasetNames}.orEmpty()
    val otherSource=datasets.optJSONObject(otherName)
    val otherCsv=otherSource?.optString("csv").orEmpty()
    val otherKind=otherSource?.optString("kind","list") ?: "list"
    val matchingIndex=expanded&&mergeColumns&&current.optString("columnAlignment")=="index"
    val otherLabels=remember(otherCsv,otherKind,matchingIndex,rightHeader) {
        if(matchingIndex&&otherCsv.isNotBlank())runCatching {
            preparationColumnLabels(preparationDataset(otherCsv,otherKind,keepTrailingEmptyRow=false,headerMode=rightHeader).headers)
        }.getOrDefault(emptyList()) else emptyList()
    }
    fun settings():Map<String,String> = fields.associate {field->
        val key=field.getString("key");var value=current.optString(key,field.getString("default"))
        if(field.getString("type")=="column"){
            val last=if(field.optString("source")=="dataset")otherLabels.lastIndex else headers.lastIndex
            value=(value.toIntOrNull()?.let {if(it==-1)last else it} ?: 0).coerceIn(0,last.coerceAtLeast(0)).toString()
        }
        key to value
    }
    val options=settings()
    fun change(key:String,value:String) {
        val next=JSONObject(formsText)
        if(id=="recode"&&key=="cuts"&&options["groups"]==defaultStatisticsGroupValues(options["cuts"].orEmpty()))next.put("groups",defaultStatisticsGroupValues(value))
        if(id=="wideToLong"&&key=="ids"&&options["measures"]!="auto")next.put("measures",options["measures"].orEmpty().split(',').filter {it.isNotBlank()&&it !in value.split(',')}.joinToString(","))
        formsText=next.put(key,value).toString()
    }
    LaunchedEffect(formsText) {
        val next=JSONObject(m.advancedStatisticsDraft.toString());val tools=next.optJSONObject("preparationTools") ?: JSONObject()
        m.updateAdvancedStatisticsDraft(next.put("preparationTools",tools.put(id,JSONObject(formsText))))
    }
    StatisticsSectionToggle(definition.getString("label"),expanded,"statistics-preparation-$id-toggle",depth=2){m.setStatisticsSectionExpanded("preparation-$id",!expanded)}
    if(expanded)Column(Modifier.fillMaxWidth().padding(start=14.dp),verticalArrangement=Arrangement.spacedBy(4.dp)) {
        for(field in fields) {
            val conditions=field.optJSONObject("when")
            val visible=conditions==null||conditions.keys().asSequence().all {key->options[key]==conditions.getString(key)}
            if(visible) {
                val key=field.getString("key");val value=options.getValue(key);val label=field.getString("label")
                if(id=="merge"&&key=="leftHeader") {
                    Row(
                        Modifier.fillMaxWidth().testTag("statistics-preparation-merge-headers"),
                        horizontalArrangement=Arrangement.spacedBy(8.dp),
                        verticalAlignment=Alignment.Bottom
                    ) {
                        fields.filter {it.getString("key") in listOf("leftHeader","rightHeader")}.forEach {header->
                            val headerKey=header.getString("key")
                            PreparationHeaderDropdown(header,options.getValue(headerKey),Modifier.weight(1f)){change(headerKey,it)}
                        }
                    }
                    continue
                }
                if(id=="merge"&&key=="rightHeader")continue
                when(field.getString("type")) {
                    "conditions"->{
                        StatisticsSelectionTitle(label)
                        val conditions=preparationFilterConditions(value)
                        val choices=field.getJSONArray("options");val keys=List(choices.length()){choices.getJSONArray(it).getString(0)}
                        val labels=List(choices.length()){tr(choices.getJSONArray(it).getString(1))}
                        fun edit(at:Int,property:String,text:String) {
                            val next=JSONArray(options.getValue(key));next.getJSONObject(at).put(property,text);change(key,next.toString())
                        }
                        conditions.forEachIndexed {i,condition->
                            Column(Modifier.fillMaxWidth(),verticalArrangement=Arrangement.spacedBy(4.dp)) {
                                StatisticsSelectionTitle("Source column")
                                if(columnLabels.isNotEmpty())Choices(columnLabels,columnLabels.getOrNull(condition.column.toIntOrNull() ?: -1).orEmpty(),{edit(i,"column",columnLabels.indexOf(it).toString())},translate=false)
                                StatisticsSelectionTitle("Filter operator")
                                Choices(labels,labels[keys.indexOf(condition.operator).coerceAtLeast(0)],{edit(i,"operator",keys[labels.indexOf(it)])},translate=false)
                                if(condition.operator !in listOf("blank","notBlank"))Field(condition.value,"Filter value",Modifier.fillMaxWidth().testTag("statistics-preparation-$id-condition-$i-value")){edit(i,"value",it)}
                                OutlinedButton(enabled=conditions.size>1,onClick={val next=JSONArray(value);next.remove(i);change(key,next.toString())}){Text(tr("Remove condition"))}
                            }
                            HorizontalDivider()
                        }
                        OutlinedButton(onClick={change(key,JSONArray(value).put(JSONObject().put("column","0").put("operator","notBlank").put("value","")).toString())}){Text(tr("Add condition"))}
                    }
                    "dataset"->{
                        StatisticsSelectionTitle(label)
                        if(datasetNames.isEmpty())Text(tr("Save another dataset to combine it with the current data"),fontSize=11.sp,color=LocalInstrument.current.muted)
                        else Choices(datasetNames,otherName,{change(key,it)},translate=false)
                    }
                    "column"->{
                        StatisticsSelectionTitle(label)
                        val names=if(field.optString("source")=="dataset")otherLabels else columnLabels
                        if(names.isNotEmpty())Choices(names,names[value.toInt().coerceIn(names.indices)],{change(key,names.indexOf(it).toString())},translate=false)
                    }
                    "columns"->{
                        StatisticsSelectionTitle(label)
                        val selected=if(value=="auto")headers.indices.filter {it.toString() !in options["ids"].orEmpty().split(',')}.toSet() else value.split(',').mapNotNull(String::toIntOrNull).toSet()
                        headers.forEachIndexed {i,name->
                            Row(verticalAlignment=Alignment.CenterVertically) {
                                Checkbox(i in selected,{checked->change(key,(if(checked)selected+i else selected-i).sorted().joinToString(","))},modifier=Modifier.testTag("statistics-preparation-$id-$key-$i"))
                                Text(columnLabels[i],fontSize=12.sp)
                            }
                        }
                    }
                    "choice"->{
                        val choices=preparationChoiceOptions(field)
                        val keys=choices.map {it.first}
                        val labels=choices.map {tr(it.second)}
                        StatisticsSelectionTitle(label);Choices(labels,labels[keys.indexOf(value).coerceAtLeast(0)],{change(key,keys[labels.indexOf(it)])},translate=false)
                    }
                    "multiline"->OutlinedTextField(value,{change(key,it)},label={Text(tr(label))},modifier=Modifier.fillMaxWidth().keepInputVisible().testTag("statistics-preparation-$id-$key"),minLines=3,maxLines=6)
                    else->Field(value,label,Modifier.fillMaxWidth().testTag("statistics-preparation-$id-$key")){change(key,it)}
                }
            }
        }
        val help=when(id) {
            "filter"->"Choose columns and add conditions. Numeric comparisons omit blank or nonnumeric cells; text comparisons are case-sensitive. AND requires every condition, OR requires at least one. Preview the kept rows, then save them as a new dataset. The source dataset is preserved."
            "dropMissing"->"Blank cells, NA and NaN count as missing."
            "merge"->"Combine the current data with a saved dataset. Index matching compares exact values and requires unique, nonmissing values in each index column. Unmatched cells are left blank."
            "wideToLong"->"ID columns are repeated for each measurement. With no ID columns, row IDs are generated. Blank measurements are retained."
            "longToWide"->"Choose ID, variable and value columns. Missing combinations become blank. Set a text prefix for numeric variable names. Duplicate pairs require an explicit policy."
            "recode"->"Write one old value, new value rule per line; <missing> matches a blank cell. Numeric intervals use < and ≥. Unmatched values follow the selected option."
            else->"Use column names (x, y, z, …) or header names in arithmetic formulas. A label such as test (x) accepts test or x. Supports sqrt, abs, exp, log, trigonometric functions (radians), round, min, max, sum, mean and if(condition,a,b). Missing or invalid numerical results become blank."
        }
        StatisticsExplanation("Usage notes",tr(help),"statistics-preparation-$id-help")
        val previewOptions=options.filterKeys {key->fields.none {field->field.getString("key")==key&&!field.optBoolean("preview",true)}}
        val removeLimits=m.removeComputationLimit
        val key=listOf(data,kind,JSONObject(previewOptions).toString(),removeLimits.toString(),otherCsv,otherKind)
        var preview by remember {mutableStateOf<Pair<List<String>,StatisticsPreparationResult>?>(null)}
        var preparing by remember {mutableStateOf(false)}
        var message by remember {mutableStateOf("")}
        val scope=rememberCoroutineScope()
        OutlinedButton(enabled=!preparing&&!m.busy&&!m.regressionBusy&&headers.isNotEmpty()&&(id!="merge"||otherName.isNotEmpty()),modifier=Modifier.testTag("statistics-preparation-$id-preview"),onClick={
            preparing=true
            scope.launch {
                try {
                    val result=withContext(Dispatchers.Default){runCatching {
                        val other=if(id=="merge")StatisticsPreparationSource(otherCsv,otherKind) else null
                        preparationTransform(data,kind,id,options,removeLimits,other)
                    }}
                    result.onSuccess {preview=key to it;message=""}.onFailure {preview=null;message=it.message.orEmpty()}
                }finally{preparing=false}
            }
        }){Text(tr(if(preparing)"Preparing preview…" else if(id=="filter")"Preview filter" else "Preview transformation"))}
        preview?.second?.let {result->
            val dimensions="${tr("Output rows")}: ${result.rows.size} · ${tr("Output columns")}: ${result.headers.size}"
            Text(when(id){
                "filter"->"${tr("Input rows")}: ${result.rows.size+result.changed} · ${tr("Kept rows")}: ${result.rows.size} · ${tr("Removed rows")}: ${result.changed}"
                "dropMissing"->"$dimensions · ${tr("Removed")}: ${result.changed}"
                "merge"->dimensions
                else->"$dimensions · ${tr("Changed / computed rows")}: ${result.changed}"+(if(result.omitted>0)" · ${tr("Blank derived values")}: ${result.omitted}" else "")
            },fontSize=11.sp)
            if(id=="filter"&&result.rows.isEmpty())Text(tr("No rows match the filter; adjust the conditions"),fontSize=11.sp,color=LocalInstrument.current.muted)
            Text((listOf(result.headers)+result.rows.take(6)).joinToString("\n"){it.joinToString(" | ")},Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()),fontFamily=FontFamily.Monospace,fontSize=11.sp)
            if(preview?.first!=key&&message.isBlank())Text(tr("Preview is outdated; preview the transformation again"),fontSize=11.sp,color=LocalInstrument.current.muted)
        }
        if(message.isNotBlank())Text(tr(message),fontSize=11.sp,color=LocalInstrument.current.muted)
        OutlinedButton(enabled=!preparing&&!m.busy&&!m.regressionBusy&&preview?.first==key&&(id!="filter"||preview?.second?.rows?.isNotEmpty()==true),modifier=Modifier.testTag("statistics-preparation-$id-apply"),onClick={
            preview?.second?.let {result->
                runCatching {if(id=="filter")onSaveAsNew(result,options["datasetName"].orEmpty()) else onApply(result)}
                    .onSuccess {preview=null;message=if(id=="filter")"Filtered rows saved as a new dataset" else "Transformation applied to current data"}
                    .onFailure {message=it.message.orEmpty()}
            }
        }){Text(tr(if(id=="filter")"Save as new dataset" else "Apply to current data"))}
    }
    HorizontalDivider()
}
