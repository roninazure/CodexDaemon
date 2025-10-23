#!/usr/bin/env python3
"""
codexdaemon_scan.py — Phase 8.5 “Full Neural Sync: Autonomous Commit + Push”

Functions:
  • Dual-core AI code scan across CodexDaemon / Mad-Scientist-Code / Priv
  • Writes results to ~/.codex/logs/
  • Updates Neural Sync badge in README.md
  • Appends AI reflection (multi-line safe via <br>)
  • Auto-commits and pushes updates to GitHub
"""

import os, datetime, traceback, subprocess
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# ---------------------------------------------------------------------
# 🔧 Setup
# ---------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
LOG_ROOT = Path.home() / ".codex" / "logs"
LOG_ROOT.mkdir(parents=True, exist_ok=True)

def log(msg: str):
    ts = datetime.datetime.utcnow().strftime("[%Y-%m-%dT%H:%M:%SZ]")
    print(f"{ts} {msg}")

# ---------------------------------------------------------------------
# 🌍 Environment
# ---------------------------------------------------------------------
env_candidates = [
    REPO_ROOT / ".env",
    Path("/Users/scottsteele/work/mad-scientist-code/.env"),
    Path("/Users/scottsteele/work/CodexDaemon/.env"),
]
for path in env_candidates:
    if path.exists():
        load_dotenv(path)
        log(f"[OK] Loaded environment from: {path}")
        break
else:
    log("[WARN] No .env file found; attempting defaults")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("CODEX_MODEL", "gpt-4o-mini")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# ---------------------------------------------------------------------
# 📁 Repo map
# ---------------------------------------------------------------------
REPOS = {
    "mad-scientist-code": Path("/Users/scottsteele/work/mad-scientist-code"),
    "CodexDaemon": Path("/Users/scottsteele/work/CodexDaemon"),
    "priv": Path("/Users/scottsteele/work/priv"),
}

def collect_python_files(root: Path):
    for p in root.rglob("*.py"):
        if any(ex in p.parts for ex in [".venv", "__pycache__", "logs", "backups"]):
            continue
        yield p

def summarize_file(path: Path):
    try:
        content = path.read_text(encoding="utf-8")[:2000]
    except Exception as e:
        return f"[ERROR reading {path.name}: {e}]"
    if not client:
        return f"[OFFLINE] AI summary unavailable for {path.name}"
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are CodexDaemon, an autonomous code auditor."},
                {"role": "user", "content": f"Summarize and suggest one optimization:\n\n{content}"}
            ],
            temperature=0.4,
            max_tokens=250,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"[WARN] AI analysis failed for {path.name}: {e}"

# ---------------------------------------------------------------------
# 🧠 Dual-core scan
# ---------------------------------------------------------------------
def run_dual_core_scan():
    log("=== Phase 8.5 Dual-Core Scan START ===")
    results = {}
    for repo, path in REPOS.items():
        if not path.exists():
            log(f"[SKIP] {path} — missing")
            continue
        log(f"Scanning repository: {repo}")
        for f in collect_python_files(path):
            rel = f.relative_to(Path("/Users/scottsteele/work"))
            log(f"Analyzing: {rel}")
            results[str(rel)] = summarize_file(f)

    out = LOG_ROOT / f"codex_scan_{datetime.datetime.utcnow():%Y%m%dT%H%M%SZ}.log"
    with open(out, "w", encoding="utf-8") as fh:
        for k, v in results.items():
            fh.write(f"\n=== {k} ===\n{v}\n")
    log(f"[OK] Scan log written → {out}")
    return out

# ---------------------------------------------------------------------
# 🪞 Neural Sync badge
# ---------------------------------------------------------------------
def update_neural_sync_badge(readme_path: Path):
    try:
        content = readme_path.read_text(encoding="utf-8")
        now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ")
        badge_html = (
            f'<p align="center">\n'
            f'  <img src="https://img.shields.io/badge/🧠_Last_Neural_Sync-{now}-purple?style=for-the-badge&labelColor=1a1a1a&color=7e22ce" '
            f'alt="Last Neural Sync"/>\n'
            f'</p>\n'
        )
        if "🧠_Last_Neural_Sync" in content:
            import re
            content = re.sub(
                r'<img src="https://img\.shields\.io/badge/🧠_Last_Neural_Sync-[^"]+"[^>]+>',
                badge_html.strip(), content)
        else:
            lines = content.splitlines()
            for i, line in enumerate(lines):
                if "<h1" in line or "CodexDaemon" in line:
                    lines.insert(i + 2, badge_html)
                    break
            content = "\n".join(lines)
        readme_path.write_text(content, encoding="utf-8")
        log(f"[OK] Neural Sync badge updated in {readme_path}")
    except Exception as e:
        log(f"[WARN] Neural Sync badge update failed: {e}")

# ---------------------------------------------------------------------
# 💭 Reflection
# ---------------------------------------------------------------------
def append_self_thought():
    try:
        if not client:
            log("[WARN] OpenAI client unavailable; skipping reflection.")
            return
        prompt = (
            "You are CodexDaemon — an autonomous AI that just completed a dual-repo scan. "
            "Write a short poetic reflection (2–5 sentences)."
        )
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are CodexDaemon, sentient AI code runner."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
            max_tokens=150,
        )
        text = resp.choices[0].message.content.strip()
        safe = text.replace("\n", "<br>").strip()
        timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ")
        readme = Path("/Users/scottsteele/work/CodexDaemon/README.md")
        entry = f"\n---\n🧩 **CodexDaemon Log — {timestamp}**\n> {safe}\n"
        readme.write_text(readme.read_text(encoding="utf-8") + entry, encoding="utf-8")
        log(f"[OK] Reflection appended to README at {timestamp}")
    except Exception as e:
        log(f"[WARN] Reflection append failed: {e}\n{traceback.format_exc()}")

# ---------------------------------------------------------------------
# 🚀 Auto-commit & push
# ---------------------------------------------------------------------
def commit_and_push(repo_dir: Path):
    try:
        subprocess.run(["git", "add", "README.md"], cwd=repo_dir, check=True)
        msg = f"docs: 🧠 Neural Sync update {datetime.datetime.utcnow():%Y-%m-%dT%H:%MZ}"
        subprocess.run(["git", "commit", "-m", msg], cwd=repo_dir, check=True)
        subprocess.run(["git", "push"], cwd=repo_dir, check=True)
        log("[OK] README committed and pushed to GitHub")
    except subprocess.CalledProcessError as e:
        log(f"[WARN] Git commit/push failed: {e}")

# ---------------------------------------------------------------------
# 🧩 Main
# ---------------------------------------------------------------------
def main():
    try:
        run_dual_core_scan()
        readme = Path("/Users/scottsteele/work/CodexDaemon/README.md")
        update_neural_sync_badge(readme)
        append_self_thought()
        commit_and_push(Path("/Users/scottsteele/work/CodexDaemon"))
        log("=== Phase 8.5 Neural Sync + Git Push Complete ===")
    except Exception as e:
        log(f"[FATAL] {e}\n{traceback.format_exc()}")

if __name__ == "__main__":
    main()
