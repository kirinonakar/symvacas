package com.kirinonakar.symvacas.ui

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.kirinonakar.symvacas.calculator.ResultDisplayMode
import org.json.JSONObject

@Composable internal fun SvmDecisionEquation(report:JSONObject,digits:Int,labels:Map<String,String>) {
    val classification=report.optString("task")=="classification"
    val equation=report.optJSONObject(if(classification)"decisionEquation" else "predictionEquation") ?: return
    val variables=equation.getJSONArray("variables").let {a->(0 until a.length()).map {a.getString(it)}}
    fun number(v:Double)=ResultDisplayFormat.formatText(v.toString(),ResultDisplayMode.OFF,false,maxFractionDigits=digits,preserveSmallValues=true)
    Text(tr(if(classification)"Decision function" else "Prediction function"),fontSize=12.sp,fontWeight=FontWeight.SemiBold)
    val source=equation.optString("expression")
    val tree=remember(source,digits){if(source.isBlank())null else regressionFormulaDisplayTree(source,digits)}
    Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState())) {
        if(tree!=null){MathText("f(x) = ",12f);MathNode(tree,12f)}
        else Text(equation.optString("formula"),fontSize=12.sp)
    }
    Text(tr(if(classification)"f(x) >= 0: class 1; f(x) < 0: class 0." else "Predicted response = f(x)."),fontSize=11.sp)
    Text(variables.mapIndexed {i,v->"$v = ${labels["b${i+1}"] ?: v}"}.joinToString(" · "),fontSize=11.sp)
    if(report.optString("kernel")!="rbf"&&classification)return
    val scales=equation.getJSONArray("scales")
    if(report.optString("kernel")=="rbf")Text("b=${number(equation.getDouble("intercept"))} · γ=${number(report.getDouble("gamma"))} · "+(0 until scales.length()).joinToString(" · "){"s${it+1}=${number(scales.getDouble(it))}"},fontSize=11.sp)
    Text(tr(if(classification)"aᵢ = αᵢyᵢ, αᵢ ≥ 0; yᵢ = −1 for class 0, +1 for class 1." else "aᵢ = αᵢ − αᵢ*, with αᵢ ≥ 0 and αᵢ* ≥ 0."),fontSize=11.sp)
    var expanded by remember(report){mutableStateOf(false)}
    TextButton(onClick={expanded=!expanded}){Text(tr("Support vector terms"))}
    if(!expanded)return
    val terms=equation.getJSONArray("supportTerms")
    val headers=listOf(tr("Observation"),tr(if(classification)"Signed coefficient (αᵢyᵢ)" else "Signed coefficient (αᵢ−αᵢ*)"))+variables.indices.map {"vᵢ${it+1}"}
    Row(Modifier.horizontalScroll(rememberScrollState()),horizontalArrangement=Arrangement.spacedBy(14.dp)) {
        headers.forEachIndexed {i,header->Column(Modifier.width(IntrinsicSize.Max)){
            Text(header,fontSize=11.sp,fontWeight=FontWeight.SemiBold)
            repeat(minOf(terms.length(),100)){j->val term=terms.getJSONObject(j);val value=when(i){0->term.getDouble("row");1->term.getDouble("coefficient");else->term.getJSONArray("coordinates").getDouble(i-2)};Text(number(value),fontSize=11.sp)}
        }}
    }
    if(terms.length()>100)Text(tr("Showing first 100 rows; copy includes all rows."),fontSize=11.sp)
}
