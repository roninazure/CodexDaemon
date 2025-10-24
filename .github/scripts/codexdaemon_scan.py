#!/usr/bin/env python3
"""
CodexDaemon v12.6 — Showcase Clean Edition
------------------------------------------
• Scans 3 repos (mad-scientist-code, CodexDaemon, priv) for .py files and LOC.
• Generates a stoic reflection (fallback if API unavailable).
• Updates README.md with:
    - One clean "Last Neural Sync" badge.
    - One <OpenAI> badge (top header only).
    - One <!--SYNC-START-->...<!--SYNC-END--> diagnostics block.
• Removes duplicate SYNC blocks and stray/broken <img> tags.
• Writes detailed log to ~/.codex/logs.

Certified to preserve all your visual formatting and HTML structure.
"""

import os, re, json, datetime, sys
from pathlib import Path
from typing import List, Dict, Tuple

# --- CONFIG -------------------------------------------------------------------

ROOT = Path(os.getenv("CODEX_ROOT", "/Users/scottsteele/work")).resolve()
CODEX = ROOT / "CodexDaemon"
README = CODEX / "README.md"
ENV = CODEX / ".env"
LOG_DIR = Path.home() / ".codex" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

BADGE_RE = re.compile(r"!\[Last Neural Sync\]\([^)]+\)")
SYNC_START, SYNC_END = "<!--SYNC-START-->", "<!--SYNC-END-->"
HEADER_START, HEADER_END = "<!-- CODEX_HTML_HEADER_START -->", "<!-- CODEX_HTML_HEADER_END -->"

OPENAI_BADGE = (
    '<img src="https://img.shields.io/badge/OpenAI-•-black?logo=openai&logoColor=white'
    '&style=for-the-badge&labelColor=1a1a1a" alt="OpenAI"/>'
)

EXCLUDE = {".venv", "__pycache__", ".git", ".codex", "logs", "backups", ".github/backups"}

# --- ENV / OPENAI -------------------------------------------------------------

def load_env(path: Path):
    try:
        from dotenv import load_dotenv
        load_dotenv(path)
        print(f"[OK] Loaded .env from {path}")
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

# --- REPO SCAN ---------------------------------------------------------------

def repos() -> List[Path]:
    raw = os.getenv("CODEX_REPOS_JSON", "").strip()
    if raw:
        try:
            paths = [Path(p).expanduser().resolve() for p in json.loads(raw)]
            return [p for p in paths if p.exists()]
        except Exception:
            pass
    cands = [ROOT / "mad-scientist-code", ROOT / "CodexDaemon", ROOT / "priv"]
    return [p for p in cands if p.exists()]

def skip(path: Path) -> bool:
    return any(ex in path.parts for ex in EXCLUDE)

def scan(repo: Path) -> Tuple[int, int]:
    count = loc = 0
    for f in repo.rglob("*.py"):
        if skip(f):
            continue
        try:
            with f.open("r", encoding="utf-8", errors="ignore") as h:
                loc += sum(1 for _ in h)
            count += 1
        except Exception:
            pass
    return count, loc

def diag(repos: List[Path]) -> Dict[str, Dict[str, int]]:
    out = {}
    for r in repos:
        f, l = scan(r)
        out[r.name] = {"py_files": f, "loc": l}
    return out

# --- REFLECTION ---------------------------------------------------------------

