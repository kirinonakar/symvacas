package com.kirinonakar.symvacas.ui

import androidx.compose.foundation.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.*
import androidx.compose.ui.graphics.*
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.semantics.*
import androidx.compose.ui.unit.*
import com.kirinonakar.symvacas.calculator.isImplicitSurface
import com.kirinonakar.symvacas.calculator.graphShadingBody
import com.kirinonakar.symvacas.math.Parser
import com.kirinonakar.symvacas.ui.theme.LocalInstrument
import org.json.JSONObject
import kotlin.math.*

// Formula AST adaptation and selectable equation/shading rows.
internal fun graphEquationTree(kind:String,source:String,index:Int,displayDigits:Int?=null):JSONObject? {
    val left=when(kind) {
        "parametric"->"[x(t),y(t)]"
        "space"->"C${index+1}(t)"
        "polar"->"r(t)"
        "sequence"->"u(n)"
        "surface"->"z"
        "differential"->"dy/dt"
        else->"f${index+1}(x)"
    }
    val parsed=runCatching {Parser(source).parse()}.getOrNull()
    val equation=if(parsed?.kind=="relation")source else if(kind=="implicit" || kind=="surface" && isImplicitSurface(source) || kind=="cartesian" && parsed?.nodes()?.any {it.kind=="symbol" && it.value=="y"}==true)"$source=0" else if(kind=="cartesian" && parsed?.kind in listOf("tuple","list"))"[x(t),y(t)]=$source" else "$left=$source"
    return if(displayDigits==null)decimalFractionFormulaTree(equation) else regressionFormulaDisplayTree(equation,displayDigits)
}

private fun splitGraphFormulaParts(source:String):List<String> {
    val result=mutableListOf<String>()
    var depth=0
    var start=0
    source.forEachIndexed {index,char->
        when(char) {
            '(','[','{'->depth++
            ')',']','}'->depth--
            ','->if(depth==0) {result+=source.substring(start,index).trim();start=index+1}
        }
    }
    result+=source.substring(start).trim()
    return result.filter(String::isNotEmpty)
}

internal data class GraphShadeFormula(val expressions:List<JSONObject>,val range:Pair<JSONObject,JSONObject>?)

internal fun graphShadeFormula(source:String,displayDigits:Int?=null):GraphShadeFormula? = runCatching {
    val parts=splitGraphFormulaParts(graphShadingBody(source))
    val expressions=mutableListOf<JSONObject>()
    var range:Pair<JSONObject,JSONObject>?=null
    parts.forEach {part->
        val ends=part.split("..")
        if(ends.size==2 && range==null) {
            range=((if(displayDigits==null)decimalFractionFormulaTree(ends[0].trim()) else regressionFormulaDisplayTree(ends[0].trim(),displayDigits)) ?: error("Invalid shade range")) to
            ((if(displayDigits==null)decimalFractionFormulaTree(ends[1].trim()) else regressionFormulaDisplayTree(ends[1].trim(),displayDigits)) ?: error("Invalid shade range"))
        } else expressions+=(if(displayDigits==null)decimalFractionFormulaTree(part) else regressionFormulaDisplayTree(part,displayDigits)) ?: error("Invalid shade expression")
    }
    GraphShadeFormula(expressions,range).takeIf {it.expressions.isNotEmpty()}
}.getOrNull()

