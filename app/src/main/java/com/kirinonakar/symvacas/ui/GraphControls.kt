package com.kirinonakar.symvacas.ui

import androidx.compose.foundation.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.*
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.graphics.*
import androidx.compose.ui.semantics.*
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.*
import com.kirinonakar.symvacas.ui.theme.LocalInstrument
import kotlin.math.*

// Shared numeric fields, range sliders, height toggle, and value table.
@Composable internal fun GraphHeightToggle(halfHeight:Boolean,onToggle:()->Unit,modifier:Modifier=Modifier) {
    val c=LocalInstrument.current
    val label=if(halfHeight) {if(isKorean())"전체 높이" else "Full height"} else {if(isKorean())"높이 ½" else "Half height"}
    Box(modifier.padding(6.dp).size(36.dp).clickable(onClick=onToggle).semantics {contentDescription=label},contentAlignment=Alignment.Center) {
        Box(Modifier.size(30.dp).background(c.body.copy(alpha=.94f),RoundedCornerShape(7.dp)).border(1.dp,c.grid,RoundedCornerShape(7.dp)),contentAlignment=Alignment.Center) {
            Canvas(Modifier.size(18.dp)) {
                val unit=size.width/18f
                val color=if(halfHeight)c.accent else c.ink
                fun at(x:Float,y:Float)=Offset(x*unit,y*unit)
                fun line(x1:Float,y1:Float,x2:Float,y2:Float)=drawLine(color,at(x1,y1),at(x2,y2),1.7f*unit)
                line(3f,2f,15f,2f);line(3f,16f,15f,16f)
                if(halfHeight) {
                    line(9f,8f,9f,5f);line(6.5f,7.5f,9f,5f);line(11.5f,7.5f,9f,5f)
                    line(9f,10f,9f,13f);line(6.5f,10.5f,9f,13f);line(11.5f,10.5f,9f,13f)
                } else {
                    line(9f,5f,9f,8f);line(6.5f,5.5f,9f,8f);line(11.5f,5.5f,9f,8f)
                    line(9f,13f,9f,10f);line(6.5f,12.5f,9f,10f);line(11.5f,12.5f,9f,10f)
                }
            }
        }
    }
}

@Composable internal fun GraphParameterValueField(name:String,value:Double,displayDigits:Int,onApply:(Double)->Unit,onError:(String)->Unit) {
    val c=LocalInstrument.current
    val korean=isKorean()
    val focusManager=LocalFocusManager.current
    var draft by rememberSaveable(name) {mutableStateOf(value.toString())}
    var focused by remember {mutableStateOf(false)}
    var invalid by remember {mutableStateOf(false)}
    LaunchedEffect(value) {if(!focused){draft=value.toString();invalid=false}}
    val shape=RoundedCornerShape(6.dp)
    BasicTextField(if(focused)draft else graphDisplayNumber(draft,displayDigits),{draft=it;invalid=false},Modifier.width(82.dp).height(32.dp).padding(horizontal=3.dp).keepInputVisible()
        .background(c.display,shape).border(1.dp,if(invalid)MaterialTheme.colorScheme.error else c.grid,shape)
        .onFocusChanged {state->
            val wasFocused=focused;focused=state.isFocused
            if(wasFocused&&!focused) {
                val number=draft.trim().toDoubleOrNull()
                if(number==null||!number.isFinite()||abs(number)>1e9) {
                    invalid=true
                    onError(if(korean)"-1e9부터 1e9 사이의 유한한 값을 입력하세요." else "Enter a finite value between -1e9 and 1e9")
                } else {invalid=false;onApply(number)}
            }
        }.semantics {contentDescription=if(korean)"매개변수 값: $name" else "Parameter value: $name"},
        textStyle=MaterialTheme.typography.bodySmall.copy(fontSize=12.sp,color=c.ink),singleLine=true,cursorBrush=SolidColor(c.accent),
        keyboardOptions=KeyboardOptions(imeAction=ImeAction.Done),keyboardActions=KeyboardActions(onDone={focusManager.clearFocus()}),
        decorationBox={inner->Box(Modifier.fillMaxSize().padding(horizontal=5.dp),contentAlignment=Alignment.CenterStart){inner()}})
}

@Composable internal fun GraphNumberField(value:String,label:String,displayDigits:Int,modifier:Modifier=Modifier,onValue:(String)->Unit) {
    val c=LocalInstrument.current
    val shape=RoundedCornerShape(7.dp)
    var focused by remember {mutableStateOf(false)}
    BasicTextField(if(focused)value else graphDisplayNumber(value,displayDigits),onValue,modifier.keepInputVisible().height(40.dp).background(c.display,shape).border(1.dp,c.grid,shape).onFocusChanged {focused=it.isFocused}.semantics {contentDescription=label},
        textStyle=MaterialTheme.typography.bodyMedium.copy(fontSize=14.sp,color=c.ink),singleLine=true,cursorBrush=SolidColor(c.accent),
        decorationBox={inner->Row(Modifier.fillMaxSize().padding(horizontal=10.dp),verticalAlignment=Alignment.CenterVertically) {
                Text(label,fontSize=11.sp,color=c.muted)
                Spacer(Modifier.width(7.dp))
                Box(Modifier.weight(1f)){inner()}
    }})
}

