# SymvaCAS Windows

A Tauri 2 Windows app that uses the web version UI together with the shared Python calculation engine. Calculations do not use WASM/Pyodide. The build copies the shared UI and adds the Windows-specific layout and native integrations.

On Windows the app uses the full window width. The graph view shows formulas, ranges, and parameters on the left and the graph on the right, while statistics shows the dataset on the left and the analysis menu and results on the right. In statistics the left panel matches the window height, and long data scrolls only inside the direct-input field or the table. The graph's left and right panels and the statistics right analysis panel scroll independently. Drag the center divider, or focus it and use the ←/→ keys, to adjust the width (Shift: larger steps, Enter or double-click: default ratio). The adjusted ratios are saved per mode. Narrow windows switch to a vertical layout, and in wide windows the ☰ button at the top left collapses and expands the sidebar.

To the right of the calculator there are **History / Functions** tabs. History search, favorites, and reuse, along with function search, insertion, recent use, and user functions, share the existing lists. Collapse the panel with its ✕ button and expand it again with the **History / Functions** button at the top. The selected tab and the collapsed state are saved, and in narrow windows the top History and Function list buttons open the existing popups.

## Build

Requirements: Windows x64, the Rust MSVC toolchain, Visual Studio C++ Build Tools, Node.js 22+, Python 3.10+ for building, and the WebView2 Runtime. The target PC does not need a system Python or Node.js.

```powershell
cd win
npm ci
npm run dev
npm run build
```

`release/SymvaCAS/` bundles `symvacas.exe`, `symvacas-cli.exe`, `skills/symvacas/`, and the documentation. Copy the **entire folder** to a writable location. `symvacas.exe` is the GUI and `symvacas-cli.exe` is for console/MCP use. Development runs install into `src-tauri/target/debug/python_embeded`, next to the actual development EXE.

The app version is **based on the single `versionName` in Android's `app/build.gradle.kts`**. When `npm run dev` or `npm run build` runs, the npm, Cargo, and Tauri versions and the lock files are synchronized automatically before Tauri reads its configuration. The app info, executable version, CLI `--version`, and MCP `serverInfo.version` use that same version. For example, bumping Android to `1.6.5` makes the next Windows build `1.6.5` as well. The web version does not need to be built separately. To run Cargo directly, run `npm run prepare:app` first. If the versions differ, a direct Cargo build aborts with an error.

## Python Installation

Pressing **Python / MCP → Install Python dependencies** in the app installs CPython 3.14.10 x64, SymPy 1.14.0, mpmath 1.3.0, and pip 26.2.2 into **`python_embeded`** in the executable folder. The download URLs, versions, and SHA-256 hashes are pinned in `runtime-lock.json`. After downloading, the hashes are verified, and the installation is only switched over if the import check in a temporary folder also succeeds. On failure the existing folder is kept, and an incomplete existing installation is replaced only after leaving a backup folder behind. Concurrent installs from another app instance are blocked.

The first install requires internet access and write permission on the executable folder. In locations without write permission, such as Program Files, move the app folder to a user-owned folder. After that, calculations work offline. Refreshing exchange rates requires internet access. Additional packages can be installed into the local Python when needed:

```powershell
.\python_embeded\python.exe -m pip install PACKAGE
```

The calculation Python process stays alive; stopping it terminates the process and starts a new one. While Python is waiting on `input()`, the execution time limit is paused. Python scripts run with the current user's privileges.

## CLI

```powershell
.\symvacas-cli.exe status
.\symvacas-cli.exe install
.\symvacas-cli.exe eval '1/3+1/6'
.\symvacas-cli.exe eval 'solve(x^2-5*x+6=0,x)'
.\symvacas-cli.exe eval 'sin(30)' --angle DEG --precision 50
.\symvacas-cli.exe catalog 'regression' --limit 5
.\symvacas-cli.exe catalog ttest2
.\symvacas-cli.exe solve 'x^2-5*x+6=0'
.\symvacas-cli.exe solve 'x+y=3' 'x-y=1' --variables x,y
.\symvacas-cli.exe solve 'cos(x)=x' --method nsolve --guess 0.5
.\symvacas-cli.exe stats 'ttest2(0,[1,2,3,4],[2,4,6,8])'
.\symvacas-cli.exe stats 'regression(data,linear)' --data trial.json
.\symvacas-cli.exe dataset save cohort cohort.csv
.\symvacas-cli.exe dataset list
.\symvacas-cli.exe dataset show cohort
.\symvacas-cli.exe stats 'stats(cohort)'
.\symvacas-cli.exe request request.json
.\symvacas-cli.exe python script.py --input 'Alice' --input '10'
.\symvacas-cli.exe --help
```

The output is shared-engine JSON. The exit code is 1 on failure. The CLI/MCP default angle is RAD, independent of the GUI setting. Because the web parser is embedded in the executable, LaTeX, implicit multiplication, and calculator syntax are handled identically. `request` accepts a web engine request JSON including the AST, variables, and functions. Passing `-` as the filename reads from stdin.

