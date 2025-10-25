#!/usr/bin/env python3
"""
CodexDaemon v12.8 – Neon Cyber Card Edition
--------------------------------------------
• Scans target repos for .py files and line counts.
• Generates a reflective AI log with Electric-Blue (0ea5e9) neon HTML card.
• Updates README between <!--SYNC-START--> and <!--SYNC-END-->.
• Retains all HTML aesthetic (CodexDaemon Showcase Baseline).
"""

import os, re, json, datetime
from pathlib import Path
from typing import List, Dict, Tuple

# --- Configuration ------------------------------------------------------------
ROOT = Path("/Users/scottsteele/work").resolve()
CODEX_ROOT = ROOT / "CodexDaemon"
README_PATH = CODEX_ROOT / "README.md"
ENV_PATH = CODEX_ROOT / ".env"
LOG_DIR = Path.home() / ".codex" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

EXCLUDE = {".venv", "__pycache__", ".git", "backups", "logs", ".codex"}

# --- Load environment ---------------------------------------------------------
def load_env():
    try:
        from dotenv import load_dotenv
        load_dotenv(ENV_PATH)
        print(f"[OK] Loaded .env from {ENV_PATH}")
    except Exception:
        pass
load_env()

# --- OpenAI client (optional) -------------------------------------------------
def get_openai_client():
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=key)
    except Exception:
        return None
client = get_openai_client()

# --- Repo scan logic ----------------------------------------------------------
def should_skip(p: Path) -> bool:
    return any(part in EXCLUDE for part in p.parts)

def scan_repo(repo: Path) -> Tuple[int, int]:
    count, loc = 0, 0
    for file in repo.rglob("*.py"):
        if should_skip(file): 
            continue
        try:
            with file.open("r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            count += 1
            loc += len(lines)
        except Exception:
            continue
    return count, loc

def resolve_repos() -> List[Path]:
    raw = os.getenv("CODEX_REPOS_JSON", "").strip()
    if raw:
        try:
            paths = [Path(p).expanduser().resolve() for p in json.loads(raw)]
            return [p for p in paths if p.exists()]
        except Exception:
            pass
    defaults = [ROOT / "mad-scientist-code", ROOT / "CodexDaemon", ROOT / "priv"]
    return [r for r in defaults if r.exists()]

def aggregate_diagnostics(repos: List[Path]) -> Dict[str, Dict[str, int]]:
    return {r.name: dict(py_files=c, loc=l) for r in repos
            for c, l in [scan_repo(r)]}

# --- Reflection generation ----------------------------------------------------
def generate_reflection(ts: str, diag: Dict[str, Dict[str, int]]) -> str:
    context = " | ".join(f"{k}: {v['py_files']} files, {v['loc']} LOC"
                         for k, v in diag.items())
    prompt = (f"You are CodexDaemon, an analytical AI with a stoic tone. "
              f"Write a concise 3–4 line reflection on scanning {len(diag)} repos "
              f"({context}). End exactly with:\nNeural synchronization achieved at {ts}.")
    if client:
        try:
            r = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role":"user","content":prompt}],
                temperature=0.3,
                max_tokens=140)
            txt = r.choices[0].message.content.strip()
            if not txt.endswith(f"Neural synchronization achieved at {ts}."):
                txt += f"\nNeural synchronization achieved at {ts}."
            return txt
        except Exception:
            pass
    return (f"In analysis of {len(diag)} repositories — {context}. "
            f"All subsystems synchronized successfully.\n"
            f"Neural synchronization achieved at {ts}.")

# --- HTML rendering -----------------------------------------------------------
SYNC_START, SYNC_END = "<!--SYNC-START-->", "<!--SYNC-END-->"

def render_neon_block(ts: str, diag: Dict[str, Dict[str, int]], reflection: str) -> str:
    table_rows = "".join(
        f"<tr><td>{n}</td><td align='right'>{d['py_files']}</td>"
        f"<td align='right'>{d['loc']}</td></tr>"
        for n, d in diag.items()
    )
    html = f"""
{SYNC_START}
<div align="center" style="background:#0a0a0a;padding:20px;border-radius:16px;
border:1px solid #0ea5e9;box-shadow:0 0 10px #0ea5e9, inset 0 0 10px #0ea5e9;">
<h3 style="color:#0ea5e9;">🧩 Neural Diagnostics — {ts}</h3>
<table style="width:80%;border-collapse:collapse;color:#e2e2e2;font-family:monospace;">
<tr style="color:#0ea5e9;"><th align="left">Repository</th>
<th align="right">.py files</th><th align="right">LOC</th></tr>
{table_rows}
</table>
<pre style="text-align:left;color:#cfcfcf;background:#111;padding:15px;
border-radius:10px;border:1px solid #0ea5e9;box-shadow:inset 0 0 6px #0ea5e9;">
{reflection}
</pre>
</div>
{SYNC_END}
"""
    return html.strip()

def update_readme(ts: str, diag: Dict[str, Dict[str, int]], reflection: str):
    text = README_PATH.read_text(encoding="utf-8") if README_PATH.exists() else ""
    block = render_neon_block(ts, diag, reflection)
    if SYNC_START in text and SYNC_END in text:
        text = re.sub(f"{re.escape(SYNC_START)}.*?{re.escape(SYNC_END)}",
                      block, text, flags=re.DOTALL)
    else:
        text = text.rstrip() + "\n\n" + block
    README_PATH.write_text(text, encoding="utf-8")
    print(f"[OK] Updated README → {README_PATH}")

# --- Logging ------------------------------------------------------------------
def write_log(ts: str, diag: Dict[str, Dict[str, int]], reflection: str):
    log_path = LOG_DIR / f"codex_scan_{ts.replace(':','').replace('-','')}.log"
    content = [f"Timestamp: {ts}",
               *(f"{k}: {v['py_files']} files, {v['loc']} LOC" for k, v in diag.items()),
               "", reflection]
    log_path.write_text("\n".join(content), encoding="utf-8")
    print(f"[OK] Log saved → {log_path}")

# --- Main ---------------------------------------------------------------------
def main():
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ")
    print(f"[{ts}] Starting CodexDaemon v12.8 scan")
    repos = resolve_repos()
    diag = aggregate_diagnostics(repos)
    reflection = generate_reflection(ts, diag)
    update_readme(ts, diag, reflection)
    write_log(ts, diag, reflection)
    print("[COMPLETE] CodexDaemon v12.8 — Neon Cyber Card")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import sys
        print(f"[FATAL] {e}", file=sys.stderr)
        sys.exit(1)
