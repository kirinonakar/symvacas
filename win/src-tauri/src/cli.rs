fn main() {
    match symvacas_windows::headless::run() {
        Ok(true) => (),
        Ok(false) => std::process::exit(1),
        Err(error) => {
            if std::env::args().nth(1).as_deref() != Some("mcp") {
                println!("{}", serde_json::json!({"ok":false,"error":error}));
            }
            eprintln!("{error}");
            std::process::exit(1);
        }
    }
}
