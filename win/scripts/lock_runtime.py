"""Maintainer command: explicitly refresh the pinned official runtime downloads."""
import hashlib
import json
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]


def main():
    version = "3.14.10"
    url = f"https://www.python.org/ftp/python/{version}/python-{version}-embed-amd64.zip"
    cache = ROOT / ".runtime-cache"
    cache.mkdir(exist_ok=True)
    archive = cache / url.rsplit("/", 1)[1]
    if not archive.exists():
        archive.write_bytes(urllib.request.urlopen(url, timeout=120).read())
    lock = {"python": {"version": version, "url": url,
                       "sha256": hashlib.sha256(archive.read_bytes()).hexdigest()}, "wheels": []}
    for name, release in [("mpmath", "1.3.0"), ("sympy", "1.14.0"), ("pip", "26.2.2")]:
        metadata = json.load(urllib.request.urlopen(f"https://pypi.org/pypi/{name}/{release}/json", timeout=60))
        wheel = next(item for item in metadata["urls"] if item["filename"].endswith("-none-any.whl"))
        lock["wheels"].append({"name": name, "version": release, "url": wheel["url"], "sha256": wheel["digests"]["sha256"]})
    (ROOT / "runtime-lock.json").write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    print("Pinned CPython, SymPy, mpmath and pip in runtime-lock.json")


if __name__ == "__main__":
    main()
