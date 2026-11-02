---
name: symvacas
description: Search the SymvaCAS function catalog, register and reuse statistics datasets, run statistical analyses, solve equations and systems, and perform symbolic calculations through the local Windows CLI or MCP server. Use Python mode for user-requested local scripts with SymPy and mpmath.
---

# SymvaCAS

Find `symvacas-cli.exe` in the user's SymvaCAS Windows application folder. Quote its absolute path; do not assume it is on PATH. Use the connected SymvaCAS MCP tools when available, otherwise run the CLI. Both return JSON from the same engine as the graphical application.

This skill is optional. MCP alone provides server instructions, tool schemas/examples and `get_usage`; the full guide is also `symvacas://guide`. Use `get_usage` for any unfamiliar tool or argument format.

Check `symvacas-cli.exe status` before the first calculation. If dependencies are missing, the user can use **Python / MCP → Install Python dependencies** or run `symvacas-cli.exe install`. Installation downloads pinned CPython, SymPy, mpmath and pip into `python_embeded` beside the executable. Never substitute a system Python or install packages globally.

## Find a function first

Use MCP `search_catalog` or CLI `catalog QUERY` when choosing an unfamiliar analysis or solver. Search accepts function names, English/Korean descriptions and examples. Results include the exact `signature`, description, category, templates and `examples[].expression`. Prefer these signatures over guessed argument order. Empty query lists functions; `category`, `limit` and `offset` narrow or page results. Catalog search works before Python installation.

```powershell
& 'C:\Tools\SymvaCAS\symvacas-cli.exe' catalog '회귀' --limit 5
& 'C:\Tools\SymvaCAS\symvacas-cli.exe' catalog ttest2
& 'C:\Tools\SymvaCAS\symvacas-cli.exe' catalog dsolve
```

## Register and reuse statistical data

Use `list_statistics_datasets` to discover available data, `get_statistics_dataset` to inspect its source/kind, and `save_statistics_dataset` to register `{name, data}` (vector or row-major table) or `{name, csv}` (CSV/TSV with optional headers). Registration persists across processes and is shared with the Windows GUI. Existing names require explicit `replace:true`; inspect the existing record before replacing it within the user's task.

```powershell
& 'C:\Tools\SymvaCAS\symvacas-cli.exe' dataset list
& 'C:\Tools\SymvaCAS\symvacas-cli.exe' dataset save cohort 'C:\Data\cohort.csv'
& 'C:\Tools\SymvaCAS\symvacas-cli.exe' dataset save trial 'C:\Data\trial.json'
& 'C:\Tools\SymvaCAS\symvacas-cli.exe' dataset show cohort
& 'C:\Tools\SymvaCAS\symvacas-cli.exe' stats 'stats(cohort)'
& 'C:\Tools\SymvaCAS\symvacas-cli.exe' stats 'ttest2(0,cohort,control)'
```

Use calculator-compatible names such as `cohort`, `control` or `trial`; names containing spaces cannot be used as expression symbols. Registered CSV data follows the GUI's header/column conventions. `data/statistics-datasets.json` beside the executable is the shared registry: do not edit it directly. GUI data is imported on first startup after this update; reopen the GUI to see changes made externally. Concurrent edits to the same saved record are rejected instead of silently overwriting them.

MCP `statistics` accepts `{expression, datasets?}`. Inline arrays and named datasets use the web Statistics request path, so large samples do not consume the formula's AST limit. For one-off data, use `datasets:{sample:[1,2,3]}` or a row-major table; local datasets override same-named registered data for that request without changing saved data. CLI `stats EXPRESSION --data FILE` accepts the same named JSON object, or a bare vector/table named `data`. Use `--data -` to read JSON from stdin. Decimal strings preserve exact input digits; JSON numbers already carry their JSON precision. `null` in one-off data becomes `NA`, subject to the analysis's missing-data rules.

Available analyses include descriptive summaries, t tests, ANOVA, correlation, regression and the advanced catalog functions. Read `statisticsReport`, `regression`, `statisticsCopyReport`, assumptions and warnings when present. The output can also contain plot data; CLI/MCP do not render those plots.

## Solve equations

MCP `solve_equations` accepts `equations` (one string, newline-separated system or string array), `variables` (symbol, comma-separated string or list), `method` (`solve`, `nsolve`, `dsolve`, `pdsolve`) and `steps` (default true). For `nsolve`, use `initialGuess`: a number for a single root, an array for a system, or `"0,1"` for bounds. Differential equations can use dependent functions such as `y(x)` or `u(x,y)`. `dsolve` also accepts `independentVariable` and calculator-syntax `initialConditions`; search its catalog entry for the exact format.

