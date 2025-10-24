#!/usr/bin/env python3
"""
CodexDaemon v12.5 — Showcase Edition (Certified)
------------------------------------------------
• Scans 3 repos (mad-scientist-code, CodexDaemon, priv) for .py files.
• Computes concise diagnostics (file count, LOC).
• Generates a stoic AI reflection (fallback if API unavailable).
• Updates CodexDaemon/README.md:
    - Pure-Markdown "Last Neural Sync" badge (GitHub-safe).
    - Replaces *all* <!--SYNC-START-->…<!--SYNC-END--> blocks with one clean block.
    - Preserves your HTML header and inserts an OpenAI logo badge next to the Model badge (idempotent).
• Writes a compact log to ~/.codex/logs/.

ENV (optional, auto-loaded from /Users/scottsteele/work/CodexDaemon/.env):
    OPENAI_API_KEY=...
    CODEX_MODEL=gpt-4o-mini
    CODEX_ROOT=/Users/scottsteele/work
    CODEX_REPOS_JSON=["/path/one","/path/two",...]
"""

import os, re, json, datetime, sys
from pathlib import Path
from typing import List, Dict, Tuple

# ---------- Configuration ------------------------------------------------------

DEFAULT_ROOT = Path(os.getenv("CODEX_ROOT", "/Users/scottsteele/work")).resolve()
CODEXDAEMON_ROOT = DEFAULT_ROOT / "CodexDaemon"
ENV_PATH = CODEXDAEMON_ROOT / ".env"
README_PATH = CODEXDAEMON_ROOT / "README.md"

LOG_DIR = Path.home() / ".codex" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

BADGE_RE = re.compile(r"!\[Last Neural Sync\]\([^)]+\)")
SYNC_START = "<!--SYNC-START-->"
SYNC_END = "<!--SYNC-END-->"
HEADER_START = "<!-- CODEX_HTML_HEADER_START -->"
HEADER_END = "<!-- CODEX_HTML_HEADER_END -->"

OPENAI_LOGO_BADGE = (
    '<img src="https://img.shields.io/badge/OpenAI-•-black?logo=openai&logoColor=white'
    '&style=for-the-badge&labelColor=1a1a1a" alt="OpenAI"/>'
)

EXCLUDE_PARTS = {
    ".venv", "__pycache__", ".git", ".codex", "backups", ".github/backups", "logs"
}

# ---------- Utilities ----------------------------------------------------------

def log(msg: str):
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{ts}] {msg}")

def load_env(dotenv_path: Path):
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path)
        log(f"Loaded environment from: {dotenv_path}")
    except Exception:
        # .env optional
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

def resolve_repos() -> List[Path]:
    raw = os.getenv("CODEX_REPOS_JSON", "").strip()
    if raw:
        try:
            paths = [Path(p).expanduser().resolve() for p in json.loads(raw)]
            repos = [p for p in paths if p.exists()]
            if repos:
                return repos
        except Exception:
            pass
    candidates = [
        DEFAULT_ROOT / "mad-scientist-code",
        DEFAULT_ROOT / "CodexDaemon",
        DEFAULT_ROOT / "priv",
    ]
    return [p for p in candidates if p.exists()]

def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    return any(ex in parts for ex in EXCLUDE_PARTS)

def scan_repo(repo: Path) -> Tuple[int, int]:
    py_count, loc = 0, 0
    for p in repo.rglob("*.py"):
        if should_skip(p):
            continue
        try:
            with p.open("r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            py_count += 1
            loc += len(lines)
        except Exception:
            continue
    return py_count, loc

def aggregate_diagnostics(repos: List[Path]) -> Dict[str, Dict[str, int]]:
    out: Dict[str, Dict[str, int]] = {}
    for r in repos:
        files, lines = scan_repo(r)
        out[r.name] = {"py_files": files, "loc": lines}
    return out

# ---------- Content renderers --------------------------------------------------

def render_badge(ts: str) -> str:
    # Pure Markdown shields badge — safe in both themes.
    return f"![Last Neural Sync](https://img.shields.io/badge/Last%20Neural%20Sync-{ts}-purple?style=for-the-badge)"

def render_block(ts: str, diag: Dict[str, Dict[str, int]], reflection: str) -> str:
    # Single deterministic block to prevent duplication.
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
        reflection.strip(),
        "```",
        SYNC_END,
        "",
    ]
    return "\n".join(lines)

# ---------- Header manipulation ------------------------------------------------

