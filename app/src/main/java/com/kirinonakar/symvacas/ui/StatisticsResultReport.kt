package com.kirinonakar.symvacas.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.Alignment
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.stateDescription
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.kirinonakar.symvacas.calculator.CalculatorModel
import com.kirinonakar.symvacas.ui.theme.LocalInstrument
import org.json.JSONObject

@Composable internal fun StatisticsExplanation(title:String,text:String,tag:String,resetKey:Any=text,expansionKey:String=tag) {
    val model=LocalStatisticsExplanationModel.current
    val stateKey="explanation:$expansionKey"
    var localExpanded by remember(resetKey) {mutableStateOf(false)}
    val expanded=model?.statisticsSectionExpanded(stateKey) ?: localExpanded
    val collapseRequest=LocalStatisticsCollapseRequest.current
    LaunchedEffect(collapseRequest){if(model==null&&collapseRequest>0)localExpanded=false}
    val description=tr(if(expanded)"Expanded" else "Collapsed")
    val compact=title=="Usage notes"
    Column(Modifier.fillMaxWidth().testTag(tag)) {
        CompositionLocalProvider(LocalMinimumInteractiveComponentSize provides if(compact)0.dp else LocalMinimumInteractiveComponentSize.current) {
            TextButton(onClick={if(model!=null)model.setStatisticsSectionExpanded(stateKey,!expanded) else localExpanded=!expanded},contentPadding=PaddingValues(horizontal=0.dp,vertical=if(compact)0.dp else 4.dp),
                modifier=Modifier.then(if(compact)Modifier.heightIn(min=24.dp) else Modifier).testTag("$tag-toggle").semantics {stateDescription=description}) {
                Text((if(expanded)"▾ " else "▸ ")+tr(title),fontSize=12.sp,color=LocalInstrument.current.muted)
            }
        }
        if(expanded)SelectionContainer {Text(text,Modifier.fillMaxWidth(),fontSize=11.sp,color=LocalInstrument.current.muted)}
    }
}

@Composable internal fun StatisticsSelectionTitle(title:String,translate:Boolean=true) {
    Text(if(translate)tr(title) else title,fontSize=14.sp,fontWeight=FontWeight.SemiBold,color=LocalInstrument.current.ink)
}

internal fun statisticsReportFor(result:JSONObject?,source:String,analyses:Set<String>):JSONObject? {
    val report=result?.optJSONObject("statisticsReport") ?: return null
    val analysis=report.optString("analysis").ifBlank {source.substringBefore('(').trim()}
    return report.takeIf {analysis in analyses}
}

internal fun statisticsCellText(m:CalculatorModel,cell:JSONObject)=ResultDisplayFormat.resultText(cell,true,false,
    m.resultDisplayMode,m.thousandsSeparator,m.engineeringConversion,m.engineeringShift,false,false,m.displayDigits)

@Composable internal fun StatisticsTextTable(headers:List<String>,rows:List<List<String>>,headerSize:Int=12,cellSize:Int=13) {
    val c=LocalInstrument.current
    // Intrinsic text widths keep columns aligned. A single scroll owns the table;
    // no child scroll receives unbounded width. Cap unusually long cells for readability.
    SelectionContainer {
        Row(Modifier.horizontalScroll(rememberScrollState())) {
            headers.forEachIndexed {column,header->Column(Modifier.widthIn(min=64.dp,max=320.dp).width(IntrinsicSize.Max)) {
                Box(Modifier.fillMaxWidth().height(38.dp).background(c.grid).padding(horizontal=8.dp),contentAlignment=Alignment.CenterStart) {
                    Text(header,fontSize=headerSize.sp,fontWeight=FontWeight.SemiBold,color=c.ink,maxLines=1,overflow=TextOverflow.Ellipsis)
                }
                rows.forEach {row->
                    Box(Modifier.fillMaxWidth().height(36.dp).padding(horizontal=8.dp),contentAlignment=Alignment.CenterStart) {
                        Text(row.getOrElse(column){""},fontSize=cellSize.sp,color=c.ink,maxLines=1,softWrap=false,overflow=TextOverflow.Ellipsis)
                    }
                    HorizontalDivider(color=c.grid)
                }
            }}
        }
    }
}

