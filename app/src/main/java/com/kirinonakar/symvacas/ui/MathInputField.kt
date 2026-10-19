package com.kirinonakar.symvacas.ui

import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.TextRange
import androidx.compose.ui.text.input.TextFieldValue
import com.kirinonakar.symvacas.math.Editor
import com.kirinonakar.symvacas.math.LatexInput

internal fun convertMathInput(previous:TextFieldValue,updated:TextFieldValue,multiline:Boolean,surface:Boolean=false):TextFieldValue {
    if(updated.composition!=null || previous.text==updated.text)return updated
    val converted=LatexInput.convertEdit(Editor(previous.text,previous.selection.end,previous.selection.start),updated.text,multiline,surface) ?: return updated
    return TextFieldValue(converted.source,TextRange(converted.cursor))
}

/** Keep the native selection and IME composition while normalizing inserted LaTeX. */
@Composable internal fun rememberMathInput(value:String,multiline:Boolean=false,surface:Boolean=false,onValue:(String)->Unit):Pair<TextFieldValue,(TextFieldValue)->Unit> {
    var draft by remember {mutableStateOf(TextFieldValue(value,TextRange(value.length)))}
    val current=if(draft.text==value)draft else TextFieldValue(value,TextRange(draft.selection.start.coerceIn(0,value.length),draft.selection.end.coerceIn(0,value.length)))
    return current to {updated->
        draft=convertMathInput(current,updated,multiline,surface)
        if(draft.text!=value)onValue(draft.text)
    }
}

@Composable internal fun MathField(value:String,label:String,modifier:Modifier=Modifier,translate:Boolean=true,multiline:Boolean=false,onValue:(String)->Unit) {
    val (input,change)=rememberMathInput(value,multiline,onValue=onValue)
    MathClipboard {OutlinedTextField(input,change,modifier=modifier.keepInputVisible(),label={Text(if(translate)tr(label) else label)},singleLine=!multiline,minLines=if(multiline)2 else 1)}
}
