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

private fun latexClipEntry(entry:ClipEntry?):ClipEntry? {
    val data=entry?.clipData ?: return null
    if(data.itemCount!=1)return entry
    val text=data.getItemAt(0).text?.toString() ?: return entry
    return ClipEntry(ClipData.newPlainText(data.description.label,mathCopyText(text,true)))
}

/** Selection menus query nativeClipboardManager before offering Paste. */
internal fun latexClipboard(clipboard:Clipboard):AndroidClipboard = object:AndroidClipboard,Clipboard by clipboard {
    // Keep the AndroidClipboard contract as well as the delegated Clipboard methods.
    // A generic Clipboard wrapper fails the platform type check on long-press.
    override val clipboardManager get()=clipboard.nativeClipboardManager
    override suspend fun setClipEntry(clipEntry:ClipEntry?)=clipboard.setClipEntry(latexClipEntry(clipEntry))
}

/** Intercept the platform Copy/Cut used by native math text fields. Reads stay untouched. */
@Composable internal fun MathClipboard(content:@Composable ()->Unit) {
    if(!LocalCopyAsLatex.current){content();return}
    val clipboard=LocalClipboard.current
    val legacy=LocalClipboardManager.current
    val wrapped=remember(clipboard){latexClipboard(clipboard)}
    val old=remember(legacy){object:ClipboardManager by legacy {
        override fun setText(annotatedString:AnnotatedString)=legacy.setText(AnnotatedString(mathCopyText(annotatedString.text,true)))
        override fun setClip(clipEntry:ClipEntry?)=legacy.setClip(latexClipEntry(clipEntry))
    }}
    CompositionLocalProvider(LocalClipboard provides wrapped,LocalClipboardManager provides old,content=content)
}