@Composable private fun StatisticsReportSection(m:CalculatorModel,report:JSONObject,section:JSONObject,collapsible:Boolean) {
    val c=LocalInstrument.current
    val collapseRequest=LocalStatisticsCollapseRequest.current
    val columns=section.getJSONArray("columns")
    val rows=section.getJSONArray("rows")
    var expanded by remember(report,section) {mutableStateOf(!collapsible)}
    LaunchedEffect(collapseRequest){if(collapseRequest>0&&collapsible)expanded=false}
    if(collapsible)TextButton(onClick={expanded=!expanded}){Text("${if(expanded)"▾" else "▸"} ${tr(section.getString("title"))} (${section.optInt("totalRows")})")}
    else Text(tr(section.getString("title")),fontSize=13.sp,fontWeight=FontWeight.SemiBold,color=c.ink)
    if(!expanded)return
    StatisticsTextTable(List(columns.length()){if(section.optBoolean("literalColumns"))columns.getString(it) else tr(columns.getString(it))},List(rows.length()){rowIndex->
        val row=rows.getJSONArray(rowIndex)
        List(columns.length()){column->
            row.optJSONObject(column)?.let {statisticsCellText(m,it)}
                ?: if(column==0&&rowIndex==section.optInt("totalRow",-1)||columns.optString(column) in listOf("Metric","Check","Interpretation","Sample","Role","R²","Kind","Effect","Intercept / drift","Status")||columns.optString(column)=="Parameter"&&report.optString("analysis") in listOf("arima","sarima")||columns.optString(column)=="Value"&&row.optString(0) in listOf("Intercept / drift","Fit status"))tr(row.optString(column)) else row.optString(column)
        }
    })
    if(section.optInt("totalRows")>rows.length())Text("${rows.length()} / ${section.optInt("totalRows")} · ${tr("Copy result includes all rows.")}",fontSize=11.sp,color=c.muted)
}

