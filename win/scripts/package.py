"""Collect both binaries and the agent skill into a portable Windows folder."""
import pathlib
import shutil
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]


def main():
    subprocess.run(["cargo", "build", "--manifest-path", str(ROOT / "src-tauri/Cargo.toml"), "--release", "--features", "tauri/custom-protocol", "--bin", "symvacas-cli"], check=True)
    target = ROOT / "release/SymvaCAS"
    target.mkdir(parents=True, exist_ok=True)
    for name in ["symvacas.exe", "symvacas-cli.exe"]:
        shutil.copyfile(ROOT / "src-tauri/target/release" / name, target / name)
    for name in ["README.md", "MCP_GUIDE.md", "THIRD_PARTY.md", "runtime-lock.json"]:
        shutil.copyfile(ROOT / name, target / name)
    shutil.copyfile(ROOT.parent / "LICENSE", target / "LICENSE")
    shutil.copytree(ROOT / "skills", target / "skills", dirs_exist_ok=True)
    print(f"Portable application: {target}")


if __name__ == "__main__":
    main()
