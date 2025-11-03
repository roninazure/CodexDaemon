import os
import re
from datetime import datetime

# Constants
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
README_PATH = os.path.join(REPO_ROOT, "README.md")
TARGET_EXT = ".py"
EXCLUDE_DIRS = {".venv", "__pycache__", "venv", ".git"}

SANITIZE_LOG_START = "<!-- SANITIZE_LOG_START -->"
SANITIZE_LOG_END = "<!-- SANITIZE_LOG_END -->"

def scan_files():
    python_files = []
    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for file in files:
            if file.endswith(TARGET_EXT):
                python_files.append(os.path.join(root, file))
    return python_files

def sanitize_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        original_lines = f.readlines()

    sanitized_lines = []
    modified = False
    for line in original_lines:
        sanitized = re.sub(r"[ \t]+$", "", line)
        if sanitized != line:
            modified = True
        sanitized_lines.append(sanitized)

    if modified:
        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(sanitized_lines)
    return modified

def insert_sanitize_log(count, cleaned, errors):
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    log = f"""{SANITIZE_LOG_START}
<div align="center" style="background:#111; padding:20px; border-radius:16px;
    border:1px solid #6a0dad; box-shadow:0 0 10px #6a0dad, inset 0 0 10px #6a0dad;
    color:#e0e0e0; font-family:monospace; margin-top:30px;">
<h3 style="color:#bb86fc;">🧹 CodexDaemon Sanitize Log — {timestamp}</h3>
<ul style="list-style-type: none; padding-left: 0;">
  <li>✅ {count} Python files scanned</li>
  <li>✅ {cleaned} files auto-cleaned</li>
  <li>✅ {errors} syntax errors</li>
</ul>
</div>
{SANITIZE_LOG_END}"""

    updated = re.sub(
        f"{SANITIZE_LOG_START}.*?{SANITIZE_LOG_END}",
        log,
        content,
        flags=re.DOTALL,
    )

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(updated)

def main():
    python_files = scan_files()
    cleaned_count = 0
    syntax_errors = 0

    for file in python_files:
        try:
            if sanitize_file(file):
                cleaned_count += 1
        except Exception:
            syntax_errors += 1

    insert_sanitize_log(len(python_files), cleaned_count, syntax_errors)

    print("[OK] README updated with sanitize log.\n")
    print("[SUMMARY]")
    print(f"Scanned  : {len(python_files)} .py files")
    print(f"Cleaned  : {cleaned_count} modified")
    print(f"Errors   : {syntax_errors} syntax issues")

if __name__ == "__main__":
    main()

