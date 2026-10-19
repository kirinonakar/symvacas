package com.kirinonakar.symvacas.calculator

import androidx.lifecycle.viewModelScope
import com.kirinonakar.symvacas.math.statisticsRequest
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch
import org.json.JSONObject

internal object CalculatorStatisticsActions {
    fun CalculatorModel.performCalculateStatistics(source:String,termLabels:Map<String,String>) {
        if(busy||regressionBusy)return
        val input=try {statisticsRequest(source,removeComputationLimit)} catch(e:Exception) {error=e.message ?: "Syntax ERROR";return}
        val calculationRequest=request().put("tree",JSONObject(input.tree.json()))
            .put("statisticsDatasets",JSONObject(input.datasets)).put("statisticsTermLabels",JSONObject(termLabels))
            .put("variables",variables).put("equationSteps",false).put("solutionSteps",false)
        job=viewModelScope.launch {
            busy=true;error=""
            try {
                val response=engine.execute(calculationRequest)
                if(response.optBoolean("ok")) {
                    statisticsResult=response;statisticsResultSource=source
                    val next=JSONObject(variables.toString())
                    if(response.has("resultAst"))next.put("Ans",response.getJSONObject("resultAst")) else next.remove("Ans")
                    variables=next
                    save()
                } else error=response.optString("error").ifBlank {"Math ERROR"}
            } catch(e:Exception) {
                if(e is CancellationException)throw e
                error=e.message?.takeIf(String::isNotBlank) ?: "Math ERROR"
            } finally {busy=false}
        }
    }
    fun CalculatorModel.performSaveDataSet(name:String,csv:String,kind:String) {
        try {
            statisticsState.saveDataSet(name,csv,kind)
            error="";save()
        } catch(e:Exception) { error=e.message ?: "Could not save dataset" }
    }
    fun CalculatorModel.performDeleteDataSet(name:String) {
        statisticsState.deleteDataSet(name)
        save()
    }
    fun CalculatorModel.performSaveStatistics(name:String,data:String,kind:String,regression:String,plot:String,csv:Boolean,selected:String,isNew:Boolean,customFormula:String,customVariable:String,customInitials:String,polynomialDegree:String,logisticResponse:String,lassoAlpha:String,forestTrees:String,forestDepth:String,forestSeed:String,regularization:String,l1Ratio:String,forestTask:String,bayesianPriorSD:String,bayesianLevel:String,bayesianShape:String,bayesianScale:String,bayesianMethod:String,nutsSamples:String,nutsWarmup:String,nutsMaxDepth:String,nutsSeed:String,nutsChains:String) {
        if(storageReplaced)return
        statisticsState.updateSelection(name,data,kind,regression,plot,csv,selected,isNew,customFormula,customVariable,customInitials,polynomialDegree,logisticResponse,lassoAlpha,forestTrees,forestDepth,forestSeed,regularization,l1Ratio,forestTask,bayesianPriorSD,bayesianLevel,bayesianShape,bayesianScale,bayesianMethod,nutsSamples,nutsWarmup,nutsMaxDepth,nutsSeed,nutsChains)
        statisticsState.saveSelection()
    }
    fun CalculatorModel.performFitRegression(source: String, data: String, responseColumn:Int?) {
        regressionJob?.cancel()
        val statisticsInput=try {statisticsRequest(source,removeComputationLimit)} catch(e:Exception) {error=e.message ?: "Syntax ERROR";return}
        val tree=statisticsInput.tree
        val fittedMode=tree.args.getOrNull(1)?.value ?: "linear"
        val calculationRequest=request().put("tree",JSONObject(tree.json())).put("statisticsDatasets",JSONObject(statisticsInput.datasets))
            .put("variables",variables).put("equationSteps",false).put("solutionSteps",false)
        regressionJob=viewModelScope.launch {
            val currentJob=coroutineContext[Job]
            statisticsState.regressionBusy=true;error=""
            try {
                val response=engine.execute(calculationRequest)
                if(response.optBoolean("ok")) {
                    statisticsResult=response;statisticsResultSource=source
                    statisticsRegressionResult=response
                    val array=response.optJSONArray("curve")
                    statisticsState.regressionCurve=if(array==null)emptyList() else (0 until array.length()).mapNotNull {index->array.optJSONArray(index)?.let {pair->pair.optDouble(0) to pair.optDouble(1)}}
                    statisticsState.regressionFit=response.optString("exact");statisticsState.regressionData=data;statisticsState.regressionMode=fittedMode
                    statisticsState.regressionResponseColumn=if(fittedMode in listOf("multiple","logistic","polynomial","ridge","lasso","elasticnet","logisticridge","logisticlasso","logisticelasticnet","randomforest","randomforestclassifier","randomforestregressor","svm","svc","svr","bayeslinear","bayeslogistic"))responseColumn else null
                    statisticsState.regressionCorrelation=response.optDouble("correlation",Double.NaN).takeIf(Double::isFinite)
                    val parameters=response.optJSONArray("parameters")
                    statisticsState.regressionReport=response.optJSONObject("regression")
                    statisticsState.regressionParameters=if(parameters==null)emptyList() else (0 until parameters.length()).mapNotNull {index->
                        parameters.optJSONArray(index)?.let {pair->pair.optString(0) to pair.optString(1)}
                    }
                    val next=JSONObject(variables.toString())
                    if(response.has("resultAst")) next.put("Ans",response.getJSONObject("resultAst")) else next.remove("Ans")
                    variables=next
                    save()
                } else {statisticsState.clearRegression();error=response.optString("error").ifBlank {"Math ERROR"}}
            } catch(e:Exception) {
                if(e is CancellationException)throw e
                statisticsState.clearRegression();error=e.message?.takeIf(String::isNotBlank) ?: "Math ERROR"
            } finally {if(regressionJob===currentJob){statisticsState.regressionBusy=false;regressionJob=null}}
        }
    }
    fun CalculatorModel.performClearRegression() {
        regressionJob?.cancel()
        statisticsState.clearRegression()
        statisticsRegressionResult=null
        save()
    }
    fun CalculatorModel.performCancelRegression() {
        if(!statisticsState.regressionBusy)return
        regressionJob?.cancel()
        regressionJob=null
        statisticsState.regressionBusy=false
    }
}
