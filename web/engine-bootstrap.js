// SymPy and mpmath are pure Python wheels. Install the bundled archives directly
// instead of waiting on Pyodide's package-manager dependency/installation locks.
export function prepareEngineAssets({runtimeURL,engineURL,fetcher=fetch}) {
  const lock=(async()=> (await fetcher(new URL('pyodide-lock.json',runtimeURL))).json())();
  // engine.zip does not depend on the package manifest. Start it immediately,
  // and fetch the wheels while WASM compiles and initializes its interpreter.
  const engine=(async()=> (await fetcher(engineURL)).arrayBuffer())();
  const wheels=lock.then(manifest=>Promise.all(['mpmath','sympy'].map(async name=>{
      const item=manifest.packages[name];
      const integrity='sha256-'+btoa(String.fromCharCode(...item.sha256.match(/../g).map(byte=>parseInt(byte,16))));
      return (await fetcher(new URL(item.file_name,runtimeURL),{integrity})).arrayBuffer();
    })));
  const archives=Promise.all([wheels,engine]).then(([packages,source])=>[...packages,source]);
  return {lock,archives};
}

export async function initializeEngine(loadRuntime,options,onRuntimeReady=()=>{}) {
  const assets=prepareEngineAssets(options);
  const runtime=loadRuntime({lockFileContents:assets.lock});
  const [pyodide,archives]=await Promise.all([
    runtime.then(pyodide=>{onRuntimeReady();return pyodide;}),assets.archives
  ]);
  await installEngine(pyodide,{...options,archives});
  return pyodide;
}

export async function installEngine(pyodide,options) {
  const archives=await (options.archives??prepareEngineAssets(options).archives);
  const sitePackages=pyodide.runPython("import sysconfig\nsysconfig.get_path('purelib')");
  for(const archive of archives.slice(0,2))pyodide.unpackArchive(archive,'zip',{extractDir:sitePackages});
  pyodide.unpackArchive(archives[2],'zip',{extractDir:'/symvacas'});
  pyodide.runPython("import sys, importlib\nimportlib.invalidate_caches()\nsys.path.insert(0, '/symvacas')\nsys.set_int_max_str_digits(0)\nimport calc_engine, script_runner\n");
}
