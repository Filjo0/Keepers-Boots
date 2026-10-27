"""Collect installed notices for the exact pinned runtime packages, without downloads."""
import argparse
from hashlib import sha256
from importlib.metadata import distribution
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]


def collect_notices(requirements, get_distribution=distribution):
    packages = []
    sections = ["Keeper's Boots: third-party runtime notices\n"
                "Generated from requirements.txt and installed package notice files.\n"
                "These components retain their own licences; the project licence does not replace them.\n"
                "Model weights, Python itself and operating-system components are not bundled here.\n"
                "Installed-package notices are not a complete audit of bundled native libraries.\n"]
    for line in requirements.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.fullmatch(r"([\w.-]+)==([^;\s]+)(?:\s*;\s*(.+))?", line.strip())
        if not match:
            raise ValueError("Expected an exact package pin")
        name, version, marker = match.groups()
        dist = get_distribution(name)
        if dist.version != version:
            raise ValueError(f"Installed version differs from pin: {name}")
        files = []
        texts = []
        for entry in sorted(dist.files or [], key=str):
            relative = Path(str(entry))
            if (not any(part.endswith(".dist-info") for part in relative.parts)
                    or not any(word in relative.name.lower() for word in ("license", "notice", "copying", "copyright"))):
                continue
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("Unexpected notice path")
            raw = Path(dist.locate_file(entry)).read_bytes()
            # Canonical aggregate whitespace survives Git checks; original bytes
            # remain independently bound by each notice's SHA-256 below.
            text = raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
            text = "\n".join(line.rstrip() for line in text.split("\n"))
            files.append({"path": relative.as_posix(), "sha256": sha256(raw).hexdigest(), "bytes": len(raw)})
            texts.append("--- " + relative.as_posix() + " ---\n" + text.rstrip() + "\n")
        if not files:
            raise ValueError(f"No installed notice found: {name}")
        expression = dist.metadata.get("License-Expression") or "See included notice text"
        package = {"name": name, "version": version, "marker": marker,
                   "declared_license_expression": expression,
                   "project_urls": dist.metadata.get_all("Project-URL") or [], "notice_files": files}
        packages.append(package)
        sections.append(f"\n=== {name} {version} ===\nDeclared expression: {expression}\n"
                        + ("Environment marker: " + marker + "\n" if marker else "")
                        + "".join(texts))
    text = "\n".join(sections)
    manifest = {"schema_version": "1", "requirements_sha256": sha256(requirements.encode("utf-8")).hexdigest(),
                "notices_sha256": sha256(text.encode("utf-8")).hexdigest(), "packages": packages,
                "scope": "Pinned Python package notice files, including Windows-marked packages; not native-library source clearance."}
    return text, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify existing outputs instead of writing")
    args = parser.parse_args()
    if Path(sys.prefix).resolve() != (ROOT / ".venv").resolve():
        parser.error("Use this project's .venv to collect its installed notices")
    text, manifest = collect_notices((ROOT / "requirements.txt").read_text(encoding="utf-8"))
    outputs = {ROOT / "THIRD_PARTY_NOTICES.txt": text,
               ROOT / "data/release/dependency-notices.json": json.dumps(manifest, indent=2) + "\n"}
    for path, content in outputs.items():
        if args.check:
            if path.read_text(encoding="utf-8") != content:
                raise SystemExit("Notice output is stale: " + path.relative_to(ROOT).as_posix())
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
    print(f"PASS: {len(manifest['packages'])} pinned package notices " + ("verified." if args.check else "exported."))


if __name__ == "__main__":
    main()
