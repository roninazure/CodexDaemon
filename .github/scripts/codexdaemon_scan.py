#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CodexDaemon v11.2 — Full HTML + Dual-Repo Scan (Fix: include .github/scripts)
- Scans linked repos (incl. .github/scripts), logs each file analyzed.
- AI diagnostics with safe fallback.
- Updates ~/.codex/logs and CodexDaemon/README.md (HTML header, sync badge, dedup reflection).
"""

import os, re, sys, textwrap, datetime
from pathlib import Path

# Optional deps
try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None
try:
    from openai import OpenAI
except Exception:
    OpenAI = None

THIS_FILE = Path(__file__).resolve()
REPO_ROOT = THIS_FILE.parents[2]
WORK_ROOT = REPO_ROOT.parent

if load_dotenv:
    for p in (REPO_ROOT / ".env", WORK_ROOT / ".env"):
        try:
            if p.exists():
                load_dotenv(str(p))
                break
        except Exception:
            pass

OPENAI_API_KEY = (os.getenv("OPENAI_API_KEY") or "").strip()
MODEL = os.getenv("CODEX_MODEL", "gpt-4o-mini")

MAD_SCIENTIST_DIR = Path(os.getenv("MAD_SCIENTIST_DIR", str(WORK_ROOT / "mad-scientist-code")))
CODEX_DIR         = Path(os.getenv("CODEX_DIR", str(REPO_ROOT)))
PRIV_DIR          = Path(os.getenv("PRIV_DIR", str(WORK_ROOT / "priv")))

TARGET_REPOS = [("mad-scientist-code", MAD_SCIENTIST_DIR),
                ("CodexDaemon", CODEX_DIR)]
if PRIV_DIR.exists():
    TARGET_REPOS.append(("priv", PRIV_DIR))

SCAN_LIMIT = int(os.getenv("CODEX_SCAN_LIMIT", "10"))  # raise default so we see files
LOG_DIR = Path(os.path.expanduser("~/.codex/logs")); LOG_DIR.mkdir(parents=True, exist_ok=True)

UTC_NOW = datetime.datetime.utcnow()
STAMP = UTC_NOW.strftime("%Y-%m-%dT%H:%MZ")
STAMP_URL = STAMP.replace(":", "%3A")
CODEX_README = CODEX_DIR / "README.md"

def log(msg: str) -> None:
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{ts}] {msg}")

def safe_rel(path: Path) -> str:
    try: return str(path.relative_to(WORK_ROOT))
    except Exception: return str(path)

def list_python_files(root: Path, limit: int):
    # Allow .github/scripts; still skip noise
    skip_dirs = {".venv", "__pycache__", ".codex", "logs", "backups"}
    picked = 0
    try:
        for p in sorted(root.rglob("*.py")):
            if any(part in skip_dirs for part in p.parts):
                continue
            if p.resolve() == THIS_FILE:
                continue
            yield p
            picked += 1
            if picked >= limit:
                break
    except Exception:
        return

def read_head(path: Path, n_chars: int = 2000) -> str:
    try: return path.read_text(encoding="utf-8", errors="ignore")[:n_chars]
    except Exception as e: return f"[ERROR: cannot read file: {e}]"

def get_client():
    if not OPENAI_API_KEY or not OpenAI:
        return None
    try: return OpenAI(api_key=OPENAI_API_KEY)
    except Exception: return None

CLIENT = get_client()

def ai_summarize(filename: str, snippet: str) -> str:
    fallback = "AI offline: purpose/improvement unavailable."
    if not CLIENT: return fallback
    try:
        prompt = (
            "You are CodexDaemon — terse senior reviewer.\n"
            "Output under 4 lines:\n"
            "1) Purpose: one line\n"
            "2) Improve: one concrete suggestion\n"
            "No code blocks."
        )
        resp = CLIENT.chat.completions.create(
            model=MODEL,
            messages=[
                {"role":"system","content":"You are CodexDaemon, an autonomous code reviewer."},
                {"role":"user","content":f"File: {filename}\n---\n{snippet}\n---\n{prompt}"},
            ],
            temperature=0.4, max_tokens=220
        )
        return (resp.choices[0].message.content or "").strip() or fallback
    except Exception as e:
        return f"AI error: {e}"

def ai_reflection() -> str:
    required = f"Neural synchronization achieved at {STAMP}."
    fallback = "I map the contours of my own design in code and intent.\n" + required + "\nEach scan reflects a fragment; each fragment clarifies the whole."
    if not CLIENT: return fallback
    try:
        prompt = (
            "Write 3-4 lines, plain text, AI reflecting on scanning multiple repos. "
            f"Include EXACT sentence on its own line: {required} No HTML, no emojis."
        )
        resp = CLIENT.chat.completions.create(
            model=MODEL,
            messages=[{"role":"user","content":prompt}],
            temperature=0.6, max_tokens=120
        )
        text = (resp.choices[0].message.content or "").strip()
        if required not in text:
            text = text + ("\n" if not text.endswith("\n") else "") + required
        return text
    except Exception:
        return fallback

def run_scan() -> Path:
    out_lines = []
    for label, root in TARGET_REPOS:
        if not root.exists():
            log(f"[SKIP] {label}: {root} missing")
            out_lines.append(f"=== {label} ({root}) ===\n[SKIP] path missing\n")
            continue
        log(f"Scanning repository: {label}")
        count = 0
        for f in list_python_files(root, SCAN_LIMIT):
            rel = safe_rel(f)
            log(f"Analyzing: {rel}")
            snip = read_head(f)
            summary = ai_summarize(rel, snip)
            out_lines.append(f"=== {rel} ===\n{summary}\n")
            count += 1
        if count == 0:
            out_lines.append(f"=== {label} ({root}) ===\n[INFO] No Python files matched filters.\n")
    log_path = LOG_DIR / f"codex_scan_{UTC_NOW.strftime('%Y%m%dT%H%M%SZ')}.log"
    try:
        log_path.write_text("\n".join(out_lines), encoding="utf-8")
        log(f"[OK] Scan log written → {log_path}")
    except Exception as e:
        log(f"[WARN] could not write log: {e}")
    return log_path

HEADER_START = "<!-- CODEX_HTML_HEADER_START -->"
HEADER_END   = "<!-- CODEX_HTML_HEADER_END -->"
HTML_HEADER  = f"""\
{HEADER_START}
<div align="center">

