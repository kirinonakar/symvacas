package com.kirinonakar.symvacas.ui

import androidx.compose.foundation.*
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
import kotlin.math.*
import com.kirinonakar.symvacas.ui.theme.InstrumentColors

// Analysis controls and results; the screen owns the saved interaction state.
internal class GraphAnalysisUiState(
    val first:MutableState<String>,
    val second:MutableState<String>,
    val pointAt:MutableState<String>,
    val tangentPositionOpen:MutableState<Boolean>,
    val tangentAction:MutableState<String>,
    val selected:MutableIntState,
    val selectedDerivativeOrder:MutableIntState,
    val other:MutableIntState
)
@Composable internal fun rememberGraphAnalysisUiState(m:CalculatorModel):GraphAnalysisUiState {
    val first=rememberSaveable {mutableStateOf(m.xMin.toString())}
    val second=rememberSaveable {mutableStateOf(m.xMax.toString())}
    val pointAt=rememberSaveable {mutableStateOf(((m.xMin+m.xMax)/2).toString())}
    val tangentPositionOpen=rememberSaveable {mutableStateOf(false)}
    val tangentAction=rememberSaveable {mutableStateOf("tangent")}
    val selected=rememberSaveable {mutableIntStateOf(0)}
    val selectedDerivativeOrder=rememberSaveable {mutableIntStateOf(0)}
    val other=rememberSaveable {mutableIntStateOf(1)}
    return remember {GraphAnalysisUiState(first,second,pointAt,tangentPositionOpen,tangentAction,selected,selectedDerivativeOrder,other)}
}

