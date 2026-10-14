package com.kirinonakar.symvacas.ui

import android.app.Activity
import android.content.Intent
import android.widget.Toast
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.*
import androidx.compose.ui.unit.*
import androidx.compose.ui.platform.LocalContext
import com.kirinonakar.symvacas.calculator.CalculatorModel
import com.kirinonakar.symvacas.ui.theme.LocalInstrument

@Composable fun SettingsDialog(m: CalculatorModel,close: ()->Unit) {
    val context=LocalContext.current
    var confirmation by remember {mutableStateOf("")}
    var dataMessage by remember {mutableStateOf("")}
    fun restart() {
        val activity=context as Activity
        activity.startActivity(Intent(activity,activity.javaClass))
        activity.finish()
    }
    fun reportFailure(e:Exception) {dataMessage=e.message ?: translateLabel("Could not save data",m.language)}
    val exportData=rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("application/json")) {uri->
        if(uri!=null)try {
            context.contentResolver.openOutputStream(uri,"wt")?.use {it.write(m.exportAllData().toByteArray(Charsets.UTF_8))} ?: error("Could not open the selected file for writing")
            dataMessage=translateLabel("Data exported",m.language)
        }catch(e:Exception){reportFailure(e)}
    }
    val importData=rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) {uri->
        if(uri!=null)try {
            val text=context.contentResolver.openInputStream(uri)?.bufferedReader(Charsets.UTF_8)?.use {it.readText()} ?: error("Could not read the selected file")
            m.importAllData(text)
            Toast.makeText(context,translateLabel("Data imported",m.language),Toast.LENGTH_SHORT).show()
            restart()
        }catch(e:Exception){reportFailure(e)}
    }
    if(confirmation.isNotEmpty())AlertDialog(onDismissRequest={confirmation=""},title={Text(tr(confirmation))},text={Text(tr(if(confirmation=="Delete all data")"Delete all variables, statistics data and functions? This cannot be undone." else "Reset history, settings, inputs, selections and expanded sections. Variables, saved statistics datasets and functions are preserved."))},
        dismissButton={TextButton(onClick={confirmation=""}){Text(tr("Cancel"))}},confirmButton={TextButton(onClick={
            try {if(confirmation=="Delete all data")m.deleteAllData()else m.resetAllSettings();restart()}catch(e:Exception){reportFailure(e)}
            confirmation=""
        }){Text(tr("Confirm"))}})
    val precisionChoices=listOf("10","15","30","50","100","200")
    val displayChoices=listOf("2","3","5","8","10","12","15")
    var customPrecision by rememberSaveable{mutableStateOf(m.precision.toString())}
    var customPrecisionVisible by rememberSaveable{mutableStateOf(m.precision.toString() !in precisionChoices)}
    var customDisplay by rememberSaveable{mutableStateOf(m.displayDigits.toString())}
    var customDisplayVisible by rememberSaveable{mutableStateOf(m.displayDigits.toString() !in displayChoices)}
    AlertDialog(onDismissRequest=close,modifier=Modifier.height(CatalogDialogHeight),title={Text(tr("Instrument setup"))},text={Column(Modifier.verticalScroll(rememberScrollState()),verticalArrangement=Arrangement.spacedBy(10.dp)) {
        Text(tr("Language")); Choices(listOf("English","한국어"),if(m.language=="ko")"한국어" else "English",{m.language=if(it=="한국어")"ko" else "en";m.save()})
        Text(tr("Appearance")); Choices(listOf("System","Light","Dark"),m.theme,{m.theme=it;m.save()})
        GraphColorSettings(m)
        Text(tr("Angle unit")); Choices(listOf("DEG","RAD","GRAD"),m.angle,{m.angle=it;m.recalculatePreview();m.save()})
        Text(tr("Internal precision · numeric algorithms")); Choices(precisionChoices+"Custom",if(customPrecisionVisible)"Custom" else m.precision.toString(),{if(it=="Custom")customPrecisionVisible=true else {customPrecisionVisible=false;m.precision=it.toInt();m.recalculatePreview();m.save()}})
        if(customPrecisionVisible) {Field(customPrecision,"Custom internal precision · 3–200",Modifier.fillMaxWidth()){customPrecision=it};TextButton(onClick={m.precision=customPrecision.toInt();m.recalculatePreview();m.save()},enabled=customPrecision.toIntOrNull() in 3..200){Text(tr("Apply internal precision"))}}
        Text(tr("Display digits · decimal places shown")); Choices(displayChoices+"Custom",if(customDisplayVisible)"Custom" else m.displayDigits.toString(),{if(it=="Custom")customDisplayVisible=true else {customDisplayVisible=false;m.displayDigits=it.toInt();m.recalculatePreview();m.save()}})
        if(customDisplayVisible) {Field(customDisplay,"Custom display digits · 2–200",Modifier.fillMaxWidth()){customDisplay=it};TextButton(onClick={m.displayDigits=customDisplay.toInt();m.recalculatePreview();m.save()},enabled=customDisplay.toIntOrNull() in 2..200){Text(tr("Apply display digits"))}}
        Text(if(isKorean())"내부 정밀도는 적분과 방정식 풀이 같은 수치 계산에 적용됩니다. 표시 자릿수는 결과에 보이는 자릿수만 제한하며 내부 정밀도를 넘지 않습니다. 정확한 정수, 분수, 기호식은 반올림하지 않습니다." else "Internal precision governs numeric algorithms such as integration and solving. Display digits limit the digits a result shows; they never exceed internal precision, and exact integers, fractions and symbolic forms are not rounded.",fontSize=11.sp,color=LocalInstrument.current.muted)
        Column(verticalArrangement=Arrangement.spacedBy(2.dp)) {
            Text("${tr("Input font")} · ${m.inputFont.toInt()} sp")
            CompactSlider(m.inputFont,{m.inputFont=it},Modifier.fillMaxWidth(),valueRange=10f..42f,steps=31,onValueChangeFinished={m.save()})
        }
        Column(verticalArrangement=Arrangement.spacedBy(2.dp)) {
            Text("${tr("Output font")} · ${m.outputFont.toInt()} sp")
            CompactSlider(m.outputFont,{m.outputFont=it},Modifier.fillMaxWidth(),valueRange=10f..48f,steps=37,onValueChangeFinished={m.save()})
        }
        Row(verticalAlignment=Alignment.CenterVertically) { Text(tr("Key vibration"),Modifier.weight(1f)); Switch(m.haptics,{m.haptics=it;m.save()}) }
        Row(verticalAlignment=Alignment.CenterVertically) { Text(tr("Key sound"),Modifier.weight(1f)); Switch(m.sound,{m.sound=it;m.save()}) }
        Row(verticalAlignment=Alignment.CenterVertically) { Text(tr("Save history locally"),Modifier.weight(1f)); Switch(m.persistHistory,{m.persistHistory=it;m.save()}) }
        Row(verticalAlignment=Alignment.CenterVertically) { Text(tr("Bracket auto-close"),Modifier.weight(1f)); Switch(m.autoCloseBrackets,{m.autoCloseBrackets=it;m.save()}) }
        Row(verticalAlignment=Alignment.CenterVertically) { Text(tr("Copy as LaTeX"),Modifier.weight(1f)); Switch(m.copyAsLatex,{m.copyAsLatex=it;m.save()}) }
        Row(verticalAlignment=Alignment.CenterVertically) { Text(tr("Remove computation limit"),Modifier.weight(1f)); Switch(m.removeComputationLimit,{m.removeComputationLimit=it;m.recalculatePreview();m.save()}) }
        Text(tr("Disables app time, workload, input size and exponent limits. Result size and precision settings stay unchanged; manual cancellation remains available."),fontSize=11.sp,color=LocalInstrument.current.muted)
        Row(verticalAlignment=Alignment.CenterVertically) { Text(tr("Calc mode step by step"),Modifier.weight(1f)); Switch(m.calcModeStepByStep,{m.calcModeStepByStep=it;m.recalculatePreview();m.save()}) }
        Row(verticalAlignment=Alignment.CenterVertically) { Text(if(isKorean())"입력 자동 줄바꿈 (Word wrap)" else "Input word wrap",Modifier.weight(1f)); Switch(m.wordWrap,{m.wordWrap=it;m.save()}) }
        HorizontalDivider()
        Text(tr("Data & reset"))
        Text(tr("Transfer variables, saved statistics datasets and functions between Android and Web. Matching names are replaced; other data and settings are kept."),fontSize=11.sp,color=LocalInstrument.current.muted)
        Row(horizontalArrangement=Arrangement.spacedBy(8.dp)) {
            TextButton(onClick={exportData.launch("symvacas-data.json")}){Text(tr("Export all data"))}
            TextButton(onClick={importData.launch(arrayOf("application/json","text/plain","application/octet-stream"))},enabled=!m.busy&&!m.graphBusy&&!m.regressionBusy&&!m.pythonBusy){Text(tr("Import all data"))}
        }
        TextButton(onClick={confirmation="Delete all data"},enabled=!m.busy&&!m.graphBusy&&!m.regressionBusy&&!m.pythonBusy){Text(tr("Delete all data"))}
        Text(tr("Reset history, settings, inputs, selections and expanded sections. Variables, saved statistics datasets and functions are preserved."),fontSize=11.sp,color=LocalInstrument.current.muted)
        TextButton(onClick={confirmation="Reset all settings"},enabled=!m.busy&&!m.graphBusy&&!m.regressionBusy&&!m.pythonBusy){Text(tr("Reset all settings"))}
        if(dataMessage.isNotBlank())Text(dataMessage,fontSize=12.sp)
    }},confirmButton={TextButton(onClick=close) { Text(tr("Done")) }})
}
