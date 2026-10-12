package com.kirinonakar.symvacas.ui

import android.graphics.Paint
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
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.kirinonakar.symvacas.ui.theme.LocalInstrument
import org.json.JSONObject

@Composable internal fun LogisticComparisonPlot(plot:JSONObject) {
    val c=LocalInstrument.current;val calibration=plot.getString("kind")=="calibration-comparison"
    val series=plot.getJSONArray("series");val title=tr(plot.getString("title"));val exports=remember {GraphExportState()}
    val captions=List(series.length()){index->val item=series.getJSONObject(index);item.getString("label")+if(calibration)"" else " · AUC=${graphDisplayNumber(item.getDouble("auc"),6)}"+(item.optJSONArray("interval")?.let {" · CI [${graphDisplayNumber(it.getDouble(0),6)}, ${graphDisplayNumber(it.getDouble(1),6)}]"} ?: "")}
    val xLabel=tr(if(calibration)"Predicted probability" else "False positive rate (FPR)");val yLabel=tr(if(calibration)"Observed event proportion" else "Sensitivity (TPR)")
    Text(title,fontSize=12.sp)
    Text(tr(when(plot.optString("evaluation")){"crossvalidation"->"Out-of-fold predictions; refitted bootstrap confidence intervals.";"apparent"->"Training-data predictions; apparent performance.";"holdout"->"Held-out predictions; models fitted on the training split only.";else->"Validation dataset predictions; conditional on the fitted training models."}),fontSize=11.sp,color=c.muted)
    ExportableGraphCanvas(Modifier.widthIn(max=520.dp).fillMaxWidth().aspectRatio(1.15f).testTag("statistics-${plot.getString("kind")}"),c.display,exports,
        exportFooterHeight=(captions.size*18+4).dp,exportFooter={
            val paint=Paint(Paint.ANTI_ALIAS_FLAG).apply {textSize=10.sp.toPx()}
            captions.forEachIndexed {index,text->paint.color=c.curves[index%c.curves.size].toArgb();drawContext.canvas.nativeCanvas.drawText(text,8.dp.toPx(),(16+index*18).dp.toPx(),paint)}
        }) {
        val left=45.dp.toPx();val top=10.dp.toPx();val width=size.width-left-15.dp.toPx();val height=size.height-top-42.dp.toPx()
        fun x(v:Double)=left+width*v.toFloat()
        fun y(v:Double)=top+height*(1-v.toFloat())
        val paint=Paint(Paint.ANTI_ALIAS_FLAG).apply {color=c.muted.toArgb();textSize=10.sp.toPx()}
        listOf(0.0,.25,.5,.75,1.0).forEach {v->
            drawLine(c.grid,Offset(x(v),y(0.0)),Offset(x(v),y(1.0)),1.dp.toPx());drawLine(c.grid,Offset(x(0.0),y(v)),Offset(x(1.0),y(v)),1.dp.toPx())
            drawLine(c.muted,Offset(x(v),y(0.0)),Offset(x(v),y(0.0)+4.dp.toPx()),1.dp.toPx());drawLine(c.muted,Offset(x(0.0)-4.dp.toPx(),y(v)),Offset(x(0.0),y(v)),1.dp.toPx())
            val text=v.toString().removeSuffix(".0");drawContext.canvas.nativeCanvas.drawText(text,x(v)-paint.measureText(text)/2,y(0.0)+16.dp.toPx(),paint);drawContext.canvas.nativeCanvas.drawText(text,left-paint.measureText(text)-6.dp.toPx(),y(v)+3.dp.toPx(),paint)
        }
        drawLine(c.muted,Offset(x(0.0),y(0.0)),Offset(x(1.0),y(0.0)),1.dp.toPx())
        drawLine(c.muted,Offset(x(0.0),y(0.0)),Offset(x(0.0),y(1.0)),1.dp.toPx())
        drawLine(c.muted,Offset(x(0.0),y(0.0)),Offset(x(1.0),y(1.0)),pathEffect=PathEffect.dashPathEffect(floatArrayOf(5.dp.toPx(),5.dp.toPx())))
        repeat(series.length()){index->
            val points=series.getJSONObject(index).getJSONArray("points");val path=Path();val color=c.curves[index%c.curves.size]
            repeat(points.length()){i->val point=points.getJSONArray(i);val px=x(point.getDouble(0));val py=y(point.getDouble(1));if(i==0)path.moveTo(px,py) else path.lineTo(px,py);if(calibration)drawCircle(color,3.dp.toPx(),Offset(px,py))}
            drawPath(path,color,style=Stroke(2.dp.toPx()))
        }
        drawContext.canvas.nativeCanvas.drawText(xLabel,left+width/2-paint.measureText(xLabel)/2,y(0.0)+35.dp.toPx(),paint)
        val native=drawContext.canvas.nativeCanvas;native.save();native.rotate(-90f,12.dp.toPx(),top+height/2);native.drawText(yLabel,12.dp.toPx()-paint.measureText(yLabel)/2,top+height/2,paint);native.restore()
    }
    captions.forEachIndexed {index,text->Text(text,fontSize=11.sp,color=c.curves[index%c.curves.size])}
    PlotExportActions(exports,"symvacas-${plot.getString("kind")}")
}
