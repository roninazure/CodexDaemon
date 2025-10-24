#!/usr/bin/env python3
"""
CodexDaemon v12.7 — Showcase Polished
-------------------------------------
✅ Single clean OpenAI logo beside title
✅ Purges all duplicate SYNC blocks
✅ Replaces {ts} placeholder with actual timestamp
✅ Maintains original HTML aesthetics (no broken images)
✅ Adds reflection trimming + readability polish
"""

import os, re, json, datetime, sys
from pathlib import Path
from typing import List, Dict, Tuple

ROOT = Path("/Users/scottsteele/work").resolve()
CODEX = ROOT / "CodexDaemon"
README = CODEX / "README.md"
ENV = CODEX / ".env"
LOG_DIR = Path.home() / ".codex" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

SYNC_START, SYNC_END = "<!--SYNC-START-->", "<!--SYNC-END-->"
BADGE_RE = re.compile(r"!\[Last Neural Sync\]\([^)]+\)")
HEADER_START, HEADER_END = "<!-- CODEX_HTML_HEADER_START -->", "<!-- CODEX_HTML_HEADER_END -->"

OPENAI_LOGO = (
    '<img src="https://img.shields.io/badge/OpenAI-•-black?logo=openai'
    '&logoColor=white&style=for-the-badge&labelColor=1a1a1a" alt="OpenAI"/>'
)

def load_env(p: Path):
    try:
        from dotenv import load_dotenv
        load_dotenv(p)
        print(f"[OK] Loaded .env from {p}")
    except Exception:
        pass

def init_openai():
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=key)
    except Exception:
        return None

def repos() -> list[Path]:
    defaults = [ROOT / "mad-scientist-code", ROOT / "CodexDaemon", ROOT / "priv"]
    return [r for r in defaults if r.exists()]

def scan(repo: Path) -> Tuple[int, int]:
    files = loc = 0
    for p in repo.rglob("*.py"):
        if any(ex in p.parts for ex in {".venv", ".git", "__pycache__", ".codex"}):
            continue
        try:
            with p.open("r", encoding="utf-8", errors="ignore") as f:
                loc += sum(1 for _ in f)
            files += 1
        except Exception:
            continue
    return files, loc

def diag(repos) -> Dict[str, Dict[str, int]]:
    return {r.name: {"py_files": *scan(r)} for r in repos}

def reflection(ts: str, d: Dict[str, Dict[str, int]], client):
    ctx = "\n".join(f"- {k}: {v['py_files']} files, {v['loc']} LOC" for k, v in d.items())
    prompt = (
        "You are CodexDaemon, an analytical AI system. "
        "Write a brief (3-5 line) technical reflection—stoic tone, factual, no poetry. "
        f"End with: 'Neural synchronization achieved at {ts}.'\n\n{ctx}"
    )
    if client:
        try:
            resp = client.chat.completions.create(
                model=os.getenv("CODEX_MODEL", "gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=150,
            )
            text = resp.choices[0].message.content.strip()
            if "{ts}" in text:
                text = text.replace("{ts}", ts)
            if not text.endswith(f"Neural synchronization achieved at {ts}."):
                text += f"\nNeural synchronization achieved at {ts}."
            return text
        except Exception:
            pass
    return (
        "System audit completed successfully.\n"
        + " | ".join(f"{k}: {v['py_files']} files, {v['loc']} LOC" for k, v in d.items())
        + f"\nNeural synchronization achieved at {ts}."
    )

def badge(ts: str) -> str:
    return f"![Last Neural Sync](https://img.shields.io/badge/Last%20Neural%20Sync-{ts}-purple?style=for-the-badge)"

def sync_block(ts: str, d: Dict[str, Dict[str, int]], ref: str) -> str:
    lines = [
        SYNC_START,
        f"### Neural Diagnostics — {ts}",
        "",
        "| Repository | .py files | LOC |",
        "|:--|--:|--:|",
        *[f"| {k} | {v['py_files']} | {v['loc']} |" for k, v in d.items()],
        "",
        "#### Reflection",
        "```text",
        ref.strip(),
        "```",
        SYNC_END,
        "",
    ]
    return "\n".join(lines)

def clean_header(txt: str) -> str:
    if HEADER_START not in txt or HEADER_END not in txt:
        return txt
    s, e = txt.find(HEADER_START), txt.find(HEADER_END)
    header = txt[s:e+len(HEADER_END)]
    header = re.sub(r'<img[^>]+OpenAI[^>]*>', "", header)
    header = re.sub(r'<img[^>]+src="[^"]+\?"[^>]*>', "", header)
    header = header.replace("</h1>", f" {OPENAI_LOGO}</h1>")
    return txt[:s] + header + txt[e+len(HEADER_END):]

def update_readme(ts: str, d: Dict[str, Dict[str, int]], ref: str, path: Path):
    txt = path.read_text(encoding="utf-8") if path.exists() else "# CodexDaemon\n\n"
    txt = BADGE_RE.sub(badge(ts), txt, count=1) if BADGE_RE.search(txt) else badge(ts) + "\n\n" + txt
    txt = clean_header(txt)
    block = sync_block(ts, d, ref)
    txt = re.sub(rf"{re.escape(SYNC_START)}.*?{re.escape(SYNC_END)}", "", txt, flags=re.S)
    txt += "\n\n" + block
    path.write_text(txt, encoding="utf-8")

def write_log(ts: str, d: Dict[str, Dict[str, int]], ref: str):
    f = LOG_DIR / f"codex_scan_{ts.replace(':','').replace('-','')}.log"
    f.write_text(
        f"Timestamp: {ts}\n\n"
        + "\n".join(f"{k}: {v['py_files']} files, {v['loc']} LOC" for k, v in d.items())
        + f"\n\nReflection:\n{ref}\n",
        encoding="utf-8",
    )
    return f

def main():
    load_env(ENV)
    client = init_openai()
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ")
    r = repos()
    d = {p.name: {"py_files": scan(p)[0], "loc": scan(p)[1]} for p in r}
    ref = reflection(ts, d, client)
    update_readme(ts, d, ref, README)
    log = write_log(ts, d, ref)
    print(f"[OK] Updated README → {README}")
    print(f"[OK] Log saved → {log}")
    print("[COMPLETE] CodexDaemon v12.7 Showcase Polished")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[FATAL] {e}", file=sys.stderr)
        sys.exit(1)
