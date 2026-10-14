package com.kirinonakar.symvacas.ui

import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.*
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.graphics.*
import androidx.compose.ui.semantics.*
import androidx.compose.ui.unit.*
import com.kirinonakar.symvacas.calculator.CalculatorModel
import com.kirinonakar.symvacas.calculator.graphRangeAxes
import com.kirinonakar.symvacas.math.SurfaceMesh
import kotlin.math.*

// Graph axis ranges and individual parameter-range dialogs.
@Composable internal fun GraphRangeDialog(m:CalculatorModel,onDismiss:()->Unit) {
    var xmin by remember {mutableStateOf(m.xMin.toString())};var xmax by remember {mutableStateOf(m.xMax.toString())};var ymin by remember {mutableStateOf(m.yMin.toString())};var ymax by remember {mutableStateOf(m.yMax.toString())}
    var tmin by remember {mutableStateOf(m.parameterMin.toString())};var tmax by remember {mutableStateOf(m.parameterMax.toString())}
    var thetaMin by remember {mutableStateOf(m.thetaMin.toString())};var thetaMax by remember {mutableStateOf(m.thetaMax.toString())}
    val rangeAxes=graphRangeAxes(m.graphSource,m.graphKind)
    val sampledMin=m.graphData?.optDouble("zMin",-1.0)?.takeIf(Double::isFinite) ?: -1.0
    val sampledMax=m.graphData?.optDouble("zMax",1.0)?.takeIf(Double::isFinite) ?: 1.0
    val sampledRange=SurfaceMesh.zRange(sampledMin,sampledMax)
    var zmin by remember {mutableStateOf((m.zMin ?: sampledRange.first).toString())}
    var zmax by remember {mutableStateOf((m.zMax ?: sampledRange.second).toString())}
    var autoZ by remember {mutableStateOf(m.zMin==null || m.zMax==null)}
    AlertDialog(onDismissRequest={onDismiss()},title={Text(tr("Graph range"))},text={Column(Modifier.verticalScroll(rememberScrollState())) {
                RangeAxisEditor(if(m.graphKind=="sequence")"n" else "x",xmin,xmax,m.xMin,m.xMax,m.displayDigits,{xmin=it},{xmax=it})
                RangeAxisEditor("y",ymin,ymax,m.yMin,m.yMax,m.displayDigits,{ymin=it},{ymax=it},logarithmic=m.yLog&&m.graphKind !in listOf("surface","space"))
                if(m.graphKind in listOf("surface","space")) {
                    SmallAction("Reset ranges") {
                        val extent=if(m.graphKind=="space")5.0 else 3.0
                        xmin=(-extent).toString();xmax=extent.toString();ymin=(-extent).toString();ymax=extent.toString();autoZ=true
                        m.resetSurfaceRanges()
                    }
                    Row(verticalAlignment=Alignment.CenterVertically) {Checkbox(autoZ,{autoZ=it});Text(tr("Automatic z range"))}
                    if(!autoZ)RangeAxisEditor("z",zmin,zmax,zmin.toDoubleOrNull() ?: -1.0,zmax.toDoubleOrNull() ?: 1.0,m.displayDigits,{zmin=it},{zmax=it})
                }
                if("t" in rangeAxes)RangeAxisEditor("t",tmin,tmax,m.parameterMin,m.parameterMax,m.displayDigits,{tmin=it},{tmax=it})
                if("theta" in rangeAxes)RangeAxisEditor("θ",thetaMin,thetaMax,m.thetaMin,m.thetaMax,m.displayDigits,{thetaMin=it},{thetaMax=it})
        }},confirmButton={TextButton(onClick={
                    val values=listOf(xmin,xmax,ymin,ymax).map {it.toDoubleOrNull()}
                    val ta=tmin.toDoubleOrNull();val tb=tmax.toDoubleOrNull()
                    val za=zmin.toDoubleOrNull();val zb=zmax.toDoubleOrNull()
                    val usesT="t" in rangeAxes
                    val usesTheta="theta" in rangeAxes
                    val pa=thetaMin.toDoubleOrNull();val pb=thetaMax.toDoubleOrNull()
                    val usesZ=m.graphKind in listOf("surface","space")&&!autoZ
                    if(values.any {it==null||!it.isFinite()} || values[0]!!>=values[1]!! || values[2]!!>=values[3]!! || (m.yLog&&m.graphKind !in listOf("surface","space")&&(values[2]!!<=0)) || (usesT&&(ta==null||tb==null||!ta.isFinite()||!tb.isFinite()||ta>=tb)) || (usesTheta&&(pa==null||pb==null||!pa.isFinite()||!pb.isFinite()||pa>=pb)) || (usesZ&&(za==null||zb==null||!za.isFinite()||!zb.isFinite()||za>=zb))) m.error="Enter finite increasing ranges" else {
                        m.xMin=values[0]!!;m.xMax=values[1]!!;m.yMin=values[2]!!;m.yMax=values[3]!!
                        if(m.graphKind in listOf("surface","space")){m.zMin=if(autoZ)null else za;m.zMax=if(autoZ)null else zb}
                        if(m.graphKind=="sequence"){m.parameterMin=values[0]!!;m.parameterMax=values[1]!!}
                        else if(usesT){m.parameterMin=ta!!;m.parameterMax=tb!!}
                        if(usesTheta){m.thetaMin=pa!!;m.thetaMax=pb!!}
                        m.save();onDismiss();m.plot()
                    }
            }) {Text(tr("Apply"))} },dismissButton={TextButton(onClick={onDismiss()}) {Text(tr("Cancel"))} })

}

@Composable internal fun GraphParameterRangeDialog(m:CalculatorModel,name:String,onDismiss:()->Unit) {
    val focusManager=LocalFocusManager.current
    val spec=m.graphParameters[name]
    if(spec!=null) {
        var low by remember(name){mutableStateOf(spec.min.toString())}
        var high by remember(name){mutableStateOf(spec.max.toString())}
        var resetRevision by remember(name){mutableIntStateOf(0)}
        AlertDialog(onDismissRequest={onDismiss()},title={Text(if(isKorean())"$name 슬라이더 범위" else "$name slider range")},text={Column{
                    SmallAction("Reset sliders") {
                        focusManager.clearFocus();m.resetGraphParameters(name)
                        low="-5.0";high="5.0";resetRevision++
                    }
                    key(resetRevision){RangeAxisEditor(name,low,high,spec.min,spec.max,m.displayDigits,{low=it},{high=it})}
            }},confirmButton={TextButton(onClick={
                        val start=low.toDoubleOrNull();val end=high.toDoubleOrNull()
                        if(start==null||end==null||!start.isFinite()||!end.isFinite()||start>=end||abs(start)>1e9||abs(end)>1e9)m.error="Enter finite values with minimum < maximum"
                        else {
                            if(start!=spec.min||end!=spec.max)m.setGraphParameterRange(name,start,end) else m.error=""
                            onDismiss()
                        }
                }) {Text(tr("Apply"))}},dismissButton={TextButton(onClick={onDismiss()}) {Text(tr("Cancel"))} })
    }

}
