use crate::runtime::{self, Result};
use serde_json::{json, Value};
use std::{
    io::{BufRead, BufReader, Write},
    path::Path,
    process::{Child, ChildStdin, Command, Stdio},
    sync::{mpsc, Arc, Mutex},
    time::{Duration, Instant},
};

struct Worker {
    child: Mutex<Child>,
    stdin: Mutex<ChildStdin>,
    messages: Mutex<mpsc::Receiver<Result<Value>>>,
    waiting: Mutex<Option<(u64, u64)>>,
}

impl Worker {
    fn stop(&self) {
        let mut child = self.child.lock().unwrap();
        let _ = child.kill();
        let _ = child.wait();
    }

    fn send(&self, value: &Value) -> Result<()> {
        let mut stdin = self.stdin.lock().unwrap();
        writeln!(stdin, "{value}")
            .and_then(|_| stdin.flush())
            .map_err(|e| e.to_string())
    }

    fn spawn(root: &Path) -> Result<Arc<Self>> {
        if !runtime::python(root).is_file() {
            return Err("Install Python dependencies with the Python / MCP button first.".into());
        }
        let archive = runtime::engine_archive(root)?;
        let mut command = Command::new(runtime::python(root));
        let mut child = runtime::quiet(&mut command).args(["-I", "-X", "utf8", "-u", "-c",
            "import sys;sys.path.insert(0,sys.argv[1]);import desktop_worker;desktop_worker.main()"])
            .arg(archive).current_dir(root).stdin(Stdio::piped()).stdout(Stdio::piped()).stderr(Stdio::piped())
            .spawn().map_err(|e| e.to_string())?;
        let stdin = child.stdin.take().unwrap();
        let stdout = child.stdout.take().unwrap();
        let stderr = child.stderr.take().unwrap();
        let (sender, receiver) = mpsc::channel();
        std::thread::spawn(move || {
            for line in BufReader::new(stdout).lines() {
                let message = line.map_err(|e| e.to_string()).and_then(|line| {
                    serde_json::from_str(&line)
                        .map_err(|e| format!("Invalid Python bridge response: {e}"))
                });
                if sender.send(message).is_err() {
                    break;
                }
            }
        });
        // Always drain stderr, including output from user-started native extensions.
        std::thread::spawn(move || {
            for line in BufReader::new(stderr)
                .lines()
                .map_while(std::result::Result::ok)
            {
                eprintln!("[Python] {line}");
            }
        });
        Ok(Arc::new(Self {
            child: Mutex::new(child),
            stdin: Mutex::new(stdin),
            messages: Mutex::new(receiver),
            waiting: Mutex::new(None),
        }))
    }
}

impl Drop for Worker {
    fn drop(&mut self) {
        self.stop();
    }
}

#[derive(Default)]
pub struct Engine {
    worker: Mutex<Option<(u64, Option<Arc<Worker>>)>>,
    executing: Mutex<()>,
}

impl Engine {
    pub fn is_ready(&self, session: u64) -> bool {
        self.get(session).is_ok()
    }
    pub fn start(&self, root: &Path, session: u64) -> Result<Value> {
        let previous = self.worker.lock().unwrap().replace((session, None));
        if let Some((_, Some(worker))) = previous {
            worker.stop();
        }
        let worker = Worker::spawn(root)?;
        {
            let mut slot = self.worker.lock().unwrap();
            if slot
                .as_ref()
                .is_some_and(|(current, _)| *current == session)
            {
                *slot = Some((session, Some(worker.clone())));
            } else {
                worker.stop();
                return Err("Engine startup cancelled".into());
            }
        }
        let ready = worker
            .messages
            .lock()
            .unwrap()
            .recv_timeout(Duration::from_secs(120))
            .map_err(|e| e.to_string())
            .and_then(|r| r);
        match ready {
            Ok(value) if value["type"] == "ready" => Ok(value),
            other => {
                self.cancel(session);
                Err(format!("Cannot start embedded Python: {other:?}"))
            }
        }
    }

