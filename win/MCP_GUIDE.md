# SymvaCAS MCP guide

## Overview

SymvaCAS runs symbolic mathematics, statistical analyses and equation solvers locally. No skill needs to be installed or activated. This guide explains tools and common data/result handling; mathematical function details live in the searchable catalog.

Workflow:

1. Call `search_catalog` to find the appropriate function, exact signature and examples. English and Korean queries work.
2. Inspect available data with `list_statistics_datasets` and `get_statistics_dataset`; register new reusable data with `save_statistics_dataset` when requested.
3. Call `statistics` for analyses, `solve_equations` for equations/systems or `evaluate` for general expressions.
4. Inspect `ok`/`error`, reports, restrictions and warnings. A successful outer result can still contain a failed subanalysis: inspect nested errors before claiming that every requested model succeeded.

`get_usage` returns this guide or a section: `catalog`, `datasets`, `statistics`, `equations`, `runtime`, `overview`, `all`. The complete guide is also the resource `symvacas://guide`. Neither route requires Python. JSON examples below are tool arguments, not JSON-RPC envelopes.

Defaults: **RAD**, 30 significant computation digits (3–200 configurable), 10 display digits. GUI angle/history/variables/functions are independent of headless calculations. Saved statistics datasets are shared. Plot fields are numeric data, not rendered images.

## Catalog

Tool: `search_catalog`. Search names, categories, English/Korean descriptions and examples. Empty query lists available functions. Use `category` to narrow results, `limit` (1–100, default 10) and `offset` to page through them; responses include `categories`, `total`, `hasMore`, `nextOffset`.

```json
{"query":"survival","limit":5}
```

Results contain `name`, `signature`, `description`, `descriptionKo`, `category`, `templates` and `examples[].expression`. Where provided, `arguments` gives explicit positions, names, defaults, allowed values and descriptions, while `rowLayouts` describes data-column order.

Before calling a function, read its full signature, argument positions and data layout from these results. Do not guess optional argument order or copy options between similarly named functions. Templates can contain empty arguments and must be completed. Use the examples to construct an actual calculator expression. Function-specific rules belong in the catalog, not in this guide.

## Datasets

Tools: `list_statistics_datasets` (arguments `{}`), `get_statistics_dataset`, `save_statistics_dataset`.

Get a registered record:

```json
{"name":"cohort"}
```

Register a vector:

```json
{"name":"cohort","data":[1,2,3,4,5]}
```

Register a table with headers:

```json
{"name":"trial","csv":"x,y\n1,3\n2,5\n3,7\n4,9"}
```

Supply either `data` (vector or row-major table) or `csv` (CSV/TSV), not both. Decimal strings preserve input digits. Choose names that parse as one calculator symbol; names with spaces cannot be referenced as expression symbols. Existing names require an intentional `replace:true`. Save returns a summary; get returns full source and kind.

Data persists in `data/statistics-datasets.json` beside the executable and is shared across GUI/CLI/MCP. Do not edit it directly. Open the updated GUI once to import older GUI-only saved datasets; reopen it to view external changes. Concurrent edits to the same record are rejected. Deleting a saved record in the GUI removes it from the shared registry.

Reference a saved name directly in the calculator expression obtained from the catalog. Registered CSV parsing follows GUI header/column and complete-row conventions. Inspect missing values and column meanings before choosing an analysis. One-off `statistics.datasets` values override matching saved names for one request without changing the registry.

## Statistics

Tool: `statistics`. Obtain the function's expression, positional option order, defaults and row layout through `search_catalog`. Put the completed calculator expression in `expression`; optionally supply a `datasets` object mapping referenced names to vectors or row-major tables. Tool schemas contain example argument objects for the API format, not an exhaustive mathematical function reference.

Named data cells may be finite JSON numbers, exact decimal strings, calculator cell expressions or `null` (NA). Each analysis applies its own missing-data policy. Inline arrays and named datasets follow the GUI Statistics request path, avoiding the ordinary formula AST limit for large samples. Normal dataset bounds are 5000 rows and 101 columns.

Common optional settings: `angle` (`RAD`/`DEG`/`GRAD`), `precision`, `displayDigits`, `removeComputationLimit` (default false). Inspect function-specific meanings and assumptions in the catalog.

Depending on the analysis, responses can include `exact`, `decimal`, `statisticsReport`, `statisticsCopyReport`, `regression`, `survival` and plot/diagnostic data. Inspect subreports for nested errors and unavailable diagnostics. A requested diagnostic is not necessarily an estimable or passed diagnostic. Preserve confidence levels, test directions, assumptions, restrictions and warnings when interpreting the output.

## Equations

Tool: `solve_equations`. The input schema describes solver methods and controls; use `search_catalog` when you need the mathematical syntax of a solver or initial-condition expression.

```json
{"equations":["x+y=3","x-y=1"],"variables":["x","y"]}
```

`equations` accepts one string, a newline-separated system or an array of strings. `variables` accepts a symbol, comma-separated list or string array; differential methods also accept a dependent function. Choose `method`, `initialGuess`, `independentVariable`, `initialConditions`, `hint` as described by the tool schema and catalog. Standard precision and angle settings apply. `steps` defaults to true; set it false to omit explanation requests.

Responses contain `exact`/`decimal` and available `equationSteps`/`solutionSteps`. Review domain restrictions and whether the result is a derivation, summary or unevaluated answer.

## Runtime

`runtime_status` checks Python. Missing dependencies can be installed through **Python / MCP → Install Python dependencies** or CLI `symvacas-cli.exe install`. The server uses `python_embeded` beside the executable, never a system interpreter. Catalog/help/data registration work without Python.

Calculations normally have a 65-second outer deadline plus an allowance for expensive resampling work. `removeComputationLimit:true` removes the deadline when intended by the user; MCP cancellation remains available. Failures have `ok:false`/`error` and MCP `isError:true`.

`engine_request` accepts lower-level structured calculator AST requests, including graphs/probability/programmer mode. Prefer dedicated tools for ordinary work. `python` runs unrestricted current-user code and requires a user-authorized script task. Supply all headless `input()` values in `inputs`.
