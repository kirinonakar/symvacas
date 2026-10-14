package com.kirinonakar.symvacas.ui

import android.graphics.Paint
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.kirinonakar.symvacas.ui.theme.LocalInstrument
import org.json.JSONArray
import org.json.JSONObject
import java.util.Locale

internal data class ResearchPlotBounds(val xmin:Double,val xmax:Double,val ymin:Double,val ymax:Double)

/** Forest pages keep all studies reachable and repeat the pooled interval. */
internal fun statisticsIntervalPage(plot:JSONObject,page:Int,pageSize:Int=40):JSONObject {
    val rows=plot.optJSONArray("rows") ?: return plot
    if(!plot.has("summaryIndex")||rows.length()<=pageSize+1)return plot
    val summary=plot.getInt("summaryIndex");val studies=(0 until rows.length()).filter {it!=summary}
    val at=page.coerceIn(0,(studies.size-1)/pageSize)
    val indices=studies.drop(at*pageSize).take(pageSize)+summary
    return JSONObject().apply {
        plot.keys().forEach {key->put(key,plot.get(key))}
        put("rows",JSONArray().apply {indices.forEach {put(rows.getJSONArray(it))}})
        put("weights",JSONArray().apply {indices.forEach {put(plot.optJSONArray("weights")?.optDouble(it,0.0) ?: 0.0)}})
        put("summaryIndex",indices.size-1)
    }
}

internal fun researchPlotBounds(points:List<Pair<Double,Double>>,lines:List<List<Pair<Double,Double>>>,horizontal:List<Double>,invertY:Boolean):ResearchPlotBounds {
    val all=points+lines.flatten();val xs=all.map {it.first};val ys=all.map {it.second}+horizontal
    val lo=xs.minOrNull() ?: 0.0;val hi=xs.maxOrNull() ?: 1.0
    val low=ys.minOrNull() ?: 0.0;val high=ys.maxOrNull() ?: 1.0
    val dx=(hi-lo).takeIf {it>0}?.times(.1) ?: .1;val dy=(high-low).takeIf {it>0}?.times(.1) ?: .1
    return ResearchPlotBounds(lo-dx,hi+dx,if(invertY)0.0 else low-dy,high+dy)
}

@Composable internal fun StatisticsResearchPlot(plot:JSONObject) {
    val c=LocalInstrument.current;val title=tr(plot.getString("title"));val exports=remember {GraphExportState()}
    fun points(array:JSONArray)=List(array.length()){i->val row=array.getJSONArray(i);row.getDouble(0) to row.getDouble(1)}
    val observations=points(plot.getJSONArray("points"));val rawLines=plot.optJSONArray("lines")
    val lines=List(rawLines?.length() ?: 0){points(rawLines!!.getJSONArray(it))}
    val rawHorizontal=plot.optJSONArray("horizontal");val horizontal=List(rawHorizontal?.length() ?: 0){rawHorizontal!!.getDouble(it)}
    val invertY=plot.optBoolean("invertY");val bounds=researchPlotBounds(observations,lines,horizontal,invertY)
    val xlabel=tr(plot.getString("xlabel"));val ylabel=tr(plot.getString("ylabel"))
    Column(Modifier.fillMaxWidth(),verticalArrangement=Arrangement.spacedBy(6.dp)) {
        Text(title,fontSize=14.sp,color=c.ink)
        ExportableGraphCanvas(Modifier.fillMaxWidth().height(300.dp).background(c.display).semantics {contentDescription="$title: $xlabel, $ylabel"},c.display,exports) {
            val left=64.dp.toPx();val top=26.dp.toPx();val w=size.width-left-18.dp.toPx();val h=size.height-top-54.dp.toPx()
            fun px(value:Double)=left+((value-bounds.xmin)/(bounds.xmax-bounds.xmin)).toFloat()*w
            fun py(value:Double)=top+(if(invertY)0f else h)+(if(invertY)1 else -1)*((value-bounds.ymin)/(bounds.ymax-bounds.ymin)).toFloat()*h
            val paint=Paint(Paint.ANTI_ALIAS_FLAG).apply {color=c.muted.toArgb();textSize=10.sp.toPx()}
            fun label(x:Float,y:Float,value:String,align:Paint.Align=Paint.Align.CENTER){paint.textAlign=align;drawContext.canvas.nativeCanvas.drawText(value,x,y,paint)}
            fun number(value:Double)=String.format(Locale.ROOT,"%.4g",value)
            for(i in 0..4) {
                val x=bounds.xmin+(bounds.xmax-bounds.xmin)*i/4;val y=bounds.ymin+(bounds.ymax-bounds.ymin)*i/4
                drawLine(c.grid,Offset(left,py(y)),Offset(left+w,py(y)));label(left-5.dp.toPx(),py(y)+4.dp.toPx(),number(y),Paint.Align.RIGHT)
                label(px(x),top+h+17.dp.toPx(),number(x))
            }
            val dashed=PathEffect.dashPathEffect(floatArrayOf(5.dp.toPx(),4.dp.toPx()))
            for(line in lines) {
                val path=Path();line.forEachIndexed {index,(x,y)->if(index==0)path.moveTo(px(x),py(y)) else path.lineTo(px(x),py(y))}
                drawPath(path,c.muted,style=Stroke(1.5.dp.toPx(),pathEffect=dashed))
            }
            horizontal.forEachIndexed {index,value->drawLine(if(index==0)c.danger else c.muted,Offset(left,py(value)),Offset(left+w,py(value)),1.5.dp.toPx(),pathEffect=if(index==0)null else dashed)}
            observations.forEach {(x,y)->drawCircle(c.accent.copy(alpha=.8f),3.dp.toPx(),Offset(px(x),py(y)))}
            label(left,16.dp.toPx(),ylabel,Paint.Align.LEFT);label(left+w/2,size.height-8.dp.toPx(),xlabel)
        }
        if(plot.has("caption"))StatisticsExplanation("Plot details",tr(plot.getString("caption")),"statistics-research-plot-help",plot)
        PlotExportActions(exports,"symvacas-${plot.getString("title").lowercase().replace(' ','-')}")
    }
}
