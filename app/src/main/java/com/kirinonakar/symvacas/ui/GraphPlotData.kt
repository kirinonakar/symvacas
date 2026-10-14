package com.kirinonakar.symvacas.ui

import androidx.compose.runtime.*
import com.kirinonakar.symvacas.calculator.CalculatorModel

// Decode immutable plot/analysis snapshots once per engine result.
internal typealias GraphPoint = Pair<Double,Double>
internal typealias GraphCurve = List<GraphPoint?>
internal typealias GraphShadingGeometry = Pair<List<List<GraphPoint>>,List<GraphCurve>>
internal data class GraphPlotData(
    val allCurves:List<GraphCurve>,val curves:List<GraphCurve>,val derivativeIndex:Int,val secondDerivativeIndex:Int,
    val derivativeSelected:Int?,val derivativeCurve:GraphCurve?,val derivativeExpression:String,
    val secondDerivativeSelected:Int?,val secondDerivativeCurve:GraphCurve?,val secondDerivativeExpression:String,
    val integralFill:List<List<GraphPoint>>,val shadings:List<GraphShadingGeometry>,val tangent:List<GraphPoint>?,
    val asymptoteLines:List<List<GraphPoint>>,val markers:List<GraphPoint>
)

@Composable internal fun rememberGraphPlotData(m:CalculatorModel):GraphPlotData {
    val allCurves=remember(m.graphData) {
        val array=m.graphData?.optJSONArray("curves")
        (0 until (array?.length() ?: 0)).map { ci->val curve=array!!.getJSONArray(ci); (0 until curve.length()).map { k->curve.optJSONArray(k)?.let { it.getDouble(0) to it.getDouble(1) } } }
    }
    val derivativeIndex=m.graphData?.optInt("derivativeCurveIndex",-1) ?: -1
    val secondDerivativeIndex=m.graphData?.optInt("secondDerivativeCurveIndex",-1) ?: -1
    val curves=allCurves.filterIndexed {index,_->index!=derivativeIndex && index!=secondDerivativeIndex}.mapIndexed {index,curve->if(m.isGraphVisible(index))curve else emptyList()}
    val derivativeSelected=m.graphDerivativeSelected
    val derivativeCurve=allCurves.getOrNull(derivativeIndex)?.takeIf {derivativeSelected==m.graphData?.optInt("derivativeSelected",-1)}
    val derivativeExpression=if(derivativeCurve!=null)m.graphData?.optString("derivativeExpression").orEmpty() else ""
    val secondDerivativeSelected=m.graphSecondDerivativeSelected
    val secondDerivativeCurve=allCurves.getOrNull(secondDerivativeIndex)?.takeIf {secondDerivativeSelected==m.graphData?.optInt("secondDerivativeSelected",-1)}
    val secondDerivativeExpression=if(secondDerivativeCurve!=null)m.graphData?.optString("secondDerivativeExpression").orEmpty() else ""
    val integralFill=remember(m.graphAnalysis) {
        val polygons=m.graphAnalysis?.optJSONArray("integralFill")
        (0 until (polygons?.length() ?: 0)).map {index->
            val polygon=polygons!!.getJSONArray(index)
            (0 until polygon.length()).mapNotNull {i->polygon.optJSONArray(i)?.let {it.getDouble(0) to it.getDouble(1)}}
        }
    }
    val shadings=remember(m.graphData,m.graphState.hiddenGraphKeys,m.graphSource,m.graphKind) {
        val array=m.graphData?.optJSONArray("shadings")
        (0 until (array?.length() ?: 0)).mapNotNull { index->
            val entry=array?.optJSONObject(index) ?: return@mapNotNull null
            if(if(entry.has("sourceIndex"))!m.isGraphVisible(entry.getInt("sourceIndex")) else !m.isGraphVisible(entry.optInt("shadeIndex",index),"shade"))return@mapNotNull emptyList<List<GraphPoint>>() to emptyList<GraphCurve>()
            val fillArray=entry.optJSONArray("fill")
            val fill=(0 until (fillArray?.length() ?: 0)).map { fi->
                val polygon=fillArray!!.optJSONArray(fi)
                (0 until (polygon?.length() ?: 0)).mapNotNull { k->polygon?.optJSONArray(k)?.let {it.getDouble(0) to it.getDouble(1)} }
            }
            val boundaryArray=entry.optJSONArray("boundary")
            val boundary=(0 until (boundaryArray?.length() ?: 0)).map { bi->
                val line=boundaryArray!!.optJSONArray(bi)
                (0 until (line?.length() ?: 0)).map { k->line?.optJSONArray(k)?.let {it.getDouble(0) to it.getDouble(1)} }
            }
            fill to boundary
        }
    }
    val tangent=remember(m.graphAnalysis) {
        val line=m.graphAnalysis?.optJSONArray("line")
        if(line==null||line.length()!=2)null else listOfNotNull(line.optJSONArray(0)?.let {it.getDouble(0) to it.getDouble(1)},line.optJSONArray(1)?.let {it.getDouble(0) to it.getDouble(1)}).takeIf {it.size==2}
    }
    val asymptoteLines=remember(m.graphAnalysis) {
        val lines=m.graphAnalysis?.optJSONArray("lines")
        (0 until (lines?.length() ?: 0)).mapNotNull {index->
            val line=lines?.optJSONArray(index)
            if(line==null||line.length()!=2)null else listOfNotNull(line.optJSONArray(0)?.let {it.getDouble(0) to it.getDouble(1)},line.optJSONArray(1)?.let {it.getDouble(0) to it.getDouble(1)}).takeIf {it.size==2}
        }
    }
    val markers=remember(m.graphAnalysis) {
        val array=m.graphAnalysis?.optJSONArray("points")
        (0 until (array?.length() ?: 0)).mapNotNull {i->array?.optJSONArray(i)?.let {it.getDouble(0) to it.getDouble(1)}}
    }
    return GraphPlotData(allCurves,curves,derivativeIndex,secondDerivativeIndex,derivativeSelected,derivativeCurve,derivativeExpression,secondDerivativeSelected,secondDerivativeCurve,secondDerivativeExpression,integralFill,shadings,tangent,asymptoteLines,markers)
}
