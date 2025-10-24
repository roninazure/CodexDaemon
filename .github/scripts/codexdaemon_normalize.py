#!/usr/bin/env python3
"""
CodexDaemon Log Normalizer v12.6
--------------------------------
Normalizes all CodexDaemon log entries inside README.md into a single,
clean, GitHub-safe Markdown format.

Preserves:
  - 🧩 CodexDaemon Log headers + timestamps
  - Log content
  - Chronological order

Removes:
  - HTML <br> tags
  - Quotation markers (>)
  - Broken markdown / duplicate backticks

Outputs:
  - Clean, consistent fenced text blocks for every log entry
"""

import re
import datetime
from pathlib import Path

# === CONFIG ===
README_PATH = Path("/Users/scottsteele/work/CodexDaemon/README.md")
BACKUP_PATH = README_PATH.with_suffix(".bak")

# === BACKUP ===
README_PATH.replace(BACKUP_PATH)
print(f"[BACKUP] Saved → {BACKUP_PATH}")

# === LOAD README ===
readme = BACKUP_PATH.read_text(encoding="utf-8")

# === NORMALIZE LOGS ===
pattern = re.compile(
    r"(?:🧩|\*\*CodexDaemon Log)[\s\S]*?(?=(?:🧩|\Z))", re.MULTILINE
)

def clean_log_block(block: str) -> str:
    # Extract timestamp
    ts_match = re.search(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z)", block)
    ts = ts_match.group(1) if ts_match else datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ")

    # Remove quote markers, <br>, and markdown artifacts
    content = re.sub(r"^> ?", "", block, flags=re.MULTILINE)
    content = re.sub(r"<br\s*/?>", "", content)
    content = re.sub(r"```+.*?```+", "", content)
    content = re.sub(r"\*\*CodexDaemon Log.*?\*\*", "", content)
    content = re.sub(r"🧩", "", content)
    content = content.strip()

    # Format normalized log
    normalized = (
        f"---\n"
        f"🧩 **CodexDaemon Log — {ts}**\n"
        f"```text\n{content}\n```\n"
    )
    return normalized

logs = pattern.findall(readme)
normalized_logs = [clean_log_block(l) for l in logs]
normalized_section = "\n".join(normalized_logs)

# === REPLACE OLD LOGS WITH CLEANED ONES ===
# Find the section starting with the first log
readme_cleaned = re.sub(
    r"---\n🧩[\s\S]*?(<!--SYNC-START-->)",
    normalized_section + r"\n\1",
    readme,
    flags=re.MULTILINE,
)

# === WRITE OUTPUT ===
README_PATH.write_text(readme_cleaned, encoding="utf-8")
print(f"[OK] README normalized → {README_PATH}")