@Composable internal fun RangeAxisEditor(axis:String,minimum:String,maximum:String,initialMin:Double,initialMax:Double,displayDigits:Int,onMin:(String)->Unit,onMax:(String)->Unit,logarithmic:Boolean=false) {
    val scale=com.kirinonakar.symvacas.math.GraphYScale(logarithmic)
    fun sliderBounds(min:Double?,max:Double?):Pair<Double,Double>? {
        if(min==null||max==null||!min.isFinite()||!max.isFinite())return null
        if(logarithmic&&(min<=0||max<=0))return null
        val low=scale.coordinate(min);val high=scale.coordinate(max)
        val span=high-low
        if(!span.isFinite()||span<=0.0)return null
        val start=if(logarithmic)(low-span/2).coerceAtLeast(-300.0) else low-span/2;val end=if(logarithmic)(high+span/2).coerceAtMost(300.0) else high+span/2
        return if(start.isFinite()&&end.isFinite()&&(end-start).isFinite()&&end>start)start to end else null
    }
    var bounds by remember(axis,logarithmic) {mutableStateOf(sliderBounds(initialMin,initialMax) ?: (-10.0 to 10.0))}
    val range=bounds.second-bounds.first
    Text("$axis range",fontSize=12.sp,color=LocalInstrument.current.muted)
    Row(horizontalArrangement=Arrangement.spacedBy(6.dp)) {
        GraphNumberField(minimum,"$axis min",displayDigits,Modifier.weight(1f)){
            onMin(it)
            sliderBounds(it.toDoubleOrNull(),maximum.toDoubleOrNull())?.let {next->bounds=next}
        }
        GraphNumberField(maximum,"$axis max",displayDigits,Modifier.weight(1f)){
            onMax(it)
            sliderBounds(minimum.toDoubleOrNull(),it.toDoubleOrNull())?.let {next->bounds=next}
        }
    }
    val low=(((minimum.toDoubleOrNull()?.let {scale.coordinate(it)}?.takeIf(Double::isFinite) ?: bounds.first)-bounds.first)/range).coerceIn(0.0,1.0).toFloat()
    val high=(((maximum.toDoubleOrNull()?.let {scale.coordinate(it)}?.takeIf(Double::isFinite) ?: bounds.second)-bounds.first)/range).coerceIn(0.0,1.0).toFloat()
    CompactRangeSlider(value=low.coerceAtMost(high)..high.coerceAtLeast(low),onValueChange={selected->
            onMin(scale.value(bounds.first+selected.start*range).toString())
            onMax(scale.value(bounds.first+selected.endInclusive*range).toString())
        },modifier=Modifier.fillMaxWidth())
}

@Composable internal fun GraphValueTable(
    curves:List<List<Pair<Double,Double>?>>,
    selected:Int,
    onTrace:(Pair<Double,Double>)->Unit,
    kind:String,
    displayDigits:Int
) {
    val c=LocalInstrument.current
    val count=curves.maxOfOrNull { it.size } ?: 0
    val stride=max(1,ceil(count/28.0).toInt())
    Column(Modifier.fillMaxWidth().heightIn(max=190.dp).verticalScroll(rememberScrollState()).padding(horizontal=10.dp)) {
        Text(if(kind=="sequence")"Sequence table · tap a row to trace" else "Visible graph values · tap a row to trace",fontSize=12.sp,color=c.muted)
        Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()).padding(vertical=4.dp)) {
            Text(if(kind=="sequence")"n" else "x",Modifier.width(72.dp),fontSize=11.sp,color=c.accent)
            curves.indices.forEach { Text("${if(kind=="sequence")"u" else "f"}${it+1}",Modifier.width(92.dp),fontSize=11.sp,color=c.accent) }
        }
        for(index in 0 until count step stride) {
            val anchor=curves.getOrNull(selected)?.getOrNull(index)
            ?: curves.firstNotNullOfOrNull { it.getOrNull(index) }
            Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()).clickable(enabled=anchor!=null) { anchor?.let(onTrace) }.padding(vertical=3.dp)) {
                Text(anchor?.first?.let { graphDisplayNumber(it,displayDigits) } ?: "—",Modifier.width(72.dp),fontSize=11.sp,color=c.ink)
                curves.forEach { curve->Text(curve.getOrNull(index)?.second?.let { graphDisplayNumber(it,displayDigits) } ?: "—",Modifier.width(92.dp),fontSize=11.sp,color=c.ink) }
            }
            HorizontalDivider(color=c.grid)
        }
    }
}
