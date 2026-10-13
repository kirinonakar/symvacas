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
import org.json.JSONObject
import java.util.Locale
import kotlin.math.roundToInt

@Composable internal fun StatisticsTimeSeriesPlot(plot:JSONObject) {
    val c=LocalInstrument.current
    val acf=plot.getString("kind")=="acf"
    val title=tr(plot.getString("title"))
    fun points(key:String):List<List<Double>> {
        val array=plot.optJSONArray(key) ?: return emptyList()
        return List(array.length()){i->val row=array.getJSONArray(i);List(row.length()){row.getDouble(it)}}
    }
    val series=if(acf)emptyList() else listOf(points("observed"),points("fitted"),points("forecast"))
    val band=points("interval")
    val values=plot.optJSONArray("values")?.let {a->List(a.length()){a.getDouble(it)}}.orEmpty()
    val bound=plot.optDouble("bound",0.0)
    val all=series.flatten()+band.flatMap {listOf(listOf(it[0],it[1]),listOf(it[0],it[2]))}
    val reference=plot.optDouble("reference",Double.NaN)
    val lo=if(acf)minOf(-1.0,-bound*1.1) else (all.map {it[1]}+listOfNotNull(reference.takeIf(Double::isFinite))).minOrNull() ?: 0.0
    val hi=if(acf)maxOf(1.0,bound*1.1) else (all.map {it[1]}+listOfNotNull(reference.takeIf(Double::isFinite))).maxOrNull() ?: 1.0
    val pad=if(acf)0.0 else ((hi-lo).takeIf {it>0} ?: 1.0)*.1
    val xmin=if(acf).5 else all.minOfOrNull {it[0]} ?: 1.0
    val xmax=if(acf)values.size+.5 else (all.maxOfOrNull {it[0]} ?: 2.0)+.5
    val timeLabels=plot.optJSONArray("timeTickLabels") ?: plot.optJSONArray("timeLabels")
    val xlabel=tr(if(acf)"Lag" else if(timeLabels!=null)"Date" else "Time index")
    val ylabel=tr(if(acf)"Autocorrelation" else "Value")
    val exports=remember {GraphExportState()}
    val colors=listOf(c.accent,c.muted,c.curves[1%c.curves.size])
    Column(Modifier.fillMaxWidth(),verticalArrangement=Arrangement.spacedBy(6.dp)) {
        Text(title,fontSize=14.sp,color=c.ink)
        ExportableGraphCanvas(Modifier.fillMaxWidth().height(310.dp).background(c.display).semantics {contentDescription=title},c.display,exports) {
            val left=60.dp.toPx();val top=26.dp.toPx();val w=size.width-left-18.dp.toPx();val h=size.height-top-50.dp.toPx()
            fun px(x:Double)=left+((x-xmin)/(xmax-xmin)).toFloat()*w
            fun py(y:Double)=top+h-((y-lo+pad)/(hi-lo+2*pad)).toFloat()*h
            val paint=Paint(Paint.ANTI_ALIAS_FLAG).apply {color=c.muted.toArgb();textSize=10.sp.toPx()}
            fun number(v:Double)=String.format(Locale.ROOT,"%.4g",v)
            fun label(x:Float,y:Float,text:String,align:Paint.Align=Paint.Align.CENTER){paint.textAlign=align;drawContext.canvas.nativeCanvas.drawText(text,x,y,paint)}
            for(i in 0..4){
                val y=lo-pad+(hi-lo+2*pad)*i/4;val x=xmin+(xmax-xmin)*i/4
                drawLine(c.grid,Offset(left,py(y)),Offset(left+w,py(y)))
                label(left-5.dp.toPx(),py(y)+4.dp.toPx(),number(y),Paint.Align.RIGHT)
                if(timeLabels==null)label(px(x),top+h+17.dp.toPx(),number(x))
            }
            if(timeLabels!=null){
                val count=if(size.width<460.dp.toPx())2 else 4
                (0..count).map {(xmin+(xmax-.5-xmin)*it/count).roundToInt()}.distinct().forEach {x->label(px(x.toDouble()),top+h+17.dp.toPx(),timeLabels.optString(x-1,x.toString()))}
            }
            val dashed=PathEffect.dashPathEffect(floatArrayOf(5.dp.toPx(),4.dp.toPx()))
            fun horizontal(y:Double)=drawLine(c.muted,Offset(left,py(y)),Offset(left+w,py(y)),pathEffect=dashed)
            if(acf){
                horizontal(-bound);horizontal(bound)
                drawLine(c.muted,Offset(left,py(0.0)),Offset(left+w,py(0.0)))
                values.forEachIndexed {i,y->drawLine(c.accent,Offset(px(i+1.0),py(0.0)),Offset(px(i+1.0),py(y)),2.dp.toPx())}
            } else {
                if(reference.isFinite())horizontal(reference)
                if(band.isNotEmpty()){
                    val polygon=Path();val outline=band.map {listOf(it[0],it[2])}+band.reversed().map {listOf(it[0],it[1])}
                    outline.forEachIndexed {i,row->if(i==0)polygon.moveTo(px(row[0]),py(row[1])) else polygon.lineTo(px(row[0]),py(row[1]))};polygon.close()
                    drawPath(polygon,colors[2].copy(alpha=.18f))
                    if(band.size==1)drawLine(colors[2],Offset(px(band[0][0]),py(band[0][1])),Offset(px(band[0][0]),py(band[0][2])),3.dp.toPx())
                }
                val boundary=plot.optDouble("boundary",Double.NaN)
                if(boundary.isFinite())drawLine(c.muted,Offset(px(boundary),top),Offset(px(boundary),top+h),pathEffect=dashed)
                series.forEachIndexed {index,rows->
                    val path=Path();rows.forEachIndexed {i,row->if(i==0)path.moveTo(px(row[0]),py(row[1])) else path.lineTo(px(row[0]),py(row[1]))}
                    drawPath(path,colors[index],style=Stroke(if(index==1)1.5.dp.toPx() else 2.5.dp.toPx(),pathEffect=if(index==1)dashed else null))
                }
            }
            label(left,15.dp.toPx(),ylabel,Paint.Align.LEFT);label(left+w/2,size.height-6.dp.toPx(),xlabel)
        }
        if(!acf&&series[2].isNotEmpty()){
            Row(horizontalArrangement=Arrangement.spacedBy(12.dp)){listOf("Observed","Fitted","Forecast").forEachIndexed {i,name->Text("● ${tr(name)}",fontSize=11.sp,color=colors[i])}}
            Text("${String.format(Locale.ROOT,"%.4g",plot.getDouble("level")*100)}% ${tr("Prediction interval")}",fontSize=11.sp,color=c.muted)
        }
        plot.optString("caption").takeIf {it.isNotBlank()}?.let {StatisticsExplanation("Plot details",tr(it),"statistics-timeseries-plot-help",plot)}
        PlotExportActions(exports,"symvacas-${plot.getString("kind")}")
    }
}
