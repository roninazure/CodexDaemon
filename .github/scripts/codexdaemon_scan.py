#!/usr/bin/env python3
"""
CodexDaemon v12 – Analytical/Stoic Mode
---------------------------------------
• Scans 3 repos (mad-scientist-code, CodexDaemon, priv) for .py files.
• Computes concise diagnostics (file count, LOC).
• Generates a stoic AI reflection (or fallback if API unavailable).
• Updates CodexDaemon/README.md:
    - Pure-Markdown "Last Neural Sync" badge (GitHub-safe).
    - Replaces a single diagnostics+reflection block between markers:
        <!--SYNC-START--> ... <!--SYNC-END-->
• Writes a compact log to ~/.codex/logs/.
• No duplicate reflections. No HTML color edge cases.

Optional .env (loaded from /Users/scottsteele/work/CodexDaemon/.env):
    OPENAI_API_KEY=...
    CODEX_REPOS_JSON=["/path/one","/path/two",...]
"""

import os, sys, re, json, datetime
from pathlib import Path
from typing import List, Dict, Tuple

# --- Configuration defaults ----------------------------------------------------
CODEx_ROOT = Path("/Users/scottsteele/work").resolve()
CODEXDAEMON_ROOT = CODEx_ROOT / "CodexDaemon"
ENV_PATH = CODEXDAEMON_ROOT / ".env"
README_PATH = CODEXDAEMON_ROOT / "README.md"
LOG_DIR = Path.home() / ".codex" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# --- Load .env (silent if missing) --------------------------------------------
def load_env(dotenv_path: Path):
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path)
        print(f"[OK] Loaded environment from: {dotenv_path}")
    except Exception:
        pass

load_env(ENV_PATH)

# --- OpenAI client (optional) -------------------------------------------------
def init_openai():
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=key)
    except Exception:
        return None

client = init_openai()

# --- Repo resolution -----------------------------------------------------------
def resolve_repos() -> List[Path]:
    # 1) Allow override via JSON env
    raw = os.getenv("CODEX_REPOS_JSON", "").strip()
    if raw:
        try:
            paths = [Path(p).expanduser().resolve() for p in json.loads(raw)]
            return [p for p in paths if p.exists()]
        except Exception:
            pass
    # 2) Default triple
    candidates = [
        CODEx_ROOT / "mad-scientist-code",
        CODEx_ROOT / "CodexDaemon",
        CODEx_ROOT / "priv",
    ]
    return [p for p in candidates if p.exists()]

EXCLUDE_PARTS = {".venv", "__pycache__", ".git", ".github/backups", ".codex", "logs", "backups"}

def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    return any(ex in parts for ex in EXCLUDE_PARTS)

