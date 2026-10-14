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
    val activeCurveIndex=graphSelectedCurveIndex(selected,selectedDerivativeOrder,if(derivativeCurve!=null)derivativeIndex else -1,if(secondDerivativeCurve!=null)secondDerivativeIndex else -1)
    val latestTraceCurve by rememberUpdatedState(allCurves.getOrNull(activeCurveIndex))
    val transform=Modifier.pointerInput(m.graphKind) {awaitEachGesture {
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
                            val w=m.xMax-m.xMin;val h=m.yMax-m.yMin
                            val anchorX=m.xMin+w*previous.x/size.width;val anchorY=m.yMax-h*previous.y/size.height
                            val newW=(w/zx).coerceIn(2e-7,2e8);val newH=(h/zy).coerceIn(2e-7,2e8)
                            m.xMin=anchorX-newW*current.x/size.width;m.xMax=m.xMin+newW
                            m.yMax=anchorY+newH*current.y/size.height;m.yMin=m.yMax-newH
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
            SmallAction("−") { val cx=(m.xMin+m.xMax)/2;val cy=(m.yMin+m.yMax)/2;val halfX=(m.xMax-m.xMin);val halfY=(m.yMax-m.yMin);m.xMin=cx-halfX;m.xMax=cx+halfX;m.yMin=cy-halfY;m.yMax=cy+halfY }
            SmallAction("+") { val cx=(m.xMin+m.xMax)/2;val cy=(m.yMin+m.yMax)/2;val halfX=(m.xMax-m.xMin)/4;val halfY=(m.yMax-m.yMin)/4;m.xMin=cx-halfX;m.xMax=cx+halfX;m.yMin=cy-halfY;m.yMax=cy+halfY }
            SmallAction("Fit Y") {val ys=curves.flatMap {it.filterNotNull()}.filter {it.first in m.xMin..m.xMax && it.second.isFinite()}.map {it.second};if(ys.isNotEmpty()){val lo=ys.min();val hi=ys.max();val pad=max((hi-lo)*.12,if(hi==lo)1.0 else 1e-6);m.yMin=lo-pad;m.yMax=hi+pad;m.save()} }
            SmallAction("Undo",enabled=m.canUndoGraph) {m.undoGraph()}
            SmallAction("Reset") {
                when(m.graphKind) {
                    "sequence"->{m.xMin=0.0;m.xMax=20.0;m.yMin=-2.0;m.yMax=20.0;m.parameterMin=0.0;m.parameterMax=20.0}
                    "implicit"->{m.xMin=-3.0;m.xMax=3.0;m.yMin=-3.0;m.yMax=3.0}
                    "differential"->{m.xMin=-5.0;m.xMax=5.0;m.yMin=-3.0;m.yMax=5.0;m.parameterMin=-5.0;m.parameterMax=5.0}
                    else->{m.xMin=-10.0;m.xMax=10.0;m.yMin=-5.0;m.yMax=5.0}
                }
                m.trace=null;m.save()
            }
        }
    }
    Box(Modifier.fillMaxWidth().height(plotHeight).clipToBounds()) {
        val derivativeDash=remember {PathEffect.dashPathEffect(floatArrayOf(10f,6f))}
        ExportableGraphCanvas(Modifier.fillMaxSize().clipToBounds().background(c.display).then(transform).pointerInput(m.graphKind,selected,selectedDerivativeOrder) { detectTapGestures { p ->
                    val target=m.xMin+(m.xMax-m.xMin)*p.x/size.width
                    val targetY=m.yMax-(m.yMax-m.yMin)*p.y/size.height
                    val xSpan=m.xMax-m.xMin;val ySpan=m.yMax-m.yMin
                    if(xSpan<=0.0 || ySpan<=0.0)return@detectTapGestures
                    if(selectedDerivativeOrder!=0 && m.graphAnalysis?.optString("analysis") in listOf("tangent","tangentangle") && m.graphAnalysis?.optJSONArray("line")!=null) {
                        val point=latestTraceCurve?.let {graphTracePointAtX(it,target,targetY)}
                        m.trace=point
                        if(point!=null){pointAt=target.toString();m.analyzeGraph(tangentAction,pointAt,pointAt,analysisCurveKey,other)}
                        return@detectTapGestures
                    }
                    if(selectedDerivativeOrder==0 && m.graphAnalysis?.optString("analysis") in listOf("tangent","tangentangle") && m.graphAnalysis?.optJSONArray("line")!=null) {
                        var nearestCurve=-1;var nearestIndex=-1;var nearestDistance=Double.POSITIVE_INFINITY
                        var nearestPoint:Pair<Double,Double>?=null
                        fun considerPoint(curveIndex:Int,pointIndex:Int,point:Pair<Double,Double>) {
                            val dx=(point.first-target)/xSpan*size.width
                            val dy=(point.second-targetY)/ySpan*size.height
                            val distance=hypot(dx,dy)
                            if(distance<nearestDistance) {nearestCurve=curveIndex;nearestIndex=pointIndex;nearestDistance=distance;nearestPoint=point}
                        }
                        latestCurves.forEachIndexed {curveIndex,curve->
                            if(m.graphKind=="cartesian")graphTracePointAtX(curve,target,targetY)?.let {considerPoint(curveIndex,-1,it)}
                            else curve.forEachIndexed {pointIndex,point->point?.let {considerPoint(curveIndex,pointIndex,it)}}
                        }
                        val point=nearestPoint
                        if(nearestCurve>=0 && point!=null && nearestDistance<=40.dp.toPx()) {
                            val at=if(m.graphKind=="cartesian")point.first else m.graphData?.optJSONArray("curveParameters")?.optJSONArray(nearestCurve)?.optDouble(nearestIndex,Double.NaN)
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
                    m.trace=if(m.graphKind=="cartesian")curve?.let {graphTracePointAtX(it,target,targetY)}
                    else curve?.filterNotNull()?.minByOrNull { ((it.first-target)/xSpan).pow(2)+((it.second-targetY)/ySpan).pow(2) }
                } }.semantics { contentDescription="Graph with ${curves.size} curves. Pinch to zoom, drag to pan, tap to trace${if(m.graphAnalysis?.optString("analysis") in listOf("tangent","tangentangle"))" or move the tangent" else ""}. Use Range and Analyze for accessible controls." },c.display,exports) {
            val xlo=m.xMin;val xhi=m.xMax
            fun px(x:Double)=((x-xlo)/(xhi-xlo)*size.width).toFloat()
            fun py(y:Double)=(size.height-(y-m.yMin)/(m.yMax-m.yMin)*size.height).toFloat()
            fun curvePath(points:List<Pair<Double,Double>?>):Path {
                val path=Path();var previous:Pair<Double,Double>?=null;var pen:Pair<Double,Double>?=null
                points.forEach {point->
                    val segment=GraphClip.segment(previous,point,xlo,xhi,m.yMin,m.yMax)
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
                val firstY=ceil(m.yMin/sy)*sy
                for(index in 0..64) {
                    val y=firstY+index*sy
                    if(!y.isFinite() || y>m.yMax)break
                    drawLine(c.grid,Offset(0f,py(y)),Offset(size.width,py(y)))
                    drawContext.canvas.nativeCanvas.drawText(graphDisplayNumber(y,m.displayDigits),4f,py(y)-3,paint)
                }
                if(0.0 in xlo..xhi)drawLine(c.muted,Offset(px(0.0),0f),Offset(px(0.0),size.height),2f)
                if(0.0 in m.yMin..m.yMax)drawLine(c.muted,Offset(0f,py(0.0)),Offset(size.width,py(0.0)),2f)
                shadings.forEachIndexed { si,shading->
                    val shadeColor=c.curves[si%c.curves.size]
                    shading.first.forEach { polygon->
                        if(polygon.size>=3) {
                            val path=Path()
                            polygon.forEachIndexed { pointIndex,point->if(pointIndex==0)path.moveTo(px(point.first),py(point.second)) else path.lineTo(px(point.first),py(point.second)) }
                            path.close()
                            drawPath(path,shadeColor.copy(alpha=.15f))
                        }
                    }
                    shading.second.forEach { line->
                        drawPath(curvePath(line),shadeColor.copy(alpha=.85f),style=Stroke(1.6.dp.toPx()))
                    }
                }
                integralFill.forEach {polygon->
                    if(polygon.size>=3) {
                        val path=Path()
                        polygon.forEachIndexed {i,point->if(i==0)path.moveTo(px(point.first),py(point.second)) else path.lineTo(px(point.first),py(point.second))}
                        path.close()
                        drawPath(path,(if(selectedDerivativeOrder==0)c.curves[selected%c.curves.size] else c.accent).copy(alpha=.18f))
                    }
                }
                curves.forEachIndexed { ci,points ->
                    val color=c.curves[ci%c.curves.size]
                    drawPath(curvePath(points),color,style=Stroke(if(selectedDerivativeOrder==0 && ci==selected)4.dp.toPx() else 1.5.dp.toPx(),cap=StrokeCap.Round,join=StrokeJoin.Round))
                }
                derivativeCurve?.let {points->
                    drawPath(curvePath(points),c.accent,style=Stroke(if(selectedDerivativeOrder==1)4.dp.toPx() else 2.5.dp.toPx(),cap=StrokeCap.Round,join=StrokeJoin.Round,pathEffect=derivativeDash))
                }
                secondDerivativeCurve?.let {points->
                    drawPath(curvePath(points),c.accent,style=Stroke(if(selectedDerivativeOrder==2)4.dp.toPx() else 2.5.dp.toPx(),cap=StrokeCap.Round,join=StrokeJoin.Round,pathEffect=PathEffect.dashPathEffect(floatArrayOf(3.dp.toPx(),5.dp.toPx()))))
                }
                if(m.graphKind=="differential") {
                    val fieldData=m.graphData?.optJSONArray("fields")
                    val dx=(xhi-xlo)/70.0
                    for(index in 0 until (fieldData?.length() ?: 0)) {
                        val field=fieldData?.optJSONArray(index) ?: continue
                        val x=field.optDouble(0);val y=field.optDouble(1);val slope=field.optDouble(2)
                        if(!x.isFinite()||!y.isFinite()||!slope.isFinite())continue
                        val dy=(slope*dx).coerceIn(-(m.yMax-m.yMin)/14,(m.yMax-m.yMin)/14)
                        drawLine(c.muted.copy(alpha=.55f),Offset(px(x-dx/2),py(y-dy/2)),Offset(px(x+dx/2),py(y+dy/2)),1.dp.toPx())
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
                tangent?.let { line->
                    GraphClip.segment(line[0],line[1],xlo,xhi,m.yMin,m.yMax)?.let {(a,b)->
                        drawLine(c.accent.copy(alpha=.75f),Offset(px(a.first),py(a.second)),Offset(px(b.first),py(b.second)),1.5.dp.toPx(),pathEffect=PathEffect.dashPathEffect(floatArrayOf(16f,8f)))
                    }
                }
                asymptoteLines.forEach {line->
                    GraphClip.segment(line[0],line[1],xlo,xhi,m.yMin,m.yMax)?.let {(a,b)->
                        drawLine(c.accent.copy(alpha=.75f),Offset(px(a.first),py(a.second)),Offset(px(b.first),py(b.second)),1.5.dp.toPx(),pathEffect=PathEffect.dashPathEffect(floatArrayOf(16f,8f)))
                    }
                }
                m.trace?.let { p ->
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
