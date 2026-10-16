package com.kirinonakar.symvacas.ui

import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.*
import androidx.compose.ui.draw.clipToBounds
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.*
import androidx.compose.ui.text.PlatformTextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.style.LineHeightStyle
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.*
import com.kirinonakar.symvacas.calculator.removeGraphInputLine
import com.kirinonakar.symvacas.ui.theme.LocalInstrument

@Composable internal fun LineNumberedMathInput(
    value:String,onValue:(String)->Unit,label:String,modifier:Modifier=Modifier,
    multiline:Boolean=true,visibleLines:Int=3,tag:String="equation"
) {
    val c=LocalInstrument.current
    val (input,change)=rememberMathInput(value,multiline=multiline,onValue=onValue)
    val vertical=rememberScrollState();val horizontal=rememberScrollState()
    var focused by remember {mutableStateOf(false)}
    val lineHeight=24.sp
    val rowHeight=with(LocalDensity.current){lineHeight.toDp()}
    // A full line box also keeps the first editable line aligned with its gutter row.
    val style=MaterialTheme.typography.bodyLarge.copy(fontFamily=FontFamily.Monospace,fontSize=14.sp,lineHeight=lineHeight,color=c.ink,
        platformStyle=PlatformTextStyle(includeFontPadding=false),
        lineHeightStyle=LineHeightStyle(LineHeightStyle.Alignment.Center,LineHeightStyle.Trim.None))
    val deleteLabel=tr("Delete line")
    val inputLabel=label
    Column(modifier) {
        Row(Modifier.fillMaxWidth().height(rowHeight*visibleLines+20.dp).border(1.dp,if(focused)c.accent else c.grid,RoundedCornerShape(7.dp))) {
            Column(Modifier.width(46.dp).fillMaxHeight().clipToBounds().background(c.scientific).verticalScroll(vertical).padding(vertical=10.dp)) {
                repeat(value.count {it=='\n'}+1) {index->
                    Row(Modifier.fillMaxWidth().height(rowHeight),verticalAlignment=Alignment.CenterVertically) {
                        Box(Modifier.width(24.dp).fillMaxHeight().clickable {onValue(removeGraphInputLine(value,index))}.semantics {contentDescription="$deleteLabel ${index+1}"}.testTag("$tag-delete-line-${index+1}"),contentAlignment=Alignment.Center) {
                            Text("×",style=style.copy(color=c.muted))
                        }
                        Text("${index+1}",Modifier.weight(1f).padding(end=4.dp),style=style.copy(color=c.muted),textAlign=TextAlign.End,softWrap=false)
                    }
                }
            }
            VerticalDivider(color=c.grid)
            BoxWithConstraints(Modifier.weight(1f).fillMaxHeight()) {
                val fieldWidth=(maxWidth-16.dp).coerceAtLeast(0.dp)
                Box(Modifier.fillMaxSize().verticalScroll(vertical)) {
                    Box(Modifier.horizontalScroll(horizontal)) {
                        MathClipboard {BasicTextField(input,change,Modifier.widthIn(min=fieldWidth).keepInputVisible().onFocusChanged {focused=it.isFocused}.testTag("$tag-source").semantics {contentDescription=inputLabel},
                                singleLine=!multiline,textStyle=style,cursorBrush=SolidColor(c.accent),
                                decorationBox={inner->Box(Modifier.padding(horizontal=8.dp,vertical=10.dp)){inner()}})}
                    }
                }
            }
        }
    }
}
