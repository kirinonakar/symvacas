package com.kirinonakar.symvacas.calculator

import java.util.concurrent.LinkedBlockingQueue
import java.util.concurrent.atomic.AtomicBoolean

/** Polled by Python without acquiring its GIL on the Android main thread. */
class ExecutionControl {
    private val cancelled = AtomicBoolean(false)
    val started = AtomicBoolean(false)
    fun isCancelled(): Boolean = cancelled.get()
    fun cancel(): Boolean = cancelled.compareAndSet(false, true)
}

class ScriptInputBridge(private val control:ExecutionControl,private val onInput:(String,String)->Unit) {
    private val values=LinkedBlockingQueue<String>()
    fun request(prompt:String,output:String):String {
        if(control.isCancelled())return ""
        onInput(prompt,output)
        return values.take()
    }
    fun submit(value:String) {values.offer(value)}
    fun cancel() {values.offer("")}
}
