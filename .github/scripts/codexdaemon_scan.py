#!/usr/bin/env python3
import os
from datetime import datetime
from pathlib import Path

# === Setup ===
repo_root = Path(__file__).resolve().parent.parent.parent
readme_path = repo_root / "README.md"
log_dir = repo_root / ".codex" / "logs"
timestamp = datetime.utcnow().isoformat() + "Z"

# === Logging Output ===
print(f"[CodexDaemon] 🧠 Starting scan @ {timestamp}")
print(f"[CodexDaemon] 📂 Repo root: {repo_root}")
print(f"[CodexDaemon] 📄 README path: {readme_path}")
print(f"[CodexDaemon] 📁 Log dir path: {log_dir}")

# === Heartbeat Injection into README.md ===
try:
    if not readme_path.exists():
        raise FileNotFoundError("README.md not found at expected location.")

    heartbeat_line = f"\n<!-- heartbeat: {timestamp} -->\n"
    with readme_path.open("a", encoding="utf-8") as f:
        f.write(heartbeat_line)

    print(f"[CodexDaemon] ✅ Heartbeat injected into README.md")
except Exception as e:
    print(f"[CodexDaemon] ❌ Failed to update README.md: {e}")
    exit(1)

# === Optional: Write a log file ===
try:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{timestamp}.log"
    with log_file.open("w", encoding="utf-8") as f:
        f.write(f"# CodexDaemon Scan Log\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write("Status: ✅ Scan completed successfully\n")

    print(f"[CodexDaemon] 📝 Log written to {log_file.relative_to(repo_root)}")
except Exception as e:
    print(f"[CodexDaemon] ⚠️ Could not write log file: {e}")
    # Non-fatal

print("[CodexDaemon] 🚀 Scan complete. Ready for commit.")
