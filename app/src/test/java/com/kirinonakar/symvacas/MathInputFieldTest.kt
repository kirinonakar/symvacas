package com.kirinonakar.symvacas

import androidx.compose.ui.text.TextRange
import androidx.compose.ui.text.input.TextFieldValue
import com.kirinonakar.symvacas.ui.convertMathInput
import org.junit.Assert.*
import org.junit.Test

class MathInputFieldTest {
    @Test fun pastedSelectionConvertsWithoutDisturbingOtherLinesOrComposition() {
        val previous=TextFieldValue("x=0\n2x+3\ny=0",TextRange(6,5))
        val pasted=TextFieldValue("x=0\n2$\\frac{1}{5}$+3\ny=0",TextRange(18))
        val converted=convertMathInput(previous,pasted,true)
        assertEquals("x=0\n2(1/5)+3\ny=0",converted.text)
        assertEquals(TextRange(10),converted.selection)
        val composing=pasted.copy(composition=TextRange(5,18))
        assertEquals(composing,convertMathInput(previous,composing,true))
        val selectionOnly=TextFieldValue("\\frac{1}{2}",TextRange(0,3))
        assertEquals(selectionOnly,convertMathInput(selectionOnly.copy(selection=TextRange(0)),selectionOnly,false))
    }
}
