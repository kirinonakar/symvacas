package com.kirinonakar.symvacas.ui

import android.graphics.Paint
import androidx.compose.foundation.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.gestures.detectTransformGestures
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
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
import com.kirinonakar.symvacas.calculator.hasImplicitSurface
import com.kirinonakar.symvacas.math.SurfaceBounds
import com.kirinonakar.symvacas.math.SurfaceMesh
import com.kirinonakar.symvacas.math.SurfaceProjection
import com.kirinonakar.symvacas.math.SurfaceColors
import com.kirinonakar.symvacas.ui.theme.LocalInstrument
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.conflate
import kotlinx.coroutines.withContext
import kotlin.math.*
import com.kirinonakar.symvacas.ui.theme.InstrumentColors

// 3D viewport appearance, gestures, surface/space geometry, and rendering.
internal class GraphSurfaceViewState(val rotation:MutableFloatState,val elevation:MutableFloatState)
@Composable internal fun rememberGraphSurfaceView():GraphSurfaceViewState {
    val rotation=rememberSaveable {mutableFloatStateOf(35f)}
    val elevation=rememberSaveable {mutableFloatStateOf(32f)}
    return remember {GraphSurfaceViewState(rotation,elevation)}
}

@Composable internal fun GraphSurfacePlot(
    m:CalculatorModel,c:InstrumentColors,view:GraphSurfaceViewState,plotHeight:Dp,
    exports:GraphExportState,halfGraphHeight:Boolean,onHeightToggle:()->Unit,
    sources:List<String>,shadeSources:List<String>,removeSource:(Int,Boolean)->Unit
) {
    var surfaceRotation by view.rotation
    var surfaceElevation by view.elevation
    Box(Modifier.fillMaxWidth().height(plotHeight).clipToBounds()) {
        SurfaceGraph(m,surfaceRotation,surfaceElevation,m.surfaceZoom,m.surfaceRenderMode,m.surfaceColor,exports,Modifier.fillMaxSize().clipToBounds().pointerInput(m.graphKind) {
                detectTransformGestures { _,pan,zoom,_->
                    surfaceRotation=((surfaceRotation+pan.x*.7f)%360f+360f)%360f
                    surfaceElevation=(surfaceElevation+pan.y*.5f).coerceIn(-90f,90f)
                    m.surfaceZoom=(m.surfaceZoom*zoom).coerceIn(.4f,3f)
                }
        })
        GraphHeightToggle(halfGraphHeight,{onHeightToggle()},Modifier.align(Alignment.TopEnd))
    }
    val surfaceZRange=m.graphData?.let {SurfaceMesh.zRange(m.zMin ?: it.optDouble("zMin",-1.0),m.zMax ?: it.optDouble("zMax",1.0))}
    Column(Modifier.fillMaxWidth()) {
        GraphFormulas(m.graphKind,sources,0,null,"",shadeSources,null,{},removeSource,m.displayDigits,if(sources.size==1)listOf(Color(android.graphics.Color.parseColor(m.surfaceColor))) else c.curves,isVisible=m::isGraphVisible,onVisibility=m::toggleGraphVisibility)
        Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()).padding(horizontal=14.dp),horizontalArrangement=Arrangement.spacedBy(6.dp),verticalAlignment=Alignment.CenterVertically) {
            Text(if(isKorean())"렌더링" else "Rendering",fontSize=11.sp,color=c.muted)
            listOf("wireframe" to (if(isKorean())"와이어프레임" else "Wireframe"),"surface" to (if(isKorean())"표면" else "Surface"),"surface-wireframe" to (if(isKorean())"표면+격자" else "Surface + mesh")).forEach { (mode,label)->
                SmallAction(label,active=m.surfaceRenderMode==mode,shaded=m.surfaceRenderMode==mode) {m.surfaceRenderMode=mode;m.save()}
            }
        }
        SurfaceAppearanceControls(m)
        Row(Modifier.fillMaxWidth().padding(horizontal=14.dp,vertical=2.dp),verticalAlignment=Alignment.CenterVertically) {
            Text("x: ${graphDisplayNumber(m.xMin,m.displayDigits)} ~ ${graphDisplayNumber(m.xMax,m.displayDigits)}   y: ${graphDisplayNumber(m.yMin,m.displayDigits)} ~ ${graphDisplayNumber(m.yMax,m.displayDigits)}"+(surfaceZRange?.let {"   z: ${graphDisplayNumber(it.first,m.displayDigits)} ~ ${graphDisplayNumber(it.second,m.displayDigits)}"} ?: ""),Modifier.weight(1f),fontSize=11.sp,color=c.muted)
        }
        Row(Modifier.fillMaxWidth().height(38.dp).padding(horizontal=14.dp),verticalAlignment=Alignment.CenterVertically) {
            Text(tr("Rotate"),fontSize=11.sp,color=c.muted);CompactSlider(surfaceRotation,{surfaceRotation=it},Modifier.weight(1f),valueRange=0f..360f);Text("${graphDisplayNumber(surfaceRotation.toString(),m.displayDigits)}°",fontSize=11.sp,color=c.muted)
        }
        Row(Modifier.fillMaxWidth().height(38.dp).padding(horizontal=14.dp),verticalAlignment=Alignment.CenterVertically) {
            Text(tr("Tilt"),fontSize=11.sp,color=c.muted);CompactSlider(surfaceElevation,{surfaceElevation=it},Modifier.weight(1f),valueRange=-90f..90f);Text("${graphDisplayNumber(surfaceElevation.toString(),m.displayDigits)}°",fontSize=11.sp,color=c.muted)
        }
        Row(Modifier.fillMaxWidth().height(38.dp).padding(horizontal=14.dp),verticalAlignment=Alignment.CenterVertically) {
            Text(tr("Zoom"),fontSize=11.sp,color=c.muted)
            CompactSlider(m.surfaceZoom,{m.surfaceZoom=it},Modifier.weight(1f),valueRange=.4f..3f,onValueChangeFinished={m.save()})
            Text("${graphDisplayNumber((m.surfaceZoom*100).toString(),m.displayDigits)}%",fontSize=11.sp,color=c.muted)
            Text(tr("Reset"),Modifier.padding(start=4.dp).background(c.scientific,RoundedCornerShape(8.dp)).clickable {
                    m.resetSurfaceRanges()
                    surfaceRotation=35f;surfaceElevation=32f;m.surfaceZoom=1f;m.save();m.plot()
                }.padding(horizontal=8.dp,vertical=7.dp),fontSize=11.sp,color=c.accent)
        }
        if(m.error.isNotBlank())Text(m.error,Modifier.padding(horizontal=14.dp,vertical=2.dp),fontSize=12.sp,color=MaterialTheme.colorScheme.error)
    }

}

