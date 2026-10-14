package com.kirinonakar.symvacas.ui

import androidx.compose.foundation.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.*
import androidx.compose.ui.draw.clipToBounds
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.graphics.*
import androidx.compose.ui.semantics.*
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.PlatformTextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.LineHeightStyle
import androidx.compose.ui.unit.*
import com.kirinonakar.symvacas.calculator.CalculatorModel
import com.kirinonakar.symvacas.calculator.removeGraphInputLine
import com.kirinonakar.symvacas.ui.theme.LocalInstrument
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
        GraphSourceInput(m.graphSource,{m.updateGraphSource(it)},m.graphKind=="differential")
        TextButton(onClick={inputHelpOpen=!inputHelpOpen},modifier=Modifier.padding(horizontal=4.dp).testTag("graph-input-help-toggle")) {
            Text("${if(inputHelpOpen)"▾" else "▸"} ${tr("Graph input help")}",fontSize=12.sp)
        }
        if(inputHelpOpen)Column(Modifier.fillMaxWidth().padding(horizontal=14.dp).testTag("graph-input-help"),verticalArrangement=Arrangement.spacedBy(6.dp)) {
            Text(if(isKorean())"Cartesian에서 y=x^2, x^2+y^2=9, r=2*cos(3*θ), (cos(t),sin(t))를 함께 표시합니다. Range에서 t와 θ 범위를 각각 설정하세요. 해당 그래프가 있을 때만 표시됩니다." else "Cartesian combines y=x^2, x^2+y^2=9, r=2*cos(3*θ), and (cos(t),sin(t)). Set separate t and θ bounds in Range; each appears when its graph is present.",fontSize=12.sp,color=c.muted)
            Text(if(isKorean())"x^2+y^2<4 또는 y>=x^2-2를 바로 입력해 영역을 채웁니다. 엄격한 부등식은 점선, <=와 >=는 실선 경계를 사용합니다." else "Enter x^2+y^2<4 or y>=x^2-2 to shade directly. Strict inequalities use dashed boundaries; <= and >= use solid boundaries.",fontSize=12.sp,color=c.muted)
            Text(if(isKorean())"수식 앞의 눈 아이콘으로 그래프를 표시하거나 숨깁니다. 3D에서는 표면 불투명도를 조정하고 단면 슬라이더에서 x = c, y = c 또는 z = c를 선택하세요." else "Use the eye before each formula to show or hide its graph. In 3D, adjust Surface opacity and choose x = c, y = c or z = c for the section slider.",fontSize=12.sp,color=c.muted)
            Text(tr("Expressions · one per line"),fontSize=12.sp,color=c.muted)
            Text(tr("One [x(t),y(t)] pair per line"),fontSize=12.sp,color=c.muted)
            Text(tr("r(t) · radians · one curve per line"),fontSize=12.sp,color=c.muted)
            Text(tr("u(n) · use u(n−1) for recurrences"),fontSize=12.sp,color=c.muted)
            Text(tr("Tap to trace · drag to pan · pinch or scroll to zoom"),fontSize=12.sp,color=c.muted)
            Text(tr("Angle analysis: choose a point for Tangent angle, or two Cartesian curves and an a–b interval for Intersection angle. Results show degrees and radians."),fontSize=12.sp,color=c.muted)
            Text(tr("Drag to rotate freely · Pinch to zoom"),fontSize=12.sp,color=c.muted)
            Text(tr("Function / y=f(x) · Implicit / F(x,y)=0 · e.g. x+1, y=x+1, y^2+x^2=1"),fontSize=12.sp,color=c.muted)
            Text(tr("Piecewise functions / domain restrictions"),fontSize=12.sp,color=c.ink,fontWeight=FontWeight.SemiBold)
            Text(tr("Use {condition:value,condition:value,default}. The first matching condition wins; without a default, unmatched values are undefined."),fontSize=12.sp,color=c.muted)
            Text("f(x)={x<0:x^2,x>=0:2*x}",fontSize=12.sp,color=c.ink)
            Text(tr("Append {condition} to restrict the whole preceding expression. Spaces and outer parentheses are optional; chained inequalities are supported."),fontSize=12.sp,color=c.muted)
            Text("y=x^2 {0<=x<=2}\ny=2*x {x>2}",fontSize=12.sp,color=c.ink)
            Text(tr("One curve per line · [shade] / [s] -1<x<1 ,-1<y<x · between functions: [s] f, g"),fontSize=12.sp,color=c.muted)
            Text(tr("Other graph types"),fontSize=12.sp,color=c.ink,fontWeight=FontWeight.SemiBold)
            Text(tr("3D implicit surfaces use the x, y and z ranges. Auto z uses the y range; other letters become sliders."),fontSize=12.sp,color=c.muted)
            Text("x^2+y^2+z^2+sin(4*x)+sin(4*y)+sin(4*z)=a",fontSize=12.sp,color=c.ink)
            Text(tr("3D graphs · up to 5 · one per line"),fontSize=12.sp,color=c.ink)
            Text(tr("3D curve: C(t)=4*(sin(t),cos(t),0.6*sin(2*t)) · [x(t),y(t),z(t)]"),fontSize=12.sp,color=c.ink)
            Text(tr("Parametric: [cos(t),sin(t)] · Polar: 1+cos(t) (radians) · Sequence: u(n-1)+1 (enter initial values) · 3D surface: z=sin(x)*cos(y) · Differential equation: -y (dy/dt; enter t₀ and initial y values)"),fontSize=12.sp,color=c.muted)
        }
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
                                CompactSlider(spec.value.toFloat(),{focusManager.clearFocus();m.setGraphParameter(name,it.toDouble())},Modifier.weight(1f),valueRange=(if(low<high)low else low-1f)..(if(high>low)high else low+1f))
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