`catalog` searches function names, categories, Korean/English descriptions, and examples, and returns function signatures and runnable examples. Narrow the results with `--category`, `--limit 1..100`, and `--offset`. Searching works even without Python installed.

`stats` runs descriptive statistics, tests, ANOVA, regression, and advanced statistics catalog formulas. `--data` JSON can be a named dataset such as `{"a":[1,2,3],"b":[2,4,6]}`, or a vector/matrix used under the name `data`. Large datasets are passed separately through the web statistics path. Specify exact decimals as JSON strings. `statisticsReport`, `regression`, and `statisticsCopyReport` are returned from the result as-is.

`solve` returns symbolic solutions and, when available, step-by-step solutions by default. For systems of equations, pass multiple arguments or enter one equation per line on stdin and name the unknowns with `--variables x,y`. `--method nsolve --guess 0.5` selects a numeric solution, `--method dsolve --variables 'y(x)' --independent x` handles ODEs, and `pdsolve` handles PDEs. `--initial` sets ODE initial conditions, `--hint` supplies a PDE hint, and `--no-steps` disables solution explanations. Check per-function arguments with `catalog solve`, `catalog dsolve`, and so on.

### Shared statistics data

`dataset save NAME FILE` registers a CSV/TSV file or a JSON vector/matrix. For stdin and other input without a JSON extension, specify `--format json`. Renaming an existing name requires an explicit `--replace`. Inspect registered data with `dataset list` and `show`, and calculate by name using `stats 'mean(cohort)'` or `eval 'mean(cohort)'`. For analysis, prefer names that the expression parser reads as a single symbol, such as `cohort`.

Registered data is stored in `data/statistics-datasets.json` next to the executable and is **shared by the Windows GUI's saved data, the CLI, and MCP**. After an update, opening the GUI once moves existing saved data into the shared registry. Data changed externally appears when the GUI is reopened, and editing the same data simultaneously reports a conflict instead of overwriting it. One-off `stats --data` data does not modify the registry and only replaces the same name for that request. GUI history, general variables, and user functions are kept separately. When moving the distribution folder, copy the `data` folder along with it.

## MCP / Skill

In the app's **Python / MCP**, copy the MCP configuration that reflects the actual install path, or run `.\symvacas-cli.exe mcp-config`.

```json
{
  "mcpServers": {
    "symvacas": {
      "command": "C:\\Tools\\SymvaCAS\\symvacas-cli.exe",
      "args": ["mcp"]
    }
  }
}
```

The stdio MCP server runs without the GUI. Use `search_catalog` to find functions and examples, and `statistics` and `solve_equations` to run analyses and equations. The dataset tools are `save_statistics_dataset`, `list_statistics_datasets`, and `get_statistics_dataset`, and registered names can be used directly in analysis expressions. The existing `evaluate`, `engine_request`, `python`, and `runtime_status` tools are also provided. MCP initialization protocols 2024-11-05, 2025-03-26, 2025-06-18, and 2025-11-25 and request cancellation are supported. Only JSON-RPC messages are written to stdout. The Python tool has permission to execute local code.

**Registering only MCP is enough; no skill is required.** Tool selection and analysis workflows are delivered in the server initialization `instructions`, and each tool description and input schema includes formats and JSON examples. The `get_usage` tool returns the requested explanation for `overview`, `catalog`, `datasets`, `statistics`, `equations`, `runtime`, or `all`. The full [MCP usage guide](MCP_GUIDE.md) is also available as the `symvacas://guide` resource. Usage, function search, and data registration work even before Python is installed.

Use **Python / MCP → Open Skill folder** to open the bundled `skills/symvacas` folder in Windows Explorer, then copy it into your agent's skills folder. For Codex, you can install it as `%USERPROFILE%\.codex\skills\symvacas\SKILL.md`. MCP can also read it as the `symvacas://skill` resource, and the CLI can print it with the `skill` command.

## Verification

```powershell
npm test
cargo test --manifest-path src-tauri/Cargo.toml
npm run build
python tests/smoke_native.py release/SymvaCAS/symvacas-cli.exe --install
python tests/smoke_analysis.py release/SymvaCAS/symvacas-cli.exe
$env:SYMVACAS_TEST_HOME = (Resolve-Path release/SymvaCAS).Path
cargo test --manifest-path src-tauri/Cargo.toml -- --include-ignored
```

`smoke_native.py --install` installs the real Python dependencies next to the executable and verifies CLI, Python input, and MCP calculations. The `--include-ignored` tests additionally check asynchronous input responses, cancellation, and restarts against that runtime. This is separate from manual GUI verification. After a release, manually check the first install, each calculation tab, stop, the input dialog, and file save/export. Data, script, and graph exports use the Windows save dialog.

Technical references: [Tauri IPC](https://v2.tauri.app/develop/calling-rust/), [Python embeddable distribution](https://docs.python.org/3/using/windows.html#the-embeddable-package), [MCP stdio](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports).
