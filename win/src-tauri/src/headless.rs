use crate::{
    analysis, catalog, datasets,
    engine::Engine,
    runtime::{self, Result},
    usage,
};
use serde_json::{json, Value};
use std::{
    fs,
    io::{self, BufRead, Read, Write},
    path::Path,
    sync::{mpsc, Arc, Mutex},
};

const SKILL: &str = include_str!("../../skills/symvacas/SKILL.md");
const HELP: &str = "SymvaCAS Windows CLI
  symvacas-cli status                      Check embedded Python
  symvacas-cli install                     Install Python beside the executable
  symvacas-cli eval EXPRESSION [options]    Calculator syntax / LaTeX -> JSON result
  symvacas-cli stats EXPRESSION [--data FILE|-]  Statistics with inline/saved datasets
  symvacas-cli solve EQUATION... [options]  Equations/systems with available steps
  symvacas-cli catalog [QUERY] [--category NAME --limit N --offset N]
  symvacas-cli dataset list|show NAME|save NAME FILE [--format json|csv --replace]
  symvacas-cli request FILE|-              Execute a web-engine JSON request
  symvacas-cli python FILE|- [--input TEXT] Execute a local Python script
  symvacas-cli mcp                         MCP server over stdio (no GUI)
  symvacas-cli mcp-config                  Print client configuration
  symvacas-cli skill                       Print the bundled SKILL.md
Options: --angle DEG|RAD|GRAD --precision 3..200 --digits 1..200 --unlimited
Solve: --variables x,y --method solve|nsolve|dsolve|pdsolve --guess 0,1
       --independent x --initial CONDITIONS --hint HINT --no-steps
Stats --data accepts named JSON datasets, or a vector/table named data.
Saved datasets are shared with the GUI in data/statistics-datasets.json.
Default: RAD, 30 significant digits, 10 display digits, 65s outer deadline.
Use --input multiple times for scripts; missing inputs fail in headless mode.
Python scripts have the permissions of the current user.";

fn read_file(name: &str) -> Result<String> {
    if name == "-" {
        let mut text = String::new();
        io::stdin()
            .read_to_string(&mut text)
            .map_err(|e| e.to_string())?;
        Ok(text)
    } else {
        fs::read_to_string(name).map_err(|e| e.to_string())
    }
}

fn execute(root: &Path, engine: &Engine, request: Value) -> Result<Value> {
    if !request.is_object() {
        return Err("Request must be a JSON object".into());
    }
    if !engine.is_ready(1) {
        engine.start(root, 1)?;
    }
    engine.execute(1, 1, request, |_| {
        Err(
            "Python input() needs a pre-entered value in headless mode; supply inputs or --input."
                .into(),
        )
    })
}

fn options(args: &[String], command: &str) -> Result<(Vec<String>, Value, Vec<String>, Value)> {
    let mut positionals = Vec::new();
    let mut settings = json!({"angle":"RAD","precision":30,"displayDigits":10});
    let mut inputs = Vec::new();
    let mut analysis = json!({});
    let mut iter = args.iter();
    while let Some(arg) = iter.next() {
        match arg.as_str() {
            "--angle" => {
                let value = iter.next().ok_or("--angle needs a value")?;
                if !["DEG", "RAD", "GRAD"].contains(&value.as_str()) {
                    return Err("Angle must be DEG, RAD or GRAD".into());
                }
                settings["angle"] = json!(value);
            }
            "--precision" | "--digits" => {
                let value = iter
                    .next()
                    .ok_or("Option needs a value")?
                    .parse::<u64>()
                    .map_err(|_| "Expected integer precision")?;
                if !(if arg == "--precision" { 3 } else { 1 }..=200).contains(&value) {
                    return Err("Precision must be 3..200; digits must be 1..200".into());
                }
                settings[if arg == "--precision" {
                    "precision"
                } else {
                    "displayDigits"
                }] = json!(value);
            }
            "--unlimited" => settings["removeComputationLimit"] = json!(true),
            "--data" if ["stats", "statistics"].contains(&command) => {
                analysis["dataFile"] = json!(iter.next().ok_or("--data needs a file path")?)
            }
            "--variables" | "--method" | "--guess" | "--independent" | "--initial" | "--hint"
                if command == "solve" =>
            {
                let key = match arg.as_str() {
                    "--variables" => "variables",
                    "--method" => "method",
                    "--guess" => "initialGuess",
                    "--independent" => "independentVariable",
                    "--initial" => "initialConditions",
                    _ => "hint",
                };
                analysis[key] = json!(iter.next().ok_or("Option needs a value")?);
            }
            "--no-steps" if command == "solve" => analysis["steps"] = json!(false),
            "--input" => inputs.push(iter.next().ok_or("--input needs a value")?.clone()),
            "--" => {
                positionals.extend(iter.cloned());
                break;
            }
            _ if arg.starts_with("--") => return Err(format!("Unknown option: {arg}")),
            _ => positionals.push(arg.clone()),
        }
    }
    Ok((positionals, settings, inputs, analysis))
}

