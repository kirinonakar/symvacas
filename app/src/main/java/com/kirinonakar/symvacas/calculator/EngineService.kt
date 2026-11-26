package com.kirinonakar.symvacas.calculator

import android.app.Service
import android.content.*
import android.os.*
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import org.json.JSONObject
import java.util.concurrent.Executors
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicReference
import kotlinx.coroutines.*
import kotlin.coroutines.resume

class EngineService : Service() {
    private class CalculationRequest(payload: EnginePayload) {
        val queuedPayload = AtomicReference<EnginePayload?>(payload)
        val control = ExecutionControl()
    }

    private val worker = Executors.newSingleThreadExecutor()
    private val inputBridges = ConcurrentHashMap<Int, ScriptInputBridge>()
    private val requests = ConcurrentHashMap<Int, CalculationRequest>()
    private val handler = Handler(Looper.getMainLooper())
    private fun cancelRequest(id: Int) {
        val request = requests[id] ?: return
        val control = request.control
        if(!control.cancel())return
        request.queuedPayload.getAndSet(null)?.close()
        inputBridges[id]?.cancel()
        // Keep the interpreter and warm SymPy caches for normal cancellations.
        // Native calls or scripts which suppress cancellation still need a process boundary.
        handler.postDelayed({
            if(requests[id] === request && control.started.get())
                android.os.Process.killProcess(android.os.Process.myPid())
        }, 750)
    }
    private val messenger = Messenger(Handler(Looper.getMainLooper()) { msg ->
        if (msg.what == 2) { cancelRequest(msg.arg1); true }
        else if (msg.what == 3) { inputBridges[msg.arg1]?.submit(msg.data.getString("value") ?: ""); true }
        else if (msg.what == 1) {
            val reply = msg.replyTo
            val id = msg.arg1
            val payload = EnginePayload.fromBundle(msg.data)
            if (reply == null || worker.isShutdown) {
                payload.close()
                return@Handler true
            }
            val request = CalculationRequest(payload)
            val control = request.control
            requests[id] = request
            worker.execute {
                val result = try {
                    val text = request.queuedPayload.getAndSet(null)?.use { it.read() }
                        ?: return@execute
                    control.started.set(true)
                    check(!control.isCancelled()) { "Calculation cancelled" }
                    // The execution deadline gets its full allowance after queueing.
                    reply.send(Message.obtain(null, 4, id, 0))
                    if (!Python.isStarted()) Python.start(AndroidPlatform(this))
                    val module=if(JSONObject(text).optString("action")=="python") "script_runner" else "calc_engine"
                    if (module == "script_runner") {
                        val bridge = ScriptInputBridge(control) { prompt, output ->
                            reply.send(Message.obtain(null, 3, id, 0).apply {
                                data=Bundle().apply {putString("prompt",prompt);putString("output",output)}
                            })
                        }
                        inputBridges[id] = bridge
                        try { Python.getInstance().getModule(module).callAttr("run", text, bridge, control).toString() }
                        finally { inputBridges.remove(id) }
                    } else Python.getInstance().getModule(module).callAttr("dispatch", text, control).toString()
                } catch (e: Exception) { JSONObject().put("ok", false).put("error", e.message ?: "Engine error").toString() }
                finally { requests.remove(id, request) }
                if (control.isCancelled()) return@execute
                runCatching {
                    sendResult(reply, id, result)
                }.onFailure {
                    // Report a transport failure immediately rather than leaving
                    // the client waiting until its calculation timeout expires.
                    runCatching {
                        val error = JSONObject().put("ok", false)
                            .put("error", "Could not transfer calculation result. Try again.")
                        sendResult(reply, id, error.toString())
                    }
                }
            }
            true
        } else false
    })

    private fun sendResult(reply: Messenger, id: Int, result: String) {
        EnginePayload.write(this, result).use { payload ->
            reply.send(Message.obtain(null, 1, id, 0).apply { data = payload.toBundle() })
        }
    }

    override fun onBind(intent: Intent): IBinder = messenger.binder
    override fun onCreate() {
        super.onCreate()
        worker.execute {runCatching {if(!Python.isStarted())Python.start(AndroidPlatform(this));Python.getInstance().getModule("calc_engine")}}
    }
    override fun onDestroy() {
        requests.keys.toList().forEach(::cancelRequest)
        worker.shutdownNow()
        super.onDestroy()
    }
}

