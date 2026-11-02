use fs2::FileExt;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{
    fs,
    io::{Cursor, Read},
    path::{Path, PathBuf},
    process::{Command, Stdio},
    time::Duration,
};

pub type Result<T> = std::result::Result<T, String>;
pub const ENGINE: &[u8] = include_bytes!("../generated/engine.zip");
const LOCK: &str = include_str!("../../runtime-lock.json");

pub fn home() -> Result<PathBuf> {
    std::env::current_exe()
        .map_err(|e| e.to_string())?
        .parent()
        .map(Path::to_path_buf)
        .ok_or_else(|| "Cannot locate executable folder".into())
}

pub fn quiet(command: &mut Command) -> &mut Command {
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        command.creation_flags(0x08000000); // CREATE_NO_WINDOW
    }
    command
}

pub fn python(root: &Path) -> PathBuf {
    root.join("python_embeded/python.exe")
}

pub fn probe_at(path: &Path) -> Result<Value> {
    let mut command = Command::new(path);
    let output = quiet(&mut command).args(["-I", "-X", "utf8", "-c",
        "import sys,json,sympy,mpmath,pip;print(json.dumps({'ready':True,'python':sys.version.split()[0],'sympy':sympy.__version__,'mpmath':mpmath.__version__,'pip':pip.__version__}))"])
        .stdin(Stdio::null()).output().map_err(|e| e.to_string())?;
    if !output.status.success() {
        return Err(String::from_utf8_lossy(&output.stderr).trim().to_string());
    }
    serde_json::from_slice(&output.stdout).map_err(|e| e.to_string())
}

pub fn status(root: &Path) -> Value {
    let path = python(root);
    let mut result = match probe_at(&path) {
        Ok(value) => value,
        Err(error) => json!({"ready":false,"error":error}),
    };
    result["path"] = json!(path.parent().unwrap().to_string_lossy());
    result["expected"] = serde_json::from_str::<Value>(LOCK).unwrap()["python"]["version"].clone();
    result
}

fn download(client: &reqwest::blocking::Client, item: &Value) -> Result<Vec<u8>> {
    let url = item["url"].as_str().ok_or("Missing download URL")?;
    let mut response = client
        .get(url)
        .send()
        .map_err(|e| e.to_string())?
        .error_for_status()
        .map_err(|e| e.to_string())?;
    let mut data = Vec::new();
    Read::by_ref(&mut response)
        .take(100 * 1024 * 1024 + 1)
        .read_to_end(&mut data)
        .map_err(|e| e.to_string())?;
    if data.len() > 100 * 1024 * 1024 {
        return Err("Download exceeds 100 MiB".into());
    }
    if format!("{:x}", Sha256::digest(&data)) != item["sha256"].as_str().unwrap_or("") {
        return Err(format!("SHA-256 mismatch: {url}"));
    }
    Ok(data)
}

fn unpack(data: Vec<u8>, target: &Path) -> Result<()> {
    let mut archive = zip::ZipArchive::new(Cursor::new(data)).map_err(|e| e.to_string())?;
    // enclosed_name prevents archive path traversal; these distributions contain no symlinks.
    for index in 0..archive.len() {
        let mut entry = archive.by_index(index).map_err(|e| e.to_string())?;
        let relative = entry.enclosed_name().ok_or("Invalid archive path")?;
        if entry
            .unix_mode()
            .is_some_and(|mode| mode & 0o170000 == 0o120000)
        {
            return Err("Archive symlink rejected".into());
        }
        let path = target.join(relative);
        if entry.is_dir() {
            fs::create_dir_all(&path).map_err(|e| e.to_string())?;
        } else {
            fs::create_dir_all(path.parent().unwrap()).map_err(|e| e.to_string())?;
            let mut file = fs::File::create(path).map_err(|e| e.to_string())?;
            std::io::copy(&mut entry, &mut file).map_err(|e| e.to_string())?;
        }
    }
    Ok(())
}

