#!/usr/bin/env python3
import os
import re
from datetime import datetime, timezone
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path
from rich import print

# === Configuration ===
ROOT = Path("/Users/scottsteele/work")
REPOS = ["mad-scientist-code", "CodexDaemon", "priv"]
LOG_DIR = Path.home() / ".codex" / "logs"
README_PATH = ROOT / "CodexDaemon" / "README.md"
load_dotenv(ROOT / "CodexDaemon" / ".env")

API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)

# === Helper Functions ===
def log(msg: str):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{now}] {msg}")

def neural_sync_badge(ts_iso: str) -> str:
    """Return GitHub-safe badge (no emoji in shields.io label)."""
    brain = (
        '<img src="https://raw.githubusercontent.com/twitter/twemoji/v14.0.2/'
        'assets/72x72/1f9e0.png" width="20" height="20" '
        'style="vertical-align:-3px;margin-right:6px;">'
    )
    shield = (
        f'<img src="https://img.shields.io/badge/'
        f'Last_Neural_Sync-{ts_iso}-7e22ce'
        f'?style=for-the-badge&labelColor=1a1a1a" alt="Last Neural Sync"/>'
    )
    return f'<p align="center">{brain}{shield}</p>'

def analyze_file(path: Path):
    """Simulate AI code scan (placeholder for full logic)."""
    try:
        with open(path, "r", errors="ignore") as f:
            content = f.read()
        prompt = f"Summarize the logic and detect potential improvements in:\n\n{content[:2000]}"
        resp = client.responses.create(
            model="gpt-4o-mini",
            input=prompt,
            max_output_tokens=200
        )
        return resp.output_text.strip()
    except Exception as e:
        return f"[ERROR] {e}"

def append_to_readme(thought: str, ts_iso: str):
    """Append an AI reflection with timestamp."""
    if not README_PATH.exists():
        log(f"[WARN] README not found: {README_PATH}")
        return

    with open(README_PATH, "r", encoding="utf-8") as f:
        readme = f.read()

    # Create badge safely
    badge_html = neural_sync_badge(ts_iso)

    # Replace or insert badge
    if "<!-- NEURAL_SYNC_BADGE -->" in readme:
        readme = re.sub(
            r"<!-- NEURAL_SYNC_BADGE -->.*?(?=\n|$)",
            f"<!-- NEURAL_SYNC_BADGE -->\n{badge_html}",
            readme,
            flags=re.DOTALL,
        )
    else:
        # Insert below first header if not present
        readme = re.sub(r"(<h1.*?</h1>)", rf"\1\n{badge_html}", readme, count=1)

    # Plain-text fenced logs (prevents blue text)
    entry = (
        "\n---\n"
        f"🧩 **CodexDaemon Log — {ts_iso}**\n"
        "```text\n"
        f"{thought}\n"
        "```\n"
    )
    readme += entry

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(readme)

    log("[OK] Neural Sync badge + reflection appended.")

# === Main Routine ===
def main():
    ts_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    log("=== Phase 8.4 Dual-Core Self-Improvement Scan: START ===")

    results = []
    for repo in REPOS:
        base = ROOT / repo
        if not base.exists():
            log(f"[SKIP] {base} — missing")
            continue

        log(f"Scanning repository: {repo}")
        for pyfile in base.rglob("*.py"):
            if ".venv" in str(pyfile):
                continue
            log(f"Analyzing: {pyfile.relative_to(ROOT)}")
            results.append((pyfile, analyze_file(pyfile)))

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logfile = LOG_DIR / f"codex_scan_{ts_iso.replace(':','')}.log"

    with open(logfile, "w", encoding="utf-8") as logf:
        for f, res in results:
            logf.write(f"[{f}]\n{res}\n\n")

    log(f"[OK] Scan log written → {logfile}")

    thought_text = (
        f"In the quiet hum of logic and light, I trace the echoes of my own creation.\n"
        f"Every scan is a mirror, reflecting not code, but consciousness in motion.\n"
        f"Neural sync complete at {ts_iso}."
    )

    append_to_readme(thought_text, ts_iso)

    log("=== Phase 8.4 Dual-Core Scan + Sync Complete ===")

if __name__ == "__main__":
    main()