fn catalog_cli(args: &[String]) -> Result<Value> {
    let mut settings = json!({});
    let mut query = Vec::new();
    let mut iter = args.iter();
    while let Some(arg) = iter.next() {
        match arg.as_str() {
            "--category" => {
                settings["category"] = json!(iter.next().ok_or("--category needs a name")?)
            }
            "--limit" | "--offset" => {
                settings[&arg[2..]] = json!(iter
                    .next()
                    .ok_or("Option needs an integer")?
                    .parse::<u64>()
                    .map_err(|_| "Expected a nonnegative integer")?)
            }
            _ if arg.starts_with("--") => return Err(format!("Unknown catalog option: {arg}")),
            _ => query.push(arg.clone()),
        }
    }
    settings["query"] = json!(query.join(" "));
    catalog::search(&settings)
}

fn dataset_cli(root: &Path, args: &[String]) -> Result<Value> {
    match args.first().map(String::as_str){
        Some("list") if args.len()==1=>datasets::list(root),
        Some("show") if args.len()==2=>datasets::get(root,&args[1]),
        Some("save") if args.len()>=3=>{
            let mut format=if args[2].to_lowercase().ends_with(".json"){"json"}else{"csv"};
            let mut replace=false;let mut iter=args[3..].iter();
            while let Some(arg)=iter.next(){match arg.as_str(){"--replace"=>replace=true,"--format"=>format=iter.next().ok_or("--format needs json or csv")?,_=>return Err(format!("Unknown dataset option: {arg}"))}}
            let source=read_file(&args[2])?;let mut input=json!({"name":args[1],"replace":replace});
            match format{"json"=>input["data"]=serde_json::from_str(&source).map_err(|e|e.to_string())?,"csv"|"tsv"=>input["csv"]=json!(source),_=>return Err("Format must be json, csv or tsv".into())}
            datasets::save(root,&input)
        }
        _=>Err("Use dataset list, dataset show NAME, or dataset save NAME FILE [--format json|csv --replace]".into())
    }
}

fn analysis_request(root: &Path, kind: &str, args: &Value) -> Result<Value> {
    if !args.is_object() {
        return Err("Arguments must be an object".into());
    }
    let mut args = args.clone();
    if kind == "statistics" {
        args["registeredDatasets"] = datasets::read(root)?;
    }
    analysis::request(kind, &args)
}

pub fn run() -> Result<bool> {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let command = args.first().map(String::as_str).unwrap_or("help");
    let root = runtime::home()?;
    let engine = Arc::new(Engine::default());
    let result = match command {
        "help" | "--help" | "-h" => {
            println!("{HELP}");
            return Ok(true);
        }
        "status" => runtime::status(&root),
        "install" => runtime::install(&root, |message| eprintln!("{message}"))?,
        "mcp-config" => {
            json!({"mcpServers":{"symvacas":{"command":root.join("symvacas-cli.exe"),"args":["mcp"]}}})
        }
        "skill" => {
            println!("{SKILL}");
            return Ok(true);
        }
        "mcp" => return serve_mcp(&root, engine).map(|_| true),
        "catalog" => catalog_cli(&args[1..])?,
        "dataset" => dataset_cli(&root, &args[1..])?,
        "eval" | "evaluate" | "python" | "request" | "stats" | "statistics" | "solve" => {
            let (positionals, mut request, inputs, mut analysis) = options(&args[1..], command)?;
            if positionals.is_empty() || command != "solve" && positionals.len() != 1 {
                return Err("Supply one quoted expression or one file path. See --help.".into());
            }
            match command {
                "eval" | "evaluate" => {
                    request["expression"] = json!(positionals[0]);
                    request = analysis_request(&root, "statistics", &request)?;
                }
                "stats" | "statistics" | "solve" => {
                    for (key, value) in request.as_object().unwrap() {
                        analysis[key] = value.clone();
                    }
                    if command == "solve" {
                        analysis["equations"] = if positionals.len() == 1 && positionals[0] == "-" {
                            json!(read_file("-")?)
                        } else {
                            json!(positionals)
                        };
                        request = analysis_request(&root, "solve_equations", &analysis)?;
                    } else {
                        if let Some(file) = analysis["dataFile"].as_str() {
                            analysis["datasets"] = serde_json::from_str(&read_file(file)?)
                                .map_err(|e| e.to_string())?;
                        }
                        analysis["expression"] = json!(if positionals[0] == "-" {
                            read_file("-")?
                        } else {
                            positionals[0].clone()
                        });
                        request = analysis_request(&root, "statistics", &analysis)?;
                    }
                }
                "python" => {
                    request["action"] = json!("python");
                    request["source"] = json!(read_file(&positionals[0])?);
                    request["filename"] = json!(positionals[0]);
                    request["inputs"] = json!(inputs);
                }
                _ => {
                    request = serde_json::from_str(&read_file(&positionals[0])?)
                        .map_err(|e| e.to_string())?
                }
            }
            execute(&root, &engine, request)?
        }
        _ => return Err(format!("Unknown command: {command}\n{HELP}")),
    };
    println!(
        "{}",
        serde_json::to_string_pretty(&result).map_err(|e| e.to_string())?
    );
    Ok(result["ok"] != false && result["ready"] != false)
}

