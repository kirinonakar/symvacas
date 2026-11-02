use crate::runtime::Result;
use boa_engine::{Context, Source};
use serde_json::Value;

pub fn parse(expression: &str, unlimited: bool) -> Result<Value> {
    evaluate(
        &format!(
            "parse(latexInput({}))",
            serde_json::to_string(expression).map_err(|e| e.to_string())?
        ),
        unlimited,
    )
}

pub fn request(kind: &str, args: &Value) -> Result<Value> {
    let function = match kind {
        "statistics" => "statisticsInput",
        "solve_equations" => "equationInput",
        "dataset" => "datasetInput",
        _ => return Err("Unknown request builder".into()),
    };
    evaluate(
        &format!("desktopRequests.{function}({args})"),
        args["removeComputationLimit"] == true,
    )
}

fn evaluate(expression: &str, unlimited: bool) -> Result<Value> {
    let mut context = Context::default();
    context
        .runtime_limits_mut()
        .set_loop_iteration_limit(2_000_000);
    let source = format!(
        "{}\ncomputationLimitsRemoved=()=>{};JSON.stringify({})",
        include_str!("../generated/parser.js"),
        unlimited,
        expression
    );
    let result = context
        .eval(Source::from_bytes(&source))
        .map_err(|e| e.to_string())?;
    let text = result
        .as_string()
        .ok_or("Parser did not return an AST")?
        .to_std_string_escaped();
    serde_json::from_str(&text).map_err(|e| e.to_string())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn shared_parser_handles_calculator_syntax() {
        for source in [
            "1/3+1/6",
            "diff(sin(x^2),x)",
            "solve(x^2-5*x+6=0,x)",
            "xy^2",
            "\\frac{1}{2}",
            "mean([1,2,3])",
        ] {
            assert!(parse(source, false).is_ok(), "{source}");
        }
        assert!(parse("__import__('os').system('bad')", false).is_err());
    }
}
