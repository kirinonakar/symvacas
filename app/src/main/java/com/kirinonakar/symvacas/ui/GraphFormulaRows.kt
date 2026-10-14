package com.kirinonakar.symvacas.ui

import androidx.compose.foundation.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.*
import androidx.compose.ui.graphics.*
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
    val equation=if(parsed?.kind=="relation")source else if(kind=="implicit" || kind=="surface" && isImplicitSurface(source) || kind=="cartesian" && parsed?.nodes()?.any {it.kind=="symbol" && it.value=="y"}==true)"$source=0" else "$left=$source"
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

@Composable internal fun GraphFormulas(kind:String,sources:List<String>,selected:Int,derivativeSelected:Int?,derivativeExpression:String,shadeSources:List<String>,onSelect:((Int)->Unit)?,onDerivative:()->Unit,onRemove:(Int,Boolean)->Unit,displayDigits:Int,colors:List<Color>,secondDerivativeSelected:Int?=null,secondDerivativeExpression:String="",onSecondDerivative:()->Unit={},selectedDerivativeOrder:Int=0,onSelectDerivative:(Int)->Unit={}) {
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
                    MathText(if(selectedDerivativeOrder==0 && index==selected)"●" else "○",11f,Modifier.alignBy(MathAxis),tint=colors[index%colors.size])
                    Box(Modifier.alignBy(MathAxis)){MathNode(tree,12f)}
                    GraphRemoveButton((if(isKorean())"그래프 삭제" else "Delete graph")+": f${index+1}") {onRemove(index,false)}
                }
            }
            listOf(derivative to onDerivative,secondDerivative to onSecondDerivative).forEachIndexed {index,(tree,toggle)->
                val isSelected=selectedDerivativeOrder==index+1
                if(tree!=null)Row(Modifier.background(if(isSelected)c.accent.copy(alpha=.16f) else c.scientific,RoundedCornerShape(8.dp)).clickable {onSelectDerivative(index+1)}.semantics {contentDescription="Select derivative curve of order ${index+1}";this.selected=isSelected}
                    .padding(horizontal=7.dp,vertical=3.dp),verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(5.dp)) {
                    MathText(if(isSelected)"●" else "○",11f,Modifier.alignBy(MathAxis),tint=c.accent)
                    Box(Modifier.alignBy(MathAxis)){MathNode(tree,12f)}
                    GraphRemoveButton((if(isKorean())"도함수 그래프 삭제" else "Delete derivative curve")+if(index==0)" f′" else " f″",toggle)
                }
            }
            shades.forEach {(index,shade)->
                Row(Modifier.background(c.scientific,RoundedCornerShape(8.dp)).padding(horizontal=7.dp,vertical=3.dp),verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(4.dp)) {
                    MathText("▨",11f,Modifier.alignBy(MathAxis),tint=c.muted)
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
                    GraphRemoveButton((if(isKorean())"음영 삭제" else "Delete shading")+": ${index+1}") {onRemove(index,true)}
                }
            }
        }
    }
}

@Composable private fun RowScope.GraphRemoveButton(label:String,onRemove:()->Unit) {
    MathText("×",14f,
        modifier=Modifier.alignBy(MathAxis)
        .clickable(role=Role.Button,onClick=onRemove)
        .semantics {contentDescription=label}
        .padding(horizontal=5.dp,vertical=3.dp),
        tint=LocalInstrument.current.muted)
}
