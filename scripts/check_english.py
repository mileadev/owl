"""Reject Chinese/Japanese scripts in tracked repository text files."""
import re
import subprocess
import sys
from pathlib import Path

pattern = re.compile(r"[\u3400-\u9fff\u3040-\u30ff]")
suffixes = {".py", ".md", ".json", ".toml", ".txt", ".yml", ".yaml",
            ".sh", ".bat", ".html", ".ini", ".cff"}
errors = []
for item in subprocess.check_output(["git", "ls-files", "-z"]).split(b"\0"):
    if not item:
        continue
    path = Path(item.decode())
    if path.suffix.lower() not in suffixes or not path.is_file() or path.name == "uv.lock":
        continue
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if pattern.search(line):
            errors.append(f"{path}:{index}")
if errors:
    sys.exit("Non-English text found:\n" + "\n".join(errors))
print("English-only source check passed.")
