package com.kirinonakar.symvacas.calculator

import androidx.compose.runtime.mutableStateListOf

internal data class StatisticsDraft(
    val csv:String,
    val kind:String,
    val columns:String,
    val autoColumns:Boolean
)

internal class StatisticsEditHistory {
    private val entries=mutableStateListOf<StatisticsDraft>()
    private var characters=0L
    private var editGroup:String?=null
    private var lastEdit=0L
    val canUndo get()=entries.isNotEmpty()

    fun record(before:StatisticsDraft,after:StatisticsDraft,group:String?,now:Long) {
        if(before==after)return
        val coalesce=group!=null&&group==editGroup&&now-lastEdit<=750&&entries.isNotEmpty()
        editGroup=group
        lastEdit=now
        if(coalesce) {
            if(entries.last()==after)undo()
            return
        }
        entries.add(before)
        characters+=before.csv.length
        while(entries.size>1&&(entries.size>50||characters>8_000_000))characters-=entries.removeAt(0).csv.length
    }

    fun endGroup() {editGroup=null}

    fun undo():StatisticsDraft? {
        endGroup()
        if(entries.isEmpty())return null
        return entries.removeAt(entries.lastIndex).also {characters-=it.csv.length}
    }
}
