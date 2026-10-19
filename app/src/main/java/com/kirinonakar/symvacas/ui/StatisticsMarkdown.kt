package com.kirinonakar.symvacas.ui

import org.json.JSONObject
import com.kirinonakar.symvacas.calculator.ResultDisplayMode

internal fun regressionEquationCopyText(result:JSONObject,digits:Int,variables:Map<String,String> = emptyMap(),prefix:String?=null):String? {
    val report=result.optJSONObject("regression") ?: return null
    if(report.optString("model")=="randomforest")return null
    val svm=report.optString("model")=="svm"
    val classification=report.optString("task")=="classification"
    val equation=report.optJSONObject(if(classification)"decisionEquation" else "predictionEquation")
    if(svm&&equation?.optString("expression").isNullOrBlank())return equation?.optString("formula")?.takeIf(String::isNotBlank)
    val source=if(svm)equation!!.getString("expression") else result.optString("exact").ifBlank {result.optString("decimal")}
    val tree=regressionFormulaDisplayTree(source.replace("**","^"),digits,variables) ?: return null
    val logistic=report.optString("fitScale")=="binomial"||report.optString("model").contains("logistic")
    return (if(svm&&classification)"f(x) = " else prefix ?: if(svm)"ŷ = " else if(logistic)"P(y = 1) = " else "y = ")+equationFormulaText(tree)
}

internal fun statisticsFormattedCopyCell(cell:JSONObject,digits:Int,mode:ResultDisplayMode=ResultDisplayMode.OFF,grouping:Boolean=false,engineeringConversion:Boolean=false,engineeringShift:Int=0):String {
    fun complex(node:JSONObject):Boolean {
        if(node.optString("kind") in setOf("sum","product","binary","function","call","root","power"))return true
        val args=node.optJSONArray("args")
        return (0 until (args?.length() ?: 0)).any {args!!.optJSONObject(it)?.let(::complex)==true}
    }
    val sourceTree=ResultDisplayFormat.resultTree(cell,true,false,engineeringConversion,false,false)
    val power=sourceTree?.optJSONArray("args")?.optJSONObject(1)
    val notation=sourceTree?.optString("kind") in listOf("product","binary")&&power?.optString("kind")=="power"&&power.optJSONArray("args")?.optJSONObject(0)?.optString("value")=="10"
    if(sourceTree!=null&&!notation&&complex(sourceTree)) {
        return equationFormulaText(ResultDisplayFormat.formatTree(sourceTree,if(engineeringConversion)ResultDisplayMode.ENGINEERING else mode,grouping,engineeringShift,engineeringConversion,digits,preserveSmallValues=true))
    }
    val source=cell.optString("decimal").ifBlank {cell.optString("exact")}
    if(sourceTree?.optString("kind")=="text"&&source.any {it in "+*/^()"}) {
        regressionFormulaDisplayTree(source,digits)?.let {return equationFormulaText(it)}
    }
    return ResultDisplayFormat.resultText(cell,true,false,mode,grouping,engineeringConversion,engineeringShift,false,false,digits,preserveSmallValues=true)
}

internal fun regressionResultForCopy(fitted:JSONObject?,report:JSONObject):JSONObject? =
    fitted?.takeIf {it.optJSONObject("regression")?.toString()==report.toString()}

internal fun markdownCell(value:String):String=value.replace("\\","\\\\")
    .replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    .replace("|","\\|").replace("*","\\*").replace("_","\\_").replace("`","\\`")
    .replace("[","\\[").replace("]","\\]")
    .replace("\r\n","\n").replace("\r","\n").replace("\n","<br>")

internal fun statisticsDetailText(detail:JSONObject,translate:(String)->String):String {
    val context=detail.optJSONArray("context")
    val identifiers=(0 until (context?.length() ?: 0)).joinToString(" / ") {
        val item=context!!.getJSONObject(it)
        translate(item.optString("label"))+": "+item.optString("value")
    }
    val section=detail.optString("section").takeUnless {it=="Summary"}.orEmpty()
    return listOf(if(section.isBlank())"" else translate(section),identifiers,
        translate(detail.optString("label"))+": "+translate(detail.optString("text"))).filter {it.isNotBlank()}.joinToString(" · ")
}

/** One presentation for model descriptions, assumptions and interpretation notes. */
internal fun statisticsModelDetails(report:JSONObject,note:String="",translate:(String)->String):List<String> {
    fun normalize(value:String)=value.trim().replace(Regex("\\s+")," ")
    val paragraphs=mutableListOf<String>();val seen=mutableSetOf<String>();val detailTexts=mutableSetOf<String>()
    fun add(text:String,key:String){if(text.isNotBlank()&&seen.add(key))paragraphs+=text}
    report.optJSONArray("details")?.let {details->for(i in 0 until details.length()) {
        val detail=details.getJSONObject(i);val raw=normalize(detail.optString("text"))
        if(raw.isNotBlank()) {
            detailTexts+=raw;val text=statisticsDetailText(detail,translate)
            add(text,if((detail.optJSONArray("context")?.length() ?: 0)>0)normalize(text) else raw)
        }
    }}
    val plain=mutableListOf<String>()
    for(key in listOf("assumptions","notes"))report.optJSONArray(key)?.let {values->for(i in 0 until values.length())plain+=values.getString(i)}
    plain+=note
    for(raw in plain){val key=normalize(raw);if(key.isNotBlank()&&key !in detailTexts)add(translate(raw.trim()),key)}
    return paragraphs
}

