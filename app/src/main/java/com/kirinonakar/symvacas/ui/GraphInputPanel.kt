package com.kirinonakar.symvacas.ui

import androidx.compose.foundation.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.*
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.graphics.*
import androidx.compose.ui.semantics.*
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.*
import com.kirinonakar.symvacas.calculator.CalculatorModel
import kotlin.math.*
import com.kirinonakar.symvacas.ui.theme.InstrumentColors

// Source editor, help, graph kinds, action buttons, and parameter controls.
@Composable internal fun GraphInputPanel(
    m:CalculatorModel,c:InstrumentColors,analysis:Boolean,showTable:Boolean,
    exporting:Boolean,exportMessage:String,prepareExport:(String)->Unit,
    onRange:()->Unit,onAnalysisToggle:()->Unit,onTableToggle:()->Unit,onParameterRange:(String)->Unit
) {
    val focusManager=LocalFocusManager.current
    var parametersOpen by rememberSaveable {mutableStateOf(true)}
    var inputHelpOpen by rememberSaveable {mutableStateOf(false)}
    Column(Modifier.fillMaxWidth().zIndex(1f)) {
        LineNumberedMathInput(m.graphSource,{m.updateGraphSource(it)},tr("Graph expression"),
            Modifier.fillMaxWidth().padding(start=10.dp,end=10.dp,top=8.dp),
            visibleLines=if(m.graphKind=="differential")1 else 3,tag="graph")
        TextButton(onClick={inputHelpOpen=!inputHelpOpen},modifier=Modifier.padding(horizontal=4.dp).testTag("graph-input-help-toggle")) {
            Text("${if(inputHelpOpen)"▾" else "▸"} ${tr("Graph input help")}",fontSize=12.sp)
        }
        if(inputHelpOpen) GraphInputHelp(m.graphKind,c)
        Column(Modifier.fillMaxWidth().zIndex(1f).background(c.body)) {
            CompositionLocalProvider(LocalMinimumInteractiveComponentSize provides 0.dp) {
                Row(Modifier.fillMaxWidth().zIndex(2f).padding(top=2.dp).horizontalScroll(rememberScrollState()).semantics { contentDescription="Graph types" },horizontalArrangement=Arrangement.spacedBy(6.dp)) {
                    listOf("cartesian" to "Cartesian","parametric" to "Parametric","polar" to "Polar","sequence" to "Sequence","surface" to "3D surface","space" to "3D curve","differential" to "Diff eq").forEach {(kind,label)->
                        SmallAction(label,active=if(m.graphKind==kind)true else null,shaded=m.graphKind==kind) {m.changeGraphKind(kind)}
                    }
                }
            }
            if(m.graphKind=="sequence") Field(m.sequenceInitials,"Initial values at n=0 · comma separated",Modifier.fillMaxWidth()) {m.sequenceInitials=it;m.save()}
            if(m.graphKind=="differential") {
                Row(horizontalArrangement=Arrangement.spacedBy(6.dp)) {GraphNumberField(m.differentialT0,"Initial time t₀",m.displayDigits,Modifier.weight(1f)){m.differentialT0=it;m.save()};Field(m.differentialInitials,"Initial y values · comma separated",Modifier.weight(2f)){m.differentialInitials=it;m.save()} }
            }
            CompositionLocalProvider(LocalMinimumInteractiveComponentSize provides 0.dp) {
                Row(Modifier.horizontalScroll(rememberScrollState())) {
                    SmallAction("Range") {onRange()}
                    if(m.graphKind in listOf("surface","space"))SmallAction("Undo",enabled=m.canUndoGraph) {m.undoGraph()}
                    if(m.graphKind in listOf("cartesian","parametric","polar"))SmallAction("Analyze",active=if(analysis)true else null,shaded=analysis) {onAnalysisToggle()}
                    if(m.graphKind !in listOf("surface","space"))SmallAction("Table",active=if(showTable)true else null,shaded=showTable) {onTableToggle()}
                    if(m.graphKind in listOf("cartesian","parametric","polar"))SmallAction(if(m.radianAxis)"x: π rad" else "x: decimal"){m.radianAxis=!m.radianAxis;m.save()}
                    if(m.graphKind !in listOf("surface","space"))SmallAction(if(m.yLog)"y: log10" else "y: linear",active=if(m.yLog)true else null,shaded=m.yLog){m.yLog=!m.yLog}
                    SmallAction("Save SVG",enabled=m.graphData!=null&&!exporting){prepareExport("svg")}
                    SmallAction("Save PNG",enabled=m.graphData!=null&&!exporting){prepareExport("png")}
                }
            }
            if(exportMessage.isNotBlank())Text(tr(exportMessage),Modifier.padding(horizontal=14.dp),fontSize=11.sp,color=c.muted)
            if(m.graphParameters.isNotEmpty()) {
                Row(Modifier.fillMaxWidth().padding(horizontal=10.dp).horizontalScroll(rememberScrollState()),verticalAlignment=Alignment.CenterVertically) {
                    SmallAction(if(parametersOpen)"Parameters ▾" else "Parameters ▸"){focusManager.clearFocus();parametersOpen=!parametersOpen}
                    val animationLabel=tr(if(m.graphAnimating)"Stop" else "Animate")
                    TextButton(
                        onClick={focusManager.clearFocus();m.toggleGraphAnimation()},
                        modifier=Modifier.width(48.dp).semantics {contentDescription=animationLabel},
                        contentPadding=PaddingValues(8.dp),
                        colors=ButtonDefaults.textButtonColors(containerColor=if(m.graphAnimating)c.accent.copy(alpha=.22f) else Color.Transparent)
                    ) {
                        val iconColor=if(m.graphAnimating)c.accent else MaterialTheme.colorScheme.onSurface
                        Canvas(Modifier.size(18.dp)) {
                            if(m.graphAnimating)drawRect(iconColor,topLeft=Offset(size.width/6,size.height/6),size=androidx.compose.ui.geometry.Size(size.width*2/3,size.height*2/3))
                            else drawPath(Path().apply {moveTo(size.width/4,size.height/6);lineTo(size.width*5/6,size.height/2);lineTo(size.width/4,size.height*5/6);close()},iconColor)
                        }
                    }
                    SmallAction("Reset sliders"){focusManager.clearFocus();m.resetGraphParameters()}
                }
                if(parametersOpen)Column(Modifier.fillMaxWidth().heightIn(max=150.dp).verticalScroll(rememberScrollState())) {
                    m.graphParameters.entries.forEach { (name,spec)->
                        key(name) {
                            val animateLabel="${tr("Animate")}: $name"
                            val low=spec.min.toFloat();val high=spec.max.toFloat()
                            Row(Modifier.fillMaxWidth().height(38.dp).padding(horizontal=12.dp),verticalAlignment=Alignment.CenterVertically) {
                                Checkbox(spec.animate,{m.setGraphParameterAnimation(name,it)},Modifier.size(32.dp).semantics {contentDescription=animateLabel})
                                Text(name,Modifier.width(24.dp),fontSize=13.sp,color=c.accent,fontWeight=FontWeight.SemiBold)
                                CompactSlider(spec.value.toFloat(),{focusManager.clearFocus();m.graphState.parameterDragging=true;m.setGraphParameter(name,it.toDouble());m.plot(auto=true,preview=true)},Modifier.weight(1f),valueRange=(if(low<high)low else low-1f)..(if(high>low)high else low+1f),onValueChangeFinished={m.graphState.parameterDragging=false;m.plot(auto=true);m.save()})
                                GraphParameterValueField(name,spec.value,m.displayDigits,{value->m.setGraphParameter(name,value,centerRange=true);m.error="";m.save()},{m.error=it})
                                Box(Modifier.size(30.dp).background(c.scientific,RoundedCornerShape(8.dp)).clickable{focusManager.clearFocus();onParameterRange(name)}.semantics {contentDescription="Set $name slider range"},contentAlignment=Alignment.Center) {
                                    Text("±",fontSize=16.sp,color=c.accent)
                                }
                            }
                        }
                    }
                }
            }
        }
    }

}
