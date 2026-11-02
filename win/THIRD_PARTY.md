# Windows third-party components

- SymvaCAS: MIT; see LICENSE.
- Tauri and Rust dependencies: licenses recorded by Cargo.lock and individual crates (Tauri MIT/Apache-2.0).
- Boa JavaScript engine: MIT/Unlicense; used to run the shared calculator parser in the headless CLI.
- CPython: Python Software Foundation license, included in the downloaded embedded Python archive (`python_embeded/LICENSE.txt`).
- SymPy 1.14.0 and mpmath 1.3.0: BSD licenses included in the installed wheel distributions' dist-info directories.
- pip: MIT, with vendored component licenses in its wheel.
- STIX Two Math: SIL Open Font License, included at fonts/OFL.txt in the application assets.

The CPython runtime and Python packages are downloaded on demand from python.org / files.pythonhosted.org; pinned versions and SHA-256 digests are in runtime-lock.json. No Pyodide/WebAssembly binaries are bundled in the Windows application.
