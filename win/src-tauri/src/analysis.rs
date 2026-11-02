use crate::{parser, runtime::Result};
use serde_json::{json, Value};

pub fn settings(args: &Value) -> Result<Value> {
    let angle = match args.get("angle") {
        Some(value) => value.as_str().ok_or("angle must be a string")?,
        None => "RAD",
    };
    if !["DEG", "RAD", "GRAD"].contains(&angle) {
        return Err("Angle must be DEG, RAD or GRAD".into());
    }
    fn integer(args: &Value, key: &str, default: u64, min: u64) -> Result<u64> {
        let value = match args.get(key) {
            Some(value) => value
                .as_u64()
                .ok_or_else(|| format!("{key} must be an integer"))?,
            None => default,
        };
        if !(min..=200).contains(&value) {
            return Err(format!("{key} must be {min}..200"));
        }
        Ok(value)
    }
    let precision = integer(args, "precision", 30, 3)?;
    let digits = integer(args, "displayDigits", 10, 1)?;
    let unlimited = match args.get("removeComputationLimit") {
        Some(value) => value
            .as_bool()
            .ok_or("removeComputationLimit must be a boolean")?,
        None => false,
    };
    Ok(
        json!({"angle":angle,"precision":precision,"displayDigits":digits,"removeComputationLimit":unlimited}),
    )
}

pub fn request(kind: &str, args: &Value) -> Result<Value> {
    if !args.is_object() {
        return Err("Arguments must be an object".into());
    }
    let settings = settings(args)?;
    let mut request = parser::request(kind, args)?;
    for (key, value) in settings.as_object().unwrap() {
        request[key] = value.clone();
    }
    Ok(request)
}

pub fn tools() -> Vec<Value> {
    let settings = json!({"angle":{"type":"string","enum":["DEG","RAD","GRAD"],"default":"RAD"},"precision":{"type":"integer","minimum":3,"maximum":200,"default":30},"displayDigits":{"type":"integer","minimum":1,"maximum":200,"default":10},"removeComputationLimit":{"type":"boolean","default":false}});
    let mut stats = settings.clone();
    stats["expression"] = json!({"type":"string","description":"Calculator statistics expression. Search search_catalog for exact signatures and examples, e.g. ttest2(0,a,b) or regression(data,linear)."});
    stats["datasets"] = json!({"type":"object","description":"Named vectors or row-major tables referenced by expression. Cells: JSON numbers, decimal strings (preserve precision), calculator expressions, or null for NA. The engine enforces analysis-specific missing-data rules.","additionalProperties":{"type":"array"}});
    let mut solve = settings;
    solve["equations"] = json!({"oneOf":[{"type":"string"},{"type":"array","items":{"type":"string"},"minItems":1}],"description":"Equation or inequality; a newline string or array for systems. Supports calculator syntax and LaTeX."});
    solve["variables"] = json!({"oneOf":[{"type":"string"},{"type":"array","items":{"type":"string"},"minItems":1}],"default":"x","description":"One symbol or comma-separated/list variables. Differential methods use one dependent variable."});
    solve["method"] =
        json!({"type":"string","enum":["solve","nsolve","dsolve","pdsolve"],"default":"solve"});
    solve["initialGuess"] = json!({"oneOf":[{"type":"number"},{"type":"string"},{"type":"array","items":{"type":"number"}}],"default":"0,1","description":"nsolve: scalar initial guess, [x0,y0] for systems, or string 0,1 for bounds."});
    solve["independentVariable"] =
        json!({"type":"string","default":"x","description":"dsolve independent variable"});
    solve["initialConditions"] = json!({"type":"string","description":"dsolve initial-condition argument in calculator syntax; see search_catalog dsolve"});
    solve["hint"] =
        json!({"type":"string","description":"Optional pdsolve hint in calculator syntax"});
    solve["steps"] = json!({"type":"boolean","default":true,"description":"Include available step-by-step explanations or solver summary"});
    vec![
        json!({"name":"search_catalog","description":"Find SymvaCAS functions before calling them. Searches function names, categories, English/Korean descriptions and examples; returns signatures, templates and runnable example expressions. Works even before Python installation. Empty query lists functions with pagination.","inputSchema":{"type":"object","properties":{"query":{"type":"string","default":""},"category":{"type":"string","description":"Optional category substring; categories are returned with every search"},"limit":{"type":"integer","minimum":1,"maximum":100,"default":10},"offset":{"type":"integer","minimum":0,"default":0}},"additionalProperties":false},"annotations":{"readOnlyHint":true}}),
        json!({"name":"statistics","description":"Run descriptive statistics, hypothesis tests, ANOVA, regression and advanced catalog analyses on inline or named datasets. Uses the same statistics request path as the web UI, including large datasets, statisticsReport and regression details when provided by the analysis. Search search_catalog to choose a function and its arguments.","inputSchema":{"type":"object","properties":stats,"required":["expression"],"additionalProperties":false},"annotations":{"readOnlyHint":true}}),
        json!({"name":"solve_equations","description":"Solve equations, systems and inequalities, numeric roots, ordinary/partial differential equations using the same equation builder as the web UI. Returns exact/numeric results and available derivations. Search search_catalog for solve/nsolve/dsolve/pdsolve examples.","inputSchema":{"type":"object","properties":solve,"required":["equations"],"additionalProperties":false},"annotations":{"readOnlyHint":true}}),
    ]
}
