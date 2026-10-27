package com.kirinonakar.symvacas.calculator

import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import org.junit.Assert.*
import org.junit.Test

class ScriptInputBridgeTest {
    @Test fun cancellingInputReleasesSingleWorkerForNextCalculation() {
        val worker=Executors.newSingleThreadExecutor()
        try {
            val control=ExecutionControl();val waiting=CountDownLatch(1)
            val bridge=ScriptInputBridge(control) {prompt,output->
                assertEquals("value=",prompt);assertEquals("before\n",output);waiting.countDown()
            }
            val script=worker.submit<String> {bridge.request("value=","before\n")}
            assertTrue(waiting.await(2,TimeUnit.SECONDS))
            val calculation=worker.submit<Int> {1+1}
            assertFalse(calculation.isDone)
            control.cancel();bridge.cancel()
            assertEquals("",script.get(2,TimeUnit.SECONDS))
            assertEquals(2,calculation.get(2,TimeUnit.SECONDS))
        } finally {worker.shutdownNow()}
    }

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

    @Test fun repeatedInputsPreserveEmptyAndUnicodeValues() {
        val control=ExecutionControl();val answers=ArrayDeque(listOf("", "  한글  "))
        lateinit var bridge:ScriptInputBridge
        bridge=ScriptInputBridge(control) {_,_->bridge.submit(answers.removeFirst())}
        assertEquals("",bridge.request("first", ""))
        assertEquals("  한글  ",bridge.request("second", ""))
    }
}