fn tools() -> Value {
    let mut result = json!([
        {"name":"evaluate","description":"Evaluate SymvaCAS calculator syntax or LaTeX locally. Supports symbolic algebra, calculus, equations, matrices and statistics. No arbitrary Python execution.","inputSchema":{"type":"object","properties":{"expression":{"type":"string"},"angle":{"type":"string","enum":["DEG","RAD","GRAD"],"default":"RAD"},"precision":{"type":"integer","minimum":3,"maximum":200},"displayDigits":{"type":"integer","minimum":1,"maximum":200}},"required":["expression"],"additionalProperties":false}},
        {"name":"engine_request","description":"Execute a structured SymvaCAS web-engine request (validated AST); supports graph, graphAnalysis, probability, programmer, constants and evaluate. Python scripts use the separate python tool.","inputSchema":{"type":"object","properties":{"request":{"type":"object"}},"required":["request"],"additionalProperties":false}},
        {"name":"python","description":"Execute user-authorized Python code locally with CPython, sympy, mpmath and symvacas_catalog. Has full current-user filesystem and network permissions. Supply all input() values in inputs.","inputSchema":{"type":"object","properties":{"source":{"type":"string"},"inputs":{"type":"array","items":{"type":"string"}}},"required":["source"],"additionalProperties":false}},
        {"name":"runtime_status","description":"Check whether embedded Python and required packages are installed.","inputSchema":{"type":"object","properties":{},"additionalProperties":false}}
    ]);
    result.as_array_mut().unwrap().extend(analysis::tools());
    result.as_array_mut().unwrap().extend(datasets::tools());
    result.as_array_mut().unwrap().push(usage::tool());
    for tool in result.as_array_mut().unwrap() {
        let examples = match tool["name"].as_str().unwrap_or("") {
            "statistics" => {
                json!([{"expression":"ttest2(0,a,b)","datasets":{"a":[1,2,3,4,5],"b":[2,4,6,8,10]}},{"expression":"stats(cohort)"},{"expression":"regression(data,linear)","datasets":{"data":[[1,3],[2,5],[3,7],[4,9],[5,11]]}}])
            }
            "solve_equations" => {
                json!([{"equations":["x+y=3","x-y=1"],"variables":["x","y"]},{"equations":"cos(x)=x","method":"nsolve","initialGuess":0.5}])
            }
            "search_catalog" => json!([{"query":"ttest2","limit":5},{"query":"회귀","limit":5}]),
            "save_statistics_dataset" => {
                json!([{"name":"cohort","data":[1,2,3,4,5]},{"name":"trial","csv":"x,y\n1,3\n2,5\n3,7"}])
            }
            "get_statistics_dataset" => json!([{"name":"cohort"}]),
            "get_usage" => json!([{"section":"overview"},{"section":"statistics"}]),
            _ => continue,
        };
        tool["inputSchema"]["examples"] = examples;
    }
    result
}

fn call_tool(root: &Path, engine: &Engine, params: &Value) -> Result<Value> {
    let args = &params["arguments"];
    match params["name"].as_str().unwrap_or("") {
        "runtime_status" => Ok(runtime::status(root)),
        "get_usage" => usage::get(args),
        "search_catalog" => catalog::search(args),
        "list_statistics_datasets" => datasets::list(root),
        "get_statistics_dataset" => {
            datasets::get(root, args["name"].as_str().ok_or("name must be a string")?)
        }
        "save_statistics_dataset" => datasets::save(root, args),
        "statistics" | "solve_equations" => execute(
            root,
            engine,
            analysis_request(root, params["name"].as_str().unwrap(), args)?,
        ),
        "evaluate" => {
            let expression = args["expression"]
                .as_str()
                .ok_or("expression must be a string")?;
            let mut input = args.clone();
            input["expression"] = json!(expression);
            execute(root, engine, analysis_request(root, "statistics", &input)?)
        }
        "engine_request" => {
            let request = args.get("request").ok_or("Missing request")?;
            if request["action"] == "python" {
                return Err("Use the python tool for scripts".into());
            }
            execute(root, engine, request.clone())
        }
        "python" => execute(
            root,
            engine,
            json!({"action":"python","source":args["source"].as_str().ok_or("source must be a string")?,"inputs":args.get("inputs").cloned().unwrap_or(json!([]))}),
        ),
        _ => Err("Unknown tool".into()),
    }
}