@Composable private fun SurfaceAppearanceControls(m:CalculatorModel) {
    val c=LocalInstrument.current
    val korean=isKorean()
    var colorPickerOpen by rememberSaveable {mutableStateOf(false)}
    if(m.graphKind=="surface")Row(Modifier.fillMaxWidth().padding(horizontal=14.dp,vertical=2.dp),horizontalArrangement=Arrangement.spacedBy(6.dp),verticalAlignment=Alignment.CenterVertically) {
        Text(if(korean)"색상 모드" else "Color mode",fontSize=11.sp,color=c.muted)
        listOf("solid" to (if(korean)"단색" else "Solid color"),"rainbow" to (if(korean)"무지개 (Z값)" else "Rainbow (Z)")).forEach {(mode,label)->
            SmallAction(label,active=m.surfaceColorMode==mode,shaded=m.surfaceColorMode==mode) {m.surfaceColorMode=mode;m.save()}
        }
    }
    if(m.graphKind!="surface"||m.surfaceColorMode=="solid")Row(Modifier.fillMaxWidth().padding(horizontal=14.dp,vertical=2.dp),horizontalArrangement=Arrangement.spacedBy(6.dp),verticalAlignment=Alignment.CenterVertically) {
        listOf("#007b68","#3b70bd","#a04c75","#b17d00","#ff0000").forEach { color->
            Box(Modifier.size(28.dp).background(Color(android.graphics.Color.parseColor(color)),RoundedCornerShape(6.dp))
                .border(if(m.surfaceColor.equals(color,true))2.dp else 0.dp,c.ink,RoundedCornerShape(6.dp))
                .clickable {m.surfaceColor=color;m.save()}.semantics {contentDescription=(if(korean)"표면 색상 " else "Surface color ")+color;selected=m.surfaceColor.equals(color,true)})
        }
        TextButton(onClick={colorPickerOpen=true}) {
            Box(Modifier.size(18.dp).background(Color(android.graphics.Color.parseColor(m.surfaceColor)),RoundedCornerShape(4.dp)).border(1.dp,c.grid,RoundedCornerShape(4.dp)))
            Spacer(Modifier.width(6.dp))
            Text(if(korean)"커스텀" else "Custom")
        }
    }
    if(colorPickerOpen)SurfaceColorPickerDialog(m.surfaceColor,onDismiss={colorPickerOpen=false},onConfirm={color->
            m.surfaceColor=color;m.save();colorPickerOpen=false
    })
    if(m.graphKind!="space") {
        Row(Modifier.fillMaxWidth().height(38.dp).padding(horizontal=14.dp),verticalAlignment=Alignment.CenterVertically) {
            Text(if(korean)"표면 불투명도" else "Surface opacity",fontSize=11.sp,color=c.muted)
            CompactSlider(m.surfaceOpacity,{m.surfaceOpacity=it},Modifier.weight(1f),valueRange=.1f..1f,onValueChangeFinished={m.save()})
            Text("${graphDisplayNumber((m.surfaceOpacity*100).toString(),m.displayDigits)}%",fontSize=11.sp,color=c.muted)
        }
        val (low,high)=when(m.surfaceSliceAxis) {
            "x"->m.xMin to m.xMax
            "y"->m.yMin to m.yMax
            else->SurfaceMesh.zRange(m.zMin ?: m.graphData?.optDouble("zMin",-1.0) ?: -1.0,m.zMax ?: m.graphData?.optDouble("zMax",1.0) ?: 1.0)
        }
        val slice=m.surfaceSlicePosition.coerceIn(low,high)
        Row(Modifier.fillMaxWidth().height(44.dp).padding(horizontal=14.dp),verticalAlignment=Alignment.CenterVertically) {
            Checkbox(m.surfaceSliceEnabled,{m.surfaceSliceEnabled=it;m.save()},Modifier.semantics {contentDescription=if(korean)"단면 표시" else "Show section"})
            Text(if(korean)"단면" else "Section",fontSize=11.sp,color=c.muted)
            listOf("x","y","z").forEach {axis->
                SmallAction("$axis = c",active=m.surfaceSliceAxis==axis,shaded=m.surfaceSliceAxis==axis) {m.surfaceSliceAxis=axis;m.save()}
            }
        }
        Row(Modifier.fillMaxWidth().height(38.dp).padding(horizontal=14.dp),verticalAlignment=Alignment.CenterVertically) {
            CompactSlider(((slice-low)/(high-low)).toFloat(),{m.surfaceSlicePosition=low+(high-low)*it},Modifier.weight(1f),valueRange=0f..1f,enabled=m.surfaceSliceEnabled,onValueChangeFinished={m.save()})
            Text("${m.surfaceSliceAxis} = ${graphDisplayNumber(slice,m.displayDigits)}",fontSize=11.sp,color=c.muted)
        }
    }
    if(m.graphKind!="space")Row(Modifier.fillMaxWidth().height(38.dp).padding(horizontal=14.dp),verticalAlignment=Alignment.CenterVertically) {
        Text(if(isKorean())"격자 밀도" else "Mesh density",fontSize=11.sp,color=c.muted)
        val implicit=hasImplicitSurface(m.graphSource)
        val count=SurfaceMesh.sampleCount(m.xMin,m.xMax,m.yMin,m.yMax,m.surfaceSamples,m.surfaceAutoDensity,m.surfaceZoom.toDouble(),implicit)
        CompactSlider(count.toFloat(),{m.surfaceSamples=it.roundToInt()},Modifier.weight(1f),valueRange=12f..(if(implicit)32f else 96f),steps=if(implicit)19 else 83,onValueChangeFinished={m.save()},enabled=!m.surfaceAutoDensity)
        Text(if(implicit)"$count × $count × $count" else "$count × $count",fontSize=11.sp,color=c.muted)
        Checkbox(m.surfaceAutoDensity,{m.surfaceAutoDensity=it;m.save()})
        Text(if(korean)"자동" else "Auto",fontSize=11.sp,color=c.muted)
    }
}

