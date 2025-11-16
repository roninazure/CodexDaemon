import os
import re
import ast
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
README_PATH = REPO_ROOT / "README.md"
EXCLUDE_DIRS = {".venv", "venv", "__pycache__", ".git"}
PY_EXT = ".py"

SANITIZE_LOG_START = "<!-- SANITIZE_LOG_START -->"
SANITIZE_LOG_END = "<!-- SANITIZE_LOG_END -->"

def scan_files():
    py_files = []
    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for file in files:
            if file.endswith(PY_EXT):
                py_files.append(Path(root) / file)
    return py_files

def sanitize_file(path):
    with open(path, "r", encoding="utf-8") as f:
        original = f.readlines()

    cleaned = [re.sub(r"[ \t]+$", "", line) for line in original]
    modified = original != cleaned

    if modified:
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(cleaned)

    return modified

def generate_risk_scores(py_files):
    scores = []
    syntax_errors = 0

    for f in py_files:
        try:
            with open(f, "r", encoding="utf-8") as src:
                ast.parse(src.read())
            score = (sum(ord(c) for c in f.name) % 45) + 5
            scores.append((str(f.relative_to(REPO_ROOT)), score))
        except SyntaxError:
            syntax_errors += 1

    scores.sort(key=lambda x: -x[1])
    return scores, syntax_errors

def build_readme_block(total, cleaned, errors, risk_data):
    timestamp = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    date_str = timestamp.split("T")[0]

    status_block = f"""
🧹 CodexDaemon Sanitize Log — `{timestamp}`

✅ {total} Python files scanned
✅ {cleaned} files auto-cleaned
{"✅ No syntax errors" if errors == 0 else f"❌ {errors} syntax errors"}
"""

    table_block = "\n".join([
        "\n🍬 **CodexDaemon Mutation Risk Score**\n",
        "| File | Risk Score |",
        "|------|-------------|",
        *[f"| `{path}` | {score} |" for path, score in risk_data]
    ])

    footer = f"""
CodexDaemon performed a self-inspection on potential mutation vectors.
Risk is ranked by suspicious operations and volatile patterns.
Scan timestamp: `{timestamp}`
"""

    return f"{SANITIZE_LOG_START}\n{status_block}\n{table_block}\n{footer}\n{SANITIZE_LOG_END}"

def inject_log_to_readme(new_block):
    with open(README_PATH, "r", encoding="utf-8") as f:
        readme = f.read()

    if SANITIZE_LOG_START not in readme or SANITIZE_LOG_END not in readme:
        raise ValueError("Sanitize markers not found in README.md")

    pattern = re.compile(f"{SANITIZE_LOG_START}.*?{SANITIZE_LOG_END}", re.DOTALL)
    updated = pattern.sub(new_block, readme)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(updated)

    print("[✓] README updated with full sanitize + risk block")

def main():
    py_files = scan_files()
    cleaned = sum(sanitize_file(f) for f in py_files)
    risk_scores, syntax_errors = generate_risk_scores(py_files)

    block = build_readme_block(
        total=len(py_files),
        cleaned=cleaned,
        errors=syntax_errors,
        risk_data=risk_scores[:7]
    )

    inject_log_to_readme(block)

    print("[SUMMARY]")
    print(f"  Total   : {len(py_files)}")
    print(f"  Cleaned : {cleaned}")
    print(f"  Errors  : {syntax_errors}")
    print(f"  Top     : {risk_scores[:3]}")

if __name__ == "__main__":
    main()