    fn get(&self, session: u64) -> Result<Arc<Worker>> {
        self.worker
            .lock()
            .unwrap()
            .as_ref()
            .filter(|(id, _)| *id == session)
            .and_then(|(_, worker)| worker.clone())
            .ok_or_else(|| "Python engine is not ready".into())
    }

    pub fn cancel(&self, session: u64) {
        let mut slot = self.worker.lock().unwrap();
        if slot.as_ref().is_some_and(|(id, _)| *id == session) {
            if let Some((_, Some(worker))) = slot.take() {
                worker.stop();
            }
        }
    }

    pub fn input(&self, session: u64, id: u64, input_id: u64, value: String) -> Result<()> {
        let worker = self.get(session)?;
        let mut waiting = worker.waiting.lock().unwrap();
        if *waiting != Some((id, input_id)) {
            return Err("Input request has expired".into());
        }
        worker.send(&json!({"type":"input","id":id,"inputId":input_id,"value":value}))?;
        *waiting = None;
        Ok(())
    }

    pub fn execute(
        &self,
        session: u64,
        id: u64,
        request: Value,
        mut on_input: impl FnMut(Value) -> Result<Option<String>>,
    ) -> Result<Value> {
        let _execution = self
            .executing
            .try_lock()
            .map_err(|_| "Calculation already running")?;
        let worker = self.get(session)?;
        worker.send(&json!({"id":id,"request":request}))?;
        let receiver = worker.messages.lock().unwrap();
        let mut elapsed = Duration::ZERO;
        let mut last = Instant::now();
        let timeout = timeout_seconds(&request);
        loop {
            if worker.waiting.lock().unwrap().is_none() {
                elapsed += last.elapsed();
            }
            last = Instant::now();
            if elapsed.as_secs_f64() > timeout {
                self.cancel(session);
                return Err("Calculation time limit exceeded".into());
            }
            match receiver.recv_timeout(Duration::from_millis(50)) {
                Ok(Ok(message)) if message["type"] == "result" && message["id"] == id => {
                    return Ok(message["result"].clone())
                }
                Ok(Ok(message)) if message["type"] == "input" && message["id"] == id => {
                    let input_id = message["inputId"].as_u64().ok_or("Invalid input ID")?;
                    *worker.waiting.lock().unwrap() = Some((id, input_id));
                    match on_input(message) {
                        Ok(Some(value)) => self.input(session, id, input_id, value)?,
                        Ok(None) => (),
                        Err(error) => {
                            self.cancel(session);
                            return Err(error);
                        }
                    }
                    last = Instant::now();
                }
                Ok(Ok(_)) => {
                    self.cancel(session);
                    return Err("Unexpected Python bridge message".into());
                }
                Ok(Err(error)) => {
                    self.cancel(session);
                    return Err(error);
                }
                Err(mpsc::RecvTimeoutError::Disconnected) => {
                    self.cancel(session);
                    return Err("Python process stopped".into());
                }
                Err(mpsc::RecvTimeoutError::Timeout) => (),
            }
        }
    }
}

impl Drop for Engine {
    fn drop(&mut self) {
        if let Some((_, Some(worker))) = self.worker.lock().unwrap().take() {
            worker.stop();
        }
    }
}