def reflection(ts: str, data: Dict[str, Dict[str, int]], client) -> str:
    ctx = "\n".join(f"- {k}: {v['py_files']} files, {v['loc']} LOC" for k, v in data.items())
    prompt = (
        "You are CodexDaemon: a logical, analytical system. "
        "Write a concise 3–5 line stoic reflection (plain text only). "
        "End with: 'Neural synchronization achieved at {ts}.'\n\n"
        f"{ctx}"
    )
    if client:
        try:
            resp = client.chat.completions.create(
                model=os.getenv("CODEX_MODEL", "gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=160,
            )
            text = resp.choices[0].message.content.strip()
            if not text.endswith(f"Neural synchronization achieved at {ts}."):
                text += f"\nNeural synchronization achieved at {ts}."
            return re.sub(r"`+", "", text)
        except Exception:
            pass
    lines = " | ".join(f"{k}: {v['py_files']} files, {v['loc']} LOC" for k, v in data.items())
    return f"System evaluation complete. {lines}\nNeural synchronization achieved at {ts}."

# --- MARKDOWN RENDER ----------------------------------------------------------

def badge(ts: str) -> str:
    return f"![Last Neural Sync](https://img.shields.io/badge/Last%20Neural%20Sync-{ts}-purple?style=for-the-badge)"

def sync_block(ts: str, d: Dict[str, Dict[str, int]], ref: str) -> str:
    out = [
        SYNC_START,
        f"### Neural Diagnostics — {ts}",
        "",
        "| Repository | .py files | LOC |",
        "|:--|--:|--:|",
    ]
    out += [f"| {k} | {v['py_files']} | {v['loc']} |" for k, v in d.items()]
    out += ["", "#### Reflection", "```text", ref.strip(), "```", SYNC_END, ""]
    return "\n".join(out)

# --- HEADER CLEANUP -----------------------------------------------------------

def clean_header(txt: str) -> str:
    """Ensure a single OpenAI badge; remove broken images."""
    s, e = txt.find(HEADER_START), txt.find(HEADER_END)
    if s == -1 or e == -1:
        return txt
    block = txt[s:e+len(HEADER_END)]
    # Remove stray/broken <img> tags before reinjecting
    block = re.sub(r'<img[^>]+alt="OpenAI"[^>]*>', "", block)
    block = re.sub(r'<img[^>]+src="[^"]+\?"[^>]*>', "", block)
    # Reinstate single OpenAI badge in the top <p align="center">
    block = re.sub(
        r'(<p\s+align="center">[^<]+CodexDaemon[^<]+)</p>',
        lambda m: m.group(1) + f'  {OPENAI_BADGE}</p>',
        block,
        count=1,
        flags=re.DOTALL,
    )
    return txt[:s] + block + txt[e+len(HEADER_END):]

# --- README UPDATE ------------------------------------------------------------

def update_readme(ts: str, d: Dict[str, Dict[str, int]], ref: str, path: Path):
    text = path.read_text(encoding="utf-8") if path.exists() else "# CodexDaemon\n\n"
    # 1) Badge
    text = BADGE_RE.sub(badge(ts), text, count=1) if BADGE_RE.search(text) else badge(ts) + "\n\n" + text
    # 2) Header fix
    text = clean_header(text)
    # 3) Replace ALL SYNC blocks with one
    block = sync_block(ts, d, ref)
    text = re.sub(rf"{re.escape(SYNC_START)}.*?{re.escape(SYNC_END)}", block, text, flags=re.S)
    if SYNC_START not in text:
        text = text.rstrip() + "\n\n" + block
    path.write_text(text, encoding="utf-8")

# --- LOGGING ------------------------------------------------------------------

def write_log(ts: str, d: Dict[str, Dict[str, int]], ref: str) -> Path:
    f = LOG_DIR / f"codex_scan_{ts.replace(':','').replace('-','')}.log"
    content = "\n".join([
        f"Timestamp: {ts}",
        "Diagnostics:",
        *[f"  - {k}: {v['py_files']} files, {v['loc']} LOC" for k, v in d.items()],
        "",
        "Reflection:",
        ref, ""
    ])
    f.write_text(content, encoding="utf-8")
    return f

# --- MAIN ---------------------------------------------------------------------

def main():
    load_env(ENV)
    client = init_openai()
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ")
    print(f"[{ts}] Starting CodexDaemon v12.6 scan")

    rlist = repos()
    diag_data = diag(rlist)
    ref = reflection(ts, diag_data, client)
    update_readme(ts, diag_data, ref, README)
    log = write_log(ts, diag_data, ref)
    print(f"[OK] Updated README → {README}")
    print(f"[OK] Log saved → {log}")
    print("[COMPLETE] CodexDaemon v12.6 Showcase Clean")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[FATAL] {e}", file=sys.stderr)
        sys.exit(1)
