use crate::runtime::Result;
use serde_json::{json, Value};

pub const GUIDE: &str = include_str!("../../MCP_GUIDE.md");
pub const INSTRUCTIONS:&str="SymvaCAS is a local calculator, statistics engine and equation solver. No skill installation or activation is needed. Start with get_usage (section overview or all) for tool argument examples and result interpretation. Use search_catalog with an English/Korean query to find exact signatures and examples before choosing unfamiliar functions. For reusable data, list_statistics_datasets/get_statistics_dataset inspect saved data; save_statistics_dataset registers data or csv (existing names require replace=true). Saved names can be used directly in statistics and evaluate expressions and are shared with the Windows GUI. For one-off analyses pass statistics {expression:'ttest2(0,a,b)',datasets:{a:[1,2,3,4,5],b:[2,4,6,8,10]}}. For equations use solve_equations {equations:['x+y=3','x-y=1'],variables:['x','y']}; numeric/ODE/PDE methods and steps are described in its schema and get_usage. Defaults: RAD, precision 30, displayDigits 10. Check ok/error, statisticsReport/regression or equationSteps/solutionSteps, including assumptions and restrictions. runtime_status checks Python; missing dependencies can be installed in the app's Python / MCP panel or CLI install. Catalog/help/data registration work without Python. Python is unrestricted local code execution and is only for user-authorized scripts. The complete guide is also resource symvacas://guide.";

pub fn get(args: &Value) -> Result<Value> {
    let section = match args.get("section") {
        Some(value) => value.as_str().ok_or("section must be a string")?,
        None => "overview",
    };
    let text = if section == "all" {
        GUIDE.to_owned()
    } else {
        let mut selected = String::new();
        let mut active = false;
        for line in GUIDE.lines() {
            if let Some(title) = line.strip_prefix("## ") {
                if active {
                    break;
                }
                active = title.eq_ignore_ascii_case(section);
            }
            if active {
                selected.push_str(line);
                selected.push('\n');
            }
        }
        if selected.is_empty() {
            return Err("section must be overview, catalog, datasets, statistics, equations, runtime or all".into());
        }
        selected
    };
    Ok(json!({"ok":true,"section":section,"text":text}))
}

pub fn tool() -> Value {
    json!({"name":"get_usage","description":"Read self-contained SymvaCAS MCP usage without an agent skill. Includes workflow, tool-argument JSON examples, saved datasets, catalog search, statistical reports, equation methods, defaults and errors. Start with section overview; request a focused section or all. Works without Python or access to local documentation files.","inputSchema":{"type":"object","properties":{"section":{"type":"string","enum":["overview","catalog","datasets","statistics","equations","runtime","all"],"default":"overview"}},"additionalProperties":false},"annotations":{"readOnlyHint":true}})
}
