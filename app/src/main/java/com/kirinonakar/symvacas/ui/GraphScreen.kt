package com.kirinonakar.symvacas.ui

import androidx.compose.foundation.*
import androidx.compose.foundation.relocation.BringIntoViewRequester
import androidx.compose.foundation.relocation.bringIntoViewRequester
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.*
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.graphics.*
import androidx.compose.ui.semantics.*
import androidx.compose.ui.unit.*
import com.kirinonakar.symvacas.calculator.CalculatorModel
import com.kirinonakar.symvacas.calculator.isGraphShading
import com.kirinonakar.symvacas.calculator.graphCurveLimit
import com.kirinonakar.symvacas.calculator.graphSourceLimit
import com.kirinonakar.symvacas.ui.theme.LocalInstrument
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlin.math.*

// Coordinates graph panels, selection state, and automatic sampling.
@Composable fun GraphScreen(m: CalculatorModel) {
    val defaults=LocalInstrument.current
    val c=defaults.copy(curves=m.graphColors.mapIndexed {index,hex->hex?.let {Color(android.graphics.Color.parseColor(it))} ?: defaults.curves[index]})
    val focusManager=LocalFocusManager.current
    val saveActions=rememberGraphSaveActions(m)
    val exports=saveActions.exports
    val exporting=saveActions.exporting
    val exportMessage=saveActions.message
    val prepareExport=saveActions.prepare
    var rangeDialog by remember { mutableStateOf(false) }
    var analysis by remember { mutableStateOf(false) }
    var showTable by rememberSaveable { mutableStateOf(false) }
    var rangeParameter by remember { mutableStateOf<String?>(null) }
    val surfaceView=rememberGraphSurfaceView()
    var halfGraphHeight by rememberSaveable { mutableStateOf(false) }
    val analysisState=rememberGraphAnalysisUiState(m)
    var first by analysisState.first; var second by analysisState.second
    var pointAt by analysisState.pointAt
    var tangentPositionOpen by analysisState.tangentPositionOpen
    var scrollToSection by remember { mutableStateOf<String?>(null) }
    val graphScrollState=rememberScrollState()
    val tableRequester=remember {BringIntoViewRequester()}
    var selected by analysisState.selected
    var selectedDerivativeOrder by analysisState.selectedDerivativeOrder
    var other by analysisState.other
    var viewportDragging by remember { mutableStateOf(false) }
    LaunchedEffect(m.graphKind){
        selected=0;selectedDerivativeOrder=0;other=1;tangentPositionOpen=false
        val low=if(m.graphKind=="cartesian")m.xMin else if(m.graphKind=="polar")m.thetaMin else m.parameterMin
        val high=if(m.graphKind=="cartesian")m.xMax else if(m.graphKind=="polar")m.thetaMax else m.parameterMax
        first=low.toString();second=high.toString();pointAt=((low+high)/2).toString()
    }
    LaunchedEffect(m.graphSource) {tangentPositionOpen=false}
    LaunchedEffect(m.graphDerivativeSelected,m.graphSecondDerivativeSelected,selectedDerivativeOrder) {
        if(selectedDerivativeOrder==1 && m.graphDerivativeSelected==null || selectedDerivativeOrder==2 && m.graphSecondDerivativeSelected==null)selectedDerivativeOrder=0
    }
    LaunchedEffect(scrollToSection,analysis,showTable) {
        delay(100)
        when(scrollToSection) {
            "analysis" -> if(analysis)graphScrollState.animateScrollTo(graphScrollState.maxValue)
            "table" -> if(showTable)tableRequester.bringIntoView()
        }
        scrollToSection=null
    }
    val parameterSignature=m.graphParameters.entries.joinToString(","){"${it.key}=${it.value.value}"}
    LaunchedEffect(m.graphSource,m.graphDerivativeSelected,m.graphSecondDerivativeSelected,m.xMin,m.xMax,m.yMin,m.yMax,m.zMin,m.zMax,m.graphKind,m.parameterMin,m.parameterMax,m.thetaMin,m.thetaMax,m.sequenceInitials,m.differentialInitials,m.differentialT0,if(m.graphAnimating)"animation" else parameterSignature,m.surfaceSamples,m.surfaceAutoDensity,if(m.graphKind=="surface" && m.surfaceAutoDensity)m.surfaceZoom else 1f,viewportDragging) { if(!m.graphAnimating && !viewportDragging){delay(350);m.plot(auto=true)} }
    LaunchedEffect(viewportDragging) {
        if(viewportDragging) {
            var sampledView:List<Double>?=null
            while(isActive) {
                delay(80)
                val view=listOf(m.xMin,m.xMax,m.yMin,m.yMax)
                if(view!=sampledView && !m.graphAnimating && m.graphKind in listOf("cartesian","implicit","differential")) {
                    sampledView=view
                    m.plot(auto=true,preview=true)
                }
            }
        }
    }
    BoxWithConstraints(Modifier.fillMaxSize()) {
        // Cartesian and every other graph use the same viewport height. Expression
        // rows, sliders, and settings scroll with the plot instead of resizing it.
        val graphHeight=if(maxWidth.value.isFinite())maxWidth else 360.dp
        val plotHeight=if(halfGraphHeight)graphHeight*0.5f else graphHeight
        Column(Modifier.fillMaxSize().verticalScroll(graphScrollState)) {
            GraphInputPanel(m,c,analysis,showTable,exporting,exportMessage,prepareExport,
                {rangeDialog=true},{analysis=!analysis;if(analysis)scrollToSection="analysis"},
                {showTable=!showTable;if(showTable)scrollToSection="table"},{rangeParameter=it})
            val plotData=rememberGraphPlotData(m)
            val curves=plotData.curves
            val derivativeSelected=plotData.derivativeSelected
            val derivativeExpression=plotData.derivativeExpression
            val secondDerivativeSelected=plotData.secondDerivativeSelected
            val secondDerivativeExpression=plotData.secondDerivativeExpression
            val markers=plotData.markers
            val visibleSources=m.graphSource.lines().filter(String::isNotBlank).take(graphSourceLimit(m.graphKind))
            val sources=visibleSources.filter {!(m.graphKind=="cartesian" && isGraphShading(it))}.take(graphCurveLimit(m.graphKind))
            val analysisCurveKey=if(selectedDerivativeOrder==0)selected else -selectedDerivativeOrder
            val analysisCurveLabels=buildMap {
                sources.indices.forEach {put(it,"f${it+1}")}
                m.graphDerivativeSelected?.takeIf {it in sources.indices}?.let {put(-1,"f${it+1}′")}
                m.graphSecondDerivativeSelected?.takeIf {it in sources.indices}?.let {put(-2,"f${it+1}″")}
            }
            LaunchedEffect(analysisCurveLabels,analysisCurveKey,other) {
                if(other !in analysisCurveLabels || other==analysisCurveKey)other=analysisCurveLabels.keys.firstOrNull {it!=analysisCurveKey} ?: 0
            }
            val shadeSources=visibleSources.map(String::trim).filter {m.graphKind=="cartesian" && isGraphShading(it)}.take(4)
            val removeSource:(Int,Boolean)->Unit={index,shading->
                focusManager.clearFocus()
                if(!shading) {
                    val last=(sources.size-2).coerceAtLeast(0)
                    selected=(if(selected>index)selected-1 else selected).coerceIn(0,last)
                    other=(if(other>index)other-1 else other).coerceIn(0,last)
                    if(last>0 && other==selected)other=(selected+1)%(last+1)
                }
                m.removeGraphSource(index,shading)
            }
            if(m.graphKind in listOf("surface","space")) {
                GraphSurfacePlot(m,c,surfaceView,plotHeight,exports,halfGraphHeight,{halfGraphHeight=!halfGraphHeight},sources,shadeSources,removeSource)
            } else GraphPlanarPlot(m,c,plotData,analysisState,plotHeight,exports,halfGraphHeight,
                {halfGraphHeight=!halfGraphHeight},{viewportDragging=it})
            Column(Modifier.fillMaxWidth()) {
                if(m.graphKind !in listOf("surface","space"))GraphFormulas(m.graphKind,sources,selected,derivativeSelected,derivativeExpression,shadeSources,{i->m.clearGraphTangent();tangentPositionOpen=false;selected=i;selectedDerivativeOrder=0;if(other==selected)other=(i+1)%sources.size},{m.toggleGraphDerivative(selected)},removeSource,m.displayDigits,c.curves,secondDerivativeSelected,secondDerivativeExpression,{m.toggleGraphDerivative(selected,2)},selectedDerivativeOrder,{order->m.clearGraphTangent();tangentPositionOpen=false;selectedDerivativeOrder=order},isVisible=m::isGraphVisible,onVisibility=m::toggleGraphVisibility)
                if(m.graphKind !in listOf("surface","space"))Text(if(m.graphBusy&&!m.graphAnimating) {if(isKorean())"그래프 계산 중…" else "Sampling locally…"} else m.trace?.let { "Trace ≈ x: ${graphDisplayNumber(it.first,m.displayDigits)}   y: ${graphDisplayNumber(it.second,m.displayDigits)}" } ?: if(isKorean()) {if(m.graphKind=="differential")"방향장 · 해를 눌러 추적 · 드래그/확대로 탐색" else "눌러 추적 · 드래그하여 이동 · 두 손가락으로 확대"} else if(m.graphKind=="differential")"Direction field · tap a solution to trace · drag/pinch to explore" else "Tap to trace · drag to pan · pinch to zoom",Modifier.padding(horizontal=14.dp,vertical=5.dp),fontSize=11.sp,color=c.muted)
            }
            if(showTable && m.graphKind !in listOf("surface","space")) Box(Modifier.bringIntoViewRequester(tableRequester)) {GraphValueTable(curves,selected,{if(selectedDerivativeOrder!=0){selectedDerivativeOrder=0;m.clearGraphTangent()};m.trace=it},m.graphKind,m.displayDigits)}
            if(analysis && m.graphKind in listOf("cartesian","parametric","polar"))
            GraphAnalysisPanel(m,c,analysisState,analysisCurveLabels,markers)
        }
    }
    if(rangeDialog)GraphRangeDialog(m){rangeDialog=false}
    rangeParameter?.let {name->GraphParameterRangeDialog(m,name){rangeParameter=null}}
}
