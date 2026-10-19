package com.kirinonakar.symvacas.ui

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.stateDescription
import androidx.compose.ui.unit.sp
import com.kirinonakar.symvacas.ui.theme.LocalInstrument
import org.json.JSONObject

internal fun statisticsInterpretationKey(schema:JSONObject,report:JSONObject,kind:String="statistics"):String=when {
    kind=="survival"->"survival"
    kind=="regression"&&report.optBoolean("bayesian")->"bayesian"
    kind=="regression"&&report.optString("model").isNotBlank()->"prediction"
    kind=="regression"->if(report.optString("fitScale")=="binomial")"logistic" else "regression"
    else->schema.getJSONObject("analyses").optString(report.optString("analysis"),"default")
}

@Composable internal fun StatisticsInterpretation(report:JSONObject,kind:String="statistics") {
    val context=LocalContext.current
    val schema=remember {context.assets.open("statistics_interpretation.json").bufferedReader().use {JSONObject(it.readText())}}
    val key=statisticsInterpretationKey(schema,report,kind)
    val text=schema.getJSONObject("guides").getJSONObject(key).getString(if(isKorean())"ko" else "en")
    // A new result starts closed; opening an explanation never changes results.
    var expanded by remember(report) {mutableStateOf(false)}
    val collapseRequest=LocalStatisticsCollapseRequest.current
    LaunchedEffect(collapseRequest){if(collapseRequest>0)expanded=false}
    val description=tr(if(expanded)"Expanded" else "Collapsed")
    val c=LocalInstrument.current
    Column(Modifier.fillMaxWidth().testTag("statistics-$kind-interpretation")) {
        TextButton(onClick={expanded=!expanded},modifier=Modifier.testTag("statistics-$kind-interpretation-toggle").semantics {stateDescription=description}) {
            Text((if(expanded)"▾ " else "▸ ")+(if(isKorean())"해석 방법" else "How to interpret"),fontSize=12.sp,color=c.muted)
        }
        if(expanded)SelectionContainer {Text(text,Modifier.fillMaxWidth(),fontSize=11.sp,color=c.muted)}
    }
}
