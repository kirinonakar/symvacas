package com.kirinonakar.symvacas.ui

import android.content.ClipData
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.relocation.BringIntoViewRequester
import androidx.compose.foundation.relocation.bringIntoViewRequester
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.ClipEntry
import androidx.compose.ui.platform.LocalClipboard
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import com.kirinonakar.symvacas.calculator.CalculatorModel
import com.kirinonakar.symvacas.ui.theme.LocalInstrument
import kotlinx.coroutines.launch

@Composable
internal fun UtilityResultCard(copyText:String?, onClear:(()->Unit)?, modifier:Modifier=Modifier, content:@Composable ColumnScope.()->Unit) {
    val clipboard=LocalClipboard.current
    val scope=rememberCoroutineScope()
    val colors=LocalInstrument.current
    Surface(modifier.fillMaxWidth(),shape=MaterialTheme.shapes.medium,color=colors.display,
        contentColor=colors.ink,border=BorderStroke(1.dp,colors.accent.copy(alpha=.45f))) {
        Column(Modifier.padding(horizontal=14.dp,vertical=8.dp)) {
            Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically) {
                Text(tr("Result"),Modifier.weight(1f),style=MaterialTheme.typography.titleMedium,color=colors.accent)
                if(copyText!=null) TextButton(onClick={scope.launch {clipboard.setClipEntry(ClipEntry(ClipData.newPlainText("Result",copyText)))}}) { Text(tr("Copy")) }
                if(onClear!=null) TextButton(onClick=onClear) { Text(tr("Clear")) }
            }
            Column(Modifier.fillMaxWidth().padding(bottom=8.dp).semantics { liveRegion=LiveRegionMode.Polite },
                verticalArrangement=Arrangement.spacedBy(6.dp),content=content)
        }
    }
}

@Composable
internal fun UtilityMathResult(m:CalculatorModel,workspace:String,decimal:Boolean,onDecimalChange:((Boolean)->Unit)?=null) {
    val snapshot=m.utilityResults[workspace] ?: return
    val result=snapshot.response
    val requester=remember { BringIntoViewRequester() }
    LaunchedEffect(snapshot) { if(!snapshot.pending) requester.bringIntoView() }
    val details=result?.let {
        val conditions=it.optJSONArray("conditions")
        listOf(it.optString("note").takeIf { snapshot.unit.isBlank() }.orEmpty())+
            (0 until (conditions?.length() ?: 0)).map { index->conditions?.optString(index).orEmpty() }
    }.orEmpty().filter { it.isNotBlank() }
    val copyText=result?.let {
        val text=if(onDecimalChange!=null&&m.copyAsLatex){
            ResultDisplayFormat.resultTree(it,decimal,false,false,false,false)?.let { tree->
                latexTree(ResultDisplayFormat.formatTree(tree,m.resultDisplayMode,false,maxFractionDigits=m.displayDigits,preserveSmallValues=true))
            } ?: mathCopyText(it.optString(if(decimal)"decimal" else "exact"),true)
        }else ResultDisplayFormat.resultText(it,decimal,false,m.resultDisplayMode,m.thousandsSeparator,false,0,false,false,m.displayDigits,preserveSmallValues=true)
        (listOf(listOf(text,snapshot.unit).filter(String::isNotBlank).joinToString(" "))+details).joinToString("\n")
    }
    val clear: (() -> Unit)? = if(snapshot.pending)null else ({m.utilityResults.remove(workspace)})
    UtilityResultCard(copyText,clear,Modifier.bringIntoViewRequester(requester)) {
        when {
            snapshot.error.isNotEmpty()->Text(tr(snapshot.error),color=MaterialTheme.colorScheme.error)
            result==null->Text(tr("Calculating…"),color=LocalInstrument.current.muted)
            else-> {
                if(onDecimalChange!=null) Row(horizontalArrangement=Arrangement.spacedBy(8.dp)) {
                    FilterChip(selected=!decimal,onClick={onDecimalChange(false)},label={Text(tr("Fraction"))})
                    FilterChip(selected=decimal,onClick={onDecimalChange(true)},label={Text(tr("Decimal"))})
                }
                UtilityResultDetail(snapshot.context)
                Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.spacedBy(8.dp),verticalAlignment=Alignment.CenterVertically) {
                    Box(Modifier.weight(1f)) {
                        ResultMath(result,decimal,m.outputFont,displayMode=m.resultDisplayMode,thousandsSeparator=m.thousandsSeparator,
                            displayDigits=m.displayDigits,preserveSmallValues=true)
                    }
                    if(snapshot.unit.isNotBlank())Text(snapshot.unit,style=MaterialTheme.typography.titleSmall,color=LocalInstrument.current.accent)
                }
                details.forEach { UtilityResultDetail(it) }
            }
        }
    }
}

@Composable
internal fun UtilityResultDetail(text:String) {
    Text(text,style=MaterialTheme.typography.bodySmall,color=LocalInstrument.current.muted)
}
