package com.kirinonakar.symvacas.ui

import android.graphics.Paint
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.kirinonakar.symvacas.calculator.ResultDisplayMode
import com.kirinonakar.symvacas.ui.theme.LocalInstrument
import org.json.JSONObject

@Composable internal fun SvmDecisionPlot(plot:JSONObject?,digits:Int,labels:Map<String,String>) {
    if(plot==null)return
    val colors=LocalInstrument.current
    val exports=remember {GraphExportState()}
    val kind=plot.optString("kind")
    val regression=kind in listOf("observedPredicted","predictionError","regressionFit")
    val title=tr(when(kind){"observedPredicted"->"Observed vs predicted";"predictionError"->"Prediction error vs predicted";"regressionFit"->"SVR fit and epsilon tube";else->"SVM decision boundary and margins"})+(if(regression)" · "+tr("Training data evaluation") else "")
    val legend=tr(when(kind){"observedPredicted"->"Dots: observations; rings: support vectors. Dashed: perfect predictions (y = x).";"predictionError"->"Dots: observations; rings: support vectors. Solid: zero prediction error.";"regressionFit"->"Solid: prediction function; dashed: f(x) ± epsilon; rings: support vectors.";else->"Blue: class 0; orange: class 1; rings: support vectors. Solid: f = 0; dashed: f = -1 and +1."})
    fun number(v:Double)=ResultDisplayFormat.formatText(v.toString(),ResultDisplayMode.OFF,false,maxFractionDigits=digits,preserveSmallValues=true)
    fun name(i:Int)=labels["b${i+1}"] ?: "x${i+1}"
    val fixed=plot.optJSONArray("fixedFeatures")
    val slice=if(fixed!=null&&fixed.length()>0)tr("First two predictors shown; other predictors fixed at training means. Points are projections.")+" "+(0 until fixed.length()).joinToString(", "){i->fixed.getJSONObject(i).let {"${name(it.getInt("index"))}=${number(it.getDouble("value"))}"}} else ""
    Text(title,fontSize=12.sp,fontWeight=FontWeight.SemiBold)
    val plottedLegend=legend+if(kind=="regressionFit")" · ε=${number(plot.getDouble("epsilon"))}" else ""
    Text(plottedLegend,fontSize=11.sp)
    if(slice.isNotBlank())Text(slice,fontSize=11.sp)
    val xlim=plot.getJSONArray("xlim");val ylim=plot.getJSONArray("ylim")
    val xmin=xlim.getDouble(0);val xmax=xlim.getDouble(1);val ymin=ylim.getDouble(0);val ymax=ylim.getDouble(1)
    val xlabel=when(kind){"observedPredicted"->tr("Observed value");"predictionError"->tr("Predicted value");else->name(0)}
    val ylabel=when(kind){"observedPredicted"->tr("Predicted value");"predictionError"->tr("Prediction error");"regressionFit"->tr("Observed value");"score"->tr("Decision score");else->name(1)}
    val footerLines=(listOf(title,plottedLegend)+if(slice.isNotBlank())listOf(slice) else emptyList()).flatMap {it.chunked(43)}
    ExportableGraphCanvas(Modifier.fillMaxWidth().height(320.dp).testTag(if(regression)"statistics-svr-$kind" else "statistics-svm-decision-plot"),colors.display,exports,
        exportFooterHeight=(footerLines.size*14+8).dp,exportFooter={
            val paint=Paint(Paint.ANTI_ALIAS_FLAG).apply {color=colors.ink.toArgb();textSize=10.sp.toPx()}
            footerLines.forEachIndexed {i,line->
                val scale=minOf(1f,(size.width-16.dp.toPx())/paint.measureText(line).coerceAtLeast(1f))
                paint.textSize=10.sp.toPx()*scale
                drawContext.canvas.nativeCanvas.drawText(line,8.dp.toPx(),((i+1)*14).dp.toPx(),paint)
                paint.textSize=10.sp.toPx()
            }
        }) {
        val left=60.dp.toPx();val top=12.dp.toPx();val availableWidth=(size.width-left-15.dp.toPx()).coerceAtLeast(1f);val availableHeight=(size.height-top-48.dp.toPx()).coerceAtLeast(1f)
        val width=if(kind=="observedPredicted")minOf(availableWidth,availableHeight) else availableWidth;val height=if(kind=="observedPredicted")width else availableHeight
        fun point(a:Double,b:Double)=Offset(left+width*((a-xmin)/(xmax-xmin)).toFloat(),top+height*(1-(b-ymin)/(ymax-ymin)).toFloat())
        val native=drawContext.canvas.nativeCanvas
        val paint=Paint(Paint.ANTI_ALIAS_FLAG).apply {color=colors.ink.toArgb();textSize=9.sp.toPx()}
        for(i in 0..4) {
            val vx=xmin+(xmax-xmin)*i/4;val vy=ymin+(ymax-ymin)*i/4
            drawLine(colors.grid,point(vx,ymin),point(vx,ymax));drawLine(colors.grid,point(xmin,vy),point(xmax,vy))
            val xt=number(vx);val yt=number(vy)
            native.drawText(xt,point(vx,ymin).x-paint.measureText(xt)/2,top+height+15.dp.toPx(),paint)
            native.drawText(yt,left-6.dp.toPx()-paint.measureText(yt),point(xmin,vy).y+3.dp.toPx(),paint)
        }
        plot.optJSONArray("contours")?.let {contours->repeat(contours.length()){i->
            val contour=contours.getJSONObject(i);val level=contour.getInt("level");val dashed=contour.optBoolean("dashed",level!=0)
            contour.getJSONArray("segments").let {segments->repeat(segments.length()){j->
                val line=segments.getJSONArray(j);val a=line.getJSONArray(0);val b=line.getJSONArray(1)
                drawLine(colors.ink,point(a.getDouble(0),a.getDouble(1)),point(b.getDouble(0),b.getDouble(1)),if(level==0)2.dp.toPx() else 1.dp.toPx(),pathEffect=if(!dashed)null else PathEffect.dashPathEffect(floatArrayOf(6.dp.toPx(),4.dp.toPx())))
            }}
        }}
        plot.optJSONArray("curve")?.let {curve->
            val path=Path();repeat(curve.length()){i->val row=curve.getJSONArray(i);val at=point(row.getDouble(0),row.getDouble(1));if(i==0)path.moveTo(at.x,at.y) else path.lineTo(at.x,at.y)}
            drawPath(path,colors.accent,style=Stroke(2.dp.toPx()))
        }
        plot.getJSONArray("points").let {points->repeat(points.length()){i->
            val item=points.getJSONObject(i);val at=point(item.getDouble("x"),item.getDouble("y"))
            drawCircle(if(regression||item.optInt("class")==0)Color(0xff397bb5) else Color(0xffcf7820),3.dp.toPx(),at)
            if(item.optBoolean("support"))drawCircle(colors.ink,6.dp.toPx(),at,style=Stroke(1.dp.toPx()))
        }}
        native.drawText(xlabel,left+width/2-paint.measureText(xlabel)/2,top+height+36.dp.toPx(),paint)
        native.save();native.rotate(-90f,12.dp.toPx(),top+height/2)
        native.drawText(ylabel,12.dp.toPx()-paint.measureText(ylabel)/2,top+height/2,paint);native.restore()
    }
    PlotExportActions(exports,if(regression)"symvacas-svr-$kind" else "symvacas-svm")
}