```powershell
& 'C:\Tools\SymvaCAS\symvacas-cli.exe' solve 'x^2-5*x+6=0'
& 'C:\Tools\SymvaCAS\symvacas-cli.exe' solve 'x+y=3' 'x-y=1' --variables x,y
& 'C:\Tools\SymvaCAS\symvacas-cli.exe' solve 'cos(x)=x' --method nsolve --guess 0.5
& 'C:\Tools\SymvaCAS\symvacas-cli.exe' solve 'diff(y(x),x)=y(x)' --method dsolve --variables 'y(x)' --independent x
```

Inspect `equationSteps`/`solutionSteps` when returned. A solver summary or unevaluated answer is not a complete derivation. `--no-steps` disables explanation requests; standard angle/precision options also apply.

## Calculator syntax

`eval` accepts the shared web calculator syntax, including implicit multiplication, `^`, exact fractions, LaTeX, lists, matrices, equations and catalog functions. The default CLI/MCP angle is **RAD**. Set `--angle DEG` for degree-based trigonometry. Precision defaults to 30 significant digits and display digits to 10.

```powershell
& 'C:\Tools\SymvaCAS\symvacas-cli.exe' eval '1/3+1/6'
& 'C:\Tools\SymvaCAS\symvacas-cli.exe' eval 'diff(sin(x^2),x)'
& 'C:\Tools\SymvaCAS\symvacas-cli.exe' eval 'solve(x^2-5*x+6=0,x)'
& 'C:\Tools\SymvaCAS\symvacas-cli.exe' eval 'sin(30)' --angle DEG
& 'C:\Tools\SymvaCAS\symvacas-cli.exe' eval 'mean([1,2,3,4])'
& 'C:\Tools\SymvaCAS\symvacas-cli.exe' eval 'det([[1,2],[3,4]])'
```

Inspect `ok` and `error` before presenting a result. Preserve exact answers when useful and report the angle convention. Symbolic solvers can return unevaluated results. `variance`, `stdev` and `covariance` default to sample values (ddof=1); a final `0` selects population values. Treat these as computation results, not a substitute for checking statistical assumptions.

Use `request FILE` or `request -` for structured web-engine requests. Requests use a validated calculator AST, never string `eval` or SymPy `parse_expr`. For a graph, supply `action: "graph"`, `graphKind`, `trees`, sampling bounds and sample count; the response contains sampling data rather than an image. `--help` lists CLI options. The default outer deadline is 65 seconds plus SEM bootstrap allowance; use `--unlimited` only when the user intends to remove computation limits.

## MCP

`symvacas-cli.exe mcp-config` prints a client configuration with the absolute executable path. Launch the stdio server as `symvacas-cli.exe mcp`; it does not launch the GUI. Available tools:

- `evaluate`: calculator expression, optional `angle`, `precision`, `displayDigits`.
- `get_usage`: self-contained MCP workflow, argument examples and result interpretation, without requiring this skill.
- `search_catalog`: find signatures, bilingual help and examples; supports category and pagination.
- `statistics`: analysis expression with optional named datasets and precision/angle settings.
- `solve_equations`: equations/systems, solver method, variables and available explanations.
- `list_statistics_datasets`, `get_statistics_dataset`, `save_statistics_dataset`: shared saved data.
- `engine_request`: structured AST request for graphing, probability, constants, programmer mode or calculation.
- `python`: source and pre-entered `inputs` for user-authorized scripts.
- `runtime_status`: installation status and runtime path.

The server also exposes this skill as the resource `symvacas://skill`. Saved statistics datasets are shared with the GUI. GUI history, calculator variables and custom functions remain independent; include variables/functions in a structured request when needed.

## Python scripts

Use `python FILE.py` or pipe UTF-8 source to `python -`. Pass `--input VALUE` once per expected `input()` call. Headless execution fails when inputs run out; the GUI supports interactive prompts. Scripts can import the standard library, `sympy`, `mpmath` and `symvacas_catalog`.

Python mode has full access to the current user's filesystem and network. Run scripts only within the user's authorized task. For ordinary mathematical expressions, prefer `evaluate`/`eval`. Errors and calculation results are JSON on stdout; diagnostic messages go to stderr. A nonzero CLI exit code indicates failure.