@Composable internal fun GraphAnalysisPanel(
    m:CalculatorModel,c:InstrumentColors,state:GraphAnalysisUiState,
    analysisCurveLabels:Map<Int,String>,markers:List<GraphPoint>
) {
    val focusManager=LocalFocusManager.current
    var first by state.first
    var second by state.second
    var pointAt by state.pointAt
    var tangentPositionOpen by state.tangentPositionOpen
    var tangentAction by state.tangentAction
    var selected by state.selected
    var selectedDerivativeOrder by state.selectedDerivativeOrder
    var other by state.other
    val analysisCurveKey=if(selectedDerivativeOrder==0)selected else -selectedDerivativeOrder
    val analysisKind=if(m.graphKind=="cartesian" && selectedDerivativeOrder==0)m.graphData?.optJSONArray("curveKinds")?.optString(selected,"cartesian") ?: "cartesian" else m.graphKind

    Column(Modifier.padding(horizontal=10.dp)) {
        Text(if(isKorean())"${analysisCurveLabels[analysisCurveKey] ?: "선택한 곡선"} 분석 · ${if(analysisKind=="cartesian")"x" else if(analysisKind=="polar")"θ" else "t"} 구간" else "Analyze ${analysisCurveLabels[analysisCurveKey] ?: "the selected curve"} · ${if(analysisKind=="cartesian")"x" else if(analysisKind=="polar")"θ" else "t"} interval",fontSize=12.sp,color=c.muted)
        Row(horizontalArrangement=Arrangement.spacedBy(6.dp)) { GraphNumberField(first,"a",m.displayDigits,Modifier.weight(1f)) {first=it};GraphNumberField(second,"b",m.displayDigits,Modifier.weight(1f)) {second=it} }
        val sliderMin=if(analysisKind=="cartesian")m.xMin else if(analysisKind=="polar")m.thetaMin else m.parameterMin
        val sliderMax=if(analysisKind=="cartesian")m.xMax else if(analysisKind=="polar")m.thetaMax else m.parameterMax
        val sliderSpan=sliderMax-sliderMin
        if(sliderMin.isFinite() && sliderMax.isFinite() && sliderSpan.isFinite() && sliderSpan>0.0) {
            val low=((first.toDoubleOrNull()?.takeIf(Double::isFinite) ?: sliderMin)-sliderMin).div(sliderSpan).coerceIn(0.0,1.0).toFloat()
            val high=((second.toDoubleOrNull()?.takeIf(Double::isFinite) ?: sliderMax)-sliderMin).div(sliderSpan).coerceIn(0.0,1.0).toFloat()
            CompactRangeSlider(low.coerceAtMost(high)..high.coerceAtLeast(low),{range->
                    first=(sliderMin+range.start*sliderSpan).toString()
                    second=(sliderMin+range.endInclusive*sliderSpan).toString()
                },Modifier.fillMaxWidth())
        }
        CompositionLocalProvider(LocalMinimumInteractiveComponentSize provides 0.dp) {
            Row(horizontalArrangement=Arrangement.spacedBy(6.dp)) {
                SmallAction("Use visible ${if(analysisKind=="cartesian")"x" else if(analysisKind=="polar")"θ" else "t"} range") {if(analysisKind=="cartesian"){first=m.xMin.toString();second=m.xMax.toString()}else if(analysisKind=="polar"){first=m.thetaMin.toString();second=m.thetaMax.toString()}else{first=m.parameterMin.toString();second=m.parameterMax.toString()}}
                SmallAction("Clear analysis") {focusManager.clearFocus();tangentPositionOpen=false;m.clearGraphTangent()}
            }
            if(analysisKind=="cartesian"&&analysisCurveLabels.size>1) {
                Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically) {
                    Text(if(isKorean())"교점 / 교점 각도: ${analysisCurveLabels[analysisCurveKey]}와" else "Intersection / angle: ${analysisCurveLabels[analysisCurveKey]} with",fontSize=12.sp,color=c.muted)
                    Spacer(Modifier.width(6.dp))
                    Row(Modifier.weight(1f).horizontalScroll(rememberScrollState())) {
                        analysisCurveLabels.filterKeys {it!=analysisCurveKey}.forEach {(key,label)->SmallAction(label,key==other) {m.clearGraphTangent();tangentPositionOpen=false;other=key}}
                    }
                }
            }
            Row(Modifier.horizontalScroll(rememberScrollState())) {
                val actions=if(analysisKind=="cartesian")listOf("Root","Y-intercept","Intersection","Intersection angle","Minimum","Maximum","Inflection","Derivative","Tangent","Tangent angle","Integral","Arc length","Asymptotes") else listOf("Root","Y-intercept","Minimum","Maximum","Inflection","Derivative","Tangent","Tangent angle","Integral","Arc length")
                actions.forEach { action->
                    val key=action.lowercase().replace(" ","").replace("-","")
                    val isTangent=key in listOf("tangent","tangentangle")
                    SmallAction(action,active=if(isTangent&&tangentPositionOpen&&tangentAction==key)true else null,shaded=isTangent&&tangentPositionOpen&&tangentAction==key) {
                        focusManager.clearFocus()
                        if(isTangent&&tangentPositionOpen&&tangentAction==key) {
                            tangentPositionOpen=false
                            m.clearGraphTangent()
                        } else {
                            tangentPositionOpen=isTangent
                            if(isTangent)tangentAction=key
                            m.analyzeGraph(key,if(isTangent)pointAt else first,second,analysisCurveKey,other)
                        }
                    }
                }
            }
        }
        if(tangentPositionOpen) {
            Text(if(isKorean())"접선 위치 (${if(analysisKind=="cartesian")"x" else if(analysisKind=="polar")"θ" else "t"})" else "Tangent position (${if(analysisKind=="cartesian")"x" else if(analysisKind=="polar")"θ" else "t"})",fontSize=12.sp,color=c.muted)
            GraphNumberField(pointAt,if(analysisKind=="cartesian")"x" else if(analysisKind=="polar")"θ" else "t",m.displayDigits,Modifier.fillMaxWidth()) {pointAt=it}
            if(sliderMin.isFinite() && sliderMax.isFinite() && sliderSpan.isFinite() && sliderSpan>0.0) {
                val position=((pointAt.toDoubleOrNull()?.takeIf(Double::isFinite) ?: sliderMin)-sliderMin).div(sliderSpan).coerceIn(0.0,1.0).toFloat()
                CompactSlider(position,{pointAt=(sliderMin+it*sliderSpan).toString()},Modifier.fillMaxWidth(),onValueChangeFinished={
                        m.analyzeGraph(tangentAction,pointAt,pointAt,analysisCurveKey,other)
                })
            }
        }
        if(m.graphAnalysisBusy)Text(if(isKorean())"분석 중…" else "Analyzing…",fontSize=12.sp,color=c.muted)
        m.graphAnalysis?.let {result->
            val name=when(result.optString("analysis")){"asymptotes"->tr("Asymptotes");"tangentangle"->tr("Tangent angle");"intersectionangle"->tr("Intersection angle");"yintercept"->tr("Y-intercept");"arclength"->"Arc length";"inflection"->"Inflection";"tangent"->"Tangent slope";"intersection"->"Intersection";"minimum"->"Minimum";"maximum"->"Maximum";"integral"->"Integral";else->result.optString("analysis").replaceFirstChar {it.uppercase()}}
            val angleResult=result.optString("unit")=="deg"
            if(angleResult)Text(tr(if(result.optString("analysis")=="tangentangle")"Tangent angle: inclination from the positive x axis (0° ≤ θ < 180°)." else "Intersection angle: smaller angle between tangents (0°–90°)."),fontSize=12.sp,color=c.muted)
            if(result.has("value"))Text("$name = ${graphDisplayNumber(result.optDouble("value"),m.displayDigits)}"+if(angleResult)"° (${graphDisplayNumber(result.optDouble("radians"),m.displayDigits)} rad)" else "",fontSize=16.sp)
            else if(result.optBoolean("vertical"))Text("$name · vertical tangent",fontSize=13.sp)
            else if(result.optString("analysis")=="asymptotes")Text("$name · ${result.optInt("count")}",fontSize=13.sp)
            else Text("$name · ${result.optInt("count")} point(s)${if(result.optBoolean("truncated"))" · first 80 shown" else ""}",fontSize=13.sp)
            val asymptotes=result.optJSONArray("asymptotes")
            for(index in 0 until (asymptotes?.length() ?: 0)) {
                asymptotes!!.getJSONObject(index).optJSONObject("tree")?.let {tree->MathNode(tree,16f)}
            }
            if(result.optString("note").isNotBlank())Text(result.optString("note"),fontSize=12.sp,color=c.muted)
            markers.forEachIndexed {i,p->
                val angle=result.optJSONArray("angles")?.optJSONObject(i)
                val angleText=if(angle==null)"" else if(angle.isNull("value"))" · ${tr("Tangent is undefined at this point")}" else " · ${graphDisplayNumber(angle.optDouble("value"),m.displayDigits)}° (${graphDisplayNumber(angle.optDouble("radians"),m.displayDigits)} rad)"
                SmallAction("${i+1}. (${graphDisplayNumber(p.first,m.displayDigits)}, ${graphDisplayNumber(p.second,m.displayDigits)})$angleText") {
                    m.trace=p
                    if(p.first !in m.xMin..m.xMax) {val half=(m.xMax-m.xMin)/2;m.xMin=p.first-half;m.xMax=p.first+half}
                    if(p.second !in m.yMin..m.yMax) {val half=(m.yMax-m.yMin)/2;m.yMin=p.second-half;m.yMax=p.second+half}
                } }
        }
        if(analysisKind=="cartesian")Row(Modifier.horizontalScroll(rememberScrollState()),horizontalArrangement=Arrangement.spacedBy(6.dp)) {
            SmallAction("f${(m.graphDerivativeSelected ?: selected)+1}′",active=if(m.graphDerivativeSelected!=null)true else null,shaded=m.graphDerivativeSelected!=null) {m.toggleGraphDerivative(selected)}
            SmallAction("f${(m.graphSecondDerivativeSelected ?: selected)+1}″",active=if(m.graphSecondDerivativeSelected!=null)true else null,shaded=m.graphSecondDerivativeSelected!=null) {m.toggleGraphDerivative(selected,2)}
        }
    }
}