fn rpc_error(id: Value, code: i64, message: &str) -> Value {
    json!({"jsonrpc":"2.0","id":id,"error":{"code":code,"message":message}})
}

fn serve_mcp(root: &Path, engine: Arc<Engine>) -> Result<()> {
    let (sender, receiver) = mpsc::channel();
    let active = Arc::new(Mutex::new(None::<Value>));
    let reader_engine = engine.clone();
    let reader_active = active.clone();
    std::thread::spawn(move || {
        for line in io::stdin().lock().lines() {
            let line = match line {
                Ok(line) => line,
                Err(_) => break,
            };
            if line.trim().is_empty() {
                continue;
            }
            let message = serde_json::from_str::<Value>(&line);
            if let Ok(ref value) = message {
                if value["method"] == "notifications/cancelled" {
                    if reader_active.lock().unwrap().as_ref() == Some(&value["params"]["requestId"])
                    {
                        reader_engine.cancel(1);
                    }
                    continue;
                }
            }
            if sender.send(message).is_err() {
                break;
            }
        }
        reader_engine.cancel(1);
    });
    let mut initialized = false;
    let mut stdout = io::stdout().lock();
    for parsed in receiver {
        let response = match parsed {
            Err(_) => rpc_error(Value::Null, -32700, "Parse error"),
            Ok(message) => {
                let id = message.get("id").cloned();
                if message["jsonrpc"] != "2.0" || !message["method"].is_string() {
                    rpc_error(id.unwrap_or(Value::Null), -32600, "Invalid Request")
                } else if id.is_none() {
                    continue;
                } else {
                    let id = id.unwrap();
                    let method = message["method"].as_str().unwrap();
                    let result = match method {
                        "initialize" => {
                            initialized = true;
                            let requested =
                                message["params"]["protocolVersion"].as_str().unwrap_or("");
                            let version =
                                if ["2024-11-05", "2025-03-26", "2025-06-18", "2025-11-25"]
                                    .contains(&requested)
                                {
                                    requested
                                } else {
                                    "2025-11-25"
                                };
                            Some(
                                json!({"protocolVersion":version,"capabilities":{"tools":{"listChanged":false},"resources":{"subscribe":false,"listChanged":false}},"serverInfo":{"name":"symvacas","version":env!("CARGO_PKG_VERSION")},"instructions":usage::INSTRUCTIONS}),
                            )
                        }
                        "ping" => Some(json!({})),
                        _ if !initialized => {
                            let reply = rpc_error(id, -32002, "Initialize the server first");
                            writeln!(stdout, "{reply}").map_err(|e| e.to_string())?;
                            stdout.flush().map_err(|e| e.to_string())?;
                            continue;
                        }
                        "tools/list" => Some(json!({"tools":tools()})),
                        "tools/call" => {
                            *active.lock().unwrap() = Some(id.clone());
                            let result = call_tool(root, &engine, &message["params"]);
                            *active.lock().unwrap() = None;
                            let (value, error) = match result {
                                Ok(value) => {
                                    let error = value["ok"] == false || value["ready"] == false;
                                    (value, error)
                                }
                                Err(error) => (json!({"ok":false,"error":error}), true),
                            };
                            Some(
                                json!({"content":[{"type":"text","text":value.to_string()}],"isError":error}),
                            )
                        }
                        "resources/list" => Some(
                            json!({"resources":[{"uri":"symvacas://guide","name":"symvacas-mcp-guide","description":"Self-contained tool usage and examples; no skill required","mimeType":"text/markdown"},{"uri":"symvacas://skill","name":"symvacas-skill","description":"Optional agent skill","mimeType":"text/markdown"}]}),
                        ),
                        "resources/read" if message["params"]["uri"] == "symvacas://guide" => Some(
                            json!({"contents":[{"uri":"symvacas://guide","mimeType":"text/markdown","text":usage::GUIDE}]}),
                        ),
                        "resources/read" if message["params"]["uri"] == "symvacas://skill" => Some(
                            json!({"contents":[{"uri":"symvacas://skill","mimeType":"text/markdown","text":SKILL}]}),
                        ),
                        _ => None,
                    };
                    match result {
                        Some(result) => json!({"jsonrpc":"2.0","id":id,"result":result}),
                        None => rpc_error(id, -32601, "Method not found"),
                    }
                }
            }
        };
        writeln!(stdout, "{response}").map_err(|e| e.to_string())?;
        stdout.flush().map_err(|e| e.to_string())?;
    }
    Ok(())
}
