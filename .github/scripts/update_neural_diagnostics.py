#!/usr/bin/env python3
import os
from datetime import datetime

# 🧠 Repositories to scan
REPOS = {
    "mad-scientist-code": "../../mad-scientist-code",
    "CodexDaemon": "../..",
    "priv": "../../priv",
    "project-darc": "../../project-darc"
}

def count_py_and_loc(path):
    py_files, total_loc = 0, 0
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith(".py"):
                py_files += 1
                try:
                    with open(os.path.join(root, file), encoding="utf-8", errors="ignore") as f:
                        total_loc += sum(1 for _ in f)
                except Exception:
                    pass
    return py_files, total_loc

timestamp = datetime.utcnow().isoformat(timespec='seconds') + "Z"

# 🔢 Count files and LOC
table_rows = []
total_files, total_loc = 0, 0
for repo, path in REPOS.items():
    files, loc = count_py_and_loc(path)
    total_files += files
    total_loc += loc
    table_rows.append(f"<tr><td>{repo}</td><td align='right'>{files}</td><td align='right'>{loc}</td></tr>")

# 🎨 Create the diagnostics block
diagnostics_block = f"""<div align="center" style="background:#0a0a0a;padding:20px;border-radius:16px;
border:1px solid #0ea5e9;box-shadow:0 0 10px #0ea5e9, inset 0 0 10px #0ea5e9;">

<h3 style="color:#0ea5e9;">🧩 Neural Diagnostics — {timestamp}</h3>

<table style="width:80%;border-collapse:collapse;color:#e2e2e2;font-family:monospace;">
<tr style="color:#0ea5e9;">
<th align="left">Repository</th>
<th align="right">.py files</th>
<th align="right">LOC</th>
</tr>
{chr(10).join(table_rows)}
</table>

<pre style="text-align:left;color:#cfcfcf;background:#111;padding:15px;
border-radius:10px;border:1px solid #0ea5e9;box-shadow:inset 0 0 6px #0ea5e9;">
The analysis of the four repositories reveals a modest volume of code,
with a combined total of {total_loc} lines across {total_files} files. Each repository exhibits distinct characteristics,
reflecting the unique intentions of their creators. The balance of complexity and simplicity is evident,
suggesting a focused approach to development. Neural synchronization achieved at {timestamp}.
</pre>

</div>
<!--SYNC-END-->"""

# 📄 Inject into README.md
readme_path = "README.md"
with open(readme_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find and replace up to SYNC-END marker
sync_idx = next(i for i, line in enumerate(lines) if "<!--SYNC-END-->" in line)
new_lines = lines[:sync_idx] + [diagnostics_block + "\n"]

# 💾 Save changes
with open(readme_path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print(f"✅ Neural Diagnostics block updated with timestamp: {timestamp}")
