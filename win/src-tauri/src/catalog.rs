use crate::runtime::Result;
use serde_json::{json, Value};
use std::sync::OnceLock;

fn index() -> &'static Vec<Value> {
    static INDEX: OnceLock<Vec<Value>> = OnceLock::new();
    INDEX.get_or_init(|| {
        serde_json::from_str(include_str!("../generated/catalog-index.json"))
            .expect("Invalid bundled catalog")
    })
}

fn normalized(text: &str) -> String {
    text.to_lowercase()
        .chars()
        .map(|c| if c.is_alphanumeric() { c } else { ' ' })
        .collect::<String>()
        .split_whitespace()
        .collect::<Vec<_>>()
        .join(" ")
}

pub fn search(args: &Value) -> Result<Value> {
    let query = match args.get("query") {
        Some(value) => value.as_str().ok_or("query must be a string")?,
        None => "",
    };
    let category = match args.get("category") {
        Some(value) => value.as_str().ok_or("category must be a string")?,
        None => "",
    };
    let limit = match args.get("limit") {
        Some(value) => value.as_u64().ok_or("limit must be an integer")?,
        None => 10,
    };
    let offset = match args.get("offset") {
        Some(value) => value.as_u64().ok_or("offset must be an integer")?,
        None => 0,
    };
    if !(1..=100).contains(&limit) {
        return Err("limit must be 1..100".into());
    }
    let needle = normalized(query);
    let terms: Vec<_> = needle.split_whitespace().collect();
    let mut categories: Vec<_> = index()
        .iter()
        .filter_map(|entry| entry["category"].as_str())
        .collect();
    categories.sort_unstable();
    categories.dedup();
    let mut matches: Vec<_> = index()
        .iter()
        .enumerate()
        .filter_map(|(position, entry)| {
            if !normalized(entry["category"].as_str().unwrap_or("")).contains(&normalized(category))
            {
                return None;
            }
            let name = normalized(entry["name"].as_str().unwrap_or(""));
            fn strings(value: &Value) -> String {
                match value {
                    Value::String(s) => s.clone(),
                    Value::Array(a) => a.iter().map(strings).collect::<Vec<_>>().join(" "),
                    Value::Object(o) => o.values().map(strings).collect::<Vec<_>>().join(" "),
                    _ => String::new(),
                }
            }
            let text = normalized(&strings(entry));
            if !terms.iter().all(|term| text.contains(term)) {
                return None;
            }
            let score = if !needle.is_empty() && name == needle {
                0
            } else if !needle.is_empty() && name.starts_with(&needle) {
                1
            } else if !needle.is_empty() && name.contains(&needle) {
                2
            } else {
                3
            };
            Some((score, position, entry))
        })
        .collect();
    matches.sort_by_key(|(score, position, entry)| {
        (
            *score,
            entry["examples"].as_array().is_none_or(Vec::is_empty),
            *position,
        )
    });
    let total = matches.len();
    let start = usize::try_from(offset).unwrap_or(usize::MAX).min(total);
    let results: Vec<_> = matches
        .into_iter()
        .skip(start)
        .take(limit as usize)
        .map(|(_, _, entry)| entry)
        .collect();
    let next = start + results.len();
    Ok(
        json!({"ok":true,"query":query,"category":category,"categories":categories,"total":total,"offset":offset,"limit":limit,"hasMore":next<total,"nextOffset":if next<total{Some(next)}else{None},"results":results}),
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn bilingual_search_returns_signatures_examples_and_pagination() {
        let found = search(&json!({"query":"ttest2"})).unwrap();
        assert_eq!(found["results"][0]["name"], "ttest2");
        assert!(found["results"][0]["signature"]
            .as_str()
            .unwrap()
            .contains('('));
        assert!(!found["results"][0]["descriptionKo"]
            .as_str()
            .unwrap()
            .is_empty());
        assert!(!found["results"][0]["examples"]
            .as_array()
            .unwrap()
            .is_empty());
        assert!(
            search(&json!({"query":"회귀"})).unwrap()["total"]
                .as_u64()
                .unwrap()
                > 0
        );
        let first = search(&json!({"limit":2})).unwrap();
        let second = search(&json!({"limit":2,"offset":2})).unwrap();
        assert_ne!(first["results"][0], second["results"][0]);
        assert_eq!(first["nextOffset"], 2);
        assert_eq!(
            search(&json!({"query":"doesnotexistttt"})).unwrap()["total"],
            0
        );
        assert!(search(&json!({"limit":0})).is_err());
    }
}
