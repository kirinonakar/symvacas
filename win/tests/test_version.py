"""Changing Android versionName must propagate before Windows metadata is read."""
import json
import pathlib
import runpy
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
versions = runpy.run_path(str(ROOT / "scripts/sync_version.py"))


class VersionTests(unittest.TestCase):
    def test_android_bump_updates_all_windows_manifests_and_only_own_lock_entry(self):
        with tempfile.TemporaryDirectory(prefix="symvacas-version-") as directory:
            project = pathlib.Path(directory)
            (project / "app").mkdir()
            win = project / "win"
            (win / "src-tauri").mkdir(parents=True)
            android = project / "app/build.gradle.kts"
            android.write_text('versionCode = 65\nversionName = "1.6.5" // app release\n', encoding="utf-8")
            for path in ("package.json", "src-tauri/tauri.conf.json"):
                (win / path).write_text(json.dumps({"version":"0.1.0","untouched":"value"}), encoding="utf-8")
            (win / "package-lock.json").write_text(json.dumps({"version":"0.1.0","packages":{"":{"version":"0.1.0"},"node_modules/dependency":{"version":"0.1.0"}}}), encoding="utf-8")
            (win / "src-tauri/Cargo.toml").write_text('[package]\nname = "symvacas-windows"\nversion = "0.1.0"\n\n[dependencies]\nother = { version = "0.1.0" }\n', encoding="utf-8")
            (win / "src-tauri/Cargo.lock").write_text('version = 4\n\n[[package]]\nname = "other"\nversion = "0.1.0"\n\n[[package]]\nname = "symvacas-windows"\nversion = "0.1.0"\ndependencies = ["other"]\n', encoding="utf-8")
            for version in ("1.6.5", "1.6.6"):
                with self.subTest(version=version):
                    android.write_text('versionName = "'+version+'" // release\n', encoding="utf-8")
                    self.assertEqual(versions["sync_versions"](project), version)
                    for path in ("package.json", "src-tauri/tauri.conf.json", "package-lock.json"):
                        self.assertEqual(json.loads((win/path).read_text())["version"],version)
                    lock=json.loads((win/"package-lock.json").read_text())
                    self.assertEqual(lock["packages"][""]["version"],version)
                    self.assertEqual(lock["packages"]["node_modules/dependency"]["version"],"0.1.0")
                    self.assertIn('version = "'+version+'"',(win/"src-tauri/Cargo.toml").read_text())
                    self.assertIn('other = { version = "0.1.0" }',(win/"src-tauri/Cargo.toml").read_text())
                    lock=(win/"src-tauri/Cargo.lock").read_text()
                    self.assertIn('name = "symvacas-windows"\nversion = "'+version+'"',lock)
                    self.assertIn('name = "other"\nversion = "0.1.0"',lock)
                    before={path:path.stat().st_mtime_ns for path in win.rglob('*') if path.is_file()}
                    versions["sync_versions"](project)
                    self.assertEqual(before,{path:path.stat().st_mtime_ns for path in before},"No-op preparation must not trigger rebuilds")

    def test_bad_android_version_fails_before_touching_windows_metadata(self):
        with tempfile.TemporaryDirectory(prefix="symvacas-version-") as directory:
            project=pathlib.Path(directory)
            (project/"app").mkdir()
            (project/"app/build.gradle.kts").write_text('versionName = "not-a-version"',encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"versionName"):
                versions["sync_versions"](project)
            self.assertFalse((project/"win").exists())


if __name__ == "__main__":
    unittest.main()
