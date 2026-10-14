package com.kirinonakar.symvacas.ui

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.*
import androidx.compose.ui.platform.LocalContext
import com.kirinonakar.symvacas.calculator.CalculatorModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

// Document launchers and asynchronous writing of a captured graph export.
internal class GraphSaveActions(val exports:GraphExportState,val exporting:Boolean,val message:String,val prepare:(String)->Unit)
@Composable internal fun rememberGraphSaveActions(m:CalculatorModel):GraphSaveActions {
    val context=LocalContext.current
    val exportScope=rememberCoroutineScope()
    val exports=remember {GraphExportState()}
    var exportImage by remember {mutableStateOf<GraphExportImage?>(null)}
    var exportMessage by remember {mutableStateOf("")}
    var exporting by remember {mutableStateOf(false)}
    fun saveExport(uri:android.net.Uri?) {
        val image=exportImage
        exportImage=null
        if(uri==null||image==null){exporting=false;return}
        exportScope.launch {
            try {
                withContext(Dispatchers.IO) {
                    context.contentResolver.openOutputStream(uri,"wt")?.use {image.writeTo(it)} ?: error("Could not open the selected file for writing")
                }
                exportMessage="Graph saved"
            } catch(e:Exception) {m.error=e.message ?: "Could not save the graph"}
            finally {exporting=false}
        }
    }
    val saveSvg=rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("image/svg+xml"),::saveExport)
    val savePng=rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("image/png"),::saveExport)
    fun prepareExport(format:String) {
        try {
            val capture=exports.capture ?: return
            exportImage=capture(format)
            exporting=true;exportMessage=""
            if(format=="svg")saveSvg.launch("symvacas-graph.svg")else savePng.launch("symvacas-graph.png")
        } catch(e:Exception) {exporting=false;exportImage=null;m.error=e.message ?: "Could not save the graph"}
    }
    return GraphSaveActions(exports,exporting,exportMessage,::prepareExport)
}