fn timeout_seconds(request: &Value) -> f64 {
    if request["removeComputationLimit"] == true {
        return f64::INFINITY;
    }
    fn number(node: &Value, request: &Value, depth: usize) -> f64 {
        if depth > 8 {
            return 0.0;
        }
        match node["kind"].as_str().unwrap_or("") {
            "number" => node["value"]
                .as_str()
                .and_then(|value| value.parse().ok())
                .unwrap_or(0.0),
            "symbol" => number(
                &request["variables"][node["value"].as_str().unwrap_or("")],
                request,
                depth + 1,
            ),
            "unary" => {
                (if node["value"] == "-" { -1.0 } else { 1.0 })
                    * number(&node["args"][0], request, depth + 1)
            }
            _ => 0.0,
        }
    }
    fn work(node: &Value, request: &Value) -> f64 {
        let args = node["args"].as_array();
        let own = if node["kind"] == "call" && node["value"] == "sem" {
            args.filter(|a| a.len() > 10).map_or(0.0, |a| {
                let count = number(&a[10], request, 0);
                let p = a[1]["args"]
                    .as_array()
                    .filter(|a| !a.is_empty())
                    .map_or(6, Vec::len) as f64;
                if count.is_finite() && count.fract() == 0.0 && count >= 20.0 {
                    count.min(10000.0)
                        * (p * p).max(10.0)
                        * if a[7]["value"] == "wlsmv" { 4.0 } else { 1.0 }
                } else {
                    0.0
                }
            })
        } else {
            0.0
        };
        own + args.map_or(0.0, |a| a.iter().map(|node| work(node, request)).sum())
    }
    65.0 + work(&request["tree"], request)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn native_timeouts_match_shared_execution_budget() {
        let cases: Value = serde_json::from_str(include_str!(
            "../../../tests/fixtures/execution_budget.json"
        ))
        .unwrap();
        for case in cases.as_array().unwrap() {
            let expected = if case["timeoutMillis"].is_null() {
                f64::INFINITY
            } else {
                case["timeoutMillis"].as_f64().unwrap() / 1000.0
            };
            assert_eq!(
                timeout_seconds(&case["request"]),
                expected,
                "{}",
                case["name"]
            );
        }
    }

    #[test]
    #[ignore = "Install the runtime first and set SYMVACAS_TEST_HOME to its application folder"]
    fn embedded_python_bridge_input_cancel_and_recovery() {
        let root = std::path::PathBuf::from(
            std::env::var("SYMVACAS_TEST_HOME").expect("Set SYMVACAS_TEST_HOME"),
        );
        let engine = Arc::new(Engine::default());
        assert_eq!(engine.start(&root, 10).unwrap()["type"], "ready");
        let scripted = engine
            .execute(
                10,
                1,
                json!({"action":"python","source":"print('안녕',input('Name? '))"}),
                |message| {
                    assert_eq!(message["prompt"], "Name? ");
                    Ok(Some("Alice".to_owned()))
                },
            )
            .unwrap();
        assert_eq!(scripted["ok"], true);
        assert!(scripted["output"].as_str().unwrap().contains("안녕 Alice"));
        // Input can arrive from another IPC call while execution is blocked.
        let (sender, receiver) = mpsc::channel();
        let pending_engine = engine.clone();
        let pending = std::thread::spawn(move || {
            pending_engine.execute(
                10,
                2,
                json!({"action":"python","source":"print(input('Value? '))"}),
                |message| {
                    sender.send(message).unwrap();
                    Ok(None)
                },
            )
        });
        let prompt = receiver.recv_timeout(Duration::from_secs(10)).unwrap();
        assert!(engine.execute(10, 3, json!({}), |_| Ok(None)).is_err());
        assert!(engine.input(9, 2, 1, "stale".into()).is_err());
        assert!(engine.input(10, 99, 1, "wrong request".into()).is_err());
        engine
            .input(10, 2, prompt["inputId"].as_u64().unwrap(), "42".into())
            .unwrap();
        assert!(pending.join().unwrap().unwrap()["output"]
            .as_str()
            .unwrap()
            .contains("42"));
        engine.cancel(9); // A terminated older UI worker must not kill the current one.
        assert!(engine.is_ready(10));
        let (sender, receiver) = mpsc::channel();
        let pending_engine = engine.clone();
        let pending = std::thread::spawn(move || {
            pending_engine.execute(
                10,
                4,
                json!({"action":"python","source":"input('Start? ')\nwhile True: pass"}),
                |message| {
                    sender.send(message).unwrap();
                    Ok(None)
                },
            )
        });
        receiver.recv_timeout(Duration::from_secs(10)).unwrap();
        engine.input(10, 4, 1, "go".into()).unwrap();
        engine.cancel(10);
        assert!(pending.join().unwrap().is_err());
        engine.start(&root, 11).unwrap();
        let result = engine
            .execute(
                11,
                5,
                json!({"tree":crate::parser::parse("6*7",false).unwrap()}),
                |_| Ok(None),
            )
            .unwrap();
        assert_eq!(result["exact"], "42");
        engine.cancel(11);
    }
}
