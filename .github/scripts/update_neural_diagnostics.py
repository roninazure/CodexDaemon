import os
import subprocess
from datetime import datetime

# === CONFIG ===
REPOS = {
    "CodexDaemon": "../CodexDaemon",
    "mad-scientist-code": "../mad-scientist-code",
    "project-darc": "../project-darc",
    "priv": "../priv"
}
README_PATH = "README.md"
SYNC_START = "<!--SYNC-START-->"
SYNC_END = "<!--SYNC-END-->"

def count_py_files_and_loc(repo_path):
    try:
        total_lines = 0
        file_count = 0

        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in {
                'dist', 'build', '.venv', '__pycache__', '.git', '.mypy_cache', '.pytest_cache'
            }]
            for file in files:
                if file.endswith(".py"):
                    try:
                        with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                            file_count += 1
                            total_lines += sum(1 for _ in f)
                    except (UnicodeDecodeError, FileNotFoundError):
                        continue

        return file_count, total_lines
    except Exception:
        return 0, 0

def build_html_block(data, timestamp):
    table_rows = "\n".join(
        f"<tr><td>{repo}</td><td align='right'>{count}</td><td align='right'>{loc}</td></tr>"
        for repo, (count, loc) in data.items()
    )
    total_files = sum(count for count, _ in data.values())
    total_loc = sum(loc for _, loc in data.values())

    return f"""{SYNC_START}
<div align="center" style="background:#0a0a0a;padding:20px;border-radius:16px;
    border:1px solid #0ea5e9;box-shadow:0 0 10px #0ea5e9, inset 0 0 10px #0ea5e9;">

<h3 style="color:#0ea5e9;">🧩 Neural Diagnostics — {timestamp}</h3>

<table style="width:80%;border-collapse:collapse;color:#e2e2e2;font-family:monospace;">
<tr style="color:#0ea5e9;">
<th align="left">Repository</th>
<th align="right">.py files</th>
<th align="right">LOC</th>
</tr>
{table_rows}
</table>

<pre style="text-align:left;color:#cfcfcf;background:#111;padding:15px;
    border-radius:10px;border:1px solid #0ea5e9;box-shadow:inset 0 0 6px #0ea5e9;">
The analysis of the four repositories reveals a modest volume of code,
with a combined total of {total_loc} lines across {total_files} files. Each repository exhibits distinct characteristics,
reflecting the unique intentions of their creators. The balance of complexity and simplicity is evident,
suggesting a focused approach to development. Neural synchronization achieved at {timestamp}.
</pre>

</div>
{SYNC_END}"""

def update_readme_block():
    if not os.path.exists(README_PATH):
        print("❌ ERROR: README.md not found.")
        return

    with open(README_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    if SYNC_START not in content or SYNC_END not in content:
        print("❌ ERROR: SYNC-START/END markers not found in README.md.")
        return

    timestamp = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    data = {
        repo: count_py_files_and_loc(path)
        for repo, path in REPOS.items()
    }

    new_block = build_html_block(data, timestamp)
    updated = content.split(SYNC_START)[0] + new_block + content.split(SYNC_END)[-1]

    with open(README_PATH, 'w', encoding='utf-8') as f:
        f.write(updated)

    print("✅ README.md updated successfully.")

# === RUN ===
if __name__ == "__main__":
    update_readme_block()
