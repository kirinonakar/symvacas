"""Assemble the shared web UI and native engine without downloading WASM."""
import io
import pathlib
import re
import shutil
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROJECT = ROOT.parent


def prepare():
    # npm predev/prebuild also run this before Tauri reads its config/metadata.
    import runpy
    version = runpy.run_path(str(ROOT / "scripts/sync_version.py"))["sync_versions"](PROJECT)
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    excluded = {"worker.js", "engine-bootstrap.js", "engine-fetch.js", "assets.js", "sw.js"}
    for path in (PROJECT / "web").iterdir():
        if path.is_file() and (path.suffix in {".html", ".css", ".js", ".json", ".png", ".md"} or path.name == "LICENSE"):
            if path.name not in excluded and not path.name.startswith("package"):
                shutil.copyfile(path, dist / path.name)
    shutil.copytree(PROJECT / "web/fonts", dist / "fonts", dirs_exist_ok=True)
    for path in (ROOT / "frontend").iterdir():
        if path.is_file() and path.name != "headless-requests.js":
            shutil.copyfile(path, dist / path.name)
    # Read Android directly: web/app-version.js may be from an older web build.
    (dist / "app-version.js").write_text('export const appVersion = "' + version + '";\n', encoding="utf-8")
    client = (dist / "engine-client.js").read_text(encoding="utf-8")
    client = "import {NativeWorker} from './native-worker.js';\n" + client
    client = client.replace("new Worker(new URL('./worker.js',import.meta.url),{type:'module'})", "new NativeWorker()")
    client = client.replace("준비 완료 · WASM", "준비 완료 · CPython")
    client = client.replace("엔진을 시작할 수 없습니다. 정적 서버와 빌드 파일을 확인해 주세요.", "Python 엔진을 시작할 수 없습니다. Python / MCP에서 설치 상태를 확인해 주세요.")
    (dist / "engine-client.js").write_text(client, encoding="utf-8")
    storage = (dist / "storage.js").read_text(encoding="utf-8")
    storage = "import {createDesktopStorage} from './desktop-storage.js';\n" + storage
    storage = storage.replace("export const readState=storage.readState,writeState=storage.writeState;", "const desktopStorage=createDesktopStorage(storage);\nexport const readState=desktopStorage.readState,writeState=desktopStorage.writeState;")
    storage = storage.replace("export function downloadFile(name,content,type='text/plain') {", "export function downloadFile(name,content,type='text/plain') {\n  if(window.__TAURI__){void import('./native-files.js').then(module=>module.saveExport(name,content,type));return;}")
    (dist / "storage.js").write_text(storage, encoding="utf-8")
    locale = (dist / "i18n.js").read_text(encoding="utf-8")
    locale = locale.replace("WASM", "CPython").replace("SymvaCAS WebAssembly", "SymvaCAS Windows")
    (dist / "i18n.js").write_text(locale, encoding="utf-8")
    # Keep the web sources untouched; only the assembled desktop distribution differs.
    index = (dist / "index.html").read_text(encoding="utf-8")
    index = index.replace('src="bootstrap.js"', 'src="desktop-bootstrap.js"')
    index = index.replace('content="SymvaCAS WebAssembly', 'content="SymvaCAS Windows')
    index = index.replace('Loading WebAssembly runtime…', 'Checking embedded Python…')
    index = re.sub(r"<script[^>]+src=['\"]https://static\.cloudflareinsights\.com/[^<]*</script>", "", index)
    index = index.replace('href="README.md">Web guide', 'href="README.md">Windows guide')
    index = index.replace('</head>', '  <link rel="stylesheet" href="desktop.css">\n</head>')
    index = index.replace('<button id="settings-button">', '<button id="desktop-settings-button" type="button">Python / MCP</button><button id="settings-button">')
    (dist / "index.html").write_text(index, encoding="utf-8")
    (dist / "cache-maintenance.js").write_text('export async function refreshOfflineCache() {}\n', encoding="utf-8")
    engine_ui = (dist / "engine-ui.js").read_text(encoding="utf-8")
    engine_ui = engine_ui.replace("if('serviceWorker' in navigator", "if(!window.__TAURI__ && 'serviceWorker' in navigator")
    (dist / "engine-ui.js").write_text(engine_ui, encoding="utf-8")
    shutil.copyfile(ROOT / "README.md", dist / "README.md")
    shutil.copyfile(ROOT / "THIRD_PARTY.md", dist / "THIRD_PARTY.md")
    generated = ROOT / "src-tauri/generated"
    generated.mkdir(parents=True, exist_ok=True)
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as target:
        for directory in [PROJECT / "app/src/main/python", ROOT / "python"]:
            for path in sorted(directory.glob("*.py")):
                info = zipfile.ZipInfo(path.name, date_time=(2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                target.writestr(info, path.read_bytes())
    (generated / "engine.zip").write_bytes(archive.getvalue())
    # The headless CLI uses the exact same parser, embedded in a Rust JS interpreter.
    def module(path):
        source = path.read_text(encoding="utf-8")
        source = re.sub(r"^import .*?;\s*", "", source, flags=re.MULTILINE)
        source = re.sub(r"^export \{[^}]+\};?", "", source, flags=re.MULTILINE)
        return re.sub(r"\bexport (?=(?:function|const|class)\b)", "", source)
    parser = "let computationLimitsRemoved=()=>false;\n" + module(PROJECT / "web/parser.js")
    parser += "\nconst desktopHeaders=(()=>{" + module(PROJECT / "web/statistics-headers.js") + "\nreturn {hasExplicitStatisticsHeader,registerStatisticsHeader};})();"
    parser += "\nconst desktopComparison=(()=>{" + module(PROJECT / "web/statistics-comparison-data.js") + "\nreturn {statisticsComparisonData};})();"
    parser += "\nconst desktopWorkspace=(()=>{const {statisticsComparisonData}=desktopComparison;const {hasExplicitStatisticsHeader,registerStatisticsHeader}=desktopHeaders;" + module(PROJECT / "web/workspace-commands.js") + "\nreturn {equationCommand,csvRows,statisticsDetectedColumns,statisticsKindForColumns,statisticsDatasetSource};})();"
    parser += "\nconst desktopStatistics=(()=>{" + module(PROJECT / "web/statistics-request.js") + "\nreturn {statisticsRequest};})();"
    parser += "\nconst desktopRequests=(()=>{const {equationCommand,csvRows,statisticsDetectedColumns,statisticsKindForColumns,statisticsDatasetSource}=desktopWorkspace;const {statisticsRequest}=desktopStatistics;" + module(ROOT / "frontend/headless-requests.js") + "\nreturn {statisticsInput,equationInput,datasetInput};})();"
    (generated / "parser.js").write_text(parser, encoding="utf-8")
    # Build a bilingual function index from the same help shipped with the web app.
    runpy.run_path(str(ROOT / "scripts/catalog_index.py"))["build_catalog"](PROJECT / "web", generated / "catalog-index.json")
    icons = ROOT / "src-tauri/icons"
    icons.mkdir(exist_ok=True)
    # Tauri's CLI creates ICO/PNG icons from the existing app artwork separately.
    print(f"Prepared {dist} (shared UI + embedded CPython bridge; no WASM)")


if __name__ == "__main__":
    prepare()