@Composable private fun GraphSourceInput(value:String,onValue:(String)->Unit,singleRule:Boolean) {
    val c=LocalInstrument.current
    val (input,change)=rememberMathInput(value,multiline=true,onValue=onValue)
    val vertical=rememberScrollState();val horizontal=rememberScrollState()
    var focused by remember {mutableStateOf(false)}
    val lineHeight=24.sp
    val rowHeight=with(LocalDensity.current){lineHeight.toDp()}
    // A full line box also keeps the first editable line aligned with its gutter row.
    val style=MaterialTheme.typography.bodyLarge.copy(fontFamily=FontFamily.Monospace,fontSize=14.sp,lineHeight=lineHeight,color=c.ink,
        platformStyle=PlatformTextStyle(includeFontPadding=false),
        lineHeightStyle=LineHeightStyle(LineHeightStyle.Alignment.Center,LineHeightStyle.Trim.None))
    val deleteLabel=tr("Delete line")
    val inputLabel=tr("Graph expression")
    Column(Modifier.fillMaxWidth().padding(start=10.dp,end=10.dp,top=8.dp)) {
        Row(Modifier.fillMaxWidth().height(rowHeight*(if(singleRule)1 else 3)+20.dp).border(1.dp,if(focused)c.accent else c.grid,RoundedCornerShape(7.dp))) {
            Column(Modifier.width(46.dp).fillMaxHeight().clipToBounds().background(c.scientific).verticalScroll(vertical).padding(vertical=10.dp)) {
                repeat(value.count {it=='\n'}+1) {index->
                    Row(Modifier.fillMaxWidth().height(rowHeight),verticalAlignment=Alignment.CenterVertically) {
                        Box(Modifier.width(24.dp).fillMaxHeight().clickable {onValue(removeGraphInputLine(value,index))}.semantics {contentDescription="$deleteLabel ${index+1}"}.testTag("graph-delete-line-${index+1}"),contentAlignment=Alignment.Center) {
                            Text("×",style=style.copy(color=c.muted))
                        }
                        Text("${index+1}",Modifier.weight(1f).padding(end=4.dp),style=style.copy(color=c.muted),textAlign=TextAlign.End,softWrap=false)
                    }
                }
            }
            VerticalDivider(color=c.grid)
            BoxWithConstraints(Modifier.weight(1f).fillMaxHeight()) {
                val fieldWidth=(maxWidth-16.dp).coerceAtLeast(0.dp)
                Box(Modifier.fillMaxSize().verticalScroll(vertical)) {
                    Box(Modifier.horizontalScroll(horizontal)) {
                        MathClipboard {BasicTextField(input,change,Modifier.widthIn(min=fieldWidth).keepInputVisible().onFocusChanged {focused=it.isFocused}.testTag("graph-source").semantics {contentDescription=inputLabel},
                                textStyle=style,cursorBrush=SolidColor(c.accent),
                                decorationBox={inner->Box(Modifier.padding(horizontal=8.dp,vertical=10.dp)){inner()}})}
                    }
                }
            }
        }
    }
}
