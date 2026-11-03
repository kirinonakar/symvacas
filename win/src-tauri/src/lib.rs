pub mod analysis;
pub mod catalog;
pub mod datasets;
pub mod engine;
pub mod headless;
pub mod parser;
pub mod runtime;
pub mod usage;

use serde_json::{json, Value};
use std::sync::Arc;
use tauri::{ipc::Channel, State};
use tauri_plugin_dialog::DialogExt;

#[tauri::command]
fn set_window_theme(window: tauri::Window, theme: Option<tauri::Theme>) -> runtime::Result<()> {
    window.set_theme(theme).map_err(|e| e.to_string())
}

#[tauri::command]
async fn sync_statistics_datasets(
    base: Value,
    changes: Value,
    bootstrap: bool,
) -> runtime::Result<Value> {
    tauri::async_runtime::spawn_blocking(move || {
        datasets::sync(&runtime::home()?, &base, &changes, bootstrap)
    })
    .await
    .map_err(|e| e.to_string())?
}

#[tauri::command]
async fn save_export(app: tauri::AppHandle, name: String, bytes: Vec<u8>) -> runtime::Result<bool> {
    tauri::async_runtime::spawn_blocking(move || {
        let filename = std::path::Path::new(&name)
            .file_name()
            .and_then(|value| value.to_str())
            .unwrap_or("symvacas-export");
        let Some(selected) = app
            .dialog()
            .file()
            .set_file_name(filename)
            .blocking_save_file()
        else {
            return Ok(false);
        };
        let path = selected.into_path().map_err(|e| e.to_string())?;
        std::fs::write(path, bytes).map_err(|e| e.to_string())?;
        Ok(true)
    })
    .await
    .map_err(|e| e.to_string())?
}

#[tauri::command]
async fn python_status() -> runtime::Result<Value> {
    tauri::async_runtime::spawn_blocking(|| Ok(runtime::status(&runtime::home()?)))
        .await
        .map_err(|e| e.to_string())?
}

#[tauri::command]
async fn install_python(on_progress: Channel<String>) -> runtime::Result<Value> {
    tauri::async_runtime::spawn_blocking(move || {
        runtime::install(&runtime::home()?, |message| {
            let _ = on_progress.send(message.to_string());
        })
    })
    .await
    .map_err(|e| e.to_string())?
}

#[tauri::command]
async fn native_start(
    session: u64,
    engine: State<'_, Arc<engine::Engine>>,
) -> runtime::Result<Value> {
    let engine = engine.inner().clone();
    tauri::async_runtime::spawn_blocking(move || engine.start(&runtime::home()?, session))
        .await
        .map_err(|e| e.to_string())?
}

#[tauri::command]
async fn native_execute(
    session: u64,
    id: u64,
    request: Value,
    on_event: Channel<Value>,
    engine: State<'_, Arc<engine::Engine>>,
) -> runtime::Result<Value> {
    let engine = engine.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        engine.execute(session, id, request, |message| {
            on_event.send(message).map_err(|e| e.to_string())?;
            Ok(None)
        })
    })
    .await
    .map_err(|e| e.to_string())?
}

#[tauri::command]
fn native_input(
    session: u64,
    id: u64,
    input_id: u64,
    value: String,
    engine: State<'_, Arc<engine::Engine>>,
) -> runtime::Result<()> {
    engine.input(session, id, input_id, value)
}

#[tauri::command]
async fn native_cancel(
    session: u64,
    engine: State<'_, Arc<engine::Engine>>,
) -> runtime::Result<()> {
    let engine = engine.inner().clone();
    tauri::async_runtime::spawn_blocking(move || engine.cancel(session))
        .await
        .map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
fn integration_info() -> runtime::Result<Value> {
    let root = runtime::home()?;
    let cli = root.join("symvacas-cli.exe");
    Ok(
        json!({"cli":cli,"skill":skill_folder(&root).join("SKILL.md"),"mcp":{"mcpServers":{"symvacas":{"command":cli,"args":["mcp"]}}}}),
    )
}

fn skill_folder(root: &std::path::Path) -> std::path::PathBuf {
    // Explorer needs a native Windows path, rather than a mixed-separator path.
    root.join("skills").join("symvacas")
}

#[tauri::command]
fn open_skill_folder() -> runtime::Result<()> {
    let folder = skill_folder(&runtime::home()?);
    if !folder.is_dir() {
        return Err(format!("Skill folder not found: {}", folder.display()));
    }
    let windows = std::env::var_os("SystemRoot").ok_or("Cannot locate Windows folder")?;
    std::process::Command::new(std::path::PathBuf::from(windows).join("explorer.exe"))
        .arg(folder)
        .spawn()
        .map_err(|e| format!("Cannot open Skill folder: {e}"))?;
    Ok(())
}

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .manage(Arc::new(engine::Engine::default()))
        .invoke_handler(tauri::generate_handler![
            set_window_theme,
            sync_statistics_datasets,
            python_status,
            install_python,
            native_start,
            native_execute,
            native_input,
            native_cancel,
            integration_info,
            open_skill_folder,
            save_export
        ])
        .run(tauri::generate_context!())
        .expect("Cannot run SymvaCAS");
}

#[cfg(all(test, windows))]
mod tests {
    #[test]
    fn skill_folder_uses_windows_separators_for_explorer() {
        let root = std::path::Path::new(r"C:\앱 폴더\SymvaCAS");
        assert_eq!(
            super::skill_folder(root).as_os_str(),
            std::ffi::OsStr::new(r"C:\앱 폴더\SymvaCAS\skills\symvacas")
        );
    }
}
