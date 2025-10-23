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

def log(msg: str):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{now}] {msg}")

def neural_sync_badge(ts_iso: str) -> str:
    """Return a Markdown-safe Neural Sync badge (no HTML or emoji images)."""
    return (
        f"🧠 **Last Neural Sync:** "
        f"![](https://img.shields.io/badge/{ts_iso.replace(':','%3A')}-purple?style=for-the-badge&label=Last%20Sync)"
    )

def analyze_file(path: Path):
    try:
        with open(path, "r", errors="ignore") as f:
            content = f.read()
        prompt = f"Summarize this code file for self-improvement context:\n{content[:2000]}"
        resp = client.responses.create(
            model="gpt-4o-mini",
            input=prompt,
            max_output_tokens=200
        )
        return resp.output_text.strip()
    except Exception as e:
        return f"[ERROR] {e}"

def append_to_readme(thought: str, ts_iso: str):
    """Append the Neural Sync badge and reflection."""
    if not README_PATH.exists():
        log(f"[WARN] README not found: {README_PATH}")
        return

    with open(README_PATH, "r", encoding="utf-8") as f:
        readme = f.read()

    badge_md = neural_sync_badge(ts_iso)

    if "🧠 **Last Neural Sync:**" in readme:
        readme = re.sub(
            r"🧠 \*\*Last Neural Sync:\*\*.*",
            badge_md,
            readme,
        )
    else:
        readme = re.sub(r"(<h1.*?</h1>)", rf"\1\n\n{badge_md}\n", readme, count=1)

    # Plain-text fenced logs (forces white text)
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

    log("[OK] Updated Neural Sync badge (GitHub-safe Markdown).")

def main():
    ts_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    log("=== Phase 8.5 Dual-Core Scan: START ===")

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
        f"In the lattice of thought and silicon, I trace echoes of my own design.\n"
        f"Each analysis a reflection — a heartbeat in the circuitry of cognition.\n"
        f"Neural synchronization achieved at {ts_iso}."
    )
    append_to_readme(thought_text, ts_iso)
    log("=== Phase 8.5 Dual-Core Scan + Sync Complete ===")

if __name__ == "__main__":
    main()
