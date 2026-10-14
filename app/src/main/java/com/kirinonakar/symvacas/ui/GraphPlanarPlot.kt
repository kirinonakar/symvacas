package com.kirinonakar.symvacas.ui

import android.graphics.Paint
import androidx.compose.foundation.*
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.gestures.awaitEachGesture
import androidx.compose.foundation.gestures.awaitFirstDown
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.*
import androidx.compose.ui.draw.clipToBounds
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.*
import androidx.compose.ui.graphics.drawscope.clipRect
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.semantics.*
import androidx.compose.ui.unit.*
import com.kirinonakar.symvacas.calculator.CalculatorModel
import com.kirinonakar.symvacas.math.PiAxis
import com.kirinonakar.symvacas.math.GraphZoom
import com.kirinonakar.symvacas.math.GraphClip
import com.kirinonakar.symvacas.math.GraphYScale
import kotlin.math.*
import com.kirinonakar.symvacas.ui.theme.InstrumentColors

// 2D viewport gestures, tracing, axes, curves, and analysis overlays.
@Composable internal fun GraphPlanarPlot(
    m:CalculatorModel,c:InstrumentColors,data:GraphPlotData,state:GraphAnalysisUiState,
    plotHeight:Dp,exports:GraphExportState,halfGraphHeight:Boolean,onHeightToggle:()->Unit,
    onViewportDragging:(Boolean)->Unit
) {
    var selected by state.selected
    val selectedDerivativeOrder by state.selectedDerivativeOrder
    var other by state.other
    var pointAt by state.pointAt
    val tangentAction by state.tangentAction
    val yAxis=remember(m.yLog){GraphYScale(m.yLog)}
    val analysisCurveKey=if(selectedDerivativeOrder==0)selected else -selectedDerivativeOrder
    val allCurves=data.allCurves
    val curves=data.curves
    val derivativeIndex=data.derivativeIndex
    val secondDerivativeIndex=data.secondDerivativeIndex
    val derivativeCurve=data.derivativeCurve
    val secondDerivativeCurve=data.secondDerivativeCurve
    val integralFill=data.integralFill
    val shadings=data.shadings
    val tangent=data.tangent
    val asymptoteLines=data.asymptoteLines
    val markers=data.markers
    val latestCurves by rememberUpdatedState(curves)
    val selectedRowKind=if(selectedDerivativeOrder!=0)"cartesian" else m.graphData?.optJSONArray("curveKinds")?.optString(selected,m.graphKind) ?: m.graphKind
    val latestSelectedRowKind by rememberUpdatedState(selectedRowKind)
    val activeCurveIndex=graphSelectedCurveIndex(selected,selectedDerivativeOrder,if(derivativeCurve!=null)derivativeIndex else -1,if(secondDerivativeCurve!=null)secondDerivativeIndex else -1)
    val latestTraceCurve by rememberUpdatedState(if(selectedDerivativeOrder==0)curves.getOrNull(selected) else if(m.isGraphVisible(selected,if(selectedDerivativeOrder==1)"derivative" else "secondDerivative"))allCurves.getOrNull(activeCurveIndex) else emptyList())
    val transform=Modifier.pointerInput(m.graphKind,m.yLog) {awaitEachGesture {
            awaitFirstDown(requireUnconsumed=false)
            var axis:String?=null
            var totalPan=Offset.Zero
            var dragging=false
            try { do {
                    val event=awaitPointerEvent()
                    val fingers=event.changes.filter{it.pressed&&it.previousPressed}
                    if(fingers.isNotEmpty()) {
                        val current=fingers.fold(Offset.Zero){a,p->a+p.position}/fingers.size.toFloat()
                        val previous=fingers.fold(Offset.Zero){a,p->a+p.previousPosition}/fingers.size.toFloat()
                        val pan=current-previous
                        totalPan+=pan
                        if(totalPan.getDistance()>viewConfiguration.touchSlop||fingers.size>=2)dragging=true
                        var zx=1.0;var zy=1.0
                        if(fingers.size>=2) {
                            val old=fingers[1].previousPosition-fingers[0].previousPosition
                            val now=fingers[1].position-fingers[0].position
                            if(axis==null)axis=GraphZoom.axis(old.x,old.y)
                            val factors=GraphZoom.factors(axis!!,old.x,old.y,now.x,now.y);zx=factors.first;zy=factors.second
                        }else axis=null
                        if(dragging) {
                            onViewportDragging(true)
                            val w=m.xMax-m.xMin
                            val anchorX=m.xMin+w*previous.x/size.width
                            val yView=yAxis.view(m.yMin,m.yMax,previous.y/size.height.toDouble(),current.y/size.height.toDouble(),zy)
                            val newW=(w/zx).coerceIn(2e-7,2e8)
                            m.xMin=anchorX-newW*current.x/size.width;m.xMax=m.xMin+newW
                            m.yMin=yView.first;m.yMax=yView.second
                            event.changes.forEach{it.consume()}
                        }
                    }
                }while(event.changes.any{it.pressed})
            } finally {
                onViewportDragging(false)
                if(dragging && !m.graphAnimating)m.plot(auto=true)
            }
    }}
    if(m.graphKind !in listOf("surface","space"))CompositionLocalProvider(LocalMinimumInteractiveComponentSize provides 0.dp) {
        Row(Modifier.horizontalScroll(rememberScrollState()),verticalAlignment=Alignment.CenterVertically) {
            fun zoom(factor:Double) {val cx=(m.xMin+m.xMax)/2;val half=(m.xMax-m.xMin)/2/factor;val view=yAxis.view(m.yMin,m.yMax,.5,.5,factor);m.xMin=cx-half;m.xMax=cx+half;m.yMin=view.first;m.yMax=view.second}
            SmallAction("−") {zoom(.5)}
            SmallAction("+") {zoom(2.0)}
            SmallAction("Fit Y") {val ys=curves.flatMap {it.filterNotNull()}.filter {it.first in m.xMin..m.xMax}.map {it.second};yAxis.fit(ys)?.let {m.yMin=it.first;m.yMax=it.second;m.save()} }
            SmallAction("Undo",enabled=m.canUndoGraph) {m.undoGraph()}
            SmallAction("Reset") {
                when(m.graphKind) {
                    "sequence"->{m.xMin=0.0;m.xMax=20.0;m.yMin=-2.0;m.yMax=20.0;m.parameterMin=0.0;m.parameterMax=20.0}
                    "implicit"->{m.xMin=-3.0;m.xMax=3.0;m.yMin=-3.0;m.yMax=3.0}
                    "differential"->{m.xMin=-5.0;m.xMax=5.0;m.yMin=-3.0;m.yMax=5.0;m.parameterMin=-5.0;m.parameterMax=5.0}
                    else->{m.xMin=-10.0;m.xMax=10.0;m.yMin=-5.0;m.yMax=5.0}
                }
                m.graphState.ensurePositiveY();m.trace=null;m.save()
            }
        }
    }
    Box(Modifier.fillMaxWidth().height(plotHeight).clipToBounds()) {
        val derivativeDash=remember {PathEffect.dashPathEffect(floatArrayOf(10f,6f))}
        ExportableGraphCanvas(Modifier.fillMaxSize().clipToBounds().background(c.display).then(transform).pointerInput(m.graphKind,selected,selectedDerivativeOrder,m.yLog) { detectTapGestures { p ->
                    val target=m.xMin+(m.xMax-m.xMin)*p.x/size.width
                    val targetY=yAxis.atFraction(1-p.y/size.height.toDouble(),m.yMin,m.yMax)
                    val xSpan=m.xMax-m.xMin;val ySpan=yAxis.coordinate(m.yMax)-yAxis.coordinate(m.yMin)
                    if(xSpan<=0.0 || ySpan<=0.0)return@detectTapGestures
                    if(selectedDerivativeOrder!=0 && m.graphAnalysis?.optString("analysis") in listOf("tangent","tangentangle") && m.graphAnalysis?.optJSONArray("line")!=null) {
                        val point=latestTraceCurve?.let {graphTracePointAtX(it,target,targetY,m.yLog)}
                        m.trace=point
                        if(point!=null){pointAt=target.toString();m.analyzeGraph(tangentAction,pointAt,pointAt,analysisCurveKey,other)}
                        return@detectTapGestures
                    }
                    if(selectedDerivativeOrder==0 && m.graphAnalysis?.optString("analysis") in listOf("tangent","tangentangle") && m.graphAnalysis?.optJSONArray("line")!=null) {
                        var nearestCurve=-1;var nearestIndex=-1;var nearestDistance=Double.POSITIVE_INFINITY
                        var nearestPoint:Pair<Double,Double>?=null
                        fun considerPoint(curveIndex:Int,pointIndex:Int,point:Pair<Double,Double>) {
                            val dx=(point.first-target)/xSpan*size.width
                            if(m.yLog&&point.second<=0)return
                            val dy=(yAxis.coordinate(point.second)-yAxis.coordinate(targetY))/ySpan*size.height
                            val distance=hypot(dx,dy)
                            if(distance<nearestDistance) {nearestCurve=curveIndex;nearestIndex=pointIndex;nearestDistance=distance;nearestPoint=point}
                        }
                        latestCurves.forEachIndexed {curveIndex,curve->
                            if(m.graphKind=="cartesian" && m.graphData?.optJSONArray("curveKinds")?.optString(curveIndex,"cartesian") !in listOf("parametric","polar"))graphTracePointAtX(curve,target,targetY,m.yLog)?.let {considerPoint(curveIndex,-1,it)}
                            else curve.forEachIndexed {pointIndex,point->point?.let {considerPoint(curveIndex,pointIndex,it)}}
                        }
                        val point=nearestPoint
                        if(nearestCurve>=0 && point!=null && nearestDistance<=40.dp.toPx()) {
                            val at=if(m.graphKind=="cartesian" && m.graphData?.optJSONArray("curveKinds")?.optString(nearestCurve,"cartesian") !in listOf("parametric","polar"))point.first else m.graphData?.optJSONArray("curveParameters")?.optJSONArray(nearestCurve)?.optDouble(nearestIndex,Double.NaN)
                            if(at!=null && at.isFinite()) {
                                selected=nearestCurve
                                if(other==selected)other=(selected+1)%latestCurves.size
                                pointAt=at.toString();m.trace=point
                                m.analyzeGraph(tangentAction,pointAt,pointAt,nearestCurve,other)
                                return@detectTapGestures
                            }
                        }
                    }
                    val curve=latestTraceCurve
                    m.trace=if(m.graphKind=="cartesian" && latestSelectedRowKind !in listOf("parametric","polar"))curve?.let {graphTracePointAtX(it,target,targetY,m.yLog)}
                    else curve?.filterNotNull()?.filter { !m.yLog||it.second>0 }?.minByOrNull { ((it.first-target)/xSpan).pow(2)+((yAxis.coordinate(it.second)-yAxis.coordinate(targetY))/ySpan).pow(2) }
                } }.semantics { contentDescription="Graph with ${curves.size} curves. Pinch to zoom, drag to pan, tap to trace${if(m.graphAnalysis?.optString("analysis") in listOf("tangent","tangentangle"))" or move the tangent" else ""}. Use Range and Analyze for accessible controls." },c.display,exports) {
            val xlo=m.xMin;val xhi=m.xMax
            fun px(x:Double)=((x-xlo)/(xhi-xlo)*size.width).toFloat()
            fun py(y:Double)=(size.height-yAxis.fraction(y,m.yMin,m.yMax)*size.height).toFloat()
            fun curvePath(points:List<Pair<Double,Double>?>):Path {
                val path=Path();var previous:Pair<Double,Double>?=null;var pen:Pair<Double,Double>?=null
                points.forEach {point->
                    val segment=yAxis.segment(previous,point,xlo,xhi,m.yMin,m.yMax)
                    previous=point
                    if(segment==null){pen=null;return@forEach}
                    val (a,b)=segment
                    if(pen!=a)path.moveTo(px(a.first),py(a.second))
                    path.lineTo(px(b.first),py(b.second));pen=b
                }
                return path
            }
            val paint=Paint(Paint.ANTI_ALIAS_FLAG).apply { color=c.muted.toArgb();textSize=11.sp.toPx() }
            fun step(range:Double):Double { val raw=range/7;val p=10.0.pow(floor(log10(raw)));val v=raw/p;return p*(if(v>5)10 else if(v>2)5 else if(v>1)2 else 1) }
            val sx=if(m.radianAxis)PiAxis.step(xhi-xlo) else step(xhi-xlo);val sy=step(m.yMax-m.yMin)
            clipRect {
                val firstX=ceil(xlo/sx)*sx
                for(index in 0..64) {
                    val x=firstX+index*sx
                    if(!x.isFinite() || x>xhi)break
                    drawLine(c.grid,Offset(px(x),0f),Offset(px(x),size.height))
                    drawContext.canvas.nativeCanvas.drawText(if(m.radianAxis)PiAxis.label(x){graphDisplayNumber(it,m.displayDigits)} else graphDisplayNumber(x,m.displayDigits),px(x)+3,size.height-8,paint)
                }
                val ticks=if(m.yLog)yAxis.ticks(m.yMin,m.yMax) else {val firstY=ceil(m.yMin/sy)*sy;(0..64).map {firstY+it*sy}.filter {it.isFinite()&&it<=m.yMax}}
                for(y in ticks) {
                    drawLine(c.grid,Offset(0f,py(y)),Offset(size.width,py(y)))
                    drawContext.canvas.nativeCanvas.drawText(graphDisplayNumber(y,m.displayDigits),4f,py(y)-3,paint)
                }
                if(0.0 in xlo..xhi)drawLine(c.muted,Offset(px(0.0),0f),Offset(px(0.0),size.height),2f)
                if(0.0 in m.yMin..m.yMax)drawLine(c.muted,Offset(0f,py(0.0)),Offset(size.width,py(0.0)),2f)
                shadings.forEachIndexed { si,shading->
                    val entry=m.graphData?.optJSONArray("shadings")?.optJSONObject(si)
                    val colorIndex=if(entry?.has("sourceIndex")==true)entry.optInt("sourceIndex",si) else entry?.optInt("shadeIndex",si) ?: si
                    val shadeColor=c.curves[colorIndex%c.curves.size]
                    shading.first.forEach {rawPolygon->
                        val polygon=if(m.yLog)yAxis.polygon(rawPolygon,xlo,xhi,m.yMin,m.yMax) else rawPolygon
                        if(polygon.size>=3) {
                            val path=Path()
                            polygon.forEachIndexed { pointIndex,point->if(pointIndex==0)path.moveTo(px(point.first),py(point.second)) else path.lineTo(px(point.first),py(point.second)) }
                            path.close()
                            drawPath(path,shadeColor.copy(alpha=.15f))
                        }
                    }
                    shading.second.forEachIndexed { bi,line->
                        val width=if(entry?.has("sourceIndex")==true) {if(selectedDerivativeOrder==0 && entry.optInt("sourceIndex")==selected)4.dp.toPx() else 1.5.dp.toPx()} else 1.6.dp.toPx()
                        val dashed=entry?.optJSONArray("boundaryStyles")?.optString(bi)=="dashed"
                        drawPath(curvePath(line),shadeColor.copy(alpha=.85f),style=Stroke(width,cap=if(dashed)StrokeCap.Butt else StrokeCap.Round,join=StrokeJoin.Round,pathEffect=if(dashed)PathEffect.dashPathEffect(floatArrayOf(6.dp.toPx(),4.dp.toPx())) else null))
                    }
                }
                integralFill.forEach {rawPolygon->
                    val polygon=if(m.yLog)yAxis.polygon(rawPolygon,xlo,xhi,m.yMin,m.yMax) else rawPolygon
                    if(polygon.size>=3) {
                        val path=Path()
                        polygon.forEachIndexed {i,point->if(i==0)path.moveTo(px(point.first),py(point.second)) else path.lineTo(px(point.first),py(point.second))}
                        path.close()
                        drawPath(path,(if(selectedDerivativeOrder==0)c.curves[selected%c.curves.size] else c.accent).copy(alpha=.18f))
                    }
                }
                curves.forEachIndexed { ci,points ->
                    val color=c.curves[ci%c.curves.size]
                    val shades=m.graphData?.optJSONArray("shadings")
                    val drawnBoundary=(0 until (shades?.length() ?: 0)).any {index->shades?.optJSONObject(index)?.let {it.optInt("sourceIndex",-1)==ci && it.has("boundaryStyles")}==true}
                    val dashed=m.graphData?.optJSONArray("curveStyles")?.optString(ci)=="dashed"
                    if(!drawnBoundary)drawPath(curvePath(points),color,style=Stroke(if(selectedDerivativeOrder==0 && ci==selected)4.dp.toPx() else 1.5.dp.toPx(),cap=if(dashed)StrokeCap.Butt else StrokeCap.Round,join=StrokeJoin.Round,pathEffect=if(dashed)PathEffect.dashPathEffect(floatArrayOf(6.dp.toPx(),4.dp.toPx())) else null))
                }
                derivativeCurve?.takeIf {m.graphDerivativeSelected?.let {m.isGraphVisible(it,"derivative")}==true}?.let {points->
                    drawPath(curvePath(points),c.accent,style=Stroke(if(selectedDerivativeOrder==1)4.dp.toPx() else 2.5.dp.toPx(),cap=StrokeCap.Round,join=StrokeJoin.Round,pathEffect=derivativeDash))
                }
                secondDerivativeCurve?.takeIf {m.graphSecondDerivativeSelected?.let {m.isGraphVisible(it,"secondDerivative")}==true}?.let {points->
                    drawPath(curvePath(points),c.accent,style=Stroke(if(selectedDerivativeOrder==2)4.dp.toPx() else 2.5.dp.toPx(),cap=StrokeCap.Round,join=StrokeJoin.Round,pathEffect=PathEffect.dashPathEffect(floatArrayOf(3.dp.toPx(),5.dp.toPx()))))
                }
                if(m.graphKind=="differential") {
                    val fieldData=m.graphData?.optJSONArray("fields")
                    val dx=(xhi-xlo)/70.0
                    for(index in 0 until (fieldData?.length() ?: 0)) {
                        val field=fieldData?.optJSONArray(index) ?: continue
                        val x=field.optDouble(0);val y=field.optDouble(1);val slope=field.optDouble(2)
                        if(!x.isFinite()||!y.isFinite()||!slope.isFinite())continue
                        if(m.yLog&&y<=0)continue
                        val angle=atan((if(m.yLog)slope/(y*ln(10.0)) else slope)*(xhi-xlo)/(yAxis.coordinate(m.yMax)-yAxis.coordinate(m.yMin))*size.height/size.width)
                        val sx=6.dp.toPx()*cos(angle).toFloat();val sy=-6.dp.toPx()*sin(angle).toFloat();val at=Offset(px(x),py(y))
                        drawLine(c.muted.copy(alpha=.55f),Offset(at.x-sx,at.y-sy),Offset(at.x+sx,at.y+sy),1.dp.toPx())
                    }
                }
                markers.forEachIndexed {index,point ->
                    val at=Offset(px(point.first),py(point.second))
                    if(at.x in 0f..size.width && at.y in 0f..size.height) {
                        drawCircle(c.display,9.dp.toPx(),at)
                        drawCircle(c.accent,5.dp.toPx(),at)
                        drawContext.canvas.nativeCanvas.drawText("${index+1}",at.x+9.dp.toPx(),at.y-9.dp.toPx(),paint)
                    }
                }
                tangent?.let {line->drawPath(curvePath(yAxis.linePoints(line[0],line[1],xlo,xhi,m.yMin,m.yMax)),c.accent.copy(alpha=.75f),style=Stroke(1.5.dp.toPx(),pathEffect=PathEffect.dashPathEffect(floatArrayOf(16f,8f))))}
                asymptoteLines.forEach {line->drawPath(curvePath(yAxis.linePoints(line[0],line[1],xlo,xhi,m.yMin,m.yMax)),c.accent.copy(alpha=.75f),style=Stroke(1.5.dp.toPx(),pathEffect=PathEffect.dashPathEffect(floatArrayOf(16f,8f))))}
                m.trace?.takeIf {!m.yLog||it.second>0}?.let { p ->
                    val at=Offset(px(p.first),py(p.second))
                    drawLine(c.muted,Offset(at.x,0f),Offset(at.x,size.height),1.dp.toPx(),pathEffect=PathEffect.dashPathEffect(floatArrayOf(3.dp.toPx(),3.dp.toPx())))
                    drawCircle(c.display,8.dp.toPx(),at)
                    drawCircle(if(selectedDerivativeOrder==0)c.curves[selected%c.curves.size] else c.accent,6.dp.toPx(),at)
                }
            }
        }
        GraphHeightToggle(halfGraphHeight,{onHeightToggle()},Modifier.align(Alignment.TopEnd))
    }

}