def ensure_openai_badge_in_header(readme_text: str) -> str:
    """
    Within CODEX_HTML_HEADER block, ensure a single OpenAI logo badge is present
    alongside the Model badge paragraph. Idempotent and preserves existing HTML.
    """
    start_idx = readme_text.find(HEADER_START)
    end_idx = readme_text.find(HEADER_END)
    if start_idx == -1 or end_idx == -1 or end_idx <= start_idx:
        return readme_text  # No header markers — do nothing.

    header_block = readme_text[start_idx:end_idx + len(HEADER_END)]

    # Already present?
    if "logo=openai" in header_block:
        return readme_text

    # Try to insert before the closing </p> of the badges line
    # We specifically look for the <p align="center"> that contains the Model badge.
    pattern = re.compile(
        r'(<p\s+align="center">\s*.*?Model-.*?</p>)',
        flags=re.DOTALL | re.IGNORECASE,
    )

    def _inject(match: re.Match) -> str:
        segment = match.group(1)
        if "logo=openai" in segment:
            return segment  # safety
        # Insert the OpenAI badge right before closing </p>, separated by space.
        return segment.replace("</p>", f"  {OPENAI_LOGO_BADGE}\n</p>")

    new_header_block, n = pattern.subn(_inject, header_block, count=1)
    if n == 0:
        # Fallback: append logo at the very end of the first <p align="center"> in header.
        fallback_pat = re.compile(r'(<p\s+align="center">.*?</p>)', re.DOTALL | re.IGNORECASE)
        new_header_block, n2 = fallback_pat.subn(
            lambda m: m.group(1).replace("</p>", f"  {OPENAI_LOGO_BADGE}\n</p>"),
            header_block,
            count=1,
        )
        if n2 == 0:
            return readme_text  # Give up silently to avoid damaging header.

    return readme_text[:start_idx] + new_header_block + readme_text[end_idx + len(HEADER_END):]

# ---------- AI reflection ------------------------------------------------------

def generate_reflection(ts: str, diag: Dict[str, Dict[str, int]], client) -> str:
    # Compose concise diagnostic context
    context = "Diagnostics:\n" + "\n".join(
        f"- {name}: {data['py_files']} files, {data['loc']} LOC"
        for name, data in diag.items()
    )
    prompt = (
        "You are CodexDaemon: a disciplined, analytical system. "
        "Write a concise, stoic reflection (3–5 lines, plain text, no emojis, no HTML). "
        "End with the exact line:\n"
        f"Neural synchronization achieved at {ts}.\n\n"
        f"{context}"
    )

    if client:
        try:
            model = os.getenv("CODEX_MODEL", "gpt-4o-mini")
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=160,
            )
            text = resp.choices[0].message.content.strip()
            if not text.endswith(f"Neural synchronization achieved at {ts}."):
                text += f"\nNeural synchronization achieved at {ts}."
            # Normalize any accidental fenced code inside to plain text
            text = re.sub(r"```+.*?```+", lambda m: m.group(0).replace("`", ""), text, flags=re.DOTALL)
            return text
        except Exception:
            pass

    # Fallback reflection
    lines = []
    for name, data in diag.items():
        lines.append(f"{name}: {data['py_files']} files, {data['loc']} LOC")
    body = " | ".join(lines) if lines else "No repositories detected."
    return (
        "System evaluation complete. No integrity drift detected.\n"
        f"{body}\n"
        f"Neural synchronization achieved at {ts}."
    )

# ---------- README update ------------------------------------------------------

def update_readme(ts: str, diag: Dict[str, Dict[str, int]], reflection: str, readme_path: Path):
    text = readme_path.read_text(encoding="utf-8") if readme_path.exists() else "# CodexDaemon\n\n"

    # 1) Update or inject the Last Neural Sync badge
    badge = render_badge(ts)
    if BADGE_RE.search(text):
        text = BADGE_RE.sub(badge, text, count=1)
    else:
        # Prefer to place after the H1 if present; else at very top.
        m = re.search(r"^# .*$", text, flags=re.MULTILINE)
        if m:
            idx = m.end()
            text = text[:idx] + "\n\n" + badge + "\n\n" + text[idx:]
        else:
            text = badge + "\n\n" + text

    # 2) Ensure a single OpenAI logo badge in the HTML header (idempotent)
    text = ensure_openai_badge_in_header(text)

    # 3) Replace ALL existing SYNC blocks with a single fresh one
    block = render_block(ts, diag, reflection)
    sync_re = re.compile(
        re.escape(SYNC_START) + r".*?" + re.escape(SYNC_END),
        flags=re.DOTALL,
    )
    if sync_re.search(text):
        text = sync_re.sub(block, text)  # Replace all occurrences
    else:
        text = text.rstrip() + "\n\n" + block

    readme_path.write_text(text, encoding="utf-8")

# ---------- Logging ------------------------------------------------------------

def write_log(ts: str, diag: Dict[str, Dict[str, int]], reflection: str, log_dir: Path) -> Path:
    safe_ts = ts.replace(":", "").replace("-", "")
    log_path = log_dir / f"codex_scan_{safe_ts}.log"
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

# ---------- Main ---------------------------------------------------------------

def main():
    load_env(ENV_PATH)
    client = init_openai()

    ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ")
    log(f"Working directory: {Path.cwd()}")

    repos = resolve_repos()
    if not repos:
        log("WARN: No target repositories found.")
    for r in repos:
        log(f"Scanning repository: {r.name}")

    diag = aggregate_diagnostics(repos)
    reflection = generate_reflection(ts, diag, client)
    update_readme(ts, diag, reflection, README_PATH)
    log_file = write_log(ts, diag, reflection, LOG_DIR)

    log(f"OK: Scan log written → {log_file}")
    log(f"OK: README updated → {README_PATH}")
    log("=== CodexDaemon v12.5: Complete ===")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[FATAL] {e}", file=sys.stderr)
        sys.exit(1)