internal fun statisticsResultMarkdown(result:JSONObject,formatCell:(JSONObject)->String,regressionEquation:String?=null,translate:(String)->String):String {
    val report=result.optJSONObject("statisticsReport") ?: result.optJSONObject("statisticsCopyReport") ?: return formatCell(result)
    val blocks=mutableListOf("## "+markdownCell(translate(report.optString("title"))))
    report.optString("context").takeIf(String::isNotBlank)?.let {blocks.add(markdownCell(it))}
    report.optJSONArray("warnings")?.let {warnings->for(index in 0 until warnings.length()) {
        val warning=warnings.optJSONObject(index)
        blocks.add(markdownCell((warning?.optString("label")?.takeIf(String::isNotBlank)?.let {"$it: "} ?: "")+translate(warning?.optString("text") ?: warnings.optString(index))))
    }}
    if(regressionEquation!=null) {
        val fence="`".repeat(maxOf(3,(Regex("`+").findAll(regressionEquation).maxOfOrNull {it.value.length} ?: 0)+1))
        blocks.add("### "+translate(if(result.optJSONObject("regression")?.optString("model")=="svm")(if(result.getJSONObject("regression").optString("task")=="classification")"Decision function" else "Prediction function") else "Regression equation")+"\n\n"+fence+"text\n"+regressionEquation+"\n"+fence)
    }
    val sections=report.optJSONArray("sections")
    for(index in 0 until (sections?.length() ?: 0)) {
        val section=sections!!.getJSONObject(index)
        val columns=section.getJSONArray("columns")
        val rows=section.optJSONArray("copyRows") ?: section.getJSONArray("rows")
        fun line(values:List<String>)="| "+values.joinToString(" | ")+" |"
        val table=mutableListOf(line(List(columns.length()){markdownCell(if(section.optBoolean("literalColumns"))columns.getString(it) else translate(columns.getString(it)))}),line(List(columns.length()){ "---" }))
        for(rowIndex in 0 until rows.length()) {
            val row=rows.getJSONArray(rowIndex)
            if(regressionEquation!=null&&columns.optString(0)=="Metric"&&row.optString(0) in listOf("Fitted expression","Decision function","Prediction function"))continue
            table.add(line(List(columns.length()){column->
                val text=row.optJSONObject(column)?.let(formatCell) ?: row.optString(column).let {
                    if(column==0&&rowIndex==section.optInt("totalRow",-1)||columns.optString(column) in listOf("Metric","Check","Interpretation","Sample","Role","R²","Kind","Support vector","Effect","Intercept / drift","Status")||columns.optString(column)=="Parameter"&&report.optString("analysis") in listOf("arima","sarima")||columns.optString(column)=="Value"&&row.optString(0) in listOf("Intercept / drift","Fit status","Evaluation","Cross-validation"))translate(it)
                    else if(report===result.optJSONObject("statisticsCopyReport")&&it.toBigDecimalOrNull()!=null)formatCell(JSONObject().put("decimal",it).put("exact",it)) else it
                }
                markdownCell(text)
            }))
        }
        if(table.size>2)blocks.add("### "+markdownCell(translate(section.optString("title")))+"\n\n"+table.joinToString("\n"))
    }
    val descriptions=statisticsModelDetails(report,result.optString("note"),translate)
    if(descriptions.isNotEmpty())blocks.add("### "+translate("Model details")+"\n\n"+descriptions.joinToString("\n\n",transform=::markdownCell))
    result.optJSONArray("conditions")?.takeIf {it.length()>0}?.let {conditions->
        blocks.add("### "+translate("Conditions")+"\n\n"+(0 until conditions.length()).joinToString("\n"){"- "+markdownCell(conditions.getString(it))})
    }
    return blocks.joinToString("\n\n")
}

internal fun statisticsResultCopyText(m:com.kirinonakar.symvacas.calculator.CalculatorModel,result:JSONObject,language:String,regressionVariables:Map<String,String> = emptyMap(),regressionPrefix:String?=null):String {
    val dedicated=result.has("statisticsCopyReport")
    return statisticsResultMarkdown(result,{statisticsFormattedCopyCell(it,m.displayDigits,
        if(dedicated)ResultDisplayMode.OFF else m.resultDisplayMode,if(dedicated)false else m.thousandsSeparator,
        !dedicated&&m.engineeringConversion,if(dedicated)0 else m.engineeringShift)},
        regressionEquationCopyText(result,m.displayDigits,regressionVariables,regressionPrefix)){translateLabel(it,language)}
}