@Composable private fun SurfaceGraph(m:CalculatorModel,rotation:Float,elevationDeg:Float,zoom:Float,renderMode:String,colorHex:String,exports:GraphExportState,modifier:Modifier=Modifier) {
    val c=LocalInstrument.current
    val range=SurfaceMesh.zRange(m.zMin ?: m.graphData?.optDouble("zMin",-1.0) ?: -1.0,m.zMax ?: m.graphData?.optDouble("zMax",1.0) ?: 1.0)
    val surfaceColor=remember(colorHex) {runCatching {Color(android.graphics.Color.parseColor(colorHex))}.getOrDefault(Color(0xFF007B68))}
    val colors=if((m.graphData?.optJSONArray("surfaces")?.length() ?: 1)>1)c.curves else listOf(surfaceColor)
    val latest by rememberUpdatedState(SurfaceSceneRequest(m.graphData,SurfaceBounds(m.xMin,m.xMax,m.yMin,m.yMax,range.first,range.second),rotation,elevationDeg,renderMode,m.surfaceOpacity,m.graphKind=="surface"&&m.surfaceColorMode=="rainbow",colors,List(5){m.isGraphVisible(it)},m.graphSource,m.graphKind))
    val scene by produceState<SurfaceScene?>(null) {
        val builder=SurfaceSceneBuilder()
        snapshotFlow {latest}.conflate().collect {request->
            val next=withContext(Dispatchers.Default){builder.build(request)}
            if(latest.source==request.source&&latest.kind==request.kind)value=next
        }
    }
    val shown=scene ?: return
    val groups=shown.groups;val prepared=shown.prepared;val projection=shown.projection;val faces=shown.faces;val batch=shown.batches;val wireEdges=shown.edges;val spaceCurves=shown.curves
    val bounds=shown.request.bounds;val xmin=bounds.xmin;val xmax=bounds.xmax;val ymin=bounds.ymin;val ymax=bounds.ymax;val zmin=bounds.zmin;val zmax=bounds.zmax
    val opacity=shown.request.opacity;val rainbow=shown.request.rainbow;val palette=shown.request.palette;val drawMode=shown.request.mode
    ExportableGraphCanvas(modifier.background(c.display).semantics { contentDescription="Three dimensional surface. Drag to rotate freely, pinch to zoom, and adjust x, y and z ranges." },c.display,exports) {
        if(groups.all {it.mesh.isEmpty()&&it.triangles.isEmpty()} && spaceCurves.isEmpty())return@ExportableGraphCanvas
        val scale=min(size.width,size.height)*.34f*zoom
        fun project(point:DoubleArray):Offset {
            val p=projection.project(point)
            return Offset(size.width/2+p[0].toFloat()*scale,size.height/2+p[1].toFloat()*scale)
        }
        fun niceStep(range:Double):Double {
            if(!range.isFinite()||range<=0.0)return 1.0
            val raw=range/4;val p=10.0.pow(floor(log10(raw)));val v=raw/p
            return p*(if(v>5)10 else if(v>2)5 else if(v>1)2 else 1)
        }
        val axisPaint=Paint(Paint.ANTI_ALIAS_FLAG).apply { color=c.muted.toArgb();textSize=11.sp.toPx() }
        val labelPaint=Paint(Paint.ANTI_ALIAS_FLAG).apply { color=c.ink.toArgb();textSize=12.sp.toPx();isFakeBoldText=true }
        fun surfaceSegment(path:Path,a:DoubleArray?,b:DoubleArray?) {
            val segment=SurfaceMesh.clipSegment(a,b,bounds) ?: return
            val from=project(segment.first);val to=project(segment.second)
            if(rainbow&&drawMode=="wireframe"&&from!=to) {
                val wire=Path().apply {moveTo(from.x,from.y);lineTo(to.x,to.y)}
                val outline=android.graphics.Path();Paint().apply {style=Paint.Style.STROKE;strokeWidth=1.dp.toPx()}.getFillPath(wire.asAndroidPath(),outline)
                drawGraphColorGradientPath(drawContext.canvas.nativeCanvas,outline,from,to,
                    intArrayOf(SurfaceColors.rainbow((segment.first[2]-zmin)/(zmax-zmin)),SurfaceColors.rainbow((segment.second[2]-zmin)/(zmax-zmin))),floatArrayOf(0f,1f),0f)
            } else {path.moveTo(from.x,from.y);path.lineTo(to.x,to.y)}
        }
        clipRect {
            val vector=isGraphVectorCanvas(drawContext.canvas.nativeCanvas)
            if(!vector&&faces.isNotEmpty()) {
                val canvas=drawContext.canvas.nativeCanvas
                canvas.save();canvas.translate(size.width/2,size.height/2);canvas.scale(scale,scale)
                try {drawGraphSurfaceBatch(canvas,batch)} finally {canvas.restore()}
                if(drawMode=="surface-wireframe") {
                    val outline=Path()
                    for(face in faces){face.projected.forEachIndexed {i,p->val x=size.width/2+p[0].toFloat()*scale;val y=size.height/2+p[1].toFloat()*scale;if(i==0)outline.moveTo(x,y)else outline.lineTo(x,y)};outline.close()}
                    drawPath(outline,c.muted,style=Stroke(.65.dp.toPx()))
                }
            }
            if(vector&&drawMode!="wireframe")for(face in SurfaceMesh.project(prepared,projection,opacity<1f)) {
                val faceColor=palette[face.group%palette.size].copy(alpha=opacity)
                val path=Path().apply {
                    face.points.forEachIndexed { index,point->val p=project(point);if(index==0)moveTo(p.x,p.y)else lineTo(p.x,p.y) };close()
                }
                val color=lerp(Color.Black.copy(alpha=opacity),faceColor,(face.brightness ?: ((.65+.35*face.height)*face.light)).toFloat())
                val lighting=face.lighting
                if(rainbow) {
                    val heights=face.points.map {(it[2]-zmin)/(zmax-zmin)}
                    val gradient=SurfaceMesh.lightingGradient(face.projected,heights) ?: lighting
                    val fallback=face.brightness ?: ((.65+.35*face.height)*face.light)
                    fun shaded(height:Double,point:DoubleArray):Int {
                        val shade=SurfaceColors.gradientValue(lighting,point,fallback).coerceIn(0.0,1.0)
                        return lerp(Color.Black,Color(SurfaceColors.rainbow(height)),shade.toFloat()).copy(alpha=opacity).toArgb()
                    }
                    if(gradient==null)drawPath(path,Color(shaded(heights.first(),face.projected.first())))
                    else {
                        val heightGradient=SurfaceMesh.lightingGradient(face.projected,heights)
                        val values=if(heightGradient==null)listOf(gradient.min,gradient.max) else listOf(gradient.min)+(0..5).map {it/5.0}.filter {it>gradient.min&&it<gradient.max}+gradient.max
                        val positions=values.map {((it-gradient.min)/(gradient.max-gradient.min)).toFloat()}.toFloatArray()
                        val colors=values.mapIndexed {i,value->
                            val t=positions[i].toDouble();val point=DoubleArray(2) {gradient.start[it]+(gradient.end[it]-gradient.start[it])*t}
                            shaded(if(heightGradient==null)heights.first() else value,point)
                        }.toIntArray()
                        val start=Offset(size.width/2+gradient.start[0].toFloat()*scale,size.height/2+gradient.start[1].toFloat()*scale)
                        val end=Offset(size.width/2+gradient.end[0].toFloat()*scale,size.height/2+gradient.end[1].toFloat()*scale)
                        drawGraphColorGradientPath(drawContext.canvas.nativeCanvas,path.asAndroidPath(),start,end,colors,positions,if(drawMode=="surface-wireframe"||opacity<1f)0f else .8.dp.toPx())
                    }
                    if(drawMode=="surface-wireframe")drawPath(path,c.muted,style=Stroke(.65.dp.toPx()))
                } else if(lighting!=null) {
                    val start=Offset(size.width/2+lighting.start[0].toFloat()*scale,size.height/2+lighting.start[1].toFloat()*scale)
                    val end=Offset(size.width/2+lighting.end[0].toFloat()*scale,size.height/2+lighting.end[1].toFloat()*scale)
                    drawGraphGradientPath(drawContext.canvas.nativeCanvas,path.asAndroidPath(),start,end,
                        lerp(Color.Black.copy(alpha=opacity),faceColor,lighting.min.toFloat()).toArgb(),lerp(Color.Black.copy(alpha=opacity),faceColor,lighting.max.toFloat()).toArgb(),
                        if(drawMode=="surface-wireframe" || opacity<1f)0f else .8.dp.toPx())
                    if(drawMode=="surface-wireframe")drawPath(path,c.muted,style=Stroke(.65.dp.toPx()))
                } else {
                    drawPath(path,color)
                    if(drawMode=="surface-wireframe" || opacity==1f)drawPath(path,if(drawMode=="surface-wireframe")c.muted else color,style=Stroke(if(drawMode=="surface-wireframe").65.dp.toPx() else .35.dp.toPx()))
                }
            }
            if(drawMode=="wireframe") {
                groups.forEachIndexed {index,group->
                    if(!m.isGraphVisible(index))return@forEachIndexed
                    val mesh=group.mesh;val wireColor=palette[index%palette.size]
                    val rows=Path();val columns=Path()
                    wireEdges[index].forEach {(a,b)->surfaceSegment(rows,a,b)}
                    mesh.forEach {row->
                        for(ci in 0 until row.lastIndex) {
                            val a=row[ci];val b=row[ci+1]
                            surfaceSegment(rows,a,b)
                        }
                    }
                    if(mesh.isNotEmpty())for(ci in mesh.first().indices) {
                        for(ri in 0 until mesh.lastIndex) {
                            val a=mesh[ri].getOrNull(ci);val b=mesh[ri+1].getOrNull(ci)
                            surfaceSegment(columns,a,b)
                        }
                    }
                    drawPath(rows,wireColor.copy(alpha=.78f),style=Stroke(1.15.dp.toPx()))
                    drawPath(columns,wireColor.copy(alpha=.78f),style=Stroke(1.dp.toPx()))
                }
            }
            if(m.surfaceSliceEnabled && m.graphKind=="surface") {
                val axis=listOf("x","y","z").indexOf(m.surfaceSliceAxis)
                val range=bounds.limits[axis]
                val position=m.surfaceSlicePosition.coerceIn(range.first,range.second)
                val corners=SurfaceMesh.sectionPlane(bounds,position,axis)
                val plane=Path().apply {corners.forEachIndexed {i,p->val at=project(p);if(i==0)moveTo(at.x,at.y)else lineTo(at.x,at.y)};close()}
                drawPath(plane,c.accent.copy(alpha=.08f))
                drawPath(plane,c.accent.copy(alpha=.6f),style=Stroke(1.dp.toPx(),pathEffect=PathEffect.dashPathEffect(floatArrayOf(5.dp.toPx(),4.dp.toPx()))))
                for((group,segment) in SurfaceMesh.sectionSegments(prepared.faces,position,axis))drawLine(if(rainbow)Color(SurfaceColors.rainbow(((segment.first[2]+segment.second[2])/2-zmin)/(zmax-zmin))) else palette[group%palette.size],project(segment.first),project(segment.second),3.dp.toPx())
            }
            spaceCurves.forEachIndexed {i,curve->
                if(!m.isGraphVisible(i))return@forEachIndexed
                val path=Path()
                for(k in 1 until curve.size)surfaceSegment(path,curve[k-1],curve[k])
                drawPath(path,if(spaceCurves.size==1)surfaceColor else c.curves[i%c.curves.size],style=Stroke(3.dp.toPx(),cap=StrokeCap.Round,join=StrokeJoin.Round))
            }
            val x0=doubleArrayOf(xmin,ymin,zmin)
            val x1=doubleArrayOf(xmax,ymin,zmin)
            val y1=doubleArrayOf(xmin,ymax,zmin)
            val z1=doubleArrayOf(xmin,ymin,zmax)
            drawLine(c.muted,project(x0),project(x1),2.dp.toPx())
            drawLine(c.muted,project(x0),project(y1),2.dp.toPx())
            drawLine(c.muted,project(x0),project(z1),2.dp.toPx())
            val xStep=niceStep(xmax-xmin);val yStep=niceStep(ymax-ymin);val zStep=niceStep(zmax-zmin)
            var tick=ceil(xmin/xStep)*xStep
            var guard=0
            while(tick<=xmax+1e-12&&guard++<12) {
                val p=project(doubleArrayOf(tick,ymin,zmin))
                drawCircle(c.muted,3.dp.toPx()/2,p)
                drawContext.canvas.nativeCanvas.drawText(graphDisplayNumber(tick,m.displayDigits),p.x+3f,p.y+12.sp.toPx(),axisPaint)
                tick+=xStep
            }
            tick=ceil(ymin/yStep)*yStep;guard=0
            while(tick<=ymax+1e-12&&guard++<12) {
                val p=project(doubleArrayOf(xmin,tick,zmin))
                drawCircle(c.muted,3.dp.toPx()/2,p)
                drawContext.canvas.nativeCanvas.drawText(graphDisplayNumber(tick,m.displayDigits),p.x+3f,p.y+12.sp.toPx(),axisPaint)
                tick+=yStep
            }
            tick=ceil(zmin/zStep)*zStep;guard=0
            while(tick<=zmax+1e-12&&guard++<12) {
                val p=project(doubleArrayOf(xmin,ymin,tick))
                drawCircle(c.muted,3.dp.toPx()/2,p)
                drawContext.canvas.nativeCanvas.drawText(graphDisplayNumber(tick,m.displayDigits),p.x+4f,p.y-4f,axisPaint)
                tick+=zStep
            }
            drawContext.canvas.nativeCanvas.drawText("x",project(x1).x+6f,project(x1).y+4f,labelPaint)
            drawContext.canvas.nativeCanvas.drawText("y",project(y1).x+6f,project(y1).y+4f,labelPaint)
            drawContext.canvas.nativeCanvas.drawText("z",project(z1).x+6f,project(z1).y+4f,labelPaint)
            if(rainbow) {
                val labels=listOf(zmin,(zmin+zmax)/2,zmax).map {graphDisplayNumber(it,m.displayDigits)}
                val barWidth=10.dp.toPx();val top=28.dp.toPx();val height=min(140.dp.toPx(),size.height-48.dp.toPx())
                val left=size.width-labels.maxOf {axisPaint.measureText(it)}-barWidth-18.dp.toPx()
                val path=android.graphics.Path().apply {addRect(left,top,left+barWidth,top+height,android.graphics.Path.Direction.CW)}
                drawGraphColorGradientPath(drawContext.canvas.nativeCanvas,path,Offset(left,top+height),Offset(left,top),SurfaceColors.stops.toIntArray(),FloatArray(6) {it/5f},0f)
                drawContext.canvas.nativeCanvas.drawText("z",left,top-6.dp.toPx(),labelPaint)
                labels.forEachIndexed {i,text->drawContext.canvas.nativeCanvas.drawText(text,left+barWidth+4.dp.toPx(),top+height*(1-i/2f)+4.dp.toPx(),axisPaint)}
            }
        }
    }
}
