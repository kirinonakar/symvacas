fn main() {
    let android = "../../app/build.gradle.kts";
    println!("cargo:rerun-if-changed={android}");
    let source = std::fs::read_to_string(android).expect("Cannot read Android versionName");
    let version = source
        .lines()
        .find_map(|line| {
            let (key, value) = line.trim().split_once('=')?;
            if key.trim() != "versionName" {
                return None;
            }
            value.trim().strip_prefix('"')?.split('"').next()
        })
        .expect("Missing Android versionName");
    assert_eq!(std::env::var("CARGO_PKG_VERSION").unwrap(), version,
        "Windows version must match Android. Run npm run prepare:app or npm run build in win/ first.");
    tauri_build::build()
}
