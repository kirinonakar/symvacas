import importlib.util
import pathlib
import unittest
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("desktop_prepare", ROOT / "scripts/prepare.py")
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


class DistributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        prepare.prepare()

    def test_native_distribution_has_no_wasm_runtime_or_network_script(self):
        dist = ROOT / "dist"
        self.assertFalse((dist / "vendor").exists())
        self.assertFalse((dist / "worker.js").exists())
        index = (dist / "index.html").read_text(encoding="utf-8")
        self.assertIn("desktop-bootstrap.js", index)
        self.assertIn('id="desktop-settings-button"', index)
        self.assertNotIn("cloudflareinsights", index)
        client = (dist / "engine-client.js").read_text(encoding="utf-8")
        self.assertIn("new NativeWorker()", client)
        self.assertNotIn("new Worker(", client)

    def test_engine_contains_all_shared_modules_and_desktop_bridge(self):
        with zipfile.ZipFile(ROOT / "src-tauri/generated/engine.zip") as archive:
            self.assertIn("desktop_worker.py", archive.namelist())
            for path in (ROOT.parent / "app/src/main/python").glob("*.py"):
                self.assertEqual(archive.read(path.name), path.read_bytes(), path.name)


if __name__ == "__main__":
    unittest.main()
