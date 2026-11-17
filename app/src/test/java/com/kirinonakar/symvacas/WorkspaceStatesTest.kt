package com.kirinonakar.symvacas

import android.content.SharedPreferences
import com.kirinonakar.symvacas.calculator.GraphState
import com.kirinonakar.symvacas.calculator.StatisticsDraft
import com.kirinonakar.symvacas.calculator.StatisticsState
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class WorkspaceStatesTest {
    @Test fun statisticsUndoRestoresDraftShapeWithoutChangingSavedDataOrSelection() {
        val state=StatisticsState(MemoryPreferences())
        val before=StatisticsDraft("a,b\n1,20","columns:2","2",true)
        val combined=before.copy(csv="a,b,c\n1,20,3",kind="columns:3",columns="3")
        state.saveDataSet("Study",combined.csv,"xyz")
        state.statisticsName="Study";state.statisticsSelected="Study";state.statisticsIsNew=false
        state.restoreDraft(combined)
        state.editHistory.record(before,combined,null,0)

        state.restoreDraft(state.editHistory.undo()!!)
        assertEquals(combined.csv,state.dataSets.getJSONObject("Study").getString("csv"))
        assertEquals(before.csv,state.statisticsData)
        assertEquals("columns:2",state.statisticsKind)
        assertTrue(state.statisticsAutoColumns)
        assertEquals("Study",state.statisticsSelected)
        assertFalse(state.statisticsIsNew)
        assertFalse(state.editHistory.canUndo)
    }

    @Test fun largeStatisticsSourcesAndResultsStayOutsideCalculatorPersistence() {
        val prefs=MemoryPreferences()
        val calculatorResult=JSONObject().put("exact","4").toString()
        val calculatorHistory="[{\"source\":\"2+2\",\"mode\":\"Scientific/CAS\"}]"
        prefs.edit().putString("expression","2+2").putString("result",calculatorResult)
            .putString("resultSource","2+2").putString("history",calculatorHistory).putBoolean("committed",true).apply()
        val state=com.kirinonakar.symvacas.calculator.StatisticsState(prefs)
        val fitted=JSONObject().put("exact","x+1").put("regression",JSONObject().put("model","linear"))
        state.regressionResult=fitted
        state.result=JSONObject().put("exact","1").put("statisticsReport",JSONObject().put("analysis","mean"))
        state.resultSource="mean(["+List(40_000){"1"}.joinToString(",")+"])"
        prefs.edit().also {state.writeTo(it);it.apply()}
        assertEquals("2+2",prefs.getString("expression",null))
        assertEquals("2+2",prefs.getString("resultSource",null))
        assertEquals(calculatorResult,prefs.getString("result",null))
        assertEquals(calculatorHistory,prefs.getString("history",null))
        assertTrue(prefs.getBoolean("committed",false))
        val restored=com.kirinonakar.symvacas.calculator.StatisticsState(prefs)
        assertEquals("mean",restored.result!!.getJSONObject("statisticsReport").getString("analysis"))
        assertEquals(fitted.toString(),restored.regressionResult!!.toString())
        assertEquals("",restored.resultSource)
    }

    @Test fun graphUndoRestoresDeletedInputsAndParametersWithoutRecordingUndo() {
        val state=GraphState(MemoryPreferences())
        val source="a*x\ncos(x)\n[s] x, 2, -1..1"
        state.updateSource(source)
        state.syncParameters(org.json.JSONArray("[\"a\"]"))
        state.setParameter("a",2.5)
        val parameters=state.graphParameters
        state.graphDerivativeSelected=0
        state.graphSecondDerivativeSelected=1
        state.updateSource("a*x\ncos(x)")
        assertNull(state.graphDerivativeSelected);assertNull(state.graphSecondDerivativeSelected)
        state.updateSource("")
        state.graphParameters=emptyMap()
        assertTrue(state.canUndoInput)
        assertTrue(state.undoInput());assertEquals("a*x\ncos(x)",state.graphSource)
        assertEquals(parameters,state.graphParameters)
        assertTrue(state.undoInput());assertEquals(source,state.graphSource)
        assertEquals(0,state.graphDerivativeSelected)
        assertEquals(1,state.graphSecondDerivativeSelected)
        assertTrue(state.undoInput());assertEquals("sin(x)\ncos(x)",state.graphSource)
        assertFalse(state.canUndoInput);assertFalse(state.undoInput())
        state.updateSource("")
        state.changeKind("polar");assertFalse(state.canUndoInput)
        state.changeKind("cartesian");assertTrue(state.canUndoInput)
        assertTrue(state.undoInput());assertEquals("sin(x)\ncos(x)",state.graphSource)
    }

    @Test fun graphKindsKeepSeparateSourcesAndDiscardOldAnalysis() {
        val prefs=MemoryPreferences()
        val graph=GraphState(prefs)
        graph.updateSource("x^2")
        graph.graphData=org.json.JSONObject().put("old",true)
        assertTrue(graph.changeKind("polar"))
        assertEquals("2*cos(3*t)",graph.graphSource)
        assertNull(graph.graphData)
        graph.updateSource("3*sin(t)")
        assertTrue(graph.changeKind("cartesian"))
        assertEquals("x^2",graph.graphSource)
        assertFalse(graph.changeKind("cartesian"))
        assertFalse(graph.changeKind("implicit"))
        assertEquals("cartesian",graph.graphKind)
        graph.updateSource("x*y=1")
        assertTrue(graph.changeKind("polar"))
        assertTrue(graph.changeKind("cartesian"))
        assertEquals("x*y=1",graph.graphSource)
        val editor=prefs.edit()
        graph.writeTo(editor);editor.apply()
        val restored=GraphState(prefs)
        assertEquals("cartesian",restored.graphKind)
        assertEquals("x*y=1",restored.graphSource)
    }

    private class MemoryPreferences(initial:Map<String,Any?> = emptyMap()):SharedPreferences {
        private val values=initial.toMutableMap()
        override fun getAll():MutableMap<String,*> = values.toMutableMap()
        override fun getString(key:String?,defValue:String?):String? = values[key] as? String ?: defValue
        override fun getStringSet(key:String?,defValues:MutableSet<String>?):MutableSet<String>? =
            (values[key] as? Set<*>)?.filterIsInstance<String>()?.toMutableSet() ?: defValues
        override fun getInt(key:String?,defValue:Int):Int = values[key] as? Int ?: defValue
        override fun getLong(key:String?,defValue:Long):Long = values[key] as? Long ?: defValue
        override fun getFloat(key:String?,defValue:Float):Float = values[key] as? Float ?: defValue
        override fun getBoolean(key:String?,defValue:Boolean):Boolean = values[key] as? Boolean ?: defValue
        override fun contains(key:String?):Boolean = values.containsKey(key)
        override fun registerOnSharedPreferenceChangeListener(listener:SharedPreferences.OnSharedPreferenceChangeListener?) {}
        override fun unregisterOnSharedPreferenceChangeListener(listener:SharedPreferences.OnSharedPreferenceChangeListener?) {}
        override fun edit():SharedPreferences.Editor = object:SharedPreferences.Editor {
            private val updates=mutableMapOf<String,Any?>()
            private val removals=mutableSetOf<String>()
            private var clearAll=false
            override fun putString(key:String?,value:String?):SharedPreferences.Editor=apply {updates[key!!]=value}
            override fun putStringSet(key:String?,values:MutableSet<String>?):SharedPreferences.Editor=apply {updates[key!!]=values}
            override fun putInt(key:String?,value:Int):SharedPreferences.Editor=apply {updates[key!!]=value}
            override fun putLong(key:String?,value:Long):SharedPreferences.Editor=apply {updates[key!!]=value}
            override fun putFloat(key:String?,value:Float):SharedPreferences.Editor=apply {updates[key!!]=value}
            override fun putBoolean(key:String?,value:Boolean):SharedPreferences.Editor=apply {updates[key!!]=value}
            override fun remove(key:String?):SharedPreferences.Editor=apply {removals+=key!!}
            override fun clear():SharedPreferences.Editor=apply {clearAll=true}
            override fun commit():Boolean {
                if(clearAll)values.clear()
                removals.forEach(values::remove)
                values.putAll(updates)
                return true
            }
            override fun apply() {commit()}
        }
    }
}