@Composable internal fun StatisticsResultReport(m:CalculatorModel,report:JSONObject,onModelWorkflow:((StatisticsModelWorkflowPlan)->Unit)?=null) {
    val c=LocalInstrument.current
    val clipboard=LocalClipboardManager.current
    val language=LocalLanguage.current
    val collapseRequest=LocalStatisticsCollapseRequest.current
    val sections=report.getJSONArray("sections")
    Column(Modifier.fillMaxWidth().testTag("statistics-result-report"),verticalArrangement=Arrangement.spacedBy(12.dp)) {
        Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically) {
            Text(tr(report.getString("title")),Modifier.weight(1f),style=MaterialTheme.typography.titleMedium,color=c.ink)
            TextButton(onClick={m.statisticsResult?.let {clipboard.setText(AnnotatedString(statisticsResultCopyText(m,it,language)))}}){Text(tr("Copy"),fontSize=12.sp)}
            TextButton(onClick={m.clearStatisticsResult()},enabled=!m.busy&&!m.regressionBusy,modifier=Modifier.testTag("statistics-result-clear")){Text(tr("Clear"),fontSize=12.sp)}
        }
        report.optString("context").takeIf(String::isNotBlank)?.let {Text(it,fontSize=12.sp,color=c.muted)}
        report.optJSONArray("warnings")?.let {warnings->for(index in 0 until warnings.length()) {
            val warning=warnings.optJSONObject(index)
            Text((warning?.optString("label")?.takeIf(String::isNotBlank)?.let {"$it: "} ?: "")+tr(warning?.optString("text") ?: warnings.optString(index)),fontSize=12.sp,color=MaterialTheme.colorScheme.error)
        }}
        if(onModelWorkflow!=null)report.optJSONObject("modelWorkflow")?.let {StatisticsModelWorkflow(it,!m.busy&&!m.regressionBusy,onModelWorkflow)}
        report.optJSONArray("highlights")?.let {highlights->
            for(start in 0 until highlights.length() step 2)Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.spacedBy(8.dp)) {
                for(index in start until minOf(start+2,highlights.length())) {
                    val item=highlights.getJSONObject(index)
                    Column(Modifier.weight(1f).background(c.grid).padding(10.dp),verticalArrangement=Arrangement.spacedBy(4.dp)) {
                        Text(tr(item.getString("label")),fontSize=11.sp,color=c.muted)
                        Text(statisticsCellText(m,item.getJSONObject("value")),fontSize=17.sp,fontWeight=FontWeight.SemiBold,color=c.ink)
                    }
                }
                if(start+1==highlights.length())Spacer(Modifier.weight(1f))
            }
        }
        report.optJSONArray("notes")?.let {notes->
            if(notes.length()>0){var notesExpanded by remember(report){mutableStateOf(false)}
                LaunchedEffect(collapseRequest){if(collapseRequest>0)notesExpanded=false}
                TextButton(onClick={notesExpanded=!notesExpanded}){Text((if(notesExpanded)"▾ " else "▸ ")+tr("Interpretation & assumptions"))}
                if(notesExpanded)for(index in 0 until notes.length())Text(tr(notes.getString(index)),fontSize=12.sp,color=c.muted)
            }
        }
        val primary=setOf("Summary","ANOVA","Overall model","Overall ANOVA","Overall Welch ANOVA",report.getString("title"))+if(report.optString("title")=="Overall")setOf("Numeric data","Categorical data") else emptySet()
        val prominent=primary+setOf("Model diagnostics","Indicator R²","Explained variance","Latent R²","Summary","Sample summaries","Assumption checks","Effect size","Mean confidence interval (95%, two-sided)","Overall ANOVA","Expected-count diagnostics")
        val ordered=(0 until sections.length()).sortedBy {when(sections.getJSONObject(it).getString("title")){in primary->0;in prominent->1;else->2}}
        var plotsShown=false
        val shownGroups=mutableSetOf<String>()
        for(index in ordered) {
            val section=sections.getJSONObject(index)
            if(section.getString("title") !in prominent&&!plotsShown){StatisticsVisualizations(report.optJSONArray("plots"));plotsShown=true}
            val group=section.optString("contingencyGroup")
            if(group.isNotBlank()) {
                if(!shownGroups.add(group))continue
                var expanded by remember(report,group) {mutableStateOf(section.optBoolean("contingencyExpanded",true))}
                var lastCollapseRequest by remember(report,group) {mutableStateOf(collapseRequest)}
                LaunchedEffect(collapseRequest){if(collapseRequest!=lastCollapseRequest){expanded=false;lastCollapseRequest=collapseRequest}}
                val title=section.optString("contingencyLabel").takeIf(String::isNotBlank)?.let {"$it · "}.orEmpty()+tr(section.optString("contingencyTitle","Contingency table"))
                Column(Modifier.fillMaxWidth(),verticalArrangement=Arrangement.spacedBy(8.dp)) {
                    TextButton(onClick={expanded=!expanded},modifier=Modifier.testTag("statistics-contingency-$group")){Text((if(expanded)"▾ " else "▸ ")+title)}
                    if(expanded)for(member in ordered){val grouped=sections.getJSONObject(member);if(grouped.optString("contingencyGroup")==group)StatisticsReportSection(m,report,grouped,false)}
                }
            } else StatisticsReportSection(m,report,section,section.optInt("totalRows")>12&&section.getString("title") !in prominent)
        }
        if(!plotsShown)StatisticsVisualizations(report.optJSONArray("plots"))
        report.optJSONArray("details")?.takeIf {it.length()>0}?.let {details->
            val descriptions=(0 until details.length()).joinToString("\n\n") {statisticsDetailText(details.getJSONObject(it)){translateLabel(it,language)}}
            StatisticsExplanation("Model details",descriptions,"statistics-result-details",report)
        }
        report.optJSONArray("assumptions")?.takeIf {it.length()>0}?.let {assumptions->
            val descriptions=mutableListOf<String>()
            for(index in 0 until assumptions.length())descriptions+=tr(assumptions.getString(index))
            StatisticsExplanation("Assumptions",descriptions.joinToString("\n\n"),"statistics-result-assumptions",report)
        }
        m.statisticsResult?.optString("note")?.takeIf(String::isNotBlank)?.let {StatisticsExplanation("Interpretation & assumptions",it,"statistics-result-note",report)}
    }
}
