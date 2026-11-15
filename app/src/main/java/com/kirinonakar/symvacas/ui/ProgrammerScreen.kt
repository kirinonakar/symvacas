package com.kirinonakar.symvacas.ui

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.relocation.BringIntoViewRequester
import androidx.compose.foundation.relocation.bringIntoViewRequester
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.*
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.*
import com.kirinonakar.symvacas.calculator.CalculatorModel
import com.kirinonakar.symvacas.calculator.UtilityCalculation
import com.kirinonakar.symvacas.ui.theme.LocalInstrument

@Composable fun ProgrammerScreen(m: CalculatorModel) {
    var a by rememberSaveable { mutableStateOf("255") }; var b by rememberSaveable { mutableStateOf("15") }
    var base by rememberSaveable { mutableIntStateOf(10) }; var width by rememberSaveable { mutableIntStateOf(32) }; var signed by rememberSaveable { mutableStateOf(false) }
    Panel("Programmer","Fixed-width integers · two’s complement · exact bit operations") {
        Choices(listOf("2","8","10","16"),base.toString(),{base=it.toInt()})
        Choices(listOf("8","16","32","64"),width.toString(),{width=it.toInt()})
        Row(verticalAlignment=Alignment.CenterVertically) { Switch(signed,{signed=it}); Text("  "+tr("Signed interpretation")) }
        Field(a,"A · base $base",Modifier.fillMaxWidth()) { a=it }
        Field(b,"B / shift count · base $base",Modifier.fillMaxWidth()) { b=it }
        val context="$width ${tr("Bits")} · ${tr(if(signed)"Signed" else "Unsigned")}"
        listOf("","AND","OR","XOR","NOT","NAND","NOR","<<",">>").chunked(3).forEach { row->
            Row {
                row.forEach { op->
                    SmallAction(op.ifBlank { "Convert" },enabled=!m.busy) { m.program(a,b,base,width,signed,op,context) }
                }
            }
        }
        m.utilityResults["Programmer"]?.let { snapshot->
            ProgrammerResult(snapshot,onClear={m.utilityResults.remove("Programmer")},onCancel={m.cancel()})
        }
    }
}

@Composable
private fun ProgrammerResult(snapshot:UtilityCalculation,onClear:()->Unit,onCancel:()->Unit) {
    val requester=remember { BringIntoViewRequester() }
    LaunchedEffect(snapshot) { if(!snapshot.pending) requester.bringIntoView() }
    val bases=snapshot.response?.optJSONObject("bases")
    val values=bases?.let { listOf("DEC","HEX","OCT","BIN").associateWith(it::optString) }
    val copyText=values?.entries?.joinToString("\n") { (base,value)->"$base $value" }
    UtilityResultCard(copyText,onClear.takeUnless { snapshot.pending },Modifier.bringIntoViewRequester(requester)) {
        when {
            snapshot.pending->Row(verticalAlignment=Alignment.CenterVertically) {
                Text(tr("Calculating…"),Modifier.weight(1f),color=LocalInstrument.current.muted)
                TextButton(onClick=onCancel) { Text(tr("Cancel")) }
            }
            values==null->Text(tr(snapshot.error.ifBlank { "Math ERROR" }),color=MaterialTheme.colorScheme.error)
            else->{
                val c=LocalInstrument.current
                UtilityResultDetail(snapshot.context)
                Surface(Modifier.fillMaxWidth(),shape=MaterialTheme.shapes.small,color=c.body) {
                    Column(Modifier.padding(12.dp),verticalArrangement=Arrangement.spacedBy(8.dp)) {
                        for(base in listOf("DEC","HEX","OCT")) {
                            Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically) {
                                Text(base,Modifier.width(40.dp),style=MaterialTheme.typography.labelMedium,color=c.muted)
                                Text(values.getValue(base),Modifier.weight(1f),textAlign=TextAlign.End,fontFamily=FontFamily.Monospace,
                                    style=MaterialTheme.typography.titleMedium,color=if(base=="DEC")c.accent else c.ink)
                            }
                        }
                        HorizontalDivider()
                        UtilityResultDetail("BIN")
                        Text(values.getValue("BIN").chunked(4).joinToString(" "),fontFamily=FontFamily.Monospace,
                            style=MaterialTheme.typography.titleMedium,color=c.ink)
                    }
                }
            }
        }
    }
}