class EngineClient(private val context: Context) {
    private val transportScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private var remote: Messenger? = null
    private var connected = CompletableDeferred<Unit>()
    private val pending = mutableMapOf<Int, CancellableContinuation<JSONObject>>()
    private val inputHandlers = mutableMapOf<Int, (String, String, (String) -> Unit) -> Unit>()
    private val timeouts = mutableMapOf<Int, Runnable>()
    private val unlimitedRequests = mutableSetOf<Int>()
    private val executionBudgets = mutableMapOf<Int, Long>()
    private val handler = Handler(Looper.getMainLooper())
    companion object {
        private val counter = AtomicInteger()
        private const val EXECUTION_TIMEOUT_MS = 60_000L+EXECUTION_RESPONSE_GRACE_MILLIS
    }
    private var closed = false
    private val incoming = Messenger(Handler(Looper.getMainLooper()) { msg ->
        if (msg.what == 4) {
            if(pending[msg.arg1]?.isActive==true)startTimeout(msg.arg1)
        } else if (msg.what == 3) {
            timeouts.remove(msg.arg1)?.let(handler::removeCallbacks)
            val id = msg.arg1
            inputHandlers[id]?.invoke(msg.data.getString("prompt") ?: "", msg.data.getString("output") ?: "") { value ->
                if (pending[id]?.isActive == true) {
                    runCatching { remote?.send(Message.obtain(null, 3, id, 0).apply { data = Bundle().apply { putString("value", value) } }) }
                    startTimeout(id)
                }
            }
        } else if (msg.what == 1) {
            val id = msg.arg1
            clearRequestState(id)
            val continuation = pending[id]
            val payload = EnginePayload.fromBundle(msg.data)
            if (continuation?.isActive == true) {
                val decoding = transportScope.launch {
                    val response=runCatching {JSONObject(payload.read())}
                        .getOrElse {JSONObject().put("ok",false).put("error","Could not read calculation result. Try again.")}
                    withContext(Dispatchers.Main.immediate) {
                        if(pending[id]===continuation) {
                            pending.remove(id)
                            if(continuation.isActive)continuation.resume(response)
                        }
                    }
                }
                decoding.invokeOnCompletion { payload.close() }
            } else {
                payload.close()
            }
        }
        true
    })
    private val connection = object : ServiceConnection {
        override fun onServiceConnected(name: ComponentName, binder: IBinder) { remote = Messenger(binder); connected.complete(Unit) }
        override fun onServiceDisconnected(name: ComponentName) {
            remote = null; if(connected.isCompleted) connected = CompletableDeferred()
            timeouts.values.forEach(handler::removeCallbacks); timeouts.clear(); inputHandlers.clear(); unlimitedRequests.clear(); executionBudgets.clear()
            pending.values.toList().forEach { if(it.isActive) it.resume(JSONObject().put("ok",false).put("error","Calculation cancelled or engine restarted")) }; pending.clear()
        }
        override fun onBindingDied(name: ComponentName) {
            onServiceDisconnected(name)
            if(!closed) { runCatching { context.unbindService(this) }; bind() }
        }
    }
    init { bind() }
    private fun bind() { context.bindService(Intent(context,EngineService::class.java), connection, Context.BIND_AUTO_CREATE) }
    private fun clearRequestState(id: Int) {
        timeouts.remove(id)?.let(handler::removeCallbacks)
        unlimitedRequests.remove(id)
        executionBudgets.remove(id)
        inputHandlers.remove(id)
    }

    private fun startTimeout(id: Int) {
        timeouts.remove(id)?.let(handler::removeCallbacks)
        if(id in unlimitedRequests)return
        val timeout = Runnable {
            pending.remove(id)?.let { if(it.isActive) it.resume(JSONObject().put("ok",false).put("error","Computation timed out. Reduce complexity and try again.")) }
            clearRequestState(id)
            cancelRequest(id)
        }
        timeouts[id] = timeout
        handler.postDelayed(timeout, executionBudgets[id] ?: EXECUTION_TIMEOUT_MS)
    }
    suspend fun execute(request: JSONObject, onInput: ((String, String, (String) -> Unit) -> Unit)? = null): JSONObject = withContext(Dispatchers.Main.immediate) {
        try {
            withTimeout(20000) { connected.await() }
            if (closed) return@withContext JSONObject().put("ok", false).put("error", "Calculation cancelled")
            // Some requests reference mutable calculator state owned by the main thread.
            val text = request.toString()
            suspendCancellableCoroutine { continuation ->
                val id = counter.incrementAndGet()
                pending[id] = continuation
                executionBudgets[id] = executionTimeoutMillis(request)
                if (request.optBoolean("removeComputationLimit")) unlimitedRequests.add(id)
                if (onInput != null) inputHandlers[id] = onInput
                val sending = transportScope.launch {
                    if (!continuation.isActive) return@launch
                    try {
                        EnginePayload.write(context, text).use { payload ->
                            withContext(Dispatchers.Main.immediate) {
                                if (pending[id] === continuation && continuation.isActive) {
                                    val destination = checkNotNull(remote) { "Engine disconnected" }
                                    destination.send(Message.obtain(null, 1, id, 0).apply {
                                        replyTo = incoming
                                        data = payload.toBundle()
                                    })
                                    startTimeout(id)
                                }
                            }
                        }
                    } catch (e: CancellationException) {
                        throw e
                    } catch (e: Exception) {
                        withContext(Dispatchers.Main.immediate) {
                            if (pending.remove(id) === continuation) {
                                clearRequestState(id)
                                if (continuation.isActive) {
                                    continuation.resume(JSONObject().put("ok", false)
                                        .put("error", e.message ?: "Could not transfer calculation request"))
                                }
                            }
                        }
                    }
                }
                continuation.invokeOnCancellation {
                    sending.cancel()
                    handler.post {
                        if (pending.remove(id) != null) cancelRequest(id)
                        clearRequestState(id)
                    }
                }
            }
        } catch(e: TimeoutCancellationException) { JSONObject().put("ok",false).put("error","Computation timed out. Reduce complexity and try again.") }
    }
    private fun cancelRequest(id: Int) {
        runCatching { remote?.send(Message.obtain(null,2,id,0)) }
    }
    fun cancel() {
        val cancelled=pending.toMap()
        pending.clear()
        cancelled.forEach { (id, continuation) ->
            clearRequestState(id)
            cancelRequest(id)
            if(continuation.isActive)continuation.resume(JSONObject().put("ok",false).put("error","Calculation cancelled"))
        }
    }
    fun close() { closed = true; cancel(); transportScope.cancel();runCatching { context.unbindService(connection) } }
}