@Composable internal fun GraphFormulas(kind:String,sources:List<String>,selected:Int,derivativeSelected:Int?,derivativeExpression:String,shadeSources:List<String>,onSelect:((Int)->Unit)?,onDerivative:()->Unit,onRemove:(Int,Boolean)->Unit,displayDigits:Int,colors:List<Color>,secondDerivativeSelected:Int?=null,secondDerivativeExpression:String="",onSecondDerivative:()->Unit={},selectedDerivativeOrder:Int=0,onSelectDerivative:(Int)->Unit={},isVisible:(Int,String)->Boolean={_,_->true},onVisibility:(Int,String)->Unit={_,_->}) {
    val c=LocalInstrument.current
    val equations=remember(kind,sources,displayDigits) {sources.mapIndexed {index,source->graphEquationTree(kind,source,index,displayDigits)}}
    val derivative=remember(derivativeSelected,derivativeExpression,displayDigits) {
        if(derivativeSelected==null || derivativeExpression.isBlank())null
        else regressionFormulaDisplayTree("diff(f${derivativeSelected+1}(x),x)=$derivativeExpression",displayDigits)
    }
    val secondDerivative=remember(secondDerivativeSelected,secondDerivativeExpression,displayDigits) {
        if(secondDerivativeSelected==null || secondDerivativeExpression.isBlank())null
        else regressionFormulaDisplayTree("diff(f${secondDerivativeSelected+1}(x),x,2)=$secondDerivativeExpression",displayDigits)
    }
    val shades=remember(shadeSources,displayDigits) {shadeSources.mapIndexedNotNull {index,source->graphShadeFormula(source,displayDigits)?.let {index to it}}}
    if(equations.all {it==null} && derivative==null && secondDerivative==null && shades.isEmpty())return
    CompositionLocalProvider(LocalMathMinimumSize provides 8f) {
        Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()).padding(horizontal=10.dp,vertical=3.dp),verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(8.dp)) {
            equations.forEachIndexed {index,tree->
                if(tree!=null)Row(Modifier.background(if(selectedDerivativeOrder==0 && index==selected)c.accent.copy(alpha=.16f) else c.scientific,RoundedCornerShape(8.dp))
                    .then(if(onSelect==null)Modifier else Modifier.clickable {onSelect(index)}.semantics {contentDescription="Select curve ${index+1}"})
                    .padding(horizontal=7.dp,vertical=3.dp),verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(5.dp)) {
                    GraphEyeButton(isVisible(index,"curve"),"f${index+1}",colors[index%colors.size]) {onVisibility(index,"curve")}
                    Box(Modifier.alignBy(MathAxis)){MathNode(tree,12f)}
                }
            }
            listOf(derivative to onDerivative,secondDerivative to onSecondDerivative).forEachIndexed {index,(tree,toggle)->
                val isSelected=selectedDerivativeOrder==index+1
                if(tree!=null)Row(Modifier.background(if(isSelected)c.accent.copy(alpha=.16f) else c.scientific,RoundedCornerShape(8.dp)).clickable {onSelectDerivative(index+1)}.semantics {contentDescription="Select derivative curve of order ${index+1}";this.selected=isSelected}
                    .padding(horizontal=7.dp,vertical=3.dp),verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(5.dp)) {
                    val sourceIndex=if(index==0)derivativeSelected!! else secondDerivativeSelected!!
                    val role=if(index==0)"derivative" else "secondDerivative"
                    GraphEyeButton(isVisible(sourceIndex,role),"f${sourceIndex+1}"+if(index==0)"′" else "″",c.accent) {onVisibility(sourceIndex,role)}
                    Box(Modifier.alignBy(MathAxis)){MathNode(tree,12f)}
                }
            }
            shades.forEach {(index,shade)->
                Row(Modifier.background(c.scientific,RoundedCornerShape(8.dp)).padding(horizontal=7.dp,vertical=3.dp),verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(4.dp)) {
                    GraphEyeButton(isVisible(index,"shade"),"${index+1}",c.muted) {onVisibility(index,"shade")}
                    shade.expressions.forEachIndexed {index,tree->
                        if(index>0)MathText(",",12f,Modifier.alignBy(MathAxis))
                        Box(Modifier.alignBy(MathAxis)){MathNode(tree,12f)}
                    }
                    shade.range?.let {(low,high)->
                        MathText("  (",12f,Modifier.alignBy(MathAxis))
                        Box(Modifier.alignBy(MathAxis)){MathNode(low,12f)}
                        MathText(" ≤ x ≤ ",12f,Modifier.alignBy(MathAxis))
                        Box(Modifier.alignBy(MathAxis)){MathNode(high,12f)}
                        MathText(")",12f,Modifier.alignBy(MathAxis))
                    }
                }
            }
        }
    }
}

@Composable private fun RowScope.GraphEyeButton(visible:Boolean,label:String,color:Color,onToggle:()->Unit) {
    val description=(if(isKorean()) {if(visible)"그래프 숨기기" else "그래프 표시"} else {if(visible)"Hide graph" else "Show graph"})+": "+label
    // Canvas has no MathAxis of its own; align its center with the formula axis.
    Canvas(Modifier.alignBy { it.measuredHeight / 2 }.size(32.dp).clickable(role=Role.Checkbox,onClick=onToggle)
        .semantics {contentDescription=description;stateDescription=if(visible)"Visible" else "Hidden"}
        .padding(8.dp)) {
        val w=size.width;val h=size.height
        val eye=Path().apply {moveTo(0f,h*.5f);cubicTo(w*.25f,-h*.02f,w*.75f,-h*.02f,w,h*.5f);cubicTo(w*.75f,h*1.02f,w*.25f,h*1.02f,0f,h*.5f);close()}
        val tint=color.copy(alpha=if(visible)1f else .5f)
        drawPath(eye,tint,style=androidx.compose.ui.graphics.drawscope.Stroke(1.4.dp.toPx()))
        drawCircle(tint,w*.14f,Offset(w*.5f,h*.5f))
        if(!visible)drawLine(tint,Offset(0f,0f),Offset(w,h),1.4.dp.toPx())
    }
}
