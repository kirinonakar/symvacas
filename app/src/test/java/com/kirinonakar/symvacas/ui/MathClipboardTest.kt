package com.kirinonakar.symvacas.ui

import androidx.compose.ui.platform.AndroidClipboard
import androidx.compose.ui.platform.ClipEntry
import androidx.compose.ui.platform.Clipboard
import androidx.compose.ui.platform.nativeClipboardManager
import com.kirinonakar.symvacas.calculator.ResultDisplayMode
import kotlinx.coroutines.runBlocking
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class MathClipboardTest {
    @Test fun selectionMenuCanReachTheNativeClipboardThroughTheLatexWrapper() = runBlocking {
        // The sentinel avoids calling Android framework stubs in this JVM test,
        // while proving the exact nativeClipboardManager type check and delegation.
        val nativeAccess=IllegalStateException("native clipboard reached")
        var reads=0
        var writes=0
        val platform=object:AndroidClipboard {
            override val clipboardManager:android.content.ClipboardManager get()=throw nativeAccess
            override suspend fun getClipEntry():ClipEntry? {reads++;return null}
            override suspend fun setClipEntry(clipEntry:ClipEntry?) {assertNull(clipEntry);writes++}
        }
        // The previous generic wrapper throws IllegalArgumentException here,
        // which is the same exception recorded by the long-press crash.
        val generic=object:Clipboard by platform {}
        assertThrows(IllegalArgumentException::class.java) {generic.nativeClipboardManager}
        val wrapped=latexClipboard(platform)
        assertSame(nativeAccess,assertThrows(IllegalStateException::class.java) {wrapped.nativeClipboardManager})
        assertEquals(0,reads)
        assertEquals(0,writes)
        assertNull(wrapped.getClipEntry())
        wrapped.setClipEntry(null)
        assertEquals(1,reads)
        assertEquals(1,writes)
    }

    @Test fun copiesEngineTextLeavesAsMathAndKeepsDisabledCopiesUnchanged() {
        val tree=JSONObject("""{"kind":"fraction","args":[{"kind":"text","value":"1"},{"kind":"text","value":"2"}]}""")
        assertEquals("\\frac{1}{2}",latexTree(tree))
        assertEquals("1/2",mathCopyText("1/2",false))
        assertEquals("\\frac{1}{2}",mathCopyText("1/2",true))
        val decimal=JSONObject("""{"kind":"number","value":"0.123456"}""")
        assertEquals("0.123",latexTree(ResultDisplayFormat.formatTree(decimal,ResultDisplayMode.OFF,false,maxFractionDigits=3)))
        val report=JSONObject("""{"steps":[{"title":"Result","explanation":"Keep this explanation.","tree":$tree}]}""")
        val copied=solutionStepsCopyText(report,3,true){it}
        assertTrue(copied.contains("Keep this explanation."));assertTrue(copied.contains("\\frac{1}{2}"))
        assertFalse(solutionStepsCopyText(report,3){it}.contains("\\frac"))
    }
}
