#!/usr/bin/env python3
"""
codexdaemon_scan.py — Phase 8.6 “Finalized Neural Sync + Reflection Formatting Fix”

✅ Fixes:
 - 🧠 Neural Sync badge no longer breaks GitHub (emoji-safe HTML)
 - Reflections always render as white text (no blue syntax)
"""

import os
import datetime
import html
import re
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# ---------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
LOG_DIR = Path.home() / ".codex" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Load env
env_paths = [
    REPO_ROOT / ".env",
    Path("/Users/scottsteele/work/mad-scientist-code/.env"),
]
for ep in env_paths:
    if ep.exists():
        load_dotenv(ep)
        print(f"[OK] Loaded environment from: {ep}")
        break

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("CODEX_MODEL", "gpt-4o-mini")

client = OpenAI(api_key=OPENAI_API_KEY)

def log(msg: str):
    ts = datetime.datetime.utcnow().strftime("[%Y-%m-%dT%H:%M:%SZ]")
    print(f"{ts} {msg}")

# ---------------------------------------------------------------------
# Repo scan
# ---------------------------------------------------------------------
def collect_python_files(root: Path):
    for p in root.rglob("*.py"):
        if any(ex in p.parts for ex in [".venv", "__pycache__", "backups", "logs"]):
            continue
        yield p

def summarize_file(path: Path):
    try:
        content = path.read_text(encoding="utf-8")[:2000]
    except Exception as e:
        return f"[ERROR reading {path.name}: {e}]"

    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system",
                 "content": "You are CodexDaemon — an autonomous code analyst. "
                            "Summarize this file and suggest one meaningful improvement."},
                {"role": "user", "content": content}
            ],
            temperature=0.4,
            max_tokens=250
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"[WARN] AI analysis failed for {path.name}: {e}"

# ---------------------------------------------------------------------
# Neural Sync Badge (fixed)
# ---------------------------------------------------------------------
def update_neural_sync_badge():
    """GitHub-safe Neural Sync badge (no ? mark issue)."""
    readme = REPO_ROOT / "README.md"
    now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ")

    badge_html = f"""
<p align="center">
  <img src="https://github.githubassets.com/images/icons/emoji/unicode/1f9e0.png" width="32" height="32" alt="🧠"/><br/>
  <img src="https://img.shields.io/badge/Last%20Neural%20Sync-{now}-7e22ce?style=for-the-badge&labelColor=1a1a1a" alt="Last Neural Sync"/>
</p>
"""

    txt = readme.read_text(encoding="utf-8")

    if "Last Neural Sync" in txt:
        import re
        txt = re.sub(
            r"<p align=\"center\">[\s\S]+?</p>",
            badge_html.strip(),
            txt,
            count=1,
        )
    else:
        txt = txt.replace("</h1>", f"</h1>\n{badge_html}")

    readme.write_text(txt, encoding="utf-8")
    log(f"[OK] Neural Sync badge updated — GitHub-safe Twemoji rendered.")

    # 🧠 outside the badge; HTML-safe and center aligned
    badge_html = (
        f'<p align="center" style="margin-top:8px;">\n'
        f'  <span style="font-size:1.4em;">🧠</span>\n'
        f'  <img src="https://img.shields.io/badge/Last%20Neural%20Sync-'
        f'{now}-7e22ce?style=for-the-badge&labelColor=1a1a1a" '
        f'alt="Last Neural Sync"/>\n'
        f'</p>\n'
    )

    txt = readme.read_text(encoding="utf-8")
    if "Last Neural Sync" in txt:
        txt = re.sub(
            r'<p align="center" style="margin-top:8px;">[\s\S]+?</p>',
            badge_html.strip(),
            txt,
            count=1,
        )
    else:
        txt = txt.replace("</h1>", f"</h1>\n{badge_html}")

    readme.write_text(txt, encoding="utf-8")
    log(f"[OK] Neural Sync badge updated (emoji-safe HTML) in {readme}")

# ---------------------------------------------------------------------
# Reflection Writer (now 100% plain white text)
# ---------------------------------------------------------------------
def append_self_thought():
    """Generate and append a CodexDaemon reflection — plain text only."""
    try:
        reflection_prompt = (
            "You are CodexDaemon — an introspective AI. Write a short poetic reflection "
            "about today's scan (2–4 lines). Avoid markdown, punctuation like *, or code formatting."
        )

        text = "No reflection generated."
        if client:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": "You are CodexDaemon, the self-writing AI."},
                    {"role": "user", "content": reflection_prompt},
                ],
                temperature=0.6,
                max_tokens=120,
            )
            text = resp.choices[0].message.content.strip()

        # Escape markdown-sensitive characters
        safe_text = html.escape(text).replace("`", "").replace("*", "").replace("_", "")

        readme_path = REPO_ROOT / "README.md"
        timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ")

        # Wrap inside fenced block with 'text' label
        entry = (
            f"\n```text\n"
            f"🧩 CodexDaemon Log — {timestamp}\n"
            f"> {safe_text}\n"
            f"```\n"
        )

        with open(readme_path, "a", encoding="utf-8") as f:
            f.write(entry)

        log(f"[OK] Reflection appended to README at {timestamp}")

    except Exception as e:
        log(f"[WARN] Reflection append failed: {e}")

# ---------------------------------------------------------------------
# Main Logic
# ---------------------------------------------------------------------
def main():
    log("=== Phase 8.6 Dual-Core Self-Improvement Scan: START ===")

    repo_targets = [
        ("mad-scientist-code", Path("/Users/scottsteele/work/mad-scientist-code")),
        ("CodexDaemon", Path("/Users/scottsteele/work/CodexDaemon")),
        ("priv", Path("/Users/scottsteele/work/priv")),
    ]

    results = {}
    for label, path in repo_targets:
        if not path.exists():
            log(f"[SKIP] {path} — missing")
            continue
        log(f"Scanning repository: {label}")
        for f in collect_python_files(path):
            log(f"Analyzing: {f.relative_to(path.parent)}")
            results[str(f.relative_to(path.parent))] = summarize_file(f)

    out_file = LOG_DIR / f"codex_scan_{datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.log"
    with open(out_file, "w", encoding="utf-8") as fh:
        for k, v in results.items():
            fh.write(f"\n=== {k} ===\n{v}\n")

    log(f"[OK] Scan log written → {out_file}")
    update_neural_sync_badge()
    append_self_thought()
    log("=== Phase 8.6 Dual-Core Scan + Sync Complete ===")

# ---------------------------------------------------------------------
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"[FATAL] {e}")
