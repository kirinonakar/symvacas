use crate::{parser, runtime::Result};
use fs2::FileExt;
use serde_json::{json, Value};
use std::{fs, path::Path};

fn transaction(root: &Path, update: impl FnOnce(&mut Value) -> Result<bool>) -> Result<Value> {
    let folder = root.join("data");
    fs::create_dir_all(&folder).map_err(|e| e.to_string())?;
    let lock = fs::OpenOptions::new()
        .read(true)
        .write(true)
        .create(true)
        .truncate(false)
        .open(folder.join("statistics-datasets.lock"))
        .map_err(|e| e.to_string())?;
    lock.lock_exclusive().map_err(|e| e.to_string())?;
    let path = folder.join("statistics-datasets.json");
    let mut registry = if path.exists() {
        serde_json::from_slice::<Value>(&fs::read(&path).map_err(|e| e.to_string())?).map_err(
            |e| format!("Cannot read statistics registry; existing data was preserved: {e}"),
        )?
    } else {
        json!({"version":1,"datasets":{}})
    };
    if registry["version"] != 1 || !registry["datasets"].is_object() {
        return Err("Unsupported statistics registry; existing data was preserved".into());
    }
    if update(&mut registry["datasets"])? {
        let temporary = folder.join(format!("statistics-datasets-{}.tmp", std::process::id()));
        let bytes = serde_json::to_vec_pretty(&registry).map_err(|e| e.to_string())?;
        let mut file = fs::File::create(&temporary).map_err(|e| e.to_string())?;
        use std::io::Write;
        file.write_all(&bytes)
            .and_then(|_| file.sync_all())
            .map_err(|e| e.to_string())?;
        drop(file);
        fs::rename(&temporary, &path).map_err(|e| e.to_string())?;
    }
    Ok(registry["datasets"].clone())
}

fn name(value: &str) -> Result<()> {
    if value.trim().is_empty() || value.len() > 512 || value.chars().any(char::is_control) {
        return Err(
            "Dataset name must be nonempty, at most 512 bytes, without control characters".into(),
        );
    }
    Ok(())
}
fn record(value: &Value) -> Result<Value> {
    let source = value["source"]
        .as_str()
        .ok_or("Dataset source must be CSV text")?;
    let kind = value["kind"].as_str().ok_or("Missing dataset kind")?;
    let valid = ["list", "xy", "xyz"].contains(&kind)
        || kind
            .strip_prefix("columns:")
            .and_then(|n| n.parse::<u64>().ok())
            .is_some_and(|n| (1..=101).contains(&n));
    if !valid || source.len() > 16 * 1024 * 1024 {
        return Err("Invalid dataset kind or input exceeds 16 MiB".into());
    }
    Ok(json!({"source":source,"kind":kind}))
}

pub fn read(root: &Path) -> Result<Value> {
    transaction(root, |_| Ok(false))
}
pub fn list(root: &Path) -> Result<Value> {
    let datasets = read(root)?;
    Ok(
        json!({"ok":true,"path":root.join("data/statistics-datasets.json"),"datasets":datasets.as_object().unwrap().iter().map(|(name,item)|json!({"name":name,"kind":item["kind"]})).collect::<Vec<_>>()}),
    )
}
pub fn get(root: &Path, name_value: &str) -> Result<Value> {
    let values = read(root)?;
    let value = values
        .get(name_value)
        .ok_or_else(|| format!("Unknown statistics dataset: {name_value}"))?;
    Ok(json!({"ok":true,"name":name_value,"source":value["source"],"kind":value["kind"]}))
}
pub fn save(root: &Path, args: &Value) -> Result<Value> {
    let name_value = args["name"].as_str().ok_or("name must be a string")?;
    name(name_value)?;
    let replacement = match args.get("replace") {
        Some(value) => value.as_bool().ok_or("replace must be a boolean")?,
        None => false,
    };
    let prepared = record(&parser::request("dataset", args)?)?;
    let kind = prepared["kind"].clone();
    transaction(root, |values| {
        if values.get(name_value).is_some() && !replacement {
            return Err(format!(
                "Dataset already exists: {name_value}. Use replace=true / --replace to overwrite."
            ));
        }
        values[name_value] = prepared;
        Ok(true)
    })?;
    Ok(
        json!({"ok":true,"name":name_value,"kind":kind,"path":root.join("data/statistics-datasets.json")}),
    )
}

