@file:Suppress("DEPRECATION")
package com.kirinonakar.symvacas.ui

import android.content.ClipData
import androidx.compose.runtime.*
import androidx.compose.ui.platform.*
import androidx.compose.ui.text.AnnotatedString
import com.kirinonakar.symvacas.math.Expr
import com.kirinonakar.symvacas.math.LatexOutput
import org.json.JSONObject

internal val LocalCopyAsLatex=staticCompositionLocalOf {false}
internal fun mathCopyText(text:String,enabled:Boolean)=if(enabled)LatexOutput.convert(text) else text
internal fun latexTree(tree:JSONObject):String {
    fun expr(node:JSONObject):Expr {
        val args=node.optJSONArray("args")
        return Expr(node.optString("kind"),node.optString("value"),List(args?.length() ?: 0){expr(args!!.getJSONObject(it))})
    }
    return LatexOutput.render(expr(tree))
}

/** Intercept the platform Copy/Cut used by native math text fields. Reads stay untouched. */
@Composable internal fun MathClipboard(content:@Composable ()->Unit) {
    if(!LocalCopyAsLatex.current){content();return}
    val clipboard=LocalClipboard.current
    val legacy=LocalClipboardManager.current
    fun convert(entry:ClipEntry?):ClipEntry? {
        val data=entry?.clipData ?: return null
        if(data.itemCount!=1)return entry
        val text=data.getItemAt(0).text?.toString() ?: return entry
        return ClipEntry(ClipData.newPlainText(data.description.label,mathCopyText(text,true)))
    }
    val wrapped=remember(clipboard){object:Clipboard by clipboard {
        override suspend fun setClipEntry(clipEntry:ClipEntry?)=clipboard.setClipEntry(convert(clipEntry))
    }}
    val old=remember(legacy){object:ClipboardManager by legacy {
        override fun setText(annotatedString:AnnotatedString)=legacy.setText(AnnotatedString(mathCopyText(annotatedString.text,true)))
        override fun setClip(clipEntry:ClipEntry?)=legacy.setClip(convert(clipEntry))
    }}
    CompositionLocalProvider(LocalClipboard provides wrapped,LocalClipboardManager provides old,content=content)
}
