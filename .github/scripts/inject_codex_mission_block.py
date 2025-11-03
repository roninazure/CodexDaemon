#!/usr/bin/env python3
import os
from datetime import datetime

README_PATH = "README.md"
START = "<!-- CODEX_MISSION_START -->"
END = "<!-- CODEX_MISSION_END -->"

HTML_TEMPLATE = f"""{START}
<div align="center" style="margin-top:30px; padding:20px; border-radius:16px;
    border:1px solid #6a0dad; box-shadow:0 0 10px #6a0dad, inset 0 0 10px #6a0dad;
    background:#111; color:#e0e0e0; font-family:monospace;">

<h3 style="color:#bb86fc;">👁️  CodexDaemon: Self-Writing AI Code Engine</h3>

<p style="max-width:750px; margin:auto; font-size:14px; line-height:1.6;">
CodexDaemon is an autonomous AI system that reads, mutates, and evolves its own codebase.<br>
It operates in a self-healing feedback loop — scanning repos, injecting diagnostics, and activating subroutines.<br>
Each commit is a potential mutation. Each scan a neurotic mirror. Each line of code, a neural spark.<br>
<code>Think. Scan. Mutate. Evolve.</code>
</p>

<p style="margin-top:20px; font-size:12px; color:#888;">Last mission sync at {datetime.utcnow().replace(microsecond=0).isoformat()}Z</p>

</div>
{END}"""

def update_codex_mission():
    if not os.path.exists(README_PATH):
        print("❌ README.md not found.")
        return

    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    if START not in content or END not in content:
        print("❌ CODEX_MISSION markers not found. Aborting update.")
        return

    pre = content.split(START)[0]
    post = content.split(END)[-1]
    updated = pre + HTML_TEMPLATE + post

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(updated)

    print("✅ CodexDaemon Mission block updated.")

if __name__ == "__main__":
    update_codex_mission()
