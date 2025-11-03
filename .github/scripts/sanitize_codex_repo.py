#!/usr/bin/env python3
"""
CodexDaemon Repository Sanitizer v1.0
-------------------------------------
Scans Python files, removes formatting issues, and logs results into README.md.
"""

import os
import re
from pathlib import Path
from datetime import datetime

# === CONFIG ===
ROOT_DIR = Path(__file__).resolve().parents[2]
README_PATH = ROOT_DIR / "README.md"
EXCLUDE_DIRS = {".venv", "__pycache__", ".git"}

# === FIND PYTHON FILES ===
py_files = [
    path for path in ROOT_DIR.rglob("*.py")
    if not any(part in EXCLUDE_DIRS for part in path.parts)
]

fixed_files = []
syntax_errors = []

# === CLEAN FILES ===
for py_file in py_files:
    try:
        src = py_file.read_text(encoding="utf-8")
    except Exception as e:
        print(f"[SKIP] {py_file} - {e}")
        continue

    cleaned = src.replace("\t", "    ")
    cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)  # strip trailing whitespace

    try:
        compile(cleaned, str(py_file), "exec")
    except SyntaxError as e:
        syntax_errors.append(f"❌ {py_file} — {e.msg} (line {e.lineno})")
        continue

    if cleaned != src:
        py_file.write_text(cleaned, encoding="utf-8")
        fixed_files.append(str(py_file))

# === BUILD LOG BLOCK ===
timestamp = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
summary = f"""<!-- SANITIZE_LOG_START -->
### 🧹 CodexDaemon Sanitize Log — {timestamp}
- ✅ {len(py_files)} Python files scanned
- ✅ {len(fixed_files)} files auto-cleaned
- {"✅ No syntax errors" if not syntax_errors else f"❌ {len(syntax_errors)} syntax issues found"}
"""

if syntax_errors:
    summary += "\n\n" + "\n".join(f"- {line}" for line in syntax_errors)

summary += "\n<!-- SANITIZE_LOG_END -->"

# === INJECT INTO README.md ===
if README_PATH.exists():
    readme = README_PATH.read_text(encoding="utf-8")
    if "<!-- SANITIZE_LOG_START -->" in readme and "<!-- SANITIZE_LOG_END -->" in readme:
        readme = re.sub(
            r"<!-- SANITIZE_LOG_START -->[\s\S]*?<!-- SANITIZE_LOG_END -->",
            summary,
            readme
        )
        README_PATH.write_text(readme, encoding="utf-8")
        print("[OK] README updated with sanitize log.")
    else:
        print("[WARN] README markers not found — skipping README injection.")
else:
    print("[WARN] README.md not found.")

# === FINAL SUMMARY ===
print("\n[SUMMARY]")
print(f"Scanned  : {len(py_files)} .py files")
print(f"Cleaned  : {len(fixed_files)} modified")
print(f"Errors   : {len(syntax_errors)} syntax issues")