@Composable internal fun SvmPredictions(report:JSONObject,digits:Int) {
    var expanded by remember(report){mutableStateOf(false)}
    val clipboard=LocalClipboardManager.current
    val classification=report.optString("task")=="classification"
    if(!classification)Text(tr("Prediction error = observed − predicted; MAE is mean absolute prediction error."),fontSize=11.sp)
    TextButton(onClick={expanded=!expanded}){Text(tr(if(classification)"Classification predictions" else "Regression predictions"))}
    if(!expanded)return
    val rows=report.optJSONArray("residuals") ?: return
    val support=(0 until rows.length()).any {rows.getJSONObject(it).has("supportVector")}
    val headers=(if(classification)listOf("Observation","Observed class","Predicted class","Decision score") else listOf("Observation","Observed value","Predicted value","Prediction error","Absolute error"))+if(support)listOf("Support vector") else emptyList()
    val keys=(if(classification)listOf("row","observed","fitted","decisionScore") else listOf("row","observed","fitted","predictionError","absoluteError"))+if(support)listOf("supportVector") else emptyList()
    val yes=tr("Yes");val no=tr("No");val translatedHeaders=headers.map {tr(it)}
    fun text(row:JSONObject,key:String)=if(key=="supportVector")(if(row.optBoolean(key))yes else no) else ResultDisplayFormat.formatText(when(key){"predictionError"->row.optString(key).ifBlank {row.optString("residual")};"absoluteError"->row.optString(key).ifBlank {kotlin.math.abs(row.optDouble("residual")).toString()};else->row.optString(key)},ResultDisplayMode.OFF,false,maxFractionDigits=digits,preserveSmallValues=true)
    Row(Modifier.horizontalScroll(rememberScrollState()),horizontalArrangement=Arrangement.spacedBy(14.dp)) {
        keys.forEachIndexed {i,key->Column(Modifier.width(IntrinsicSize.Max)) {
            Text(translatedHeaders[i],fontSize=11.sp,fontWeight=FontWeight.SemiBold)
            repeat(minOf(rows.length(),100)){j->Text(text(rows.getJSONObject(j),key),fontSize=11.sp)}
        }}
    }
    if(rows.length()>100)Text(tr("Showing first 100 rows; copy includes all rows."),fontSize=11.sp)
    TextButton(onClick={clipboard.setText(AnnotatedString(translatedHeaders.joinToString(",")+"\n"+(0 until rows.length()).joinToString("\n"){i->keys.joinToString(","){text(rows.getJSONObject(i),it)}}))}){Text(tr("Copy prediction CSV"))}
}
