package com.kirinonakar.symvacas.calculator

import org.junit.Assert.*
import org.junit.Test

class ScriptInputBridgeTest {
    @Test fun cancellationBeforeOrDuringPromptCannotLoseWakeup() {
        val control=ExecutionControl()
        val bridge=ScriptInputBridge(control) {_,_->fail("Already cancelled")}
        control.cancel()
        assertEquals("",bridge.request("", ""))
        val racingControl=ExecutionControl()
        lateinit var racing:ScriptInputBridge
        racing=ScriptInputBridge(racingControl) {_,_->racingControl.cancel();racing.cancel()}
        assertEquals("",racing.request("", ""))
    }

}
