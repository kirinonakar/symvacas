package com.kirinonakar.symvacas.ui

import android.graphics.Paint
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.*
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.unit.*
import com.kirinonakar.symvacas.ui.theme.LocalInstrument
import java.time.LocalDate
import kotlin.math.ceil
import kotlin.math.floor
import kotlin.math.max
import kotlin.math.roundToLong
import kotlin.math.abs

@Composable internal fun StatisticsPlot(type:String,points:List<Pair<Double,Double>>,values:List<Double>,secondary:List<Double> = emptyList(),curve:List<Pair<Double,Double>> = emptyList(),fitLabel:String="",displayDigits:Int=10,showCorrelation:Boolean=false,correlation:Double?=null,tertiary:List<Double> = emptyList(),xDateOrigin:LocalDate?=null,xAxisLabel:String="x",yAxisLabel:String="y",fitPrefix:String="y ≈ ",fitVariables:Map<String,String> = emptyMap(),allColumns:List<Pair<String,List<Double>>>? = null,orientation:String="horizontal",namedBars:StatisticsNamedBarData?=null,histogramKde:Boolean=false,scatterSeries:List<StatisticsScatterSeries>?=null) {
    val c=LocalInstrument.current
    val exports=remember {GraphExportState()}
    val series=if(type=="Bar"&&namedBars!=null)namedBars.series.mapIndexed {index,entry->Triple(entry.label,entry.values.filterNotNull(),c.curves[index%c.curves.size])} else if(allColumns!=null)allColumns.mapIndexed {index,(name,observations)->Triple(name,observations,c.curves[index%c.curves.size])}.filter {it.second.isNotEmpty()} else (if(secondary.isEmpty()&&tertiary.isEmpty())listOf(Triple("",values,c.accent)) else listOf(Triple("x",values,c.accent),Triple("y",secondary,c.danger),Triple("z",tertiary,c.curves[2]))).filter {it.second.isNotEmpty()}
    val fitEquation=remember(fitLabel,displayDigits,fitVariables) {if(fitLabel.isBlank())null else regressionFormulaDisplayTree(fitLabel,displayDigits,fitVariables)}
    val densities=remember(type,series.map {it.second}) {if(type=="Violin + points")series.map {violinDensity(it.second)} else emptyList()}
    val frequencies=remember(type,namedBars,series.map {it.second}) {if(type=="Bar"&&namedBars==null)statisticsFrequencyData(series.map {it.second}) else null}
    val histogram=remember(type,histogramKde,series.map {it.second}) {if(type=="Histogram")statisticsHistogramData(series.map {it.second},histogramKde) else null}
    val densityLabel=tr("Density");val kdeUnavailable=tr("KDE unavailable for this series")
    fun seriesCaption(index:Int)=if(type=="Bar"&&namedBars!=null)series[index].first else "${series[index].first.ifBlank {"value"}} (n=${series[index].second.size})"+(if(type=="Histogram"&&histogramKde)" · KDE" else "")+(if(histogram?.unavailable?.contains(index)==true)" · $kdeUnavailable" else "")
    val scatterLegend=if(type=="Scatter")scatterSeries.orEmpty().mapIndexed {index,entry->"${entry.label} (n=${entry.points.size})" to c.curves[index%c.curves.size]} else emptyList()
    val exportLabels=if(type=="Scatter")scatterLegend+(if(fitLabel.isNotBlank())listOf((fitPrefix+fitLabel) to c.danger) else emptyList()) else if(type in listOf("Histogram","Bar"))series.mapIndexed {index,entry->seriesCaption(index) to entry.third}
        else if(type=="Scatter"&&fitLabel.isNotBlank())listOf((fitPrefix+fitLabel) to c.danger) else emptyList()

    val countLabel=tr("Count");val valueLabel=tr("Value")
    val namedValueLabel=tr(namedBars?.valueLabel ?: "Value");val namedCategoryLabel=tr(namedBars?.categoryLabel ?: "x")
    val distribution=type in listOf("Box plot","Violin + points")
    val vertical=distribution&&orientation=="vertical"
    val swarmCache=remember(series.map {it.second},vertical) {mutableMapOf<Int,Pair<Triple<List<Double>,Double,Double>,StatisticsBeeswarm>>()}
    BoxWithConstraints(Modifier.fillMaxWidth()) {
    val chartWidth=if(vertical)maxOf(maxWidth,(series.size*70+82).dp) else if(namedBars!=null)maxOf(maxWidth,(namedBars.labels.size*54+76).dp) else maxWidth
    Box(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState())) {
    ExportableGraphCanvas(Modifier.width(chartWidth).height(if(vertical)300.dp else if(distribution)(series.size*70+70).coerceAtLeast(220).dp else 220.dp).background(c.display),c.display,exports,
        exportFooterHeight=if(exportLabels.isEmpty())0.dp else (exportLabels.size*18+6).dp,exportFooter={
            val paint=Paint(Paint.ANTI_ALIAS_FLAG).apply {textSize=11.sp.toPx()}
            exportLabels.forEachIndexed {index,(label,color)->paint.color=color.toArgb();drawContext.canvas.nativeCanvas.drawText(label,8.dp.toPx(),(index*18+16).dp.toPx(),paint)}
        }) {
        val left=(if(vertical)70 else if(type=="Histogram"&&histogramKde)80 else if(type in listOf("Bar","Histogram"))56 else 38).dp.toPx();val right=12.dp.toPx();val top=14.dp.toPx();val bottom=(if(vertical)48 else if(namedBars!=null)56 else if(type=="Scatter")46 else if(type=="Bar")42 else 28).dp.toPx()
        val width=size.width-left-right;val height=size.height-top-bottom
        val text=Paint(Paint.ANTI_ALIAS_FLAG).apply {color=c.muted.toArgb();textSize=10.sp.toPx()}
        drawLine(c.grid,Offset(left,top+height),Offset(left+width,top+height),1.dp.toPx())
        drawLine(c.grid,Offset(left,top),Offset(left,top+height),1.dp.toPx())
        if(type=="Scatter") {
            if(points.isEmpty())return@ExportableGraphCanvas
            val range=if(curve.isEmpty())points else points+curve
            var x0=range.minOf {it.first};var x1=range.maxOf {it.first};var y0=range.minOf {it.second};var y1=range.maxOf {it.second}
            if(x0==x1){x0-=1;x1+=1};if(y0==y1){y0-=1;y1+=1}
            fun px(x:Double)=left+((x-x0)/(x1-x0)).toFloat()*width
            fun py(y:Double)=top+height-((y-y0)/(y1-y0)).toFloat()*height
            if(curve.size>1) {
                val path=androidx.compose.ui.graphics.Path()
                curve.forEachIndexed {index,point->val at=Offset(px(point.first),py(point.second));if(index==0)path.moveTo(at.x,at.y) else path.lineTo(at.x,at.y)}
                drawPath(path,c.danger,style=Stroke(2.dp.toPx()))
            }
            if(scatterSeries==null)points.forEach {drawCircle(c.accent,4.dp.toPx(),Offset(px(it.first),py(it.second)))}
            else scatterSeries.forEachIndexed {index,entry->entry.points.forEach {drawCircle(c.curves[index%c.curves.size],4.dp.toPx(),Offset(px(it.first),py(it.second)))}}
            if(xDateOrigin==null)drawContext.canvas.nativeCanvas.drawText(xAxisLabel,left+width-text.measureText(xAxisLabel),top+height+36.dp.toPx(),text)
            drawContext.canvas.nativeCanvas.drawText(yAxisLabel,5.dp.toPx(),top+12.dp.toPx(),text)
            val firstTick=xDateOrigin?.let {origin->runCatching {origin.plusDays(x0.roundToLong()).toString()}.getOrNull()} ?: "%.4g".format(x0)
            val lastTick=xDateOrigin?.let {origin->runCatching {origin.plusDays(x1.roundToLong()).toString()}.getOrNull()} ?: "%.4g".format(x1)
            drawContext.canvas.nativeCanvas.drawText(firstTick,left,top+height+16.dp.toPx(),text)
            drawContext.canvas.nativeCanvas.drawText(lastTick,left+width-text.measureText(lastTick),top+height+16.dp.toPx(),text)
        } else if(series.isEmpty()) {
            drawContext.canvas.nativeCanvas.drawText("Add finite numeric observations to plot",left,top+20.dp.toPx(),text)
        } else if(type=="Bar"&&namedBars!=null) {
            val data=namedBars;val scale=maxOf(abs(data.minimum),abs(data.maximum)).takeIf {it>0} ?: 1.0
            val baseline=top+height*data.baseline.toFloat()
            for(i in 0..(if(data.minimum==data.maximum)0 else 4)) {
                val fraction=if(data.minimum==data.maximum)1.0 else i/4.0
                val value=(data.maximum/scale*(1-fraction)+data.minimum/scale*fraction)*scale;val y=top+height*fraction.toFloat()
                drawLine(c.grid,Offset(left,y),Offset(left+width,y),1.dp.toPx())
                val label=graphDisplayNumber(value,displayDigits)
                drawContext.canvas.nativeCanvas.drawText(label,left-text.measureText(label)-5.dp.toPx(),y+3.dp.toPx(),text)
            }
            drawLine(c.muted,Offset(left,baseline),Offset(left+width,baseline),1.dp.toPx())
            val slotWidth=width/data.labels.size;val groupWidth=slotWidth*.75f;val lane=groupWidth/data.series.size
            data.labels.forEachIndexed {index,name->
                val center=left+(index+.5f)*slotWidth;var label=name
                while(label.length>1&&text.measureText(label)>slotWidth-4.dp.toPx())label=label.dropLast(1)
                if(label!=name)label=label.dropLast(1)+"…"
                drawContext.canvas.nativeCanvas.drawText(label,center-text.measureText(label)/2,top+height+30.dp.toPx(),text)
                data.series.forEachIndexed {seriesIndex,entry->
                    val value=entry.values[index];val position=data.positions[seriesIndex][index]
                    if(value!=null&&position!=null) {
                        val y=top+height*position.toFloat();val x=center-groupWidth/2+seriesIndex*lane
                        drawRect(series[seriesIndex].third.copy(alpha=.78f),Offset(x+lane*.05f,minOf(y,baseline)),androidx.compose.ui.geometry.Size(lane*.9f,abs(y-baseline)))
                        val valueText=graphDisplayNumber(value,displayDigits)
                        drawContext.canvas.nativeCanvas.drawText(valueText,x+lane/2-text.measureText(valueText)/2,y+(if(value<0)12 else -3).dp.toPx(),text)
                    }
                }
            }
            drawContext.canvas.nativeCanvas.drawText(namedCategoryLabel,left+width-text.measureText(namedCategoryLabel),top+height+49.dp.toPx(),text)
            val canvas=drawContext.canvas.nativeCanvas
            canvas.save();canvas.rotate(-90f,14.dp.toPx(),top+height/2)
            canvas.drawText(namedValueLabel,14.dp.toPx()-text.measureText(namedValueLabel)/2,top+height/2,text);canvas.restore()
        } else if(type=="Bar") {
            val data=frequencies ?: return@ExportableGraphCanvas
            if(data.values.isEmpty())return@ExportableGraphCanvas
            val step=ceil(data.peak/4.0).toInt().coerceAtLeast(1)
            ((0..data.peak step step).toSet()+data.peak).sorted().forEach {count->
                val y=top+height-height*count/data.peak
                drawLine(c.grid,Offset(left,y),Offset(left+width,y),1.dp.toPx())
                val label=count.toString()
                drawContext.canvas.nativeCanvas.drawText(label,left-text.measureText(label)-5.dp.toPx(),y+3.dp.toPx(),text)
            }
            val groupWidth=maxOf(width*data.barWidth.toFloat(),series.size*.75.dp.toPx());val lane=groupWidth/series.size
            data.values.forEachIndexed {index,value->
                val center=left+width*data.positions[index].toFloat()
                if(data.values.size<=10||index==0||index==data.values.lastIndex||index%ceil(data.values.size/8.0).toInt()==0) {
                    val label=graphDisplayNumber(value,displayDigits)
                    drawContext.canvas.nativeCanvas.drawText(label,center-text.measureText(label)/2,top+height+16.dp.toPx(),text)
                }
                data.counts.forEachIndexed {seriesIndex,counts->
                    val count=counts[index]
                    if(count>0) {
                        val h=height*count/data.peak;val x=center-groupWidth/2+seriesIndex*lane
                        drawRect(series[seriesIndex].third.copy(alpha=.78f),Offset(x+lane*.05f,top+height-h),androidx.compose.ui.geometry.Size(lane*.9f,h))
                        val label=count.toString()
                        drawContext.canvas.nativeCanvas.drawText(label,x+lane/2-text.measureText(label)/2,top+height-h-3.dp.toPx(),text)
                    }
                }
            }
            drawContext.canvas.nativeCanvas.drawText(valueLabel,left+width-text.measureText(valueLabel),top+height+35.dp.toPx(),text)
            val canvas=drawContext.canvas.nativeCanvas
            canvas.save();canvas.rotate(-90f,14.dp.toPx(),top+height/2)
            canvas.drawText(countLabel,14.dp.toPx()-text.measureText(countLabel)/2,top+height/2,text);canvas.restore()
        } else if(type=="Histogram") {
            val data=histogram ?: return@ExportableGraphCanvas;val peak=data.peak*(if(histogramKde)1.08 else 1.0)
            fun px(value:Double)=left+((value-data.viewMinimum)/(data.viewMaximum-data.viewMinimum)).toFloat()*width
            fun py(value:Double)=top+height-(value/peak).toFloat()*height
            for(i in 0..4) {
                val value=peak*i/4;val y=py(value)
                drawLine(c.grid,Offset(left,y),Offset(left+width,y),1.dp.toPx())
                val label=if(histogramKde)java.math.BigDecimal(histogramDensityNumber(value,data)).round(java.math.MathContext(4)).stripTrailingZeros().toString().replace("E","e") else graphDisplayNumber(value,displayDigits)
                drawContext.canvas.nativeCanvas.drawText(label,left-text.measureText(label)-5.dp.toPx(),y+3.dp.toPx(),text)
                val position=data.viewMinimum+(data.viewMaximum-data.viewMinimum)*i/4.0
                val tick=graphDisplayNumber((data.minimum+position*data.span)*data.scale,displayDigits)
                drawContext.canvas.nativeCanvas.drawText(tick,px(position)-text.measureText(tick)/2,top+height+16.dp.toPx(),text)
            }
            data.heights.forEachIndexed {seriesIndex,buckets->buckets.forEachIndexed {index,value->
                val start=px(index.toDouble()/data.bins);val end=px((index+1.0)/data.bins);val bar=end-start;val lane=bar/series.size
                val x=if(histogramKde)start else start+lane*seriesIndex
                val w=if(histogramKde)bar else (lane-1.dp.toPx()).coerceAtLeast(1f)
                drawRect(series[seriesIndex].third.copy(alpha=if(histogramKde).25f else .78f),Offset(x,py(value)),androidx.compose.ui.geometry.Size(w,top+height-py(value)))
            }}
            data.curves.forEachIndexed {index,points->
                if(points.isNotEmpty()) {
                    val path=androidx.compose.ui.graphics.Path()
                    points.forEachIndexed {i,(at,density)->if(i==0)path.moveTo(px(at),py(density)) else path.lineTo(px(at),py(density))}
                    drawPath(path,series[index].third,style=Stroke(2.dp.toPx()))
                }
            }
            val axisLabel=if(histogramKde)densityLabel else countLabel
            drawContext.canvas.nativeCanvas.drawText(axisLabel,left,top-3.dp.toPx(),text)
        } else if(distribution) {
            val all=series.flatMap {it.second};val scale=all.maxOf {abs(it)}.takeIf {it>0} ?: 1.0
            val lo=all.min();val hi=all.max();val span=hi/scale-lo/scale
            fun fraction(value:Double)=if(span==0.0).5f else ((value/scale-lo/scale)/span).toFloat()
            fun position(value:Double,index:Int,offset:Float=0f):Offset=if(vertical)Offset(left+width*(index+.5f)/series.size+offset,top+height*(1-fraction(value))) else Offset(left+width*fraction(value),top+height*(index+.5f)/series.size+offset)
            fun quantile(data:List<Double>,p:Double):Double {val at=(data.size-1)*p;val low=floor(at).toInt();val high=ceil(at).toInt();val f=at-low;return data[low]*(1-f)+data[high]*f}
            series.forEachIndexed {index,entry->
                val half=minOf(23.dp.toPx(),(if(vertical)width else height)/series.size*.35f)
                val density=if(type=="Violin + points")densities[index] else emptyList()
                if(type=="Box plot") {
                    val sorted=entry.second.sorted();val low=sorted.first();val q1=quantile(sorted,.25);val median=quantile(sorted,.5);val q3=quantile(sorted,.75);val high=sorted.last()
                    drawLine(c.muted,position(low,index),position(high,index),2.dp.toPx())
                    for(value in listOf(low,high))drawLine(c.muted,position(value,index,-half*.6f),position(value,index,half*.6f),2.dp.toPx())
                    val a=position(q1,index,-half);val b=position(q3,index,half)
                    val origin=Offset(minOf(a.x,b.x),minOf(a.y,b.y));val boxSize=androidx.compose.ui.geometry.Size(abs(b.x-a.x).coerceAtLeast(1f),abs(b.y-a.y).coerceAtLeast(1f))
                    drawRect(entry.third.copy(alpha=.24f),origin,boxSize);drawRect(entry.third,origin,boxSize,style=Stroke(1.5.dp.toPx()))
                    drawLine(c.danger,position(median,index,-half),position(median,index,half),2.dp.toPx())
                    val at=position(median,index,half+12.dp.toPx());val label="%.4g".format(java.util.Locale.US,median)
                    drawContext.canvas.nativeCanvas.drawText(label,if(vertical)at.x else at.x-text.measureText(label)/2,at.y+3.dp.toPx(),text)
                } else if(density.isNotEmpty()) {
                    val path=androidx.compose.ui.graphics.Path()
                    density.forEachIndexed {i,(value,fraction)->val at=position(value,index,-fraction.toFloat()*half);if(i==0)path.moveTo(at.x,at.y) else path.lineTo(at.x,at.y)}
                    density.asReversed().forEach {(value,fraction)->val at=position(value,index,fraction.toFloat()*half);path.lineTo(at.x,at.y)}
                    path.close();drawPath(path,entry.third.copy(alpha=.24f));drawPath(path,entry.third,style=Stroke(1.dp.toPx()))
                }
                if(type=="Violin + points") {
                    val axes=entry.second.map {value->val at=position(value,index);(if(vertical)at.y else at.x).toDouble()}
                    val key=Triple(axes,2.5.dp.toPx().toDouble(),half.toDouble())
                    val cached=swarmCache[index]
                    val swarm=if(cached?.first==key)cached.second else beeswarmLayout(axes,key.second,key.third).also {swarmCache[index]=key to it}
                    entry.second.forEachIndexed {i,value->
                        drawCircle(entry.third.copy(alpha=.75f),swarm.radius.toFloat(),position(value,index,swarm.offsets[i].toFloat()))
                    }
                }
                val label="${entry.first.ifBlank {"value"}} (n=${entry.second.size})"
                if(vertical) {
                    val center=left+width*(index+.5f)/series.size
                    var shown=entry.first.ifBlank {"value"};val available=width/series.size-4.dp.toPx()
                    while(shown.length>1&&text.measureText(shown)>available)shown=shown.dropLast(1)
                    if(shown!=entry.first.ifBlank {"value"})shown=shown.dropLast(1)+"…"
                    drawContext.canvas.nativeCanvas.drawText(shown,center-text.measureText(shown)/2,top+height+17.dp.toPx(),text)
                    val count="n=${entry.second.size}";drawContext.canvas.nativeCanvas.drawText(count,center-text.measureText(count)/2,top+height+32.dp.toPx(),text)
                } else drawContext.canvas.nativeCanvas.drawText(label,left,top+height*(index+.5f)/series.size-half-4.dp.toPx(),text)
            }
            for(index in 0..(if(span==0.0)0 else 4)) {
                val fraction=if(span==0.0).5 else index/4.0
                val value=(lo/scale*(1-fraction)+hi/scale*fraction)*scale
                val label="%.4g".format(java.util.Locale.US,value)
                val at=(left+fraction.toFloat()*width-text.measureText(label)/2).coerceIn(0f,(size.width-text.measureText(label)).coerceAtLeast(0f))
                drawContext.canvas.nativeCanvas.drawText(label,if(vertical)left-text.measureText(label)-6.dp.toPx() else at,if(vertical)top+height*(1-fraction.toFloat())+3.dp.toPx() else top+height+16.dp.toPx(),text)
            }
        }
    }
    }
    }
    PlotExportActions(exports,"symvacas-statistics-plot")
    if(type=="Box plot")series.forEach {entry->
        val summary=remember(entry.second) {
            val sorted=entry.second.sorted()
            fun q(p:Double):Double {val at=(sorted.size-1)*p;val low=floor(at).toInt();val high=ceil(at).toInt();val f=at-low;return sorted[low]*(1-f)+sorted[high]*f}
            "min %.4g   Q1 %.4g   median %.4g   Q3 %.4g   max %.4g".format(java.util.Locale.US,sorted.first(),q(.25),q(.5),q(.75),sorted.last())
        }
        Text(entry.first.takeIf {it.isNotBlank()}?.let {"$it  $summary"} ?: summary,Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()),fontSize=10.sp,color=entry.third,maxLines=1)
    }
    if(type=="Histogram"&&histogramKde&&histogram?.unavailable?.isNotEmpty()==true)Text(kdeUnavailable,fontSize=11.sp,color=c.muted)
    if(type in listOf("Histogram","Bar")&&series.isNotEmpty())Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()),horizontalArrangement=Arrangement.spacedBy(16.dp)) {
        series.forEachIndexed {index,entry->Text(seriesCaption(index),fontSize=11.sp,color=entry.third,maxLines=1)}
    }
    if(scatterLegend.isNotEmpty())Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()),horizontalArrangement=Arrangement.spacedBy(16.dp)) {
        scatterLegend.forEach {(label,color)->Text(label,fontSize=11.sp,color=color,maxLines=1)}
    }
    if(type=="Scatter" && fitEquation!=null)CompositionLocalProvider(LocalMathMinimumSize provides 8f) {
        Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()).padding(horizontal=10.dp,vertical=3.dp),verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(5.dp)) {
            MathText("●",11f,Modifier.alignBy(MathAxis),tint=c.danger)
            MathText(fitPrefix,12f,Modifier.alignBy(MathAxis))
            Box(Modifier.alignBy(MathAxis)){MathNode(fitEquation,12f)}
            if(showCorrelation) {
                MathText("    r = ",12f,Modifier.alignBy(MathAxis))
                MathText(correlation?.let {"%.3f".format(java.util.Locale.US,it)} ?: "—",12f,Modifier.alignBy(MathAxis))
            }
        }
    }
}
