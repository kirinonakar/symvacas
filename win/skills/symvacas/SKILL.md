---
name: symvacas
description: Search the SymvaCAS function catalog, register and reuse statistics datasets, run statistical analyses, solve equations and systems, and perform symbolic calculations through the local Windows CLI or MCP server. Use Python mode for user-requested local scripts with SymPy and mpmath.
---

# SymvaCAS

Use the connected SymvaCAS MCP tools when available; otherwise find `symvacas-cli.exe` in the user's application folder and quote its absolute path. Do not assume it is on PATH. Both interfaces use the same local engine as the GUI. This skill is optional: MCP server instructions, tool schemas/examples and `get_usage` provide the workflow independently.

## Discover, then calculate

1. Use `get_usage` for tool-level guidance and `search_catalog` for the mathematical function required by the task. CLI equivalents are `--help` and `catalog QUERY`.
2. Read the returned `signature`, descriptions, `examples`, and any structured `arguments`/`rowLayouts`. Check positional order, defaults, allowed values and input columns in the catalog. Do not infer one function's arguments from another function with a similar name.
3. For registered data, use `list_statistics_datasets` and `get_statistics_dataset` before selecting an analysis. Register new reusable data with `save_statistics_dataset` when requested.
4. Run `statistics`, `solve_equations`, or `evaluate` with the discovered expression or tool arguments. Inspect `ok`/`error`, returned reports, explanations, restrictions and warnings before presenting the result. A successful outer result can contain a failed subanalysis; check nested errors too.

Keep individual mathematical function signatures, option rules and examples in the catalog, not in this skill or the MCP guide. Use `get_usage` only for common tool/data/result handling. Catalog search supports English/Korean queries, categories and pagination and works before Python installation.

## Shared statistics data

`save_statistics_dataset` accepts a name and either a vector/row-major table or CSV/TSV text. Inspect an existing record before intentionally replacing it with `replace:true`. Prefer names that parse as a single calculator symbol. Named one-off datasets in a statistics request override a saved name only for that request.

The registry is `data/statistics-datasets.json` beside the executable; GUI/CLI/MCP share it. Do not edit it directly. Open the updated GUI once to import older saved GUI datasets; reopen it to see external changes. Concurrent edits to the same record are rejected. GUI history, general variables and custom functions are independent.

CLI workflow (replace capitalized arguments with actual values):

```text
symvacas-cli.exe catalog QUERY
symvacas-cli.exe dataset list
symvacas-cli.exe dataset show NAME
symvacas-cli.exe dataset save NAME FILE
symvacas-cli.exe stats EXPRESSION --data FILE
symvacas-cli.exe solve EQUATION --variables VARIABLES
```

`stats --data FILE` accepts a named JSON object or a vector/table named `data`; `--data -` reads stdin. Decimal strings preserve input digits. Registered CSV data follows the GUI's header/column conventions. Inspect missing values and column meanings before analysis.

## Runtime and scripts

Use `runtime_status` or CLI `status` to check dependencies. Missing dependencies can be installed through **Python / MCP → Install Python dependencies** or CLI `install`. Keep runtime/packages in `python_embeded` beside the executable; do not substitute system Python or install packages globally.

CLI/MCP default to RAD, 30 significant computation digits and 10 display digits, independently of GUI settings. Set the angle explicitly when the task requires it. Inspect the tool schema for precision, execution-limit and solver controls.

Prefer dedicated calculator tools for mathematical work. `python` runs unrestricted current-user code; use it only within a user-authorized script task. Supply headless `input()` values in advance. `engine_request` handles lower-level structured calculator AST requests. CLI failures return a nonzero exit code; MCP errors set `isError` and include error details.
