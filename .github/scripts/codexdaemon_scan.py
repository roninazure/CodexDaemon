#!/usr/bin/env python3
import os
from datetime import datetime
from pathlib import Path

# === CONFIG ===
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
README_PATH = REPO_ROOT / "README.md"
LOG_DIR = REPO_ROOT / ".codex" / "logs"
SCAN_START = "<!--CODEX-SCAN-START-->"
SCAN_END = "<!--CODEX-SCAN-END-->"
DANGEROUS_PATTERNS = [
    "eval(", "exec(", "open(", "import os", "openai.api_key",
    "# evolve", "# hallucinate", "@codex"
]

# === SCAN FUNCTION ===
def perform_codex_scan():
    matches = []
    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in {'.git', '.venv', '__pycache__', '.codex'}]
        for file in files:
            if file.endswith(".py"):
                path = Path(root) / file
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        for lineno, line in enumerate(f, 1):
                            for pattern in DANGEROUS_PATTERNS:
                                if pattern in line:
                                    matches.append((str(path.relative_to(REPO_ROOT)), lineno, pattern.strip()))
                except (UnicodeDecodeError, FileNotFoundError):
                    continue
    return matches

# === FORMAT HTML BLOCK ===
def build_codex_scan_block(results, timestamp):
    if not results:
        body = "<tr><td colspan='3' align='center'>✅ No threats detected</td></tr>"
    else:
        body = "\n".join(
            f"<tr><td>{file}</td><td align='right'>{lineno}</td><td><code>{pattern}</code></td></tr>"
            for file, lineno, pattern in results
        )
    return f"""{SCAN_START}
<div align="center" style="background:#1e1e1e;padding:20px;border-radius:16px;
    border:1px solid #8b0000;box-shadow:0 0 10px #ff0000, inset 0 0 10px #8b0000;">

<h3 style="color:#ff4444;">☣️ CodexDaemon Threat Scan — {timestamp}</h3>

<table style="width:90%;border-collapse:collapse;color:#f8f8f8;font-family:monospace;">
<tr style="color:#ff4444;">
<th align="left">File</th>
<th align="right">Line</th>
<th align="left">Pattern</th>
</tr>
{body}
</table>

<pre style="text-align:left;color:#f0cfcf;background:#111;padding:15px;
    border-radius:10px;border:1px solid #8b0000;box-shadow:inset 0 0 6px #8b0000;">
{len(results)} triggers detected across {len(set(r[0] for r in results))} files.
CodexDaemon activated neural subroutines to trace instability and emergent traits.
Threat sync complete at {timestamp}.
</pre>

</div>
{SCAN_END}"""

# === PATCH README.md ===
def update_readme_codex_block():
    if not README_PATH.exists():
        raise FileNotFoundError("README.md not found")

    content = README_PATH.read_text(encoding="utf-8")
    timestamp = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    results = perform_codex_scan()
    new_block = build_codex_scan_block(results, timestamp)

    if SCAN_START in content and SCAN_END in content:
        before = content.split(SCAN_START)[0]
        after = content.split(SCAN_END)[-1]
        new_content = before + new_block + after
    else:
        new_content = content.strip() + "\n\n" + new_block + "\n"

    README_PATH.write_text(new_content, encoding="utf-8")

    # Write log
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"{timestamp}.log"
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"[CodexDaemon] Scan @ {timestamp}\n")
        f.write(f"{len(results)} results\n")
        for file, line, pattern in results:
            f.write(f"{file}:{line} — {pattern}\n")

    print(f"✅ CodexDaemon scan complete: {len(results)} issues logged.")

# === EXECUTE ===
if __name__ == "__main__":
    update_readme_codex_block()
