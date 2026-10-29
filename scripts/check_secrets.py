"""Reject accidentally committed credential files and common high-entropy token formats."""

import re
import subprocess
import sys
from pathlib import Path

PATTERNS = [
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bASIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),
    re.compile(r"\bglpat-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bsk-proj-[A-Za-z0-9_-]{25,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]
exts = {".py", ".md", ".json", ".toml", ".txt", ".yml", ".yaml", ".sh",
        ".bat", ".html", ".cff", ".example", ".template"}
errors = []
for raw in subprocess.check_output(["git", "ls-files", "-z"]).split(b"\0"):
    if not raw:
        continue
    path = Path(raw.decode())
    if path.name == ".env" or (path.name.startswith(".env.") and path.name not in {".env.example", ".env.template"}):
        errors.append(f"Tracked environment file: {path}")
    if not path.is_file() or path.suffix not in exts:
        continue
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if any(pattern.search(line) for pattern in PATTERNS):
            errors.append(f"Potential credential: {path}:{line_no}")
if errors:
    sys.exit("\n".join(errors))
print("No obvious tracked secrets detected (heuristic; not a full secret scan).")
