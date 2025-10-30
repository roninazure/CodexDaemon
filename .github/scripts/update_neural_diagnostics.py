import os
from datetime import datetime
from pathlib import Path

REPO_DIRS = {
    "CodexDaemon": "../",  # current repo
    "mad-scientist-code": "../../mad-scientist-code",
    "project-darc": "../../project-darc",
    "priv": "../../priv"
}

EXCLUDE_DIRS = {".venv", "__pycache__", ".git"}

README_PATH = Path("README.md")
SYNC_START = "<!--SYNC-START-->"
SYNC_END = "<!--SYNC-END-->"


def count_py_and_loc(repo_path):
    total_files = 0
    total_loc = 0
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for file in files:
            if file.endswith(".py"):
                total_files += 1
                with open(Path(root) / file, encoding="utf-8", errors="ignore") as f:
                    total_loc += sum(1 for _ in f)
    return total_files, total_loc


def build_diagnostics_block(results):
    timestamp = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    rows = "\n".join(
        f"<tr><td>{repo}</td><td align='right'>{files}</td><td align='right'>{loc}</td></tr>"
        for repo, (files, loc) in results.items()
    )
    total_files = sum(f for f, _ in results.values())
    total_loc = sum(l for _, l in results.values())

    narrative = f"""The analysis of the four repositories reveals a modest volume of code,
with a combined total of {total_loc} lines across {total_files} files. Each repository exhibits distinct characteristics,
reflecting the unique intentions of their creators. The balance of complexity and simplicity is evident,
suggesting a focused approach to development. Neural synchronization achieved at {timestamp}."""

    return f"""
<div align="center" style="background:#0a0a0a;padding:20px;border-radius:16px;
    border:1px solid #0ea5e9;box-shadow:0 0 10px #0ea5e9, inset 0 0 10px #0ea5e9;">

<h3 style="color:#0ea5e9;">🧩 Neural Diagnostics — {timestamp}</h3>

<table style="width:80%;border-collapse:collapse;color:#e2e2e2;font-family:monospace;">
<tr style="color:#0ea5e9;">
<th align="left">Repository</th>
<th align="right">.py files</th>
<th align="right">LOC</th>
</tr>
{rows}
</table>

<pre style="text-align:left;color:#cfcfcf;background:#111;padding:15px;
    border-radius:10px;border:1px solid #0ea5e9;box-shadow:inset 0 0 6px #0ea5e9;">
{narrative}
</pre>

</div>""".strip()


def update_readme_block():
    if not README_PATH.exists():
        print("❌ ERROR: README.md not found.")
        return

    readme_text = README_PATH.read_text(encoding="utf-8", errors="ignore")

    if SYNC_START not in readme_text or SYNC_END not in readme_text:
        print("❌ ERROR: SYNC-START/END markers not found in README.md.")
        return

    before = readme_text.split(SYNC_START)[0]
    after = readme_text.split(SYNC_END)[-1]

    results = {}
    for repo, path in REPO_DIRS.items():
        full_path = Path(path).resolve()
        if not full_path.exists():
            results[repo] = (0, 0)
            continue
        results[repo] = count_py_and_loc(full_path)

    diagnostics_block = build_diagnostics_block(results)
    new_content = f"{before}{SYNC_START}\n{diagnostics_block}\n{SYNC_END}{after}"

    with open(README_PATH, "w", encoding="utf-8", errors="replace") as f:
        f.write(new_content)

    print("✅ README.md updated successfully.")


if __name__ == "__main__":
    update_readme_block()