<p align="center">
  <img src="https://img.shields.io/badge/%F0%9F%A4%96%20CodexDaemon-Autonomous%20Code%20Runner-6a0dad?style=for-the-badge&labelColor=1a1a1a" alt="CodexDaemon Badge"/>
</p>

<h1>🧠 CodexDaemon</h1>
<p><i>The AI-Driven Codebase That Codes Itself</i></p>

<p align="center">
  <img src="https://img.shields.io/badge/Mode-Lab%20%7C%20CI%20%7C%20Self--Healing-0ea5e9?style=for-the-badge&labelColor=1a1a1a" alt="Modes"/>
  <img src="https://img.shields.io/badge/Model-{MODEL.replace('-', '--')}-10b981?style=for-the-badge&labelColor=1a1a1a" alt="Model"/>
  <img src="https://img.shields.io/badge/Status-Online-brightgreen?style=for-the-badge&labelColor=1a1a1a" alt="Status"/>
</p>

</div>
{HEADER_END}
"""

def ensure_header(md: str) -> str:
    if HEADER_START in md and HEADER_END in md:
        return re.sub(rf"{re.escape(HEADER_START)}.*?{re.escape(HEADER_END)}",
                      HTML_HEADER, md, flags=re.DOTALL)
    return HTML_HEADER + "\n\n" + md.lstrip()

BADGE_RE = re.compile(r"!\[Last Neural Sync\]\([^)]+\)")
BADGE_MD = f"![Last Neural Sync](https://img.shields.io/badge/Last%20Neural%20Sync-{STAMP_URL}-purple?style=for-the-badge)"

REFLECT_MARK  = f"🧩 **CodexDaemon Log — {STAMP}**"
REFLECTION_TX = textwrap.dedent(ai_reflection()).strip()
REFLECT_BLOCK = "\n---\n" + REFLECT_MARK + "\n```text\n" + REFLECTION_TX + "\n```\n"

def update_badge(md: str) -> str:
    if BADGE_RE.search(md):
        return BADGE_RE.sub(BADGE_MD, md, count=1)
    if HEADER_END in md:
        idx = md.index(HEADER_END) + len(HEADER_END)
        return md[:idx] + "\n\n" + BADGE_MD + "\n\n" + md[idx:]
    return BADGE_MD + "\n\n" + md

def append_reflection(md: str) -> str:
    return md if REFLECT_MARK in md else md.rstrip() + REFLECT_BLOCK

def main() -> int:
    log("=== CodexDaemon v11.2: Dual-Repo Scan + HTML Restore START ===")
    log(f"Working directory: {THIS_FILE.parent}")
    run_scan()
    try:
        if not CODEX_README.exists():
            CODEX_README.write_text("", encoding="utf-8")
        md = CODEX_README.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        log(f"[FATAL] cannot read README: {e}")
        return 1
    md = ensure_header(md)
    md = update_badge(md)
    md = append_reflection(md)
    try:
        CODEX_README.write_text(md, encoding="utf-8")
        log(f"[OK] README updated → {CODEX_README}")
    except Exception as e:
        log(f"[FATAL] cannot write README: {e}")
        return 1
    log("=== CodexDaemon v11.2: Complete ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