pub fn install(root: &Path, progress: impl Fn(&str)) -> Result<Value> {
    let lock_file = fs::OpenOptions::new()
        .create(true)
        .truncate(false)
        .read(true)
        .write(true)
        .open(root.join(".symvacas-install.lock"))
        .map_err(|e| {
            format!("Cannot write to executable folder: {e}. Move the app to a writable folder.")
        })?;
    lock_file
        .try_lock_exclusive()
        .map_err(|_| "Another SymvaCAS instance is installing Python")?;
    let destination = root.join("python_embeded");
    if status(root)["ready"] == true {
        progress("Python dependencies are already installed.");
        return Ok(status(root));
    }
    let stage = root.join(format!(".python_embeded-install-{}", std::process::id()));
    // Never overwrite an unknown directory left by a previous installation.
    fs::create_dir(&stage).map_err(|e| {
        format!(
            "Cannot create installation staging folder {}: {e}",
            stage.display()
        )
    })?;
    let result = (|| {
        let manifest: Value = serde_json::from_str(LOCK).map_err(|e| e.to_string())?;
        let client = reqwest::blocking::Client::builder()
            .timeout(Duration::from_secs(180))
            .user_agent("SymvaCAS-Windows/0.1")
            .build()
            .map_err(|e| e.to_string())?;
        progress("Downloading and verifying embedded CPython…");
        unpack(download(&client, &manifest["python"])?, &stage)?;
        let packages = stage.join("Lib/site-packages");
        fs::create_dir_all(&packages).map_err(|e| e.to_string())?;
        fs::create_dir_all(stage.join("Scripts")).map_err(|e| e.to_string())?;
        fs::write(
            stage.join("python314._pth"),
            "python314.zip\n.\nLib/site-packages\nimport site\n",
        )
        .map_err(|e| e.to_string())?;
        for item in manifest["wheels"].as_array().ok_or("Missing wheels")? {
            progress(&format!(
                "Downloading and verifying {} {}…",
                item["name"].as_str().unwrap_or("package"),
                item["version"].as_str().unwrap_or("")
            ));
            unpack(download(&client, item)?, &packages)?;
        }
        progress("Checking Python, SymPy, mpmath and pip…");
        probe_at(&stage.join("python.exe"))?;
        fs::write(stage.join("symvacas-runtime.json"), LOCK).map_err(|e| e.to_string())?;
        let backup = root.join(format!("python_embeded-backup-{}", std::process::id()));
        let had_existing = destination.exists();
        if had_existing {
            fs::rename(&destination, &backup)
                .map_err(|e| format!("Cannot preserve the existing Python folder: {e}"))?;
        }
        if let Err(error) = fs::rename(&stage, &destination) {
            if had_existing {
                let _ = fs::rename(&backup, &destination);
            }
            return Err(error.to_string());
        }
        if had_existing {
            progress(&format!(
                "Previous Python folder preserved at {}",
                backup.display()
            ));
        }
        progress("Python installation complete.");
        Ok(status(root))
    })();
    // stage is a fixed child created by this invocation; destination is never deleted.
    if stage.exists() {
        let _ = fs::remove_dir_all(stage);
    }
    result
}

pub fn engine_archive(root: &Path) -> Result<PathBuf> {
    let directory = root.join("python_embeded/_symvacas");
    fs::create_dir_all(&directory).map_err(|e| e.to_string())?;
    let digest = format!("{:x}", Sha256::digest(ENGINE));
    let path = directory.join(format!("engine-{digest}.zip"));
    if !path.is_file() {
        let temporary = directory.join(format!("engine-{}-{}.tmp", digest, std::process::id()));
        fs::write(&temporary, ENGINE).map_err(|e| e.to_string())?;
        // Another process may have written the identical content meanwhile.
        if let Err(error) = fs::rename(&temporary, &path) {
            let _ = fs::remove_file(&temporary);
            if !path.is_file() {
                return Err(error.to_string());
            }
        }
    }
    Ok(path)
}
