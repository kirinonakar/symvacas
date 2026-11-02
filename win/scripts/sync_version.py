"""Use Android versionName as the single application version for Windows builds."""
import json
import pathlib
import re

PROJECT = pathlib.Path(__file__).resolve().parents[2]
SEMVER = r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?"


def android_version(project=PROJECT):
    source = (pathlib.Path(project) / "app/build.gradle.kts").read_text(encoding="utf-8")
    matches = re.findall(r'^\s*versionName\s*=\s*"([^"]+)"', source, re.MULTILINE)
    if len(matches) != 1 or not re.fullmatch(SEMVER, matches[0]):
        raise ValueError('Android app/build.gradle.kts must contain one semantic versionName, e.g. "1.6.5"')
    return matches[0]


def sync_versions(project=PROJECT):
    project = pathlib.Path(project)
    root = project / "win"
    version = android_version(project)
    updates = {}
    for relative in ("package.json", "src-tauri/tauri.conf.json", "package-lock.json"):
        path = root / relative
        if relative == "package-lock.json" and not path.exists():
            continue
        contents = json.loads(path.read_text(encoding="utf-8"))
        contents["version"] = version
        if relative == "package-lock.json" and "" in contents.get("packages", {}):
            contents["packages"][""]["version"] = version
        updates[path] = json.dumps(contents, ensure_ascii=False, indent=2) + "\n"

    cargo = root / "src-tauri/Cargo.toml"
    source = cargo.read_text(encoding="utf-8")
    section = re.search(r'^\[package\]\s*\n(?P<body>.*?)(?=^\[|\Z)', source, re.MULTILINE | re.DOTALL)
    if not section:
        raise ValueError("Cargo.toml has no [package] section")
    body, count = re.subn(r'^(version\s*=\s*")[^"]+(".*)$', lambda match: match[1] + version + match[2],
                         section["body"], count=1, flags=re.MULTILINE)
    if count != 1:
        raise ValueError("Cargo.toml [package] has no version")
    updates[cargo] = source[:section.start("body")] + body + source[section.end("body"):]

    lock = root / "src-tauri/Cargo.lock"
    if lock.exists():
        source = lock.read_text(encoding="utf-8")
        updates[lock] = re.sub(r'(^\[\[package\]\]\nname = "symvacas-windows"\nversion = ")[^"]+("[\s\S]*?)(?=^\[\[package\]\]|\Z)',
                               lambda match: match[1] + version + match[2], source, count=1, flags=re.MULTILINE)

    # Parse and validate every input before changing any version manifest.
    for path, contents in updates.items():
        if path.read_text(encoding="utf-8") != contents:
            path.write_text(contents, encoding="utf-8")
    return version


if __name__ == "__main__":
    print(f"Windows version synchronized with Android: {sync_versions()}")