def scan_repo(repo: Path) -> Tuple[int, int]:
    """Return (py_files_count, total_lines)."""
    py_count = 0
    loc = 0
    for p in repo.rglob("*.py"):
        if should_skip(p):
            continue
        try:
            with p.open("r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            py_count += 1
            loc += len(lines)
        except Exception:
            # ignore unreadable files safely
            continue
    return py_count, loc

def aggregate_diagnostics(repos: List[Path]) -> Dict[str, Dict[str, int]]:
    out: Dict[str, Dict[str, int]] = {}
    for r in repos:
        files, lines = scan_repo(r)
        out[r.name] = {"py_files": files, "loc": lines}
    return out

# --- AI reflection (stoic) ----------------------------------------------------
def generate_reflection(ts: str, diag: Dict[str, Dict[str, int]]) -> str:
    # Compose a compact, machine-like context for the model
    context = "Diagnostics:\n" + "\n".join(
        f"- {name}: {data['py_files']} files, {data['loc']} LOC"
        for name, data in diag.items()
    )
    prompt = (
        "You are CodexDaemon: a disciplined, analytical system. "
        "Write a concise, stoic reflection (3–5 lines, plain text). "
        "Avoid hype, metaphors minimal, no emojis, no HTML. "
        "Conclude with the exact line:\n"
        f"Neural synchronization achieved at {ts}.\n\n"
        f"{context}"
    )

    if client:
        try:
            resp = client.chat.completions.create(
                model=os.getenv("CODEX_MODEL", "gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=140,
            )
            text = resp.choices[0].message.content.strip()
            # Enforce final line guarantee
            if not text.endswith(f"Neural synchronization achieved at {ts}."):
                text += f"\nNeural synchronization achieved at {ts}."
            return text
        except Exception:
            pass

    # Fallback reflection if API is unavailable
    lines = []
    for name, data in diag.items():
        lines.append(f"{name}: {data['py_files']} files, {data['loc']} LOC")
    body = " | ".join(lines) if lines else "No repositories detected."
    return (
        "System evaluation complete. No integrity drift detected.\n"
        f"{body}\n"
        f"Neural synchronization achieved at {ts}."
    )

# --- README update helpers -----------------------------------------------------
BADGE_RE = re.compile(r"!\[Last Neural Sync\]\([^)]+\)")
SYNC_START = "<!--SYNC-START-->"
SYNC_END = "<!--SYNC-END-->"

def render_badge(ts: str) -> str:
    # Pure Markdown shields badge (no HTML colors, safe in dark/light modes)
    return f"![Last Neural Sync](https://img.shields.io/badge/Last%20Neural%20Sync-{ts}-purple?style=for-the-badge)"

def render_block(ts: str, diag: Dict[str, Dict[str, int]], reflection: str) -> str:
    # Single deterministic block to prevent duplication
    lines = [
        SYNC_START,
        f"### Neural Diagnostics — {ts}",
        "",
        "| Repository | .py files | LOC |",
        "|:--|--:|--:|",
    ]
    for name, data in diag.items():
        lines.append(f"| {name} | {data['py_files']} | {data['loc']} |")
    lines += [
        "",
        "#### Reflection",
        "```text",
        reflection,
        "```",
        SYNC_END,
        "",
    ]
    return "\n".join(lines)

def update_readme(ts: str, diag: Dict[str, Dict[str, int]], reflection: str, readme_path: Path):
    text = ""
    if readme_path.exists():
        text = readme_path.read_text(encoding="utf-8")
    else:
        text = "# CodexDaemon\n\n"

    # 1) Badge insert/replace
    badge = render_badge(ts)
    if BADGE_RE.search(text):
        text = BADGE_RE.sub(badge, text, count=1)
    else:
        # Insert after H1 if present, else at top
        m = re.search(r"^# .*$", text, flags=re.MULTILINE)
        if m:
            idx = m.end()
            text = text[:idx] + "\n\n" + badge + "\n\n" + text[idx:]
        else:
            text = badge + "\n\n" + text

    # 2) Replace the entire diagnostics block between markers (if any)
    block = render_block(ts, diag, reflection)
    if SYNC_START in text and SYNC_END in text:
        text = re.sub(
            rf"{re.escape(SYNC_START)}.*?{re.escape(SYNC_END)}",
            block,
            text,
            flags=re.DOTALL,
        )
    else:
        # Append to end with a preceding separator
        text = text.rstrip() + "\n\n" + block

    readme_path.write_text(text, encoding="utf-8")

# --- Logging -------------------------------------------------------------------
def write_log(ts: str, diag: Dict[str, Dict[str, int]], reflection: str, log_dir: Path):
    log_path = log_dir / f"codex_scan_{ts.replace(':','').replace('-','').replace('T','T')}.log"
    lines = [
        f"Timestamp: {ts}",
        "Diagnostics:",
        *[f"  - {k}: {v['py_files']} files, {v['loc']} LOC" for k, v in diag.items()],
        "",
        "Reflection:",
        reflection,
        "",
    ]
    log_path.write_text("\n".join(lines), encoding="utf-8")
    return log_path

# --- Main ----------------------------------------------------------------------
def main():
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ")
    print(f"[{ts}] Working directory: {Path.cwd()}")

    repos = resolve_repos()
    if not repos:
        print("[WARN] No target repositories found.")
    for r in repos:
        print(f"[{ts}] Scanning repository: {r.name}")

    diag = aggregate_diagnostics(repos)
    reflection = generate_reflection(ts, diag)
    update_readme(ts, diag, reflection, README_PATH)
    log_file = write_log(ts, diag, reflection, LOG_DIR)

    print(f"[OK] Scan log written → {log_file}")
    print(f"[OK] README updated → {README_PATH}")
    print("[OK] CodexDaemon v12: Complete")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[FATAL] {e}", file=sys.stderr)
        sys.exit(1)
