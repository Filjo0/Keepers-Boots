"""Build a small, clearly unpublished source preview from tracked project files."""
import argparse
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import subprocess
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
BLOCKED = {".git", ".venv", "local-artifacts", "node_modules", ".agents", ".codex"}
TEXT_SUFFIXES = {".py", ".js", ".mjs", ".css", ".html", ".svg", ".json", ".md", ".txt", ".csv", ".srt", ".yml", ".yaml", ".ps1", ".in"}
ROOT_FILES = {"Dockerfile", "LICENSE", ".dockerignore", ".gitignore", ".gitattributes"}


def checked_member(name):
    path = PurePosixPath(name)
    if (path.is_absolute() or ".." in path.parts or "\\" in name or ":" in name
            or not path.parts or path.parts[0] in BLOCKED
            or (path.name.startswith(".env") and path.name != ".env.example")
            or (path.suffix.lower() not in TEXT_SUFFIXES and name not in ROOT_FILES)):
        raise ValueError("Forbidden preview member: " + name)
    return path.as_posix()


def build_preview(root, names, destination):
    root = root.resolve()
    contents = {}
    for name in sorted(set(names)):
        name = checked_member(name)
        source = root / name
        if not source.resolve().is_relative_to(root) or source.is_symlink():
            raise ValueError("Preview source escapes the project")
        if any(parent.is_symlink() for parent in source.parents if parent != root and root in parent.parents):
            raise ValueError("Preview source has a symlinked parent")
        if source.stat().st_size > 10 * 1024 * 1024:
            raise ValueError("Preview source exceeds the text-asset bound")
        contents[name] = source.read_bytes()
    status = ("LOCAL PREVIEW - NOT CLEARED FOR PUBLICATION\n"
              "This is a source/test preview, not a public release or a licence grant.\n"
              "Project licensing is in LICENSE when included; public publication is a separate action.\n"
              "Recorded mode replays labelled prior agent executions; live inference is experimental.\n"
              "Follow README.md. Model weights, dependencies, private data and local artifacts are excluded.\n")
    manifest = {"schema_version": "1", "publication_status": "unpublished_local_preview",
                "source_basis": "Git-tracked names with current working-tree bytes; hashes define this snapshot.",
                "files": [{"path": name, "bytes": len(raw), "sha256": sha256(raw).hexdigest()}
                          for name, raw in contents.items()]}
    contents["PREVIEW_STATUS.txt"] = status.encode()
    contents["preview-manifest.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(destination, "x", compression=ZIP_DEFLATED, compresslevel=6) as archive:
        for name, raw in contents.items():
            info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, raw)
    with ZipFile(destination) as archive:
        if archive.testzip() is not None:
            raise ValueError("Preview archive integrity failed")
        for member in manifest["files"]:
            if sha256(archive.read(member["path"])).hexdigest() != member["sha256"]:
                raise ValueError("Preview manifest hash mismatch")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="local-artifacts/release-preview/keepers-boots-preview.zip")
    args = parser.parse_args()
    destination = (ROOT / args.output).resolve()
    if not destination.is_relative_to((ROOT / "local-artifacts").resolve()):
        parser.error("Preview output must stay in ignored local-artifacts")
    names = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, check=True, capture_output=True).stdout.decode().split("\0")
    names = [name for name in names if name]
    required = {"README.md", "LICENSE", "THIRD_PARTY_NOTICES.txt", "keepers_boots/api.py", "docs/api.schema.json",
                "web/index.html", "web/app.js", "web/styles.css", "docs/knowledge/keeper-principles.md"}
    required |= {"data/agent-recordings/" + name + ".json"
                 for name in ("tempting-short-pass", "press-arrives", "uncertain-outlet")}
    if not required <= set(names):
        parser.error("Stage the complete preview source and notices first")
    manifest = build_preview(ROOT, names, destination)
    print(f"PASS: {len(manifest['files'])} hashed source files in unpublished preview: {destination.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