// Compare against the GUI's last saved snapshot so unrelated CLI/MCP edits survive.
pub fn sync(root: &Path, base: &Value, changes: &Value, bootstrap: bool) -> Result<Value> {
    let changes = changes
        .as_object()
        .ok_or("Dataset changes must be an object")?;
    let values = transaction(root, |values| {
        let mut next = values.clone();
        for (key, value) in changes {
            name(key)?;
            if bootstrap && values.get(key).is_some() {
                continue;
            }
            let old = base.get(key).unwrap_or(&Value::Null);
            let current = values.get(key).unwrap_or(&Value::Null);
            let desired = if value.is_null() {
                Value::Null
            } else {
                record(value)?
            };
            if !bootstrap && current != old && current != &desired {
                return Err(format!("Statistics dataset changed in another client: {key}. Reload the app before editing it."));
            }
            if desired.is_null() {
                next.as_object_mut().unwrap().remove(key);
            } else {
                next[key] = desired;
            }
        }
        let changed = next != *values;
        *values = next;
        Ok(changed)
    })?;
    Ok(json!({"datasets":values}))
}

pub fn tools() -> Vec<Value> {
    vec![
        json!({"name":"list_statistics_datasets","description":"List names and types of saved statistics datasets shared with the Windows GUI, CLI and MCP. Use saved names directly in statistics/evaluate expressions.","inputSchema":{"type":"object","properties":{},"additionalProperties":false},"annotations":{"readOnlyHint":true}}),
        json!({"name":"get_statistics_dataset","description":"Read one registered statistics dataset as its CSV/TSV source and kind.","inputSchema":{"type":"object","properties":{"name":{"type":"string"}},"required":["name"],"additionalProperties":false},"annotations":{"readOnlyHint":true}}),
        json!({"name":"save_statistics_dataset","description":"Register a vector, row-major table or CSV/TSV text as a named statistics dataset shared with the Windows GUI. Provide data or csv, not both. Existing names require explicit replace=true. Use parser-compatible names such as cohort or trial for expressions.","inputSchema":{"type":"object","properties":{"name":{"type":"string"},"data":{"type":"array"},"csv":{"type":"string"},"replace":{"type":"boolean","default":false}},"required":["name"],"oneOf":[{"required":["data"],"not":{"required":["csv"]}},{"required":["csv"],"not":{"required":["data"]}}],"additionalProperties":false},"annotations":{"readOnlyHint":false,"destructiveHint":true}}),
    ]
}

#[cfg(test)]
mod tests {
    use super::*;
    struct Workspace(std::path::PathBuf);
    impl Workspace {
        fn new() -> Self {
            let unique = std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos();
            let root = std::env::temp_dir()
                .join(format!("symvacas-registry-{}-{unique}", std::process::id()));
            fs::create_dir(&root).unwrap();
            Self(root)
        }
    }
    impl Drop for Workspace {
        fn drop(&mut self) {
            let _ = fs::remove_dir_all(&self.0);
        }
    }
    #[test]
    fn registry_preserves_concurrent_edits_and_refuses_implicit_replacement() {
        let workspace = Workspace::new();
        let root = &workspace.0;
        save(root, &json!({"name":"cohort","data":[1,2,3]})).unwrap();
        assert!(save(root, &json!({"name":"cohort","data":[9]})).is_err());
        let base = read(root).unwrap();
        save(root, &json!({"name":"cohort","data":[8,10],"replace":true})).unwrap();
        assert!(sync(
            root,
            &base,
            &json!({"cohort":{"source":"4\n5","kind":"list"}}),
            false
        )
        .is_err());
        sync(
            root,
            &base,
            &json!({"newdata":{"source":"6\n7","kind":"list"}}),
            false,
        )
        .unwrap();
        assert_eq!(get(root, "cohort").unwrap()["source"], "8\n10");
        assert_eq!(list(root).unwrap()["datasets"].as_array().unwrap().len(), 2);
        let migrated = sync(
            root,
            &json!({}),
            &json!({"cohort":{"source":"stale","kind":"list"}}),
            true,
        )
        .unwrap();
        assert_eq!(migrated["datasets"]["cohort"]["source"], "8\n10");
        let current = read(root).unwrap();
        sync(root, &current, &json!({"newdata":null}), false).unwrap();
        assert!(get(root, "newdata").is_err());
    }
    #[test]
    fn corrupt_registry_is_preserved() {
        let workspace = Workspace::new();
        let root = &workspace.0;
        fs::create_dir(root.join("data")).unwrap();
        let path = root.join("data/statistics-datasets.json");
        fs::write(&path, "broken-json").unwrap();
        assert!(save(root, &json!({"name":"cohort","data":[1,2]})).is_err());
        assert_eq!(fs::read_to_string(path).unwrap(), "broken-json");
    }
}
