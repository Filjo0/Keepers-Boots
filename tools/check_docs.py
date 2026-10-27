"""Validate project Markdown encoding and local file links without network access."""
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
IGNORED = {".git", ".venv", "__pycache__", "node_modules", "local-artifacts"}
errors = []
count = 0
for path in sorted(ROOT.rglob("*.md")):
    if any(part in IGNORED for part in path.relative_to(ROOT).parts):
        continue
    count += 1
    try:
        content = path.read_bytes().decode("utf-8")
    except UnicodeDecodeError:
        errors.append(f"{path.relative_to(ROOT)}: not UTF-8")
        continue
    if content.startswith("\ufeff") or "\ufffd" in content:
        errors.append(f"{path.relative_to(ROOT)}: BOM or replacement character")
    # Strip fenced examples; links inside examples need not be local files.
    outside = re.sub(r"(?ms)^~~~.*?^~~~\s*$|^```.*?^```\s*$", "", content)
    for raw in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", outside):
        target = raw.strip().strip("<>")
        parsed = urlsplit(target)
        if parsed.scheme or target.startswith("#"):
            continue
        local = (path.parent / unquote(parsed.path)).resolve()
        if not local.is_relative_to(ROOT):
            errors.append(f"{path.relative_to(ROOT)}: link outside project: {target}")
        elif not local.exists():
            errors.append(f"{path.relative_to(ROOT)}: missing link: {target}")
if errors:
    print("\n".join(errors))
    raise SystemExit(1)
print(f"PASS: {count} Markdown files are UTF-8 and all local file links resolve.")
